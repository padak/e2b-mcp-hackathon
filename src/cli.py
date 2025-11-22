#!/usr/bin/env python3
"""
News Scenario Simulator - Interactive CLI with Batch Mode

Compare prediction market odds with AI-powered Monte Carlo simulations.
"""

import asyncio
import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.live import Live
from dotenv import load_dotenv

load_dotenv()

console = Console()

# Categories for breaking news
CATEGORIES = {
    "1": ("politics", "Politics"),
    "2": ("world", "World"),
    "3": ("sports", "Sports"),
    "4": ("crypto", "Crypto"),
    "5": ("finance", "Finance"),
    "6": ("tech", "Tech"),
    "7": ("culture", "Culture"),
}


def display_markets(markets: list, title: str, show_change: bool = False) -> None:
    """Display markets in a Rich table."""
    table = Table(title=title, show_lines=True)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Question", style="white")
    table.add_column("Yes", style="green", justify="right", width=6)

    if show_change:
        table.add_column("24h", style="yellow", justify="right", width=8)
    else:
        table.add_column("Volume", style="yellow", justify="right", width=12)

    for i, m in enumerate(markets, 1):
        question = m.get("question", "Unknown")

        # Get odds
        outcome_prices = m.get("outcomePrices", [])
        if isinstance(outcome_prices, str):
            import json
            try:
                outcome_prices = json.loads(outcome_prices)
            except:
                outcome_prices = []

        yes_odds = float(outcome_prices[0]) * 100 if outcome_prices else 50

        if show_change:
            change = m.get("oneDayPriceChange", 0) * 100
            change_str = f"{change:+.0f}%"
            table.add_row(str(i), question, f"{yes_odds:.0f}%", change_str)
        else:
            volume = float(m.get("volumeNum") or m.get("volume") or 0)
            table.add_row(str(i), question, f"{yes_odds:.0f}%", f"${volume:,.0f}")

    console.print(table)


def format_market_for_sim(market: dict) -> dict:
    """Format market data for simulation."""
    import json

    outcome_prices = market.get("outcomePrices", [])
    if isinstance(outcome_prices, str):
        try:
            outcome_prices = json.loads(outcome_prices)
        except:
            outcome_prices = []

    yes_price = float(outcome_prices[0]) if outcome_prices else 0.5
    volume = float(market.get("volumeNum") or market.get("volume") or 0)

    return {
        "question": market.get("question", "Unknown"),
        "yes_odds": yes_price,
        "volume": volume,
        "slug": market.get("slug", ""),
    }


