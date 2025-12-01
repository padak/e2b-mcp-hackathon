"""Tests for arena runner module."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from arena.runner.tools import (
    execute_code,
    install_package,
    validate_prediction,
    ExecutionResult,
    PredictionResult,
    ToolMetrics,
    TOOL_DEFINITIONS,
)
from arena.runner.hooks import (
    create_tool_handler,
    ToolHandler,
    RunLog,
    ToolCall,
)
from arena.runner.prompts import (
    get_system_prompt,
    get_user_prompt,
    format_direct_prompt,
    format_simulation_prompt,
)


class TestExecuteCode:
    """Tests for execute_code function."""

    def test_simple_print(self):
        """Test simple print statement."""
        result = execute_code("print('hello world')")
        assert result.success is True
        assert "hello world" in result.stdout
        assert result.exit_code == 0

    def test_math_calculation(self):
        """Test math calculation."""
        result = execute_code("print(2 + 2)")
        assert result.success is True
        assert "4" in result.stdout

    def test_numpy_available(self):
        """Test that numpy is available."""
        result = execute_code("import numpy as np; print(np.array([1,2,3]).sum())")
        assert result.success is True
        assert "6" in result.stdout

    def test_syntax_error(self):
        """Test that syntax errors are caught."""
        result = execute_code("print('unclosed string")
        assert result.success is False
        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr or "EOL" in result.stderr

    def test_runtime_error(self):
        """Test that runtime errors are caught."""
        result = execute_code("x = 1/0")
        assert result.success is False
        assert "ZeroDivisionError" in result.stderr

    def test_timeout(self):
        """Test timeout handling."""
        result = execute_code("import time; time.sleep(5)", timeout=1)
        assert result.success is False
        assert "timed out" in result.stderr.lower()


class TestValidatePrediction:
    """Tests for validate_prediction function."""

    def test_valid_prediction(self):
        """Test valid prediction."""
        result = validate_prediction(0.75, "Based on my analysis of the data")
        assert result.valid is True
        assert result.probability == 0.75
        assert result.error is None

    def test_probability_too_low(self):
        """Test probability below 0."""
        result = validate_prediction(-0.1, "Some reasoning here")
        assert result.valid is False
        assert "between 0.0 and 1.0" in result.error

    def test_probability_too_high(self):
        """Test probability above 1."""
        result = validate_prediction(1.5, "Some reasoning here")
        assert result.valid is False
        assert "between 0.0 and 1.0" in result.error

    def test_reasoning_too_short(self):
        """Test reasoning too short."""
        result = validate_prediction(0.5, "short")
        assert result.valid is False
        assert "10 characters" in result.error

    def test_edge_values(self):
        """Test edge values 0.0 and 1.0."""
        result_zero = validate_prediction(0.0, "Definitely won't happen")
        result_one = validate_prediction(1.0, "Definitely will happen")
        assert result_zero.valid is True
        assert result_one.valid is True


class TestToolMetrics:
    """Tests for ToolMetrics class."""

    def test_initial_state(self):
        """Test initial metrics state."""
        metrics = ToolMetrics()
        assert metrics.execute_code_calls == 0
        assert metrics.first_try_success is None
        assert metrics.heal_rate is None

    def test_record_first_success(self):
        """Test recording first successful execution."""
        metrics = ToolMetrics()
        metrics.record_execution(success=True, time_ms=100)
        assert metrics.first_try_success is True
        assert metrics.execute_code_calls == 1
        assert metrics.execute_code_successes == 1

    def test_record_first_failure_then_success(self):
        """Test healing (failure then success)."""
        metrics = ToolMetrics()
        metrics.record_execution(success=False, time_ms=100)
        metrics.record_execution(success=True, time_ms=150)
        assert metrics.first_try_success is False
        assert metrics.heal_rate == 1.0
        assert metrics.execute_code_calls == 2

    def test_no_healing_if_first_success(self):
        """Test no heal rate if first try succeeded."""
        metrics = ToolMetrics()
        metrics.record_execution(success=True, time_ms=100)
        metrics.record_execution(success=True, time_ms=100)
        assert metrics.heal_rate is None

    def test_to_dict(self):
        """Test serialization to dict."""
        metrics = ToolMetrics()
        metrics.record_execution(success=True, time_ms=100)
        d = metrics.to_dict()
        assert d["execute_code_calls"] == 1
        assert d["first_try_success"] is True


class TestToolHandler:
    """Tests for ToolHandler class."""

    def test_handle_execute_code(self):
        """Test execute_code tool handling."""
        handler, run_log = create_tool_handler(
            question_id="test-1",
            model_id="test-model",
            mode="simulation",
            trial=1,
        )
        result = handler.handle_tool_call("execute_code", {"code": "print('test')"})
        assert result["success"] is True
        assert "test" in result["output"]
        assert len(run_log.tool_calls) == 1

    def test_handle_submit_prediction(self):
        """Test submit_prediction tool handling."""
        handler, run_log = create_tool_handler(
            question_id="test-1",
            model_id="test-model",
            mode="direct",
            trial=1,
        )
        result = handler.handle_tool_call(
            "submit_prediction",
            {"probability": 0.8, "reasoning": "Based on my careful analysis"},
        )
        assert result["success"] is True
        assert result["stop"] is True
        assert run_log.prediction["probability"] == 0.8

    def test_cannot_submit_twice(self):
        """Test that prediction can only be submitted once."""
        handler, run_log = create_tool_handler(
            question_id="test-1",
            model_id="test-model",
            mode="direct",
            trial=1,
        )
        handler.handle_tool_call(
            "submit_prediction",
            {"probability": 0.8, "reasoning": "First prediction here"},
        )
        result = handler.handle_tool_call(
            "submit_prediction",
            {"probability": 0.9, "reasoning": "Second prediction here"},
        )
        assert result["success"] is False
        assert "already submitted" in result["error"]

    def test_unknown_tool(self):
        """Test handling of unknown tool."""
        handler, _ = create_tool_handler("test-1", "test-model", "direct", 1)
        result = handler.handle_tool_call("unknown_tool", {})
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


class TestRunLog:
    """Tests for RunLog class."""

    def test_create_run_log(self):
        """Test run log creation."""
        handler, run_log = create_tool_handler(
            question_id="q1",
            model_id="gpt-4o",
            mode="simulation",
            trial=2,
        )
        assert run_log.question_id == "q1"
        assert run_log.model_id == "gpt-4o"
        assert run_log.mode == "simulation"
        assert run_log.trial == 2

    def test_finalize(self):
        """Test finalization sets end time."""
        _, run_log = create_tool_handler("q1", "model", "direct", 1)
        assert run_log.end_time is None
        run_log.finalize()
        assert run_log.end_time is not None

    def test_to_dict(self):
        """Test serialization to dict."""
        handler, run_log = create_tool_handler("q1", "model", "direct", 1)
        handler.handle_tool_call(
            "submit_prediction",
            {"probability": 0.5, "reasoning": "Uncertain about outcome"},
        )
        run_log.finalize()

        d = run_log.to_dict()
        assert d["question_id"] == "q1"
        assert d["prediction"]["probability"] == 0.5
        assert len(d["tool_calls"]) == 1


class TestPrompts:
    """Tests for prompt generation."""

    def test_get_system_prompt_direct(self):
        """Test direct mode system prompt."""
        prompt = get_system_prompt("direct")
        assert "prediction analyst" in prompt.lower()
        assert "submit_prediction" in prompt

    def test_get_system_prompt_simulation(self):
        """Test simulation mode system prompt."""
        prompt = get_system_prompt("simulation")
        assert "monte carlo" in prompt.lower() or "simulation" in prompt.lower()
        assert "execute_code" in prompt

    def test_get_system_prompt_invalid(self):
        """Test invalid mode raises error."""
        with pytest.raises(ValueError):
            get_system_prompt("invalid_mode")

    def test_format_direct_prompt(self):
        """Test direct mode user prompt formatting."""
        prompt = format_direct_prompt(
            question="Will X happen?",
            description="Resolves Yes if X happens",
            market_id="test-1",
            volume=1000000,
            closed_time="2024-12-01",
        )
        assert "Will X happen?" in prompt
        assert "test-1" in prompt
        assert "$1,000,000" in prompt

    def test_format_simulation_prompt(self):
        """Test simulation mode user prompt formatting."""
        prompt = format_simulation_prompt(
            question="Will Y occur?",
            description="Market about Y",
            market_id="test-2",
            volume=500000,
            closed_time="2024-12-15",
        )
        assert "Will Y occur?" in prompt
        assert "Monte Carlo" in prompt
        assert "execute_code" in prompt

    def test_get_user_prompt(self):
        """Test get_user_prompt dispatcher."""
        direct = get_user_prompt(
            mode="direct",
            question="Test?",
            description="Desc",
            market_id="m1",
            volume=100,
            closed_time="2024-01-01",
        )
        simulation = get_user_prompt(
            mode="simulation",
            question="Test?",
            description="Desc",
            market_id="m1",
            volume=100,
            closed_time="2024-01-01",
        )
        assert "submit your prediction" in direct.lower()
        assert "simulation" in simulation.lower()


class TestToolDefinitions:
    """Tests for tool definitions."""

    def test_tool_definitions_structure(self):
        """Test tool definitions have correct structure."""
        assert len(TOOL_DEFINITIONS) == 3

        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert tool_names == {"execute_code", "install_package", "submit_prediction"}

        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"

    def test_submit_prediction_schema(self):
        """Test submit_prediction has correct schema."""
        submit_tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "submit_prediction")
        props = submit_tool["input_schema"]["properties"]
        assert "probability" in props
        assert "reasoning" in props
        assert props["probability"]["minimum"] == 0.0
        assert props["probability"]["maximum"] == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
