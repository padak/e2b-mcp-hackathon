#!/usr/bin/env python3
"""Test script to regenerate chart for a single simulation."""

import json
import sys
import os
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.viz.plotter import create_dashboard

# Load the Bitcoin simulation results
result_dir = "results/top10_volume_20251122_004541/08_will-bitcoin-reach-150-000-by-december-3"

# Import the model.py dynamically
spec = importlib.util.spec_from_file_location("model", f"{result_dir}/model.py")
model_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_module)

# Run simulation
print("Running Monte Carlo simulation...")
sim_result = model_module.run_monte_carlo(n_runs=200, threshold=model_module.THRESHOLD, mode="threshold")
print(f"Simulation complete: {sim_result['probability']:.0%}")

# Market data (extracted from the question context - Bitcoin $150k by Dec 31)
market = {
    "question": "Will Bitcoin reach $150,000 by December 31, 2025?",
    "yes_odds": 0.03  # From the screenshot showing Market: 3%
}

# Build model info from the model
model_info = {
    "name": "Agent-Based Monte Carlo Simulation",
    "description": f"Simulates {sum(model_module.AGENT_CONFIG.values())} agents across {len(model_module.AGENT_CONFIG)} types to model the probability of the predicted outcome based on agent interactions and behaviors.",
    "agents": [
        {"name": cls.__name__, "count": count}
        for cls, count in model_module.AGENT_CONFIG.items()
    ],
    "parameters": model_module.MODEL_PARAMS
}

# Create dashboard
html = create_dashboard(
    simulation=sim_result,
    market_odds=market["yes_odds"],
    title=market["question"],
    model_info=model_info
)

# Save result
output_path = f"{result_dir}/result.html"
with open(output_path, "w") as f:
    f.write(html)

print(f"Chart saved to: {output_path}")
