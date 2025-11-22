#!/usr/bin/env python3
"""
News Scenario Simulator - Interactive CLI

Compare prediction market odds with AI-powered Monte Carlo simulations.
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

load_dotenv()

console = Console()


def display_markets(markets: list, formatted_markets: list) -> None:
    """Display markets in a nice table."""
    table = Table(title="Polymarket - Active Markets", show_lines=True)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Question", style="white", max_width=50)
    table.add_column("Yes", style="green", justify="right", width=6)
    table.add_column("Volume", style="yellow", justify="right", width=12)

    for i, m in enumerate(formatted_markets, 1):
        question = m["question"]
        if len(question) > 50:
            question = question[:47] + "..."
        table.add_row(
            str(i),
            question,
            f"{m['yes_odds']:.0%}",
            f"${m['volume']:,.0f}"
        )

    console.print(table)


async def run_simulation(market: dict) -> None:
    """Run simulation for selected market."""
    from src.orchestrator import run_pipeline
    from src.sandbox.runner import create_sandbox

    question = market["question"]
    yes_odds = market["yes_odds"]

    console.print(f"\n[bold]Selected:[/bold] {question}")
    console.print(f"[bold]Market odds:[/bold] {yes_odds:.0%} Yes")

    # Ask for number of runs
    n_runs = IntPrompt.ask(
        "\nNumber of Monte Carlo runs",
        default=200,
        console=console
    )

    console.print()

    # Run the pipeline with progress indicators
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Creating sandbox...", total=None)

        from src.sandbox.runner import create_sandbox
        from src.mcp_clients.perplexity_client import search
        from src.generator.generator import generate_model_async
        from src.sandbox.retry import execute_monte_carlo
        from src.viz.plotter import create_chart

        # Create sandbox (with MCP for Perplexity)
        sbx = await create_sandbox()
        loop = asyncio.get_event_loop()

        try:
            # Research
            progress.update(task, description="Researching with Perplexity...")
            research_query = f"""
            Provide current data and context for this prediction market question:
            "{question}"
            Include recent news, key statistics, expert opinions, and factors that could influence the outcome.
            """
            research = await search(sbx, research_query)

            # Generate model
            progress.update(task, description="Generating simulation model...")
            code = await generate_model_async(
                question=question,
                yes_odds=yes_odds,
                research=research
            )

            # Save generated code locally for debugging
            debug_path = os.path.join(os.path.dirname(__file__), '..', 'debug_model.py')
            with open(debug_path, 'w') as f:
                f.write(code)
            console.print(f"[dim]Model saved to: {debug_path}[/dim]")

            # Load fallback
            fallback_path = os.path.join(
                os.path.dirname(__file__),
                'models',
                'economic_shock.py'
            )
            fallback_code = None
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r') as f:
                    fallback_code = f.read()

            # Execute Monte Carlo
            progress.update(task, description=f"Running Monte Carlo ({n_runs} runs)...")
            result = await execute_monte_carlo(
                sbx=sbx,
                code=code,
                n_runs=n_runs,
                max_retries=5,
                fallback_code=fallback_code
            )

            if not result.success:
                console.print(f"\n[red]Error:[/red] {result.error}")
                return

            # Create visualization
            progress.update(task, description="Creating visualization...")
            simulation_data = {
                "probability": result.probability,
                "ci_95": result.ci_95,
                "n_runs": result.n_runs,
                "results": result.results
            }
            html = create_chart(simulation_data, yes_odds, question)

            # Save results locally
            progress.update(task, description="Saving results...")
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = Path(__file__).parent.parent / "results" / session_id
            results_dir.mkdir(parents=True, exist_ok=True)

            # Save HTML chart
            html_path = results_dir / "result.html"
            html_path.write_text(html)

            # Copy generated model
            model_path = results_dir / "model.py"
            debug_model_path = Path(__file__).parent.parent / "debug_model.py"
            if debug_model_path.exists():
                model_path.write_text(debug_model_path.read_text())

            url = f"file://{html_path.absolute()}"

        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")
            sbx.kill()
            return

    # Display results
    diff = result.probability - yes_odds
    diff_sign = "+" if diff > 0 else ""

    results_panel = Panel(
        f"[bold green]Simulation:[/bold green] {result.probability:.0%} ± {result.ci_95:.0%}\n"
        f"[bold blue]Market:[/bold blue] {yes_odds:.0%}\n"
        f"[bold]Difference:[/bold] {diff_sign}{diff*100:.1f}pp\n"
        f"\n{'[yellow]Used fallback model[/yellow]' if result.used_fallback else ''}",
        title="Results",
        border_style="green" if abs(diff) < 0.1 else "yellow"
    )
    console.print(results_panel)

    console.print(f"\n[bold green]Results saved to:[/bold green] {results_dir}")
    console.print(f"[bold green]View chart:[/bold green] {url}")

    sbx.kill()


async def main_menu():
    """Main menu loop."""
    from src.mcp_clients.polymarket import get_markets, format_for_llm, select_high_volume_markets

    console.print(Panel.fit(
        "[bold]News Scenario Simulator[/bold]\n"
        "Compare Polymarket odds with AI-powered Monte Carlo simulations",
        border_style="blue"
    ))

    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("  1. List markets")
        console.print("  2. Run simulation")
        console.print("  3. Quit")

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"], default="1")

        if choice == "1":
            # Fetch and display markets
            with console.status("Fetching markets from Polymarket..."):
                markets = get_markets(limit=50)
                high_volume = select_high_volume_markets(markets, min_volume=10000)
                formatted = [format_for_llm(m) for m in high_volume[:15]]

            if not formatted:
                console.print("[yellow]No markets found[/yellow]")
                continue

            display_markets(high_volume[:15], formatted)

        elif choice == "2":
            # Fetch markets first
            with console.status("Fetching markets..."):
                markets = get_markets(limit=50)
                high_volume = select_high_volume_markets(markets, min_volume=10000)
                formatted = [format_for_llm(m) for m in high_volume[:15]]

            if not formatted:
                console.print("[yellow]No markets found[/yellow]")
                continue

            display_markets(high_volume[:15], formatted)

            # Select market
            market_num = IntPrompt.ask(
                "\nSelect market number",
                default=1,
                console=console
            )

            if market_num < 1 or market_num > len(formatted):
                console.print("[red]Invalid selection[/red]")
                continue

            market = formatted[market_num - 1]

            # Run simulation
            await run_simulation(market)

        elif choice == "3":
            console.print("\n[dim]Goodbye![/dim]")
            break


def main():
    """Entry point."""
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
