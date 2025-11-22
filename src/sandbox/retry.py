"""
Retry loop and Monte Carlo execution for E2B sandbox.
"""

import os
from dataclasses import dataclass
from typing import Optional
from e2b import AsyncSandbox
from dotenv import load_dotenv

load_dotenv()


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


async def execute_with_retry(
    sbx: AsyncSandbox,
    code: str,
    max_retries: int = 5,
    fallback_code: Optional[str] = None
) -> ExecutionResult:
    """
    Execute code in E2B sandbox with retry on error.

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
    from src.generator.fixer import fix_code

    current_code = code
    last_error = None

    for attempt in range(max_retries):
        # Write code to sandbox
        await sbx.files.write('/tmp/simulation.py', current_code)

        # Execute
        result = await sbx.commands.run('python3 /tmp/simulation.py', timeout=120)

        if result.exit_code == 0:
            # Success - parse output
            return ExecutionResult(
                success=True,
                output=result.stdout,
                error=None
            )

        # Error - try to fix
        last_error = result.stderr or result.stdout
        print(f"Attempt {attempt + 1}/{max_retries} failed: {last_error[:200]}...")

        if attempt < max_retries - 1:
            # Ask LLM to fix the code
            current_code = await fix_code(current_code, last_error)

    # All retries failed - use fallback if provided
    if fallback_code:
        print("All retries failed, using fallback model...")
        await sbx.files.write('/tmp/simulation.py', fallback_code)
        result = await sbx.commands.run('python3 /tmp/simulation.py', timeout=120)

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


async def execute_monte_carlo(
    sbx: AsyncSandbox,
    code: str,
    n_runs: int = 200,
    max_retries: int = 5,
    fallback_code: Optional[str] = None
) -> ExecutionResult:
    """
    Execute Monte Carlo simulation with retry loop.

    The code must define a run_trial(seed: int) -> bool function.
    This wrapper runs it n_runs times and aggregates results.

    Args:
        sbx: E2B sandbox instance
        code: Python code with run_trial function
        n_runs: Number of Monte Carlo runs
        max_retries: Maximum retry attempts
        fallback_code: Fallback code if all retries fail

    Returns:
        ExecutionResult with aggregated probability
    """
    # Wrap the code with Monte Carlo runner
    monte_carlo_wrapper = f'''
{code}

# Monte Carlo execution
import json

results = []
for seed in range({n_runs}):
    try:
        outcome = run_trial(seed)
        results.append(1 if outcome else 0)
    except Exception as e:
        print(f"Trial {{seed}} failed: {{e}}", file=__import__('sys').stderr)
        results.append(0)

probability = sum(results) / len(results)
ci_95 = 1.96 * (probability * (1 - probability) / {n_runs}) ** 0.5 if 0 < probability < 1 else 0

output = {{
    "probability": probability,
    "n_runs": {n_runs},
    "results": results,
    "ci_95": ci_95
}}
print(json.dumps(output))
'''

    # Also prepare fallback wrapper if provided
    fallback_wrapped = None
    if fallback_code:
        fallback_wrapped = f'''
{fallback_code}

# Monte Carlo execution
import json

results = []
for seed in range({n_runs}):
    try:
        outcome = run_trial(seed)
        results.append(1 if outcome else 0)
    except Exception as e:
        results.append(0)

probability = sum(results) / len(results)
ci_95 = 1.96 * (probability * (1 - probability) / {n_runs}) ** 0.5 if 0 < probability < 1 else 0

output = {{
    "probability": probability,
    "n_runs": {n_runs},
    "results": results,
    "ci_95": ci_95
}}
print(json.dumps(output))
'''

    # Execute with retry
    result = await execute_with_retry(sbx, monte_carlo_wrapper, max_retries, fallback_wrapped)

    if result.success:
        # Parse the JSON output
        import json
        try:
            data = json.loads(result.output.strip())
            result.probability = data["probability"]
            result.ci_95 = data["ci_95"]
            result.n_runs = data["n_runs"]
            result.results = data["results"]
        except json.JSONDecodeError:
            result.success = False
            result.error = f"Failed to parse output: {result.output}"

    return result
