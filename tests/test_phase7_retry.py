"""
Tests for Phase 7: Retry Loop & Monte Carlo.
"""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.sandbox.retry import run_monte_carlo, ExecutionResult


class TestMonteCarloAggregation:
    """Test Monte Carlo result aggregation (no sandbox needed)."""

    def test_run_monte_carlo_basic(self):
        """Test basic Monte Carlo aggregation."""
        results = [True] * 65 + [False] * 35  # 65% success
        mc = run_monte_carlo(results, n_runs=100)

        assert mc["probability"] == 0.65
        assert mc["n_runs"] == 100
        assert len(mc["results"]) == 100
        assert mc["ci_95"] > 0  # Should have confidence interval

    def test_run_monte_carlo_all_true(self):
        """Test with all True results."""
        results = [True] * 100
        mc = run_monte_carlo(results, n_runs=100)

        assert mc["probability"] == 1.0
        assert mc["ci_95"] == 0  # No variance

    def test_run_monte_carlo_all_false(self):
        """Test with all False results."""
        results = [False] * 100
        mc = run_monte_carlo(results, n_runs=100)

        assert mc["probability"] == 0.0
        assert mc["ci_95"] == 0

    def test_run_monte_carlo_ci_calculation(self):
        """Test confidence interval calculation."""
        results = [True] * 50 + [False] * 50  # 50%
        mc = run_monte_carlo(results, n_runs=100)

        # CI for 50% with n=100 should be about 0.098
        expected_ci = 1.96 * (0.5 * 0.5 / 100) ** 0.5
        assert abs(mc["ci_95"] - expected_ci) < 0.001


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_execution_result_success(self):
        """Test successful execution result."""
        result = ExecutionResult(
            success=True,
            output="test output",
            probability=0.65,
            ci_95=0.05,
            n_runs=200,
            results=[1, 0, 1]
        )

        assert result.success
        assert result.probability == 0.65
        assert not result.used_fallback

    def test_execution_result_failure(self):
        """Test failed execution result."""
        result = ExecutionResult(
            success=False,
            output="",
            error="SyntaxError: invalid syntax"
        )

        assert not result.success
        assert result.error is not None


@pytest.mark.slow
class TestRetryLoopIntegration:
    """Integration tests requiring E2B sandbox."""

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful execution without retry."""
        from e2b_code_interpreter import Sandbox
        from src.sandbox.retry import execute_with_retry
        import asyncio

        loop = asyncio.get_event_loop()
        sbx = await loop.run_in_executor(
            None, lambda: Sandbox.create(template="code-interpreter-v1", timeout=60)
        )
        try:
            code = '''
print("Hello from test!")
'''
            result = await execute_with_retry(sbx, code, max_retries=3)

            assert result.success
            assert "Hello from test!" in result.output
        finally:
            await loop.run_in_executor(None, sbx.kill)

    @pytest.mark.asyncio
    async def test_execute_with_retry_with_fix(self):
        """Test execution that needs fixing."""
        from e2b_code_interpreter import Sandbox
        from src.sandbox.retry import execute_with_retry
        import asyncio

        loop = asyncio.get_event_loop()
        sbx = await loop.run_in_executor(
            None, lambda: Sandbox.create(template="code-interpreter-v1", timeout=120)
        )
        try:
            # Intentionally broken code
            broken_code = '''
import mesa
print(undefined_variable)  # This will fail
'''
            result = await execute_with_retry(sbx, broken_code, max_retries=3)

            # Should either fix it or fail gracefully
            # The LLM should recognize and fix the undefined variable
            assert result.success or result.error is not None
        finally:
            await loop.run_in_executor(None, sbx.kill)

    @pytest.mark.asyncio
    async def test_execute_monte_carlo_basic(self):
        """Test Monte Carlo execution with simple trial function."""
        from e2b_code_interpreter import Sandbox
        from src.sandbox.retry import execute_monte_carlo
        import asyncio

        loop = asyncio.get_event_loop()
        sbx = await loop.run_in_executor(
            None, lambda: Sandbox.create(template="code-interpreter-v1", timeout=120)
        )
        try:
            # Install dependencies
            await loop.run_in_executor(
                None, lambda: sbx.commands.run('pip install mesa numpy', timeout=60)
            )

            # Simple trial function that returns True 70% of the time
            code = '''
import random

def run_trial(seed: int) -> bool:
    """Simple trial that returns True 70% of the time."""
    random.seed(seed)
    return random.random() < 0.7
'''
            result = await execute_monte_carlo(sbx, code, n_runs=100, max_retries=3)

            assert result.success
            assert result.probability is not None
            # Should be around 0.7 with some variance
            assert 0.5 < result.probability < 0.9
            assert result.n_runs == 100
            assert len(result.results) == 100
        finally:
            await loop.run_in_executor(None, sbx.kill)

    @pytest.mark.asyncio
    async def test_execute_with_fallback(self):
        """Test that fallback is used when code fails."""
        from e2b_code_interpreter import Sandbox
        from src.sandbox.retry import execute_with_retry
        import asyncio

        loop = asyncio.get_event_loop()
        sbx = await loop.run_in_executor(
            None, lambda: Sandbox.create(template="code-interpreter-v1", timeout=120)
        )
        try:
            # Completely broken code
            broken_code = '''
this is not valid python at all!@#$%
'''
            # Fallback that works
            fallback_code = '''
print("Fallback executed!")
'''
            result = await execute_with_retry(
                sbx,
                broken_code,
                max_retries=2,
                fallback_code=fallback_code
            )

            assert result.success
            assert result.used_fallback
            assert "Fallback executed!" in result.output
        finally:
            await loop.run_in_executor(None, sbx.kill)


if __name__ == "__main__":
    # Run just the unit tests without sandbox
    pytest.main([__file__, "-v", "-m", "not slow"])
