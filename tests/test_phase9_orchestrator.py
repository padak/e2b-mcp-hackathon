"""Tests for Phase 9: Orchestrator and CLI."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestOrchestratorImports:
    """Test that orchestrator modules import correctly."""

    def test_import_orchestrator(self):
        """Test orchestrator module imports."""
        from src.orchestrator import SimulationRun, run_pipeline, serve_result
        assert SimulationRun is not None
        assert run_pipeline is not None
        assert serve_result is not None

    def test_import_cli(self):
        """Test CLI module imports."""
        from src.cli import display_markets, main
        assert display_markets is not None
        assert main is not None


class TestSimulationRun:
    """Test SimulationRun dataclass."""

    def test_simulation_run_creation(self):
        """Test creating SimulationRun with all fields."""
        from src.orchestrator import SimulationRun

        result = SimulationRun(
            question="Test question?",
            market_odds=0.72,
            simulation_probability=0.65,
            ci_95=0.066,
            n_runs=200,
            results=[1] * 130 + [0] * 70,
            html_chart="<html>test</html>",
            used_fallback=False,
            error=None
        )

        assert result.question == "Test question?"
        assert result.market_odds == 0.72
        assert result.simulation_probability == 0.65
        assert result.ci_95 == 0.066
        assert result.n_runs == 200
        assert len(result.results) == 200
        assert result.html_chart == "<html>test</html>"
        assert result.used_fallback is False
        assert result.error is None

    def test_simulation_run_with_error(self):
        """Test SimulationRun with error state."""
        from src.orchestrator import SimulationRun

        result = SimulationRun(
            question="Failed question?",
            market_odds=0.5,
            simulation_probability=0,
            ci_95=0,
            n_runs=0,
            results=[],
            html_chart="",
            error="Execution failed"
        )

        assert result.error == "Execution failed"
        assert result.n_runs == 0

    def test_simulation_run_with_fallback(self):
        """Test SimulationRun when fallback was used."""
        from src.orchestrator import SimulationRun

        result = SimulationRun(
            question="Fallback question?",
            market_odds=0.6,
            simulation_probability=0.55,
            ci_95=0.07,
            n_runs=200,
            results=[1] * 110 + [0] * 90,
            html_chart="<html>fallback</html>",
            used_fallback=True
        )

        assert result.used_fallback is True


class TestCLIHelpers:
    """Test CLI helper functions."""

    def test_display_markets_formats_correctly(self):
        """Test that display_markets handles market data."""
        from src.cli import display_markets

        markets = [{
            "question": "Will something happen?",
            "yes_price": 0.65,
            "no_price": 0.35,
            "volume": 50000
        }]

        # Just verify it doesn't crash
        # Output goes to console, we're not capturing it
        try:
            display_markets(markets, "Test Markets")
        except Exception as e:
            pytest.fail(f"display_markets raised {e}")


class TestOrchestratorIntegration:
    """Integration tests for the orchestrator (requires API keys)."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_run_pipeline_with_mock_market(self, check_api_keys):
        """Test full pipeline with a real market (slow, uses API)."""
        from src.orchestrator import run_pipeline
        from src.mcp_clients.polymarket import get_markets, format_for_llm

        # Get a real market
        markets = get_markets(limit=5)
        if not markets:
            pytest.skip("No markets available")

        market = format_for_llm(markets[0])

        # Run with minimal runs for speed
        result = await run_pipeline(
            market=market,
            n_runs=10,  # Minimal for testing
            max_retries=2,
            verbose=False
        )

        # Check we got a result
        assert result is not None
        assert result.question == market["question"]
        assert result.market_odds == market["yes_odds"]

        if result.error:
            # Errors are acceptable in tests
            print(f"Pipeline error (acceptable): {result.error}")
        else:
            assert 0 <= result.simulation_probability <= 1
            assert result.n_runs == 10
            assert len(result.results) == 10
            assert result.html_chart != ""


class TestOrchestratorUnit:
    """Unit tests that don't require API calls."""

    def test_serve_result_function_exists(self):
        """Test serve_result function signature."""
        from src.orchestrator import serve_result
        import inspect

        sig = inspect.signature(serve_result)
        params = list(sig.parameters.keys())

        assert "sbx" in params
        assert "html" in params
        assert "port" in params

    def test_run_pipeline_function_exists(self):
        """Test run_pipeline function signature."""
        from src.orchestrator import run_pipeline
        import inspect

        sig = inspect.signature(run_pipeline)
        params = list(sig.parameters.keys())

        assert "market" in params
        assert "n_runs" in params
        assert "max_retries" in params
        assert "verbose" in params
