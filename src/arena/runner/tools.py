"""Arena tools for LLM agents.

These tools are provided to LLM agents during arena evaluation:
- execute_code: Run Python code and capture output
- install_package: Install pip packages
- submit_prediction: Submit final prediction (0.0 to 1.0)
"""

import subprocess
import sys
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
