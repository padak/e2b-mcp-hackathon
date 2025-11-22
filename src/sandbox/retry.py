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
    fallback_code: Optional[str] = None,
    filename_prefix: str = "simulation"
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
        filename = f'/tmp/{filename_prefix}_{attempt}.py'
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
    fallback_code: Optional[str] = None,
    auto_calibrate: bool = True,
    n_calibration: int = 50
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
        auto_calibrate: Whether to auto-calibrate threshold
        n_calibration: Number of calibration runs

    Returns:
        ExecutionResult with aggregated probability
    """
    import re
    import json as json_module

    current_code = code

    # Auto-calibrate threshold if enabled
    if auto_calibrate:
        logger.info(f"Running calibration with {n_calibration} runs...")

        # Create calibration code - replaces the main block to output calibration data
        calibration_code = re.sub(
            r'if __name__ == "__main__":\s*\n\s*results = run_monte_carlo\([^)]+\)\s*\n\s*print\(json\.dumps\(results\)\)',
            f'''if __name__ == "__main__":
    import numpy as np
    outcomes = []
    for seed in range({n_calibration}):
        model = SimulationModel(seed=seed)
        for _ in range(100):
            model.step()
        results = model.get_results()
        outcomes.append(results["final_outcome"])
    calibration = {{
        "min": float(min(outcomes)),
        "max": float(max(outcomes)),
        "mean": float(np.mean(outcomes)),
        "std": float(np.std(outcomes))
    }}
    print(json.dumps(calibration))''',
            code
        )

        # Run calibration
        cal_result = execute_with_retry_sync(sbx, calibration_code, max_retries=3, fallback_code=None, filename_prefix="calibration")

        if cal_result.success:
            try:
                output_lines = cal_result.output.strip().split('\n')
                cal_data = json_module.loads(output_lines[-1])
                logger.info(f"Calibration: min={cal_data['min']:.3f}, max={cal_data['max']:.3f}, "
                           f"mean={cal_data['mean']:.3f}, std={cal_data['std']:.3f}")

                # Check for degenerate case (no variance)
                if cal_data['std'] < 0.001:
                    logger.warning(f"No variance in calibration (std={cal_data['std']:.3f}), fixing model...")
                    from src.generator.fixer import fix_model_variance_sync

                    # Fix the model
                    current_code = fix_model_variance_sync(code, cal_data)
                    logger.info(f"Variance fixer returned {len(current_code)} chars of code")

                    # Re-run calibration with fixed code
                    calibration_code = re.sub(
                        r'if __name__ == "__main__":\s*\n\s*results = run_monte_carlo\([^)]+\)\s*\n\s*print\(json\.dumps\(results\)\)',
                        f'''if __name__ == "__main__":
    import numpy as np
    outcomes = []
    for seed in range({n_calibration}):
        model = SimulationModel(seed=seed)
        for _ in range(100):
            model.step()
        results = model.get_results()
        outcomes.append(results["final_outcome"])
    calibration = {{
        "min": float(min(outcomes)),
        "max": float(max(outcomes)),
        "mean": float(np.mean(outcomes)),
        "std": float(np.std(outcomes))
    }}
    print(json.dumps(calibration))''',
                        current_code
                    )

                    cal_result2 = execute_with_retry_sync(sbx, calibration_code, max_retries=3, fallback_code=None, filename_prefix="calibration_fixed")

                    if cal_result2.success:
                        try:
                            output_lines2 = cal_result2.output.strip().split('\n')
                            cal_data2 = json_module.loads(output_lines2[-1])
                            logger.info(f"Re-calibration: min={cal_data2['min']:.3f}, max={cal_data2['max']:.3f}, "
                                       f"mean={cal_data2['mean']:.3f}, std={cal_data2['std']:.3f}")

                            # If still low variance, use threshold slightly below mean
                            if cal_data2['std'] < 0.01:
                                calibrated_threshold = cal_data2["mean"] - 0.01
                                logger.warning(f"Still low variance after fix, using threshold={calibrated_threshold:.3f}")
                            else:
                                calibrated_threshold = cal_data2["mean"]
                        except:
                            calibrated_threshold = 0.5
                    else:
                        calibrated_threshold = 0.5
                else:
                    calibrated_threshold = cal_data["mean"]

                logger.info(f"Using calibrated threshold: {calibrated_threshold:.3f}")

                # Update threshold in code
                current_code = re.sub(
                    r'THRESHOLD\s*=\s*[\d.]+',
                    f'THRESHOLD = {calibrated_threshold}',
                    code
                )
            except Exception as e:
                logger.warning(f"Calibration parsing failed: {e}, using original threshold")
        else:
            logger.warning(f"Calibration failed: {cal_result.error}, using original threshold")

    # Execute the generated code (with calibrated threshold if successful)
    result = execute_with_retry_sync(sbx, current_code, max_retries, fallback_code)

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

            # Log final results
            yes_count = sum(result.results)
            no_count = result.n_runs - yes_count
            logger.info(f"Monte Carlo complete: {result.probability:.1%} ± {result.ci_95:.1%} "
                       f"({yes_count} yes / {no_count} no)")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            result.success = False
            result.error = f"Failed to parse output: {result.output[:500]}... Error: {e}"

    return result


async def execute_monte_carlo(
    sbx: Sandbox,
    code: str,
    n_runs: int = 200,
    max_retries: int = 5,
    fallback_code: Optional[str] = None,
    auto_calibrate: bool = True,
    n_calibration: int = 50
) -> ExecutionResult:
    """Async wrapper for execute_monte_carlo_sync."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, lambda: execute_monte_carlo_sync(
            sbx, code, n_runs, max_retries, fallback_code, auto_calibrate, n_calibration
        )
    )
