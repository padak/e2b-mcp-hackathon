"""End-to-end test using OpenAI SDK against OpenRouter API."""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from arena.runner.tools import TOOL_DEFINITIONS
from arena.runner.hooks import create_tool_handler
from arena.runner.prompts import get_system_prompt, get_user_prompt


def convert_tools_to_openai_format(tools: list) -> list:
    """Convert Anthropic-style tools to OpenAI function calling format."""
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
        })
    return openai_tools


def test_direct_mode():
    """Test direct mode with OpenRouter via OpenAI SDK."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set, skipping")
        return None

    # Create OpenAI client pointing to OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # Setup
    handler, run_log = create_tool_handler(
        question_id="test-coin",
        model_id="openai/gpt-4o-mini",
        mode="direct",
        trial=1,
    )

    system_prompt = get_system_prompt("direct")
    user_prompt = get_user_prompt(
        mode="direct",
        question="Will a fair coin flip land heads?",
        description="A fair coin is flipped once. Market resolves Yes if heads.",
        market_id="test-coin",
        volume=1000,
        closed_time="2024-12-01",
    )

    # Only submit_prediction tool for direct mode
    tools = convert_tools_to_openai_format([
        t for t in TOOL_DEFINITIONS if t["name"] == "submit_prediction"
    ])

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    print("\n=== Direct Mode Test ===")
    print(f"Question: Will a fair coin flip land heads?")

    for turn in range(5):
        print(f"\nTurn {turn + 1}/5")

        # Force tool use on first turn, auto after
        choice = "required" if turn == 0 else "auto"
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice=choice,
            max_tokens=1024,
        )

        msg = response.choices[0].message

        # Add assistant message
        messages.append(msg.model_dump())

        # Check for text
        if msg.content:
            print(f"Assistant: {msg.content[:200]}...")

        # Check for tool calls
        if msg.tool_calls:
            tool_results = []
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                print(f"Tool call: {fn_name}({fn_args})")

                result = handler.handle_tool_call(fn_name, fn_args)
                print(f"  Result: {result}")

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

                if result.get("stop"):
                    print("\n✓ Prediction submitted!")
                    run_log.finalize()
                    return run_log

            messages.extend(tool_results)
        else:
            # No tool call and stop reason is "stop"
            if response.choices[0].finish_reason == "stop":
                print("Model stopped without prediction")
                break

    run_log.finalize()
    return run_log


def test_simulation_mode():
    """Test simulation mode with OpenRouter via OpenAI SDK."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set, skipping")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    handler, run_log = create_tool_handler(
        question_id="test-rain",
        model_id="openai/gpt-4o-mini",
        mode="simulation",
        trial=1,
    )

    system_prompt = get_system_prompt("simulation")
    user_prompt = get_user_prompt(
        mode="simulation",
        question="What is the probability of getting exactly 3 heads in 5 fair coin flips?",
        description="Calculate using simulation or formula. Market resolves based on mathematical probability.",
        market_id="test-binomial",
        volume=10000,
        closed_time="2024-12-01",
    )

    # All tools for simulation mode
    tools = convert_tools_to_openai_format(TOOL_DEFINITIONS)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    print("\n=== Simulation Mode Test ===")
    print(f"Question: P(exactly 3 heads in 5 flips)?")
    print(f"Expected: ~0.3125 (binomial)")

    for turn in range(8):
        print(f"\nTurn {turn + 1}/8")

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=2048,
        )

        msg = response.choices[0].message
        messages.append(msg.model_dump())

        if msg.content:
            print(f"Assistant: {msg.content[:150]}...")

        if msg.tool_calls:
            tool_results = []
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)

                if fn_name == "execute_code":
                    print(f"Tool call: execute_code")
                    print(f"  Code: {fn_args.get('code', '')[:100]}...")
                else:
                    print(f"Tool call: {fn_name}({fn_args})")

                result = handler.handle_tool_call(fn_name, fn_args)

                if fn_name == "execute_code":
                    print(f"  Success: {result.get('success')}")
                    if result.get('output'):
                        print(f"  Output: {result['output'][:100]}")
                    if result.get('error'):
                        print(f"  Error: {result['error'][:100]}")
                else:
                    print(f"  Result: {result}")

                tool_results.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

                if result.get("stop"):
                    print("\n✓ Prediction submitted!")
                    run_log.finalize()
                    return run_log

            messages.extend(tool_results)
        else:
            if response.choices[0].finish_reason == "stop":
                print("Model stopped without prediction")
                break

    run_log.finalize()
    return run_log


if __name__ == "__main__":
    print("=" * 60)
    print("E2E Test: Arena Runner with OpenRouter (OpenAI SDK)")
    print("=" * 60)

    # Test 1: Direct mode
    direct_log = test_direct_mode()
    if direct_log and direct_log.prediction:
        print(f"\nDirect Mode Result: {direct_log.prediction['probability']:.2%}")
        print(f"Reasoning: {direct_log.prediction['reasoning']}")

    print("\n" + "=" * 60)

    # Test 2: Simulation mode
    sim_log = test_simulation_mode()
    if sim_log and sim_log.prediction:
        print(f"\nSimulation Mode Result: {sim_log.prediction['probability']:.2%}")
        print(f"Reasoning: {sim_log.prediction['reasoning']}")
        print(f"\nMetrics:")
        print(f"  execute_code calls: {sim_log.metrics.execute_code_calls}")
        print(f"  first_try_success: {sim_log.metrics.first_try_success}")
        print(f"  heal_rate: {sim_log.metrics.heal_rate}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if direct_log and direct_log.prediction:
        print(f"Direct:     {direct_log.prediction['probability']:.2%}")
    if sim_log and sim_log.prediction:
        print(f"Simulation: {sim_log.prediction['probability']:.2%} (expected ~31.25%)")
