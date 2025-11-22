"""E2B Sandbox runner with MCP Gateway support."""

import os
import asyncio
import logging
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('e2b-runner')


def create_sandbox_sync(verbose: bool = True) -> Sandbox:
    """Create E2B sandbox with Perplexity MCP enabled (sync version).

    Args:
        verbose: Enable detailed logging

    Returns:
        Sandbox with MCP gateway configured
    """
    if verbose:
        logger.info("Creating E2B sandbox with MCP gateway...")
        logger.debug(f"PERPLEXITY_API_KEY present: {bool(os.getenv('PERPLEXITY_API_KEY'))}")
        logger.debug(f"E2B_API_KEY present: {bool(os.getenv('E2B_API_KEY'))}")

    try:
        sbx = Sandbox.create(
            template="mesa-mcp-gateway",
            timeout=300,  # 5 minutes
            mcp={
                "perplexityAsk": {
                    "perplexityApiKey": os.getenv("PERPLEXITY_API_KEY"),
                },
            }
        )

        if verbose:
            logger.info(f"Sandbox created: {sbx.sandbox_id}")
            mcp_url = sbx.get_mcp_url()
            logger.info(f"MCP Gateway URL: {mcp_url}")

        return sbx

    except Exception as e:
        logger.error(f"Failed to create sandbox: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        raise


async def create_sandbox(verbose: bool = True) -> Sandbox:
    """Create E2B sandbox with Perplexity MCP enabled (async wrapper).

    Args:
        verbose: Enable detailed logging

    Returns:
        Sandbox with MCP gateway configured
    """
    # Run sync creation in thread pool
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, create_sandbox_sync, verbose)


def create_sandbox_without_mcp_sync(verbose: bool = True) -> Sandbox:
    """Create E2B sandbox without MCP (for code execution only).

    Args:
        verbose: Enable detailed logging

    Returns:
        Sandbox for code execution
    """
    if verbose:
        logger.info("Creating E2B sandbox with mesa-mcp-gateway template...")

    sbx = Sandbox.create(template="mesa-mcp-gateway", timeout=300)

    if verbose:
        logger.info(f"Sandbox created: {sbx.sandbox_id}")

    return sbx


