"""Arena tools for LLM agents.

These tools are provided to LLM agents during arena evaluation:
- execute_code: Run Python code and capture output
- install_package: Install pip packages
- submit_prediction: Submit final prediction (0.0 to 1.0)
- generate_mesa_model: Submit Mesa agent code for calibration + Monte Carlo
"""

import subprocess
import sys
import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExecutionResult:
    """Result of code execution."""

    stdout: str
    stderr: str
    exit_code: int
    success: bool


@dataclass
class ToolMetrics:
    """Metrics collected from tool usage."""

    execute_code_calls: int = 0
    execute_code_successes: int = 0
    execute_code_failures: int = 0
    install_package_calls: int = 0
    install_package_successes: int = 0
    total_execution_time_ms: float = 0.0
    first_try_success: Optional[bool] = None  # Was first execute_code successful?

    # MESA-specific metrics
    mesa_model_calls: int = 0
    mesa_model_successes: int = 0
    mesa_execution_errors: int = 0
    mesa_variance_fixes: int = 0
    calibration_std: Optional[float] = None
    calibration_threshold: Optional[float] = None

    # Token/cost tracking
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def record_execution(self, success: bool, time_ms: float) -> None:
        """Record an execute_code call."""
        if self.execute_code_calls == 0:
            self.first_try_success = success
        self.execute_code_calls += 1
        self.total_execution_time_ms += time_ms
        if success:
            self.execute_code_successes += 1
        else:
            self.execute_code_failures += 1

    def record_install(self, success: bool) -> None:
        """Record an install_package call."""
        self.install_package_calls += 1
        if success:
            self.install_package_successes += 1

    def record_mesa_model(self, success: bool, execution_error: bool = False,
                          variance_fix: bool = False) -> None:
        """Record a generate_mesa_model call."""
        self.mesa_model_calls += 1
        if success:
            self.mesa_model_successes += 1
        if execution_error:
            self.mesa_execution_errors += 1
        if variance_fix:
            self.mesa_variance_fixes += 1

    def record_calibration(self, std: float, threshold: float) -> None:
        """Record calibration results."""
        self.calibration_std = std
        self.calibration_threshold = threshold

    def record_tokens(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model_id: str = "",
    ) -> None:
        """Record token usage from API response.

        Args:
            prompt_tokens: Number of input/prompt tokens
            completion_tokens: Number of output/completion tokens
            model_id: Model ID for cost estimation
        """
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens

        # Estimate cost based on model
        self.estimated_cost_usd += self._estimate_cost(
            prompt_tokens, completion_tokens, model_id
        )

    def _estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model_id: str,
    ) -> float:
        """Estimate cost for tokens based on model pricing.

        Prices from OpenRouter (Dec 2024).
        """
        # Model pricing per 1M tokens
        pricing = {
            # OpenAI
            "openai/gpt-4o": (2.50, 10.00),
            "openai/gpt-4o-mini": (0.15, 0.60),
            # Anthropic
            "anthropic/claude-sonnet-4": (3.00, 15.00),
            "anthropic/claude-3.5-sonnet": (3.00, 15.00),
            "anthropic/claude-3-haiku": (0.25, 1.25),
            # Google (free tier)
            "google/gemini-2.0-flash-exp:free": (0.0, 0.0),
            "google/gemini-pro-1.5": (1.25, 5.00),
            # Meta (free)
            "meta-llama/llama-3.2-3b-instruct:free": (0.0, 0.0),
        }

        # Get pricing or use default
        input_price, output_price = pricing.get(model_id, (1.0, 2.0))

        input_cost = (prompt_tokens / 1_000_000) * input_price
        output_cost = (completion_tokens / 1_000_000) * output_price

        return input_cost + output_cost

    @property
    def heal_rate(self) -> Optional[float]:
        """Calculate heal rate (successful recovery after failure)."""
        if self.execute_code_calls < 2:
            return None
        if self.first_try_success:
            return None  # No healing needed
        # If first try failed but we eventually succeeded
        if self.execute_code_successes > 0:
            return 1.0
        return 0.0

    @property
    def mesa_heal_rate(self) -> Optional[float]:
        """Calculate MESA model heal rate (success after errors)."""
        if self.mesa_model_calls < 2:
            return None
        if self.mesa_execution_errors == 0 and self.mesa_variance_fixes == 0:
            return None  # No healing needed
        if self.mesa_model_successes > 0:
            return 1.0
        return 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "execute_code_calls": self.execute_code_calls,
            "execute_code_successes": self.execute_code_successes,
            "execute_code_failures": self.execute_code_failures,
            "install_package_calls": self.install_package_calls,
            "install_package_successes": self.install_package_successes,
            "total_execution_time_ms": self.total_execution_time_ms,
            "first_try_success": self.first_try_success,
            "heal_rate": self.heal_rate,
            # MESA metrics
            "mesa_model_calls": self.mesa_model_calls,
            "mesa_model_successes": self.mesa_model_successes,
            "mesa_execution_errors": self.mesa_execution_errors,
            "mesa_variance_fixes": self.mesa_variance_fixes,
            "calibration_std": self.calibration_std,
            "calibration_threshold": self.calibration_threshold,
            "mesa_heal_rate": self.mesa_heal_rate,
            # Token/cost metrics
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


