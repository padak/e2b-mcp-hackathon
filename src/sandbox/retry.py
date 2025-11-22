"""
Retry loop and Monte Carlo execution for E2B sandbox.
"""

import os
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from e2b_code_interpreter import Sandbox
from e2b.sandbox.commands.command_handle import CommandExitException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('e2b-retry')


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    probability: Optional[float] = None
    ci_95: Optional[float] = None
    n_runs: int = 0
    results: Optional[list] = None
    used_fallback: bool = False


def execute_with_retry_sync(
    sbx: Sandbox,
    code: str,
    max_retries: int = 5,
    fallback_code: Optional[str] = None
) -> ExecutionResult:
    """
    Execute code in E2B sandbox with retry on error (sync version).

    On error, sends error + code to LLM for fix.
    Returns success result or fallback to reference model.

    Args:
        sbx: E2B sandbox instance
        code: Python code to execute
        max_retries: Maximum number of retry attempts
        fallback_code: Optional fallback code if all retries fail

    Returns:
        ExecutionResult with output or error
    """
    from src.generator.fixer import fix_code_sync

    current_code = code
    last_error = None

    for attempt in range(max_retries):
        # Write code to sandbox - use unique filename to avoid permission issues
        filename = f'/tmp/simulation_{attempt}.py'
        sbx.files.write(filename, current_code)

        # Execute - catch exception on non-zero exit
        try:
            result = sbx.commands.run(f'python3 {filename}', timeout=120)

            if result.exit_code == 0:
                # Success - parse output
                return ExecutionResult(
                    success=True,
                    output=result.stdout,
                    error=None
                )

            # Non-zero exit without exception
            last_error = result.stderr or result.stdout

        except CommandExitException as e:
            # E2B raises this on non-zero exit
            last_error = str(e)

        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error[:300]}...")

        if attempt < max_retries - 1:
            # Ask LLM to fix the code
            logger.info(f"Calling fixer to repair code...")
            current_code = fix_code_sync(current_code, last_error)
            logger.info(f"Fixer returned {len(current_code)} chars of code")

    # All retries failed - use fallback if provided
    if fallback_code:
        logger.warning("All retries failed, using fallback model...")
        sbx.files.write('/tmp/simulation.py', fallback_code)
        result = sbx.commands.run('python3 /tmp/simulation.py', timeout=120)

        if result.exit_code == 0:
            return ExecutionResult(
                success=True,
                output=result.stdout,
                error=None,
                used_fallback=True
            )

    # Complete failure
    return ExecutionResult(
        success=False,
        output="",
        error=last_error
    )


async def execute_with_retry(
    sbx: Sandbox,
    code: str,
    max_retries: int = 5,
    fallback_code: Optional[str] = None
) -> ExecutionResult:
    """Async wrapper for execute_with_retry_sync."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, execute_with_retry_sync, sbx, code, max_retries, fallback_code
    )


def run_monte_carlo(run_trial_results: list[bool], n_runs: int = 200) -> dict:
    """
    Aggregate Monte Carlo results into probability with confidence interval.

    Args:
        run_trial_results: List of boolean results from trials
        n_runs: Number of runs performed

    Returns:
        Dictionary with probability, CI, and raw results
    """
    results = [1 if r else 0 for r in run_trial_results]
    probability = sum(results) / len(results) if results else 0

    # 95% confidence interval using normal approximation
    if probability > 0 and probability < 1:
        ci_95 = 1.96 * (probability * (1 - probability) / n_runs) ** 0.5
    else:
        ci_95 = 0

    return {
        "probability": probability,
        "n_runs": n_runs,
        "results": results,
        "ci_95": ci_95
    }


def execute_monte_carlo_sync(
    sbx: Sandbox,
    code: str,
    n_runs: int = 200,
    max_retries: int = 5,
    fallback_code: Optional[str] = None
) -> ExecutionResult:
    """
    Execute Monte Carlo simulation with retry loop (sync version).

    The code should be a complete simulation that prints JSON output
    with keys: probability, n_runs, results, ci_95

    Args:
        sbx: E2B sandbox instance
        code: Complete Python simulation code
        n_runs: Number of Monte Carlo runs (for fallback only)
        max_retries: Maximum retry attempts
        fallback_code: Fallback code if all retries fail

    Returns:
        ExecutionResult with aggregated probability
    """
    # Execute the generated code directly (it already has run_monte_carlo)
    result = execute_with_retry_sync(sbx, code, max_retries, fallback_code)

    if result.success:
        # Parse the JSON output
        import json
        try:
            # Find the JSON in output (might have other prints)
            output_lines = result.output.strip().split('\n')
            json_line = output_lines[-1]  # JSON should be last line
            data = json.loads(json_line)
            result.probability = data["probability"]
            result.ci_95 = data["ci_95"]
            result.n_runs = data["n_runs"]
            result.results = data["results"]
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            result.success = False
            result.error = f"Failed to parse output: {result.output[:500]}... Error: {e}"

    return result


async def execute_monte_carlo(
    sbx: Sandbox,
    code: str,
    n_runs: int = 200,
    max_retries: int = 5,
    fallback_code: Optional[str] = None
) -> ExecutionResult:
    """Async wrapper for execute_monte_carlo_sync."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, execute_monte_carlo_sync, sbx, code, n_runs, max_retries, fallback_code
    )