async def create_sandbox_without_mcp(verbose: bool = True) -> Sandbox:
    """Create E2B sandbox without MCP (async wrapper).

    Args:
        verbose: Enable detailed logging

    Returns:
        Sandbox for code execution
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, create_sandbox_without_mcp_sync, verbose)


def install_dependencies_sync(sbx: Sandbox, verbose: bool = True):
    """Install Mesa and other dependencies in sandbox.

    Args:
        sbx: E2B sandbox instance
        verbose: Enable logging
    """
    if verbose:
        logger.info("Installing dependencies (mesa, numpy, pandas, plotly)...")

    result = sbx.commands.run(
        "pip install -q mesa==2.1.5 numpy pandas plotly",
        timeout=120
    )

    if result.exit_code != 0:
        logger.error(f"Failed to install dependencies: {result.stderr}")
        raise RuntimeError(f"Dependency installation failed: {result.stderr}")

    if verbose:
        logger.info("Dependencies installed successfully")


def calibrate_threshold_sync(
    sbx: Sandbox,
    model_code: str,
    n_calibration: int = 50,
    verbose: bool = True
) -> dict:
    """Run calibration to find optimal threshold.

    Args:
        sbx: E2B sandbox instance
        model_code: Python code with SimulationModel class
        n_calibration: Number of calibration runs
        verbose: Enable logging

    Returns:
        dict with min, max, mean, std, suggested_threshold
    """
    import json
    import numpy as np

    if verbose:
        logger.info(f"Running calibration with {n_calibration} runs...")

    # Code to run calibration in sandbox
    calibration_code = f'''
import json
import numpy as np

{model_code}

# Run calibration
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
    "std": float(np.std(outcomes)),
    "suggested_threshold": float(np.mean(outcomes))
}}
print(json.dumps(calibration))
'''

    # Execute in sandbox
    result = sbx.run_code(calibration_code)

    if result.error:
        logger.error(f"Calibration failed: {result.error}")
        # Return default calibration
        return {
            "min": 0.0,
            "max": 1.0,
            "mean": 0.5,
            "std": 0.25,
            "suggested_threshold": 0.5,
            "error": str(result.error)
        }

    # Get output from logs.stdout
    output = ""
    if result.logs and result.logs.stdout:
        output = "".join(result.logs.stdout).strip()
    elif result.text:
        output = result.text.strip()

    if not output:
        logger.error("Calibration produced no output")
        return {
            "min": 0.0,
            "max": 1.0,
            "mean": 0.5,
            "std": 0.25,
            "suggested_threshold": 0.5,
            "error": "No output from calibration"
        }

    try:
        calibration = json.loads(output)
        if verbose:
            logger.info(f"Calibration results: min={calibration['min']:.3f}, "
                       f"max={calibration['max']:.3f}, mean={calibration['mean']:.3f}, "
                       f"std={calibration['std']:.3f}")
        return calibration
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse calibration result: {e}")
        return {
            "min": 0.0,
            "max": 1.0,
            "mean": 0.5,
            "std": 0.25,
            "suggested_threshold": 0.5,
            "error": f"Parse error: {e}"
        }


def run_monte_carlo_sync(
    sbx: Sandbox,
    model_code: str,
    n_runs: int = 200,
    threshold: float = None,
    auto_calibrate: bool = True,
    n_calibration: int = 50,
    verbose: bool = True,
    install_deps: bool = False  # mesa-mcp-gateway template has deps pre-installed
) -> dict:
    """Run Monte Carlo simulation with optional auto-calibration.

    Args:
        sbx: E2B sandbox instance
        model_code: Python code with SimulationModel class
        n_runs: Number of Monte Carlo runs
        threshold: User-specified threshold (None = auto-calibrate)
        auto_calibrate: Whether to run calibration first
        n_calibration: Number of calibration runs
        verbose: Enable logging
        install_deps: Whether to install dependencies first

    Returns:
        dict with probability, ci_95, results, calibration info
    """
    import json

    # Install dependencies if needed
    if install_deps:
        install_dependencies_sync(sbx, verbose)

    calibration = None

    # Auto-calibrate if no threshold specified
    if threshold is None and auto_calibrate:
        calibration = calibrate_threshold_sync(sbx, model_code, n_calibration, verbose)
        threshold = calibration["suggested_threshold"]
        if verbose:
            logger.info(f"Using auto-calibrated threshold: {threshold:.3f}")
    elif threshold is None:
        threshold = 0.5
        if verbose:
            logger.info(f"Using default threshold: {threshold}")
    else:
        if verbose:
            logger.info(f"Using user-specified threshold: {threshold}")

    # Run full Monte Carlo
    if verbose:
        logger.info(f"Running Monte Carlo with {n_runs} runs...")

    monte_carlo_code = f'''
import json

{model_code}

# Override threshold
THRESHOLD = {threshold}

results = run_monte_carlo(n_runs={n_runs}, threshold=THRESHOLD)
print(json.dumps(results))
'''

    result = sbx.run_code(monte_carlo_code)

    if result.error:
        logger.error(f"Monte Carlo failed: {result.error}")
        return {
            "probability": 0.0,
            "n_runs": n_runs,
            "results": [],
            "ci_95": 0.0,
            "threshold_used": threshold,
            "calibration": calibration,
            "error": str(result.error)
        }

    # Get output from logs.stdout
    output = ""
    if result.logs and result.logs.stdout:
        output = "".join(result.logs.stdout).strip()
    elif result.text:
        output = result.text.strip()

    if not output:
        logger.error("Monte Carlo produced no output")
        return {
            "probability": 0.0,
            "n_runs": n_runs,
            "results": [],
            "ci_95": 0.0,
            "threshold_used": threshold,
            "calibration": calibration,
            "error": "No output from Monte Carlo"
        }

    try:
        mc_results = json.loads(output)
        mc_results["threshold_used"] = threshold
        mc_results["calibration"] = calibration

        if verbose:
            logger.info(f"Monte Carlo results: probability={mc_results['probability']:.1%} "
                       f"± {mc_results['ci_95']:.1%}")

        return mc_results
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Monte Carlo result: {e}")
        return {
            "probability": 0.0,
            "n_runs": n_runs,
            "results": [],
            "ci_95": 0.0,
            "threshold_used": threshold,
            "calibration": calibration,
            "error": f"Parse error: {e}"
        }


async def calibrate_threshold(
    sbx: Sandbox,
    model_code: str,
    n_calibration: int = 50,
    verbose: bool = True
) -> dict:
    """Async wrapper for calibrate_threshold_sync."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, calibrate_threshold_sync, sbx, model_code, n_calibration, verbose
    )