# Tool definitions for Claude Agent SDK
TOOL_DEFINITIONS = [
    {
        "name": "execute_code",
        "description": """Execute Python code and return the output.

Use this tool to run Python code for data analysis, calculations, or simulations.
The code runs in an isolated environment with common packages available.

IMPORTANT:
- Print your final result to stdout - that's what gets captured
- Handle exceptions gracefully
- For Monte Carlo simulations, print the probability as a float between 0 and 1

Example usage:
```python
import random

# Simple Monte Carlo simulation
successes = sum(1 for _ in range(1000) if random.random() > 0.5)
probability = successes / 1000
print(f"Probability: {probability}")
```""",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                }
            },
            "required": ["code"],
        },
    },
    {
        "name": "install_package",
        "description": """Install a Python package using pip.

Use this to install packages you need for your analysis or simulation.
Common packages like numpy, pandas, scipy are pre-installed.

Example: install_package(package="mesa") to install the Mesa ABM framework.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "package": {
                    "type": "string",
                    "description": "Package name to install (e.g., 'mesa', 'numpy>=1.20')",
                }
            },
            "required": ["package"],
        },
    },
    {
        "name": "submit_prediction",
        "description": """Submit your final prediction for this market.

Call this tool ONCE when you have determined your prediction.
The prediction must be a probability between 0.0 and 1.0.

- 0.0 = You predict the event will NOT happen (No)
- 1.0 = You predict the event WILL happen (Yes)
- 0.5 = You are completely uncertain

Include a brief reasoning for your prediction.

Example: submit_prediction(probability=0.75, reasoning="Based on historical data and current trends...")""",
        "input_schema": {
            "type": "object",
            "properties": {
                "probability": {
                    "type": "number",
                    "description": "Your prediction as a probability between 0.0 and 1.0",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of your prediction",
                },
            },
            "required": ["probability", "reasoning"],
        },
    },
    {
        "name": "generate_mesa_model",
        "description": """Submit Mesa agent-based model code for simulation.

Use this tool to submit your Mesa 2.x agent code. The system will:
1. Validate the code structure
2. Run calibration (50 runs) to determine threshold
3. Check for low variance (std < 0.001 triggers error)
4. Run Monte Carlo (200 runs) to compute probability

⚠️ CRITICAL: Use Mesa 2.x syntax!
- super().__init__(unique_id, model)  # CORRECT
- super().__init__(model)  # WRONG - Mesa 3.x syntax

Your code MUST include:
- Agent classes with __init__(unique_id, model) and step()
- compute_outcome(model) function returning 0-1
- AGENT_CONFIG dict mapping agent classes to counts
- MODEL_PARAMS dict with model parameters
- THRESHOLD float for outcome comparison

Example:
```python
class Voter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.support = np.random.uniform(0, 1)

    def step(self):
        self.support += np.random.normal(0, 0.05)
        self.support = np.clip(self.support, 0, 1)

def compute_outcome(model):
    agents = model.schedule.agents
    return np.mean([a.support for a in agents])

AGENT_CONFIG = {Voter: 50}
MODEL_PARAMS = {"volatility": 0.1}
THRESHOLD = 0.5
```

If your code has errors, you'll receive the error message. Fix and resubmit.
If variance is too low, add more randomness to agent initialization.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_code": {
                    "type": "string",
                    "description": "Mesa agent code (classes, compute_outcome, AGENT_CONFIG, MODEL_PARAMS, THRESHOLD)",
                }
            },
            "required": ["agent_code"],
        },
    },
]


# Tool definitions for simulation mode (includes generate_mesa_model)
SIMULATION_TOOL_DEFINITIONS = [
    TOOL_DEFINITIONS[0],  # execute_code
    TOOL_DEFINITIONS[1],  # install_package
    TOOL_DEFINITIONS[2],  # submit_prediction
    TOOL_DEFINITIONS[3],  # generate_mesa_model
]

# Tool definitions for direct mode (no code tools)
DIRECT_TOOL_DEFINITIONS = [
    TOOL_DEFINITIONS[2],  # submit_prediction only
]

