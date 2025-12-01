"""Arena Runner - Main entry point for LLM evaluation.

This module runs inside E2B sandbox and handles:
1. Setting up the LLM client (OpenAI SDK -> OpenRouter)
2. Running the agent loop with tools
3. Collecting metrics and returning results

Usage (inside E2B sandbox):
    python arena_runner.py \
        --question "Will X happen?" \
        --description "Market resolves Yes if..." \
        --market-id "sample-1" \
        --volume 1000000 \
        --closed-time "2024-12-01" \
        --mode simulation \
        --model "openai/gpt-4o"
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Optional

# These imports work when running as a script
try:
    from tools import TOOL_DEFINITIONS, SIMULATION_TOOL_DEFINITIONS, DIRECT_TOOL_DEFINITIONS, REASONING_TOOL_DEFINITIONS, ToolMetrics
    from hooks import create_tool_handler, RunLog
    from prompts import get_system_prompt, get_user_prompt
except ImportError:
    # When imported as a module
    from .tools import TOOL_DEFINITIONS, SIMULATION_TOOL_DEFINITIONS, DIRECT_TOOL_DEFINITIONS, REASONING_TOOL_DEFINITIONS, ToolMetrics
    from .hooks import create_tool_handler, RunLog
    from .prompts import get_system_prompt, get_user_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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


class ArenaRunner:
    """Runs LLM agent evaluation for a single question."""

    def __init__(
        self,
        model_id: str,
        api_base_url: str = "https://openrouter.ai/api/v1",
        api_key: Optional[str] = None,
        max_turns: int = 10,
        max_budget_usd: float = 5.0,
    ):
        """Initialize the arena runner.

        Args:
            model_id: Model ID for OpenRouter (e.g., "openai/gpt-4o")
            api_base_url: Base URL for OpenRouter API
            api_key: OpenRouter API key (or from OPENROUTER_API_KEY env var)
            max_turns: Maximum conversation turns before timeout
            max_budget_usd: Maximum budget per run (not enforced by OpenRouter)
        """
        self.model_id = model_id
        self.api_base_url = api_base_url
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.max_turns = max_turns
        self.max_budget_usd = max_budget_usd

        if not self.api_key:
            raise ValueError("API key required. Set OPENROUTER_API_KEY or pass api_key")

    def run(
        self,
        question: str,
        description: str,
        market_id: str,
        volume: float,
        closed_time: str,
        mode: str,
        trial: int = 1,
    ) -> dict:
        """Run a single evaluation.

        Args:
            question: The prediction market question
            description: Detailed description
            market_id: Market identifier
            volume: Trading volume
            closed_time: When market closed
            mode: "direct" or "simulation"
            trial: Trial number

        Returns:
            Dictionary with results and metrics
        """
        start_time = time.time()

        # Create tool handler and run log
        handler, run_log = create_tool_handler(
            question_id=market_id,
            model_id=self.model_id,
            mode=mode,
            trial=trial,
        )

        try:
            # Get prompts
            system_prompt = get_system_prompt(mode)
            user_prompt = get_user_prompt(
                mode=mode,
                question=question,
                description=description,
                market_id=market_id,
                volume=volume,
                closed_time=closed_time,
            )

            # Run the agent loop
            self._run_agent_loop(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                handler=handler,
                run_log=run_log,
            )

            run_log.finalize()

            # Calculate duration
            duration_s = time.time() - start_time

            return {
                "success": run_log.prediction is not None,
                "prediction": run_log.prediction,
                "metrics": run_log.metrics.to_dict(),
                "duration_s": duration_s,
                "tool_calls": len(run_log.tool_calls),
                "log": run_log.to_dict(),
                "error": run_log.error,
            }

        except Exception as e:
            run_log.error = str(e)
            run_log.finalize()

            return {
                "success": False,
                "error": str(e),
                "prediction": None,
                "metrics": run_log.metrics.to_dict(),
                "duration_s": time.time() - start_time,
                "log": run_log.to_dict(),
            }

    def _run_agent_loop(
        self,
        system_prompt: str,
        user_prompt: str,
        handler,
        run_log: RunLog,
    ) -> None:
        """Run the agent conversation loop using OpenAI SDK.

        Uses OpenAI-compatible API format for OpenRouter.
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

        # Create OpenAI client pointing to OpenRouter
        client = OpenAI(
            base_url=self.api_base_url,
            api_key=self.api_key,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Determine which tools to provide based on mode
        if run_log.mode == "direct":
            # Direct mode only gets submit_prediction
            tools_list = DIRECT_TOOL_DEFINITIONS
        elif run_log.mode == "reasoning":
            # Reasoning mode gets execute_code, install_package, submit_prediction (no Mesa)
            tools_list = REASONING_TOOL_DEFINITIONS
        else:
            # Simulation mode gets all tools including generate_mesa_model
            tools_list = SIMULATION_TOOL_DEFINITIONS

        tools = convert_tools_to_openai_format(tools_list)

        for turn in range(self.max_turns):
            logger.info(f"Turn {turn + 1}/{self.max_turns}")

            try:
                # Force tool use on first turn for ALL modes
                # GPT-4o-mini tends to just output text without calling tools
                if turn == 0:
                    tool_choice = "required"
                else:
                    tool_choice = "auto"

                # Make API call
                response = client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    max_tokens=4096,
                )

                # Record token usage if available
                if response.usage:
                    run_log.metrics.record_tokens(
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        model_id=self.model_id,
                    )

                # Defensive checks for malformed API responses
                if not response.choices:
                    logger.error("Empty choices in API response")
                    run_log.error = "API returned empty choices"
                    return

                msg = response.choices[0].message
                if msg is None:
                    logger.error("Null message in API response")
                    run_log.error = "API returned null message"
                    return

                # Add assistant message to history
                messages.append(msg.model_dump())

                # Log text response
                if msg.content:
                    logger.info(f"Assistant: {msg.content[:200]}...")

                # Process tool calls
                if msg.tool_calls:
                    tool_results = []
                    should_stop = False

                    for tc in msg.tool_calls:
                        # Defensive check for malformed tool calls
                        if tc.function is None:
                            logger.warning("Null function in tool call, skipping")
                            continue
                        fn_name = tc.function.name
                        fn_args = json.loads(tc.function.arguments or "{}")

                        logger.info(f"Tool call: {fn_name}")
                        result = handler.handle_tool_call(fn_name, fn_args)

                        # Check if we should stop (prediction submitted)
                        if result.get("stop"):
                            should_stop = True

                        # Add tool result to messages
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result),
                        })

                    messages.extend(tool_results)

                    if should_stop:
                        logger.info("Prediction submitted, stopping")
                        return

                else:
                    # No tool calls - check if model stopped
                    if response.choices[0].finish_reason == "stop":
                        logger.warning("Model stopped without submitting prediction")
                        run_log.error = "Model stopped without submitting prediction"
                        return

            except Exception as e:
                logger.error(f"API error: {e}")
                run_log.error = f"API error: {e}"
                return

        # Reached max turns without prediction
        logger.warning("No prediction submitted after max turns")
        run_log.error = "No prediction submitted after max turns"