async def run_monte_carlo(
    sbx: Sandbox,
    model_code: str,
    n_runs: int = 200,
    threshold: float = None,
    auto_calibrate: bool = True,
    n_calibration: int = 50,
    verbose: bool = True,
    install_deps: bool = False  # mesa-mcp-gateway template has deps pre-installed
) -> dict:
    """Async wrapper for run_monte_carlo_sync."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, run_monte_carlo_sync, sbx, model_code, n_runs, threshold,
        auto_calibrate, n_calibration, verbose, install_deps
    )


async def test_sandbox():
    """Test E2B sandbox with MCP gateway."""
    sbx = await create_sandbox()

    try:
        # 2.2 Test MCP connection
        mcp_url = sbx.get_mcp_url()
        mcp_token = await sbx.get_mcp_token()
        print(f"MCP Gateway URL: {mcp_url}")
        print(f"MCP Token: {mcp_token[:20]}...")

        # 2.3 Test code execution via commands
        result = await sbx.commands.run('python3 -c "print(\'Hello from E2B\')"')
        print(f"Code execution: {result.stdout}")

        # 2.4 Test Mesa installation and import
        print("Installing Mesa, plotly, pandas, numpy...")
        await sbx.commands.run('pip install mesa==2.1.5 plotly pandas numpy', timeout=120)

        result = await sbx.commands.run('''python3 -c "
from mesa import Agent, Model
import pandas as pd
import numpy as np
print('Mesa, pandas, numpy imported successfully!')
"''')
        print(f"Mesa test: {result.stdout}")

        return True

    finally:
        await sbx.kill()


async def test_perplexity_mcp():
    """Test Perplexity search via MCP gateway."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.mcp_clients.perplexity_client import create_mcp_client, search

    sbx = await create_sandbox()

    try:
        print("Connecting to MCP gateway...")
        async with create_mcp_client(sbx) as session:
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

        # Test search
        print("\nSearching for Fed interest rate decision...")
        result = await search(sbx, "Fed interest rate decision December 2024")
        print(f"Search result:\n{result[:500]}..." if len(result) > 500 else f"Search result:\n{result}")

        return True

    finally:
        await sbx.kill()


async def test_economic_model():
    """Test economic shock model in E2B sandbox."""
    # Use code-interpreter-v1 for Python 3.12 (no MCP needed for model)
    sbx = await AsyncSandbox.create(
        template="code-interpreter-v1",
        timeout=300,
    )

    try:
        # Install dependencies from requirements.txt
        print("Installing dependencies...")
        req_path = os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt')
        with open(req_path, 'r') as f:
            req_content = f.read()
        await sbx.files.write('/tmp/requirements.txt', req_content)
        await sbx.commands.run('pip install -r /tmp/requirements.txt', timeout=120)

        # Check installed version
        ver = await sbx.commands.run('pip show mesa | grep Version')
        print(f"Mesa version: {ver.stdout}")

        # Read and upload the model code
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'economic_shock.py')
        with open(model_path, 'r') as f:
            model_code = f.read()

        # Write model to sandbox
        await sbx.files.write('/tmp/economic_shock.py', model_code)

        # Run the model test
        print("Running economic shock model in E2B...")
        result = await sbx.commands.run('python3 /tmp/economic_shock.py', timeout=60)

        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")

        return True

    finally:
        await sbx.kill()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        asyncio.run(test_perplexity_mcp())
    elif len(sys.argv) > 1 and sys.argv[1] == "model":
        asyncio.run(test_economic_model())
    else:
        asyncio.run(test_sandbox())
