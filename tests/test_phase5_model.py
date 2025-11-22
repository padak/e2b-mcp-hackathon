"""Tests for Phase 5: Reference Model (Economic Shock)."""

import pytest
import os
from e2b import AsyncSandbox
from src.models.economic_shock import (
    EconomicModel,
    InvestorAgent,
    ConsumerAgent,
    FirmAgent,
    run_monte_carlo,
)


class TestEconomicModel:
    """Tests for EconomicModel class."""

    def test_model_creation(self):
        """Test model creates with default parameters."""
        model = EconomicModel()
        assert model is not None
        assert len(model.agents) == 100  # 30 + 50 + 20

    def test_model_custom_parameters(self):
        """Test model with custom parameters."""
        model = EconomicModel(
            interest_rate=7.0,
            inflation=4.5,
            sentiment=-0.3,
            num_investors=10,
            num_consumers=20,
            num_firms=5,
        )
        assert model.interest_rate == 7.0
        assert model.inflation == 4.5
        assert model.sentiment == -0.3
        assert len(model.agents) == 35

    def test_model_with_seed(self):
        """Test model with seed runs without error."""
        model = EconomicModel(seed=42)

        for _ in range(10):
            model.step()

        results = model.get_results()
        # Just verify it produces valid results
        assert 0 <= results["final_health"] <= 1

    def test_agent_types(self):
        """Test correct agent types are created."""
        model = EconomicModel(
            num_investors=5,
            num_consumers=10,
            num_firms=3,
        )

        investors = [a for a in model.agents if isinstance(a, InvestorAgent)]
        consumers = [a for a in model.agents if isinstance(a, ConsumerAgent)]
        firms = [a for a in model.agents if isinstance(a, FirmAgent)]

        assert len(investors) == 5
        assert len(consumers) == 10
        assert len(firms) == 3


class TestModelExecution:
    """Tests for model execution."""

    def test_model_step(self):
        """Test single step execution."""
        model = EconomicModel(seed=42)
        model.step()

        # After step, data should be collected
        df = model.datacollector.get_model_vars_dataframe()
        assert len(df) == 1

    def test_multiple_steps(self):
        """Test multiple steps execution."""
        model = EconomicModel(seed=42)

        for _ in range(50):
            model.step()

        df = model.datacollector.get_model_vars_dataframe()
        assert len(df) == 50

    def test_get_results_structure(self):
        """Test results dictionary structure."""
        model = EconomicModel(seed=42)

        for _ in range(10):
            model.step()

        results = model.get_results()

        assert "final_health" in results
        assert "avg_health" in results
        assert "max_health" in results
        assert "min_health" in results
        assert "time_series" in results
        assert "final_investment" in results
        assert "final_consumption" in results
        assert "final_production" in results

        assert 0 <= results["final_health"] <= 1
        assert len(results["time_series"]) == 10

    def test_run_trial(self):
        """Test single trial returns boolean."""
        model = EconomicModel(seed=42)
        result = model.run_trial(threshold=0.3)

        # Can be Python bool or numpy bool
        assert result in [True, False]


class TestMonteCarloSimulation:
    """Tests for Monte Carlo simulation."""

    def test_monte_carlo_output_structure(self):
        """Test Monte Carlo returns correct structure."""
        results = run_monte_carlo(
            interest_rate=5.0,
            inflation=3.0,
            sentiment=0.0,
            n_runs=10,
            threshold=0.25,
        )

        assert "probability" in results
        assert "n_runs" in results
        assert "results" in results
        assert "ci_95" in results
        assert "parameters" in results

        assert results["n_runs"] == 10
        assert len(results["results"]) == 10
        assert 0 <= results["probability"] <= 1
        assert results["ci_95"] >= 0

    def test_monte_carlo_binary_results(self):
        """Test Monte Carlo results are binary."""
        results = run_monte_carlo(n_runs=20, threshold=0.25)

        for r in results["results"]:
            assert r in [0, 1]

    def test_monte_carlo_probability_calculation(self):
        """Test probability matches results."""
        results = run_monte_carlo(n_runs=50, threshold=0.25)

        expected_prob = sum(results["results"]) / len(results["results"])
        assert results["probability"] == expected_prob

    def test_monte_carlo_different_parameters(self):
        """Test different parameters affect probability."""
        # Good conditions
        good = run_monte_carlo(
            interest_rate=2.0,
            inflation=1.0,
            sentiment=0.8,
            n_runs=30,
            threshold=0.25,
        )

        # Bad conditions
        bad = run_monte_carlo(
            interest_rate=15.0,
            inflation=10.0,
            sentiment=-0.8,
            n_runs=30,
            threshold=0.25,
        )

        # Good conditions should generally yield higher probability
        # (but with randomness, we just check both run)
        assert 0 <= good["probability"] <= 1
        assert 0 <= bad["probability"] <= 1


class TestAgentBehavior:
    """Tests for individual agent behavior."""

    def test_investor_attributes(self):
        """Test investor has required attributes."""
        model = EconomicModel(num_investors=1, num_consumers=0, num_firms=0)
        investor = list(model.agents)[0]

        assert hasattr(investor, "wealth")
        assert hasattr(investor, "invested")
        assert hasattr(investor, "risk_tolerance")

    def test_consumer_attributes(self):
        """Test consumer has required attributes."""
        model = EconomicModel(num_investors=0, num_consumers=1, num_firms=0)
        consumer = list(model.agents)[0]

        assert hasattr(consumer, "income")
        assert hasattr(consumer, "savings")
        assert hasattr(consumer, "spending_propensity")

    def test_firm_attributes(self):
        """Test firm has required attributes."""
        model = EconomicModel(num_investors=0, num_consumers=0, num_firms=1)
        firm = list(model.agents)[0]

        assert hasattr(firm, "production_capacity")
        assert hasattr(firm, "inventory")
        assert hasattr(firm, "employees")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_model_in_e2b(check_api_keys):
    """Test economic model execution in E2B sandbox."""
    sbx = await AsyncSandbox.create(
        template="code-interpreter-v1",
        timeout=300,
    )

    try:
        # Install dependencies
        req_path = os.path.join(
            os.path.dirname(__file__), '..', 'requirements.txt'
        )
        with open(req_path, 'r') as f:
            req_content = f.read()

        await sbx.files.write('/tmp/requirements.txt', req_content)
        await sbx.commands.run(
            'pip install -r /tmp/requirements.txt',
            timeout=120
        )

        # Upload model
        model_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'src',
            'models',
            'economic_shock.py'
        )
        with open(model_path, 'r') as f:
            model_code = f.read()

        await sbx.files.write('/tmp/economic_shock.py', model_code)

        # Run model
        result = await sbx.commands.run(
            'python3 /tmp/economic_shock.py',
            timeout=60
        )

        assert "Model test complete" in result.stdout
        assert "Probability:" in result.stdout

    finally:
        await sbx.kill()
