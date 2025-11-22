#!/usr/bin/env python3
"""Regenerate all charts in results/ with updated styling."""

import os
import re
import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.viz.plotter import create_dashboard

def extract_from_html(html_path):
    """Extract market odds and question from existing result.html."""
    with open(html_path, 'r') as f:
        content = f.read()

    # Extract market odds - try multiple formats
    market_match = re.search(r'Market: (\d+)%', content)
    if not market_match:
        # Try older format: "Market odds (Polymarket): 74%"
        market_match = re.search(r'Market odds \(Polymarket\): (\d+)%', content)
    if not market_match:
        # Try another format
        market_match = re.search(r'market_odds["\s:]+(\d+\.?\d*)', content)
    if not market_match:
        return None, None
    market_odds = float(market_match.group(1))
    if market_odds > 1:
        market_odds = market_odds / 100

    # Extract question from title (first text in <title> or the main title)
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if title_match:
        question = title_match.group(1).strip()
    else:
        # Try to get from the plot title
        question_match = re.search(r'"text":"([^"]+)"', content)
        question = question_match.group(1) if question_match else "Unknown Question"

    return question, market_odds

def regenerate_chart(result_dir):
    """Regenerate chart for a single result directory."""
    model_path = result_dir / "model.py"
    html_path = result_dir / "result.html"

    if not model_path.exists() or not html_path.exists():
        return False, "Missing model.py or result.html"

    # Extract data from existing HTML
    question, market_odds = extract_from_html(html_path)
    if market_odds is None:
        return False, "Could not extract market odds"

    # Import and run model
    try:
        spec = importlib.util.spec_from_file_location("model", str(model_path))
        model_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model_module)

        # Run simulation - handle both old and new signatures
        try:
            sim_result = model_module.run_monte_carlo(
                n_runs=200,
                threshold=model_module.THRESHOLD,
                mode="threshold"
            )
        except TypeError:
            # Old signature without mode
            sim_result = model_module.run_monte_carlo(
                n_runs=200,
                threshold=model_module.THRESHOLD
            )

        # Build model info
        model_info = {
            "name": "Agent-Based Monte Carlo Simulation",
            "description": f"Simulates {sum(model_module.AGENT_CONFIG.values())} agents across {len(model_module.AGENT_CONFIG)} types to model the probability of the predicted outcome based on agent interactions and behaviors.",
            "agents": [
                {"name": cls.__name__, "count": count}
                for cls, count in model_module.AGENT_CONFIG.items()
            ],
            "parameters": model_module.MODEL_PARAMS
        }

        # Create new dashboard
        html = create_dashboard(
            simulation=sim_result,
            market_odds=market_odds,
            title=question,
            model_info=model_info
        )

        # Save
        with open(html_path, "w") as f:
            f.write(html)

        return True, f"{sim_result['probability']:.0%}"

    except Exception as e:
        return False, str(e)

def main():
    results_dir = Path("results")

    # Find all batch directories
    batch_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()])

    total = 0
    success = 0

    for batch_dir in batch_dirs:
        # Find simulation result directories (those with model.py)
        sim_dirs = sorted([d for d in batch_dir.iterdir() if d.is_dir() and (d / "model.py").exists()])

        if not sim_dirs:
            continue

        print(f"\n{batch_dir.name}: {len(sim_dirs)} simulations")

        for sim_dir in sim_dirs:
            total += 1
            ok, msg = regenerate_chart(sim_dir)
            status = "✓" if ok else "✗"
            print(f"  {status} {sim_dir.name}: {msg}")
            if ok:
                success += 1

    print(f"\nDone: {success}/{total} charts regenerated")

if __name__ == "__main__":
    main()