# Tool definitions for reasoning mode (code execution, no Mesa)
REASONING_TOOL_DEFINITIONS = [
    TOOL_DEFINITIONS[0],  # execute_code
    TOOL_DEFINITIONS[1],  # install_package
    TOOL_DEFINITIONS[2],  # submit_prediction
]


def execute_code(code: str, timeout: int = 60) -> ExecutionResult:
    """Execute Python code in a subprocess.

    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds

    Returns:
        ExecutionResult with stdout, stderr, exit_code, and success flag
    """
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            success=result.returncode == 0,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="",
            stderr=f"Execution timed out after {timeout} seconds",
            exit_code=-1,
            success=False,
        )
    except Exception as e:
        return ExecutionResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
            success=False,
        )


def install_package(package: str, timeout: int = 120) -> ExecutionResult:
    """Install a Python package using pip.

    Args:
        package: Package specification (e.g., "mesa", "numpy>=1.20")
        timeout: Maximum installation time in seconds

    Returns:
        ExecutionResult with installation output
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "-q"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            success=result.returncode == 0,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="",
            stderr=f"Installation timed out after {timeout} seconds",
            exit_code=-1,
            success=False,
        )
    except Exception as e:
        return ExecutionResult(
            stdout="",
            stderr=str(e),
            exit_code=-1,
            success=False,
        )


@dataclass
class PredictionResult:
    """Result of a prediction submission."""

    probability: float
    reasoning: str
    valid: bool
    error: Optional[str] = None


def validate_prediction(probability: float, reasoning: str) -> PredictionResult:
    """Validate a prediction submission.

    Args:
        probability: Predicted probability (0.0 to 1.0)
        reasoning: Explanation for the prediction

    Returns:
        PredictionResult with validation status
    """
    if not isinstance(probability, (int, float)):
        return PredictionResult(
            probability=0.0,
            reasoning=reasoning,
            valid=False,
            error=f"Probability must be a number, got {type(probability).__name__}",
        )

    if probability < 0.0 or probability > 1.0:
        return PredictionResult(
            probability=probability,
            reasoning=reasoning,
            valid=False,
            error=f"Probability must be between 0.0 and 1.0, got {probability}",
        )

    if not reasoning or len(reasoning.strip()) < 10:
        return PredictionResult(
            probability=probability,
            reasoning=reasoning,
            valid=False,
            error="Reasoning must be at least 10 characters",
        )

    return PredictionResult(
        probability=probability,
        reasoning=reasoning,
        valid=True,
    )


# ==============================================================================
# MESA MODEL EXECUTION
# ==============================================================================


@dataclass
class MesaModelResult:
    """Result of Mesa model execution."""

    success: bool
    calibration: Optional[dict] = None  # {mean, std, min, max, threshold, outcomes}
    monte_carlo: Optional[dict] = None  # {probability, ci_95, n_runs, threshold}
    error: Optional[str] = None
    error_type: Optional[str] = None  # "execution", "low_variance", "validation"
    execution_time_ms: float = 0.0


def validate_mesa_code(agent_code: str) -> tuple[bool, Optional[str]]:
    """Validate that Mesa agent code has required components.

    Args:
        agent_code: The agent code to validate

    Returns:
        Tuple of (valid, error_message)
    """
    required = [
        ("AGENT_CONFIG", "AGENT_CONFIG dict mapping agent classes to counts"),
        ("MODEL_PARAMS", "MODEL_PARAMS dict with model parameters"),
        ("THRESHOLD", "THRESHOLD float for outcome comparison"),
        ("def compute_outcome", "compute_outcome(model) function"),
        ("class ", "At least one Agent class"),
    ]

    for pattern, description in required:
        if pattern not in agent_code:
            return False, f"Missing required: {description}"

    # Check for Mesa 2.x syntax issues
    if "super().__init__(model)" in agent_code and "super().__init__(unique_id, model)" not in agent_code:
        return False, "Using Mesa 3.x syntax. Change super().__init__(model) to super().__init__(unique_id, model)"

    return True, None


def execute_mesa_model(agent_code: str, timeout: int = 120) -> MesaModelResult:
    """Execute a Mesa model with calibration and Monte Carlo.

    Args:
        agent_code: The agent code (classes, compute_outcome, AGENT_CONFIG, etc.)
        timeout: Maximum execution time in seconds

    Returns:
        MesaModelResult with calibration and Monte Carlo results
    """
    import time

    # Import the template assembler
    try:
        from .prompts import assemble_mesa_code
    except ImportError:
        from prompts import assemble_mesa_code

    start_time = time.time()

    # Validate code structure first
    valid, error = validate_mesa_code(agent_code)
    if not valid:
        return MesaModelResult(
            success=False,
            error=error,
            error_type="validation",
        )

    # Assemble full code with template
    full_code = assemble_mesa_code(agent_code)

    # Execute the model
    result = execute_code(full_code, timeout=timeout)
    execution_time = (time.time() - start_time) * 1000

    if not result.success:
        return MesaModelResult(
            success=False,
            error=result.stderr or "Execution failed",
            error_type="execution",
            execution_time_ms=execution_time,
        )

    # Parse the output
    try:
        # Look for JSON output at the end of stdout
        stdout_lines = result.stdout.strip().split("\n")

        # Find the last line that looks like JSON
        json_line = None
        for line in reversed(stdout_lines):
            if line.strip().startswith("{"):
                json_line = line.strip()
                break

        if not json_line:
            return MesaModelResult(
                success=False,
                error="No JSON output found in stdout",
                error_type="execution",
                execution_time_ms=execution_time,
            )

        output = json.loads(json_line)

        # Check for low variance error
        if "error" in output and output["error"] == "low_variance":
            return MesaModelResult(
                success=False,
                calibration=output.get("calibration"),
                error="Low variance detected - model produces constant outputs (std < 0.001)",
                error_type="low_variance",
                execution_time_ms=execution_time,
            )

        # Success - return both calibration and Monte Carlo results
        return MesaModelResult(
            success=True,
            calibration=output.get("calibration"),
            monte_carlo=output.get("monte_carlo"),
            execution_time_ms=execution_time,
        )

    except json.JSONDecodeError as e:
        return MesaModelResult(
            success=False,
            error=f"Failed to parse JSON output: {e}\nStdout: {result.stdout[:500]}",
            error_type="execution",
            execution_time_ms=execution_time,
        )


def get_mesa_error_feedback(result: MesaModelResult, agent_code: str) -> str:
    """Generate feedback message for LLM to fix Mesa model errors.

    Args:
        result: The MesaModelResult with error
        agent_code: The original agent code

    Returns:
        Feedback string for the LLM
    """
    if result.error_type == "validation":
        return f"""Your Mesa model code is missing required components.

