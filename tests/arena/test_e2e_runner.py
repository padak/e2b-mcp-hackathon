"""End-to-end test of arena runner against real OpenRouter API."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from arena.runner import ArenaRunner


def test_direct_mode_real_api():
    """Test direct mode against real OpenRouter API."""

    # Check for API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set, skipping")
        return

    # Use OpenRouter directly (no local router needed for this test)
    # Note: Anthropic SDK adds /v1/messages, so base_url should NOT include /v1
    runner = ArenaRunner(
        model_id="openai/gpt-4o-mini",  # Cheap model for testing
        api_base_url="https://openrouter.ai/api",
        max_turns=5,
    )

    # Set the API key for OpenRouter
    os.environ["ANTHROPIC_API_KEY"] = api_key

    result = runner.run(
        question="Will a coin flip land heads?",
        description="A fair coin is flipped once. Market resolves Yes if heads.",
        market_id="test-coin-flip",
        volume=1000,
        closed_time="2024-12-01",
        mode="direct",
        trial=1,
    )

    print("\n=== Direct Mode Result ===")
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration_s']:.2f}s")
    print(f"Tool calls: {result['tool_calls']}")

    if result['prediction']:
        print(f"Prediction: {result['prediction']['probability']:.2%}")
        print(f"Reasoning: {result['prediction']['reasoning'][:200]}...")
    else:
        print(f"No prediction - Error: {result.get('error')}")

    print(f"\nMetrics: {result['metrics']}")

    return result


def test_simulation_mode_real_api():
    """Test simulation mode against real OpenRouter API."""

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set, skipping")
        return

    runner = ArenaRunner(
        model_id="openai/gpt-4o-mini",
        api_base_url="https://openrouter.ai/api",
        max_turns=8,
    )

    os.environ["ANTHROPIC_API_KEY"] = api_key

    result = runner.run(
        question="Will it rain in London tomorrow?",
        description="Market resolves Yes if measurable precipitation (>0.1mm) falls in central London.",
        market_id="test-london-rain",
        volume=50000,
        closed_time="2024-12-01",
        mode="simulation",
        trial=1,
    )

    print("\n=== Simulation Mode Result ===")
    print(f"Success: {result['success']}")
    print(f"Duration: {result['duration_s']:.2f}s")
    print(f"Tool calls: {result['tool_calls']}")

    if result['prediction']:
        print(f"Prediction: {result['prediction']['probability']:.2%}")
        print(f"Reasoning: {result['prediction']['reasoning'][:200]}...")
    else:
        print(f"No prediction - Error: {result.get('error')}")

    print(f"\nMetrics: {result['metrics']}")

    # Show tool call details
    if result['log']['tool_calls']:
        print("\n--- Tool Calls ---")
        for tc in result['log']['tool_calls']:
            print(f"  {tc['tool_name']}: success={tc['success']}, duration={tc['duration_ms']:.0f}ms")
            if tc['tool_name'] == 'execute_code' and tc['output']:
                print(f"    Output: {tc['output'][:100]}...")

    return result


if __name__ == "__main__":
    print("Testing Arena Runner with OpenRouter API")
    print("=" * 50)

    print("\n1. Testing Direct Mode (reasoning only)...")
    direct_result = test_direct_mode_real_api()

    print("\n" + "=" * 50)
    print("\n2. Testing Simulation Mode (with code execution)...")
    sim_result = test_simulation_mode_real_api()

    print("\n" + "=" * 50)
    print("\nSUMMARY:")
    if direct_result and direct_result.get('prediction'):
        print(f"  Direct Mode: {direct_result['prediction']['probability']:.2%}")
    if sim_result and sim_result.get('prediction'):
        print(f"  Simulation Mode: {sim_result['prediction']['probability']:.2%}")
