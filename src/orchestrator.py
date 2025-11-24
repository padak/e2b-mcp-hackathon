"""
Orchestrator - connects all components for the News Scenario Simulator.

Flow: Polymarket → Perplexity Research → Generate → Execute → Visualize
"""

import os
import asyncio
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SimulationRun:
    """Result of a complete simulation run."""
    question: str
    market_odds: float
    simulation_probability: float
    ci_95: float
    n_runs: int
    results: list
    html_chart: str
    used_fallback: bool = False
    error: Optional[str] = None


async def run_pipeline(
    market: dict,
    n_runs: int = 200,
    max_retries: int = 5,
    verbose: bool = True
) -> SimulationRun:
    """
    Run the complete simulation pipeline.

    Args:
        market: Market data from Polymarket (formatted with format_for_llm)
        n_runs: Number of Monte Carlo runs
        max_retries: Maximum code fix retries
        verbose: Print progress messages

    Returns:
        SimulationRun with all results
    """
    from src.sandbox.runner import create_sandbox
    from src.mcp_clients.perplexity_client import search
    from src.generator.generator import generate_model_async
    from src.sandbox.retry import execute_monte_carlo
    from src.viz.plotter import create_chart

    question = market["question"]
    yes_odds = market["yes_odds"]

    if verbose:
        print(f"Starting pipeline for: {question}")

    # Create sandbox
    if verbose:
        print("Creating E2B sandbox...")
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        # Step 1: Research with Perplexity
        if verbose:
            print("Researching with Perplexity...")

        research_query = f"""
        Provide current data and context for this prediction market question:
        "{question}"

        Include:
        - Recent news and developments
        - Key statistics and data points
        - Expert opinions and forecasts
        - Historical context
        - Factors that could influence the outcome
        """

        research = await search(sbx, research_query)

        if verbose:
            print(f"Research gathered: {len(research)} characters")

        # Step 2: Generate simulation model
        if verbose:
            print("Generating simulation model with Claude...")

        code = await generate_model_async(
            question=question,
            yes_odds=yes_odds,
            research=research
        )

        if verbose:
            print(f"Generated code: {len(code)} characters")

        # Step 3: Load fallback model
        fallback_path = os.path.join(
            os.path.dirname(__file__),
            'models',
            'economic_shock.py'
        )
        fallback_code = None
        if os.path.exists(fallback_path):
            with open(fallback_path, 'r') as f:
                fallback_code = f.read()

        # Step 4: Execute Monte Carlo simulation
        if verbose:
            print(f"Running Monte Carlo simulation ({n_runs} runs)...")

        result = await execute_monte_carlo(
            sbx=sbx,
            code=code,
            n_runs=n_runs,
            max_retries=max_retries,
            fallback_code=fallback_code,
            simulation_mode=os.getenv("SIMULATION_MODE", "probability")
        )

        if not result.success:
            return SimulationRun(
                question=question,
                market_odds=yes_odds,
                simulation_probability=0,
                ci_95=0,
                n_runs=0,
                results=[],
                html_chart="",
                error=result.error
            )

        if verbose:
            print(f"Simulation complete: {result.probability:.1%} ± {result.ci_95:.1%}")
            if result.used_fallback:
                print("(Used fallback model)")

        # Step 5: Create visualization
        if verbose:
            print("Creating visualization...")

        simulation_data = {
            "probability": result.probability,
            "ci_95": result.ci_95,
            "n_runs": result.n_runs,
            "results": result.results
        }

        html = create_chart(
            simulation=simulation_data,
            market_odds=yes_odds,
            title=question
        )

        return SimulationRun(
            question=question,
            market_odds=yes_odds,
            simulation_probability=result.probability,
            ci_95=result.ci_95,
            n_runs=result.n_runs,
            results=result.results,
            html_chart=html,
            used_fallback=result.used_fallback
        )

    finally:
        sbx.kill()


async def serve_result(sbx, html: str, port: int = 8080) -> str:
    """
    Serve HTML result from E2B sandbox.

    Args:
        sbx: E2B sandbox instance
        html: HTML content to serve
        port: Port to serve on

    Returns:
        Public URL to access the result
    """
    loop = asyncio.get_event_loop()

    # Write HTML to file
    await loop.run_in_executor(
        None, lambda: sbx.files.write('/tmp/result.html', html)
    )

    # Start HTTP server in background
    await loop.run_in_executor(
        None, lambda: sbx.commands.run(
            f'python -m http.server {port} -d /tmp',
            background=True
        )
    )

    # Get public host
    host = sbx.get_host(port)
    return f"https://{host}/result.html"


async def run_quick_test():
    """Quick test of the orchestrator with a mock market."""
    from src.mcp_clients.polymarket import get_markets, format_for_llm

    print("Fetching markets...")
    markets = get_markets(limit=5)

    if not markets:
        print("No markets found!")
        return

    market = format_for_llm(markets[0])
    print(f"\nSelected market: {market['question']}")
    print(f"Current odds: {market['yes_odds']:.0%}")

    result = await run_pipeline(market, n_runs=50, verbose=True)

    if result.error:
        print(f"\nError: {result.error}")
    else:
        print(f"\nResult:")
        print(f"  Simulation: {result.simulation_probability:.0%} ± {result.ci_95:.0%}")
        print(f"  Market: {result.market_odds:.0%}")
        diff = result.simulation_probability - result.market_odds
        print(f"  Difference: {diff*100:+.1f}pp")

        # Save chart
        with open('/tmp/result.html', 'w') as f:
            f.write(result.html_chart)
        print(f"\nChart saved to /tmp/result.html")


if __name__ == "__main__":
    asyncio.run(run_quick_test())