Error: {result.error}

Please fix and resubmit with generate_mesa_model. Your code must include:
- Agent classes with __init__(unique_id, model) and step()
- compute_outcome(model) function returning 0-1
- AGENT_CONFIG dict
- MODEL_PARAMS dict
- THRESHOLD float"""

    elif result.error_type == "execution":
        return f"""Your Mesa model code failed to execute.

Error: {result.error}

Common issues:
- Mesa 2.x requires: super().__init__(unique_id, model)
- Wrong: super().__init__(model)

Please fix and resubmit with generate_mesa_model."""

    elif result.error_type == "low_variance":
        cal = result.calibration or {}
        return f"""Your Mesa model produces constant outputs with no variance.

Calibration results:
- mean: {cal.get('mean', 0):.4f}
- std: {cal.get('std', 0):.6f} (< 0.001 is too low)
- min: {cal.get('min', 0):.4f}
- max: {cal.get('max', 0):.4f}

The model outputs nearly the same value regardless of random seed. To fix:
1. Ensure agents initialize random attributes: self.attr = np.random.uniform(0, 1)
2. compute_outcome MUST use agent states: np.mean([a.attr for a in agents])
3. Add noise: outcome + np.random.uniform(-0.05, 0.05)

Please fix and resubmit with generate_mesa_model."""

    return f"Unknown error: {result.error}"


def format_mesa_success_output(result: MesaModelResult) -> str:
    """Format successful Mesa model output for the LLM.

    Args:
        result: The successful MesaModelResult

    Returns:
        Formatted string with results
    """
    cal = result.calibration or {}
    mc = result.monte_carlo or {}

    return f"""Mesa simulation completed successfully!

## Calibration Results (50 runs)
- Mean outcome: {cal.get('mean', 0):.4f}
- Std deviation: {cal.get('std', 0):.4f}
- Range: [{cal.get('min', 0):.4f}, {cal.get('max', 0):.4f}]
- Threshold: {cal.get('threshold', 0):.4f}

## Monte Carlo Results (200 runs)
- **Probability: {mc.get('probability', 0):.4f}** ({mc.get('probability', 0):.1%})
- 95% CI: ±{mc.get('ci_95', 0):.4f}
- Threshold used: {mc.get('threshold', 0):.4f}

Based on these simulation results, use submit_prediction to submit your final probability.
You can use the Monte Carlo probability ({mc.get('probability', 0):.4f}) directly, or adjust based on your analysis."""
