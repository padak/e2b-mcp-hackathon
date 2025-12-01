"""Logging hooks for arena evaluation.

These hooks capture tool usage metrics during LLM agent runs.
"""

import time
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timezone

# Support both relative and absolute imports (for E2B sandbox)
try:
    from .tools import (
        ToolMetrics,
        execute_code,
        install_package,
        validate_prediction,
        execute_mesa_model,
        get_mesa_error_feedback,
        format_mesa_success_output,
    )
except ImportError:
    from tools import (
        ToolMetrics,
        execute_code,
        install_package,
        validate_prediction,
        execute_mesa_model,
        get_mesa_error_feedback,
        format_mesa_success_output,
    )

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Record of a single tool call."""

    tool_name: str
    input_args: dict
    output: Any
    success: bool
    duration_ms: float
    timestamp: str
    error: Optional[str] = None


@dataclass
class RunLog:
    """Complete log of an arena run."""

    question_id: str
    model_id: str
    mode: str  # "direct" or "simulation"
    trial: int
    start_time: str
    end_time: Optional[str] = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    metrics: ToolMetrics = field(default_factory=ToolMetrics)
    prediction: Optional[dict] = None  # {probability, reasoning, valid}
    error: Optional[str] = None

    # MESA-specific fields
    mesa_calibration: Optional[dict] = None  # {mean, std, min, max, threshold}
    mesa_monte_carlo: Optional[dict] = None  # {probability, ci_95, n_runs}
    mesa_agent_code: Optional[str] = None  # Last successful agent code

    def add_tool_call(self, call: ToolCall) -> None:
        """Add a tool call to the log."""
        self.tool_calls.append(call)

    def set_prediction(self, probability: float, reasoning: str, valid: bool) -> None:
        """Set the final prediction."""
        self.prediction = {
            "probability": probability,
            "reasoning": reasoning,
            "valid": valid,
        }

    def set_mesa_results(
        self,
        calibration: Optional[dict] = None,
        monte_carlo: Optional[dict] = None,
        agent_code: Optional[str] = None,
    ) -> None:
        """Set MESA simulation results."""
        if calibration:
            self.mesa_calibration = calibration
            # Record calibration metrics
            if "std" in calibration and "threshold" in calibration:
                self.metrics.record_calibration(
                    calibration["std"],
                    calibration["threshold"],
                )
        if monte_carlo:
            self.mesa_monte_carlo = monte_carlo
        if agent_code:
            self.mesa_agent_code = agent_code

    def finalize(self) -> None:
        """Mark the run as complete."""
        self.end_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "question_id": self.question_id,
            "model_id": self.model_id,
            "mode": self.mode,
            "trial": self.trial,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "input_args": tc.input_args,
                    "output": tc.output if isinstance(tc.output, str) else str(tc.output),
                    "success": tc.success,
                    "duration_ms": tc.duration_ms,
                    "timestamp": tc.timestamp,
                    "error": tc.error,
                }
                for tc in self.tool_calls
            ],
            "metrics": self.metrics.to_dict(),
            "prediction": self.prediction,
            "error": self.error,
        }

        # Add MESA results if present
        if self.mesa_calibration:
            result["mesa_calibration"] = self.mesa_calibration
        if self.mesa_monte_carlo:
            result["mesa_monte_carlo"] = self.mesa_monte_carlo
        if self.mesa_agent_code:
            result["mesa_agent_code"] = self.mesa_agent_code

        return result


class ToolHandler:
    """Handles tool execution with logging and metrics."""

    def __init__(self, run_log: RunLog):
        """Initialize the tool handler.

        Args:
            run_log: RunLog instance to record tool calls
        """
        self.run_log = run_log
        self.prediction_submitted = False
        self.last_mesa_agent_code: Optional[str] = None

    def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        """Handle a tool call from the LLM.

        Args:
            tool_name: Name of the tool to call
            tool_input: Input arguments for the tool

        Returns:
            Dictionary with tool result
        """
        start_time = time.time()
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        try:
            if tool_name == "execute_code":
                result = self._handle_execute_code(tool_input)
            elif tool_name == "install_package":
                result = self._handle_install_package(tool_input)
            elif tool_name == "submit_prediction":
                result = self._handle_submit_prediction(tool_input)
            elif tool_name == "generate_mesa_model":
                result = self._handle_generate_mesa_model(tool_input)
            else:
                result = {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                }

            duration_ms = (time.time() - start_time) * 1000

            # Log the tool call
            call = ToolCall(
                tool_name=tool_name,
                input_args=tool_input,
                output=result.get("output", result.get("error", "")),
                success=result.get("success", False),
                duration_ms=duration_ms,
                timestamp=timestamp,
                error=result.get("error"),
            )
            self.run_log.add_tool_call(call)

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)

            call = ToolCall(
                tool_name=tool_name,
                input_args=tool_input,
                output="",
                success=False,
                duration_ms=duration_ms,
                timestamp=timestamp,
                error=error_msg,
            )
            self.run_log.add_tool_call(call)

            return {"success": False, "error": error_msg}

    def _handle_execute_code(self, tool_input: dict) -> dict:
        """Handle execute_code tool call."""
        code = tool_input.get("code", "")
        if not code:
            return {"success": False, "error": "No code provided"}

        start = time.time()
        result = execute_code(code)
        duration_ms = (time.time() - start) * 1000

        # Record metrics
        self.run_log.metrics.record_execution(result.success, duration_ms)

        if result.success:
            return {
                "success": True,
                "output": result.stdout,
                "stderr": result.stderr if result.stderr else None,
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Code execution failed",
                "stdout": result.stdout if result.stdout else None,
            }

    def _handle_install_package(self, tool_input: dict) -> dict:
        """Handle install_package tool call."""
        package = tool_input.get("package", "")
        if not package:
            return {"success": False, "error": "No package specified"}

        result = install_package(package)
        self.run_log.metrics.record_install(result.success)

        if result.success:
            return {
                "success": True,
                "output": f"Successfully installed {package}",
            }
        else:
            return {
                "success": False,
                "error": result.stderr or f"Failed to install {package}",
            }

    def _handle_submit_prediction(self, tool_input: dict) -> dict:
        """Handle submit_prediction tool call."""
        if self.prediction_submitted:
            return {
                "success": False,
                "error": "Prediction already submitted. You can only submit once.",
            }

        probability = tool_input.get("probability")
        reasoning = tool_input.get("reasoning", "")

        if probability is None:
            return {"success": False, "error": "No probability provided"}

        validation = validate_prediction(probability, reasoning)

        if validation.valid:
            self.prediction_submitted = True
            self.run_log.set_prediction(
                probability=validation.probability,
                reasoning=validation.reasoning,
                valid=True,
            )
            return {
                "success": True,
                "output": f"Prediction submitted: {validation.probability:.2%}",
                "stop": True,  # Signal to stop the agent loop
            }
        else:
            return {
                "success": False,
                "error": validation.error,
            }

    def _handle_generate_mesa_model(self, tool_input: dict) -> dict:
        """Handle generate_mesa_model tool call.

        Executes the Mesa model with calibration and Monte Carlo,
        returning results or error feedback for self-healing.
        """
        agent_code = tool_input.get("agent_code", "")
        if not agent_code:
            return {"success": False, "error": "No agent_code provided"}

        # Store for potential later reference
        self.last_mesa_agent_code = agent_code

        # Execute the Mesa model
        result = execute_mesa_model(agent_code)

        # Record metrics based on result type
        is_execution_error = result.error_type == "execution"
        is_variance_error = result.error_type == "low_variance"

        self.run_log.metrics.record_mesa_model(
            success=result.success,
            execution_error=is_execution_error,
            variance_fix=is_variance_error,
        )

        # Record execution time
        self.run_log.metrics.total_execution_time_ms += result.execution_time_ms

        if result.success:
            # Store successful results
            self.run_log.set_mesa_results(
                calibration=result.calibration,
                monte_carlo=result.monte_carlo,
                agent_code=agent_code,
            )

            return {
                "success": True,
                "output": format_mesa_success_output(result),
            }
        else:
            # Store partial results (e.g., calibration even if low variance)
            if result.calibration:
                self.run_log.set_mesa_results(calibration=result.calibration)

            # Return error feedback for self-healing
            return {
                "success": False,
                "error": get_mesa_error_feedback(result, agent_code),
                "error_type": result.error_type,
            }


def create_tool_handler(
    question_id: str,
    model_id: str,
    mode: str,
    trial: int,
) -> tuple[ToolHandler, RunLog]:
    """Create a tool handler for an arena run.

    Args:
        question_id: ID of the question being evaluated
        model_id: ID of the model being tested
        mode: "direct" or "simulation"
        trial: Trial number (1-indexed)

    Returns:
        Tuple of (ToolHandler, RunLog)
    """
    run_log = RunLog(
        question_id=question_id,
        model_id=model_id,
        mode=mode,
        trial=trial,
        start_time=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    handler = ToolHandler(run_log)
    return handler, run_log