def main():
    """Main entry point for arena runner."""
    parser = argparse.ArgumentParser(description="Run arena evaluation")
    parser.add_argument("--question", required=True, help="Market question")
    parser.add_argument("--description", default="", help="Market description")
    parser.add_argument("--market-id", required=True, help="Market ID")
    parser.add_argument("--volume", type=float, default=0, help="Trading volume")
    parser.add_argument("--closed-time", default="", help="When market closed")
    parser.add_argument(
        "--mode",
        choices=["direct", "simulation", "reasoning"],
        required=True,
        help="Evaluation mode",
    )
    parser.add_argument("--model", required=True, help="Model ID (e.g., openai/gpt-4o)")
    parser.add_argument("--trial", type=int, default=1, help="Trial number")
    parser.add_argument(
        "--api-base",
        default="https://openrouter.ai/api/v1",
        help="API base URL",
    )
    parser.add_argument("--api-key", default=None, help="API key (or set OPENROUTER_API_KEY)")
    parser.add_argument("--max-turns", type=int, default=10, help="Max conversation turns")
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")

    args = parser.parse_args()

    # Create runner
    runner = ArenaRunner(
        model_id=args.model,
        api_base_url=args.api_base,
        api_key=args.api_key,
        max_turns=args.max_turns,
    )

    # Run evaluation
    result = runner.run(
        question=args.question,
        description=args.description,
        market_id=args.market_id,
        volume=args.volume,
        closed_time=args.closed_time,
        mode=args.mode,
        trial=args.trial,
    )

    # Output result
    output_json = json.dumps(result, indent=2)

    if args.output == "-":
        print(output_json)
    else:
        with open(args.output, "w") as f:
            f.write(output_json)
        logger.info(f"Result written to {args.output}")


if __name__ == "__main__":
    main()