def slugify(text: str, max_len: int = 40) -> str:
    """Convert text to URL-safe slug."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:max_len]


def extract_model_info(code: str, question: str) -> dict:
    """Extract agent and parameter info from generated code."""
    info = {"agents": [], "parameters": {}}

    # Extract AGENT_CONFIG
    config_match = re.search(r'AGENT_CONFIG\s*=\s*\{([^}]+)\}', code)
    if config_match:
        config_str = config_match.group(1)
        for line in config_str.split(','):
            match = re.search(r'(\w+):\s*(\d+)', line)
            if match:
                agent_name = match.group(1)
                count = int(match.group(2))
                info["agents"].append({"name": agent_name, "count": count})

    # Extract MODEL_PARAMS
    params_match = re.search(r'MODEL_PARAMS\s*=\s*\{([^}]+)\}', code)
    if params_match:
        params_str = params_match.group(1)
        for line in params_str.split(','):
            match = re.search(r'"(\w+)":\s*([^,\n]+)', line)
            if match:
                key = match.group(1)
                value = match.group(2).strip()
                info["parameters"][key] = value

    # Generate name and description
    if info["agents"]:
        total_agents = sum(a["count"] for a in info["agents"])
        agent_types = len(info["agents"])
        info["name"] = "Agent-Based Monte Carlo Simulation"
        info["description"] = (
            f"Simulates {total_agents} agents across {agent_types} types to model "
            f"the probability of the predicted outcome based on agent interactions and behaviors."
        )

    return info


async def run_single_market(
    market: dict,
    results_dir: Path,
    n_runs: int = 100,
    progress_callback=None,
    market_index: int = 0
) -> dict:
    """Run simulation for a single market."""
    from src.sandbox.runner import create_sandbox
    from src.mcp_clients.perplexity_client import search
    from src.generator.generator import generate_model_async
    from src.sandbox.retry import execute_monte_carlo
    from src.viz.plotter import create_dashboard
    import io
    import sys

    formatted = format_market_for_sim(market)
    question = formatted["question"]
    yes_odds = formatted["yes_odds"]

    # Create market-specific directory with index to avoid collisions
    market_slug = f"{market_index:02d}_{slugify(question)}"
    market_dir = results_dir / market_slug
    market_dir.mkdir(parents=True, exist_ok=True)

    # Set up logging for this market
    log_buffer = io.StringIO()

    def log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_buffer.write(f"[{timestamp}] {msg}\n")

    log(f"Starting simulation for: {question[:60]}...")
    log(f"Market odds: {yes_odds:.0%}")

    sbx = await create_sandbox()
    log(f"Sandbox created: {sbx.sandbox_id}")

    try:
        # Research
        if progress_callback:
            progress_callback("research")

        log("Researching with Perplexity...")
        research_query = f"""
        Provide current data and context for this prediction market question:
        "{question}"
        Include recent news, key statistics, expert opinions, and factors that could influence the outcome.
        """
        research = await search(sbx, research_query)
        log(f"Research complete: {len(research)} chars")

        # Generate model
        if progress_callback:
            progress_callback("generate")

        log("Generating simulation model...")
        code = await generate_model_async(
            question=question,
            yes_odds=yes_odds,
            research=research
        )
        log(f"Model generated: {len(code)} chars")

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
        if progress_callback:
            progress_callback("simulate")

        log(f"Running Monte Carlo ({n_runs} runs)...")
        result = await execute_monte_carlo(
            sbx=sbx,
            code=code,
            n_runs=n_runs,
            max_retries=5,
            fallback_code=fallback_code
        )

        if not result.success:
            log(f"ERROR: {result.error}")
            # Save log even on failure
            (market_dir / "execution.log").write_text(log_buffer.getvalue())
            return {
                "market": formatted,
                "success": False,
                "error": result.error
            }

        log(f"Monte Carlo complete: {result.probability:.0%} (±{result.ci_95:.0%})")
        if result.outcome_mean is not None:
            log(f"Outcome stats: mean={result.outcome_mean:.3f}, std={result.outcome_std:.3f}")
            log(f"Outcome range: [{result.outcome_min:.3f}, {result.outcome_max:.3f}]")
        if result.used_fallback:
            log("WARNING: Used fallback model")

        # Create visualization
        if progress_callback:
            progress_callback("visualize")

        log("Creating visualization...")
        simulation_data = {
            "probability": result.probability,
            "ci_95": result.ci_95,
            "n_runs": result.n_runs,
            "results": result.results
        }
        model_info = extract_model_info(code, question)
        html = create_dashboard(simulation_data, yes_odds, question, model_info)

        # Save results
        log("Saving results...")
        (market_dir / "model.py").write_text(code)
        (market_dir / "result.html").write_text(html)
        (market_dir / "research.txt").write_text(research)

        # Save execution log
        log(f"Complete! Results saved to {market_dir}")
        (market_dir / "execution.log").write_text(log_buffer.getvalue())

        return {
            "market": formatted,
            "success": True,
            "probability": result.probability,
            "ci_95": result.ci_95,
            "used_fallback": result.used_fallback,
            "result_dir": str(market_dir)
        }

    except Exception as e:
        log(f"EXCEPTION: {str(e)}")
        # Save log on exception
        (market_dir / "execution.log").write_text(log_buffer.getvalue())
        return {
            "market": formatted,
            "success": False,
            "error": str(e)
        }
    finally:
        sbx.kill()


async def run_batch_simulation(markets: list, batch_name: str, n_runs: int = 100):
    """Run simulations for multiple markets in parallel."""
    from src.viz.plotter import create_batch_dashboard

    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent.parent / "results" / f"{batch_name}_{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold]Running batch simulation:[/bold] {len(markets)} markets")
    console.print(f"[dim]Results will be saved to: {results_dir}[/dim]\n")

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        overall_task = progress.add_task(
            f"[cyan]Simulating {len(markets)} markets...",
            total=len(markets)
        )

        # Run all markets in parallel
        tasks = []
        for i, market in enumerate(markets, 1):
            task = run_single_market(market, results_dir, n_runs, market_index=i)
            tasks.append(task)

        # Gather results as they complete
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

            # Update progress
            market_name = result["market"]["question"][:30]
            if result["success"]:
                progress.console.print(f"  [green]✓[/green] {market_name}...")
            else:
                progress.console.print(f"  [red]✗[/red] {market_name}... ({result.get('error', 'Unknown error')[:50]})")

            progress.advance(overall_task)

    # Generate batch summary
    console.print("\n[bold]Generating batch summary...[/bold]")

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Create batch dashboard
    batch_html = create_batch_dashboard(results, batch_name)
    (results_dir / "summary.html").write_text(batch_html)

    # Save batch report JSON
    import json
    report = {
        "batch_name": batch_name,
        "timestamp": timestamp,
        "total_markets": len(markets),
        "successful": len(successful),
        "failed": len(failed),
        "results": results
    }
    (results_dir / "batch_report.json").write_text(json.dumps(report, indent=2, default=str))

    # Display summary
    console.print(f"\n[bold green]Batch complete![/bold green]")
    console.print(f"  Successful: {len(successful)}/{len(markets)}")
    if failed:
        console.print(f"  [red]Failed: {len(failed)}[/red]")

    console.print(f"\n[bold]Results saved to:[/bold] {results_dir}")
    console.print(f"[bold]Open summary:[/bold] file://{results_dir.absolute()}/summary.html")

    return results


async def run_single_simulation(market: dict):
    """Run simulation for a single market (legacy mode)."""
    from src.sandbox.runner import create_sandbox
    from src.mcp_clients.perplexity_client import search
    from src.generator.generator import generate_model_async
    from src.sandbox.retry import execute_monte_carlo
    from src.viz.plotter import create_dashboard

    formatted = format_market_for_sim(market)
    question = formatted["question"]
    yes_odds = formatted["yes_odds"]

    console.print(f"\n[bold]Selected:[/bold] {question}")
    console.print(f"[bold]Market odds:[/bold] {yes_odds:.0%} Yes")

    # Ask for number of runs
    n_runs = IntPrompt.ask(
        "\nNumber of Monte Carlo runs",
        default=200,
        console=console
    )

    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Creating sandbox...", total=None)

        sbx = await create_sandbox()

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
            generated_code = code

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
            model_info = extract_model_info(generated_code, question)
            html = create_dashboard(simulation_data, yes_odds, question, model_info)

            # Save results
            progress.update(task, description="Saving results...")
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = Path(__file__).parent.parent / "results" / session_id
            results_dir.mkdir(parents=True, exist_ok=True)

            html_path = results_dir / "result.html"
            html_path.write_text(html)

            model_path = results_dir / "model.py"
            model_path.write_text(generated_code)

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
    from src.mcp_clients.polymarket import (
        get_markets, format_for_llm, select_high_volume_markets,
        get_biggest_movers, search_markets
    )

    console.print(Panel.fit(
        "[bold]News Scenario Simulator[/bold]\n"
        "Compare Polymarket odds with AI-powered Monte Carlo simulations\n"
        "[dim]Batch Mode v2[/dim]",
        border_style="blue"
    ))

    while True:
        console.print("\n[bold]Breaking News Categories:[/bold]")
        for key, (_, name) in CATEGORIES.items():
            console.print(f"  {key}. {name}")

        console.print("\n[bold]Other Options:[/bold]")
        console.print("  8. Top 10 by Volume")
        console.print("  9. Custom Search")
        console.print("  0. Single Market (legacy)")
        console.print("  q. Quit")

        choice = Prompt.ask(
            "\nSelect option",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "q"],
            default="8"
        )

        if choice == "q":
            console.print("\n[dim]Goodbye![/dim]")
            break

        markets = []
        batch_name = ""
        show_change = False

        if choice in CATEGORIES:
            # Breaking news category
            category_id, category_name = CATEGORIES[choice]
            with console.status(f"Fetching {category_name} markets..."):
                markets = get_biggest_movers(category_id, 10)
            batch_name = category_id
            show_change = True
            title = f"{category_name.upper()} - Breaking News"

        elif choice == "8":
            # Top 10 by volume
            with console.status("Fetching top markets by volume..."):
                all_markets = get_markets(limit=50)
                markets = select_high_volume_markets(all_markets, min_volume=10000)[:10]
            batch_name = "top10_volume"
            title = "TOP 10 BY VOLUME"

        elif choice == "9":
            # Custom search
            query = Prompt.ask("\nEnter search query")
            if not query.strip():
                continue

            with console.status(f"Searching for '{query}'..."):
                markets = search_markets(query, 10)
            batch_name = f"search_{slugify(query)[:20]}"
            title = f"SEARCH: {query.upper()}"

        elif choice == "0":
            # Legacy single market mode
            with console.status("Fetching markets..."):
                all_markets = get_markets(limit=50)
                high_volume = select_high_volume_markets(all_markets, min_volume=10000)
                formatted = [format_for_llm(m) for m in high_volume[:15]]

            if not formatted:
                console.print("[yellow]No markets found[/yellow]")
                continue

            # Display markets
            table = Table(title="Polymarket - Active Markets", show_lines=True)
            table.add_column("#", style="cyan", width=3)
            table.add_column("Question", style="white", max_width=50)
            table.add_column("Yes", style="green", justify="right", width=6)
            table.add_column("Volume", style="yellow", justify="right", width=12)

            for i, m in enumerate(formatted, 1):
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

            # Select market
            market_num = IntPrompt.ask(
                "\nSelect market number",
                default=1,
                console=console
            )

            if market_num < 1 or market_num > len(formatted):
                console.print("[red]Invalid selection[/red]")
                continue

            # Run single simulation
            await run_single_simulation(high_volume[market_num - 1])
            continue

        # Display fetched markets
        if not markets:
            console.print("[yellow]No markets found[/yellow]")
            continue

        display_markets(markets, title, show_change=show_change)

        # Ask to run batch
        if Confirm.ask("\nRun batch simulation?", default=False):
            n_runs = IntPrompt.ask(
                "Monte Carlo runs per market",
                default=100,
                console=console
            )
            await run_batch_simulation(markets, batch_name, n_runs)


def main():
    """Entry point."""
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted[/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
