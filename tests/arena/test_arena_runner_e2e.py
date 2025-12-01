"""Quick E2E test of the refactored ArenaRunner."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from arena.runner import ArenaRunner


def test_runner_direct():
    """Test ArenaRunner in direct mode."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return

    runner = ArenaRunner(
        model_id="openai/gpt-4o-mini",
        api_key=api_key,
        max_turns=3,
    )

    result = runner.run(
        question="Will a fair coin flip land heads?",
        description="A fair coin is flipped. Resolves Yes if heads.",
        market_id="test-coin",
        volume=1000,
        closed_time="2024-12-01",
        mode="direct",
        trial=1,
    )

    print("=== Direct Mode ===")
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration_s']:.2f}s")
    if result['prediction']:
        print(f"Prediction: {result['prediction']['probability']:.2%}")
        print(f"Reasoning: {result['prediction']['reasoning'][:100]}...")
    else:
        print(f"Error: {result.get('error')}")

    return result


def test_runner_simulation():
    """Test ArenaRunner in simulation mode."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return

    runner = ArenaRunner(
        model_id="openai/gpt-4o-mini",
        api_key=api_key,
        max_turns=5,
    )

    result = runner.run(
        question="What is P(exactly 3 heads in 5 fair coin flips)?",
        description="Calculate probability. Expected: ~31.25%",
        market_id="test-binomial",
        volume=10000,
        closed_time="2024-12-01",
        mode="simulation",
        trial=1,
    )

    print("\n=== Simulation Mode ===")
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration_s']:.2f}s")
    print(f"Tool calls: {result['tool_calls']}")
    print(f"Metrics: first_try={result['metrics']['first_try_success']}, "
          f"execute_calls={result['metrics']['execute_code_calls']}")
    if result['prediction']:
        print(f"Prediction: {result['prediction']['probability']:.2%} (expected ~31.25%)")
        print(f"Reasoning: {result['prediction']['reasoning'][:100]}...")
    else:
        print(f"Error: {result.get('error')}")

    return result


if __name__ == "__main__":
    print("Testing refactored ArenaRunner\n")
    test_runner_direct()
    test_runner_simulation()
