"""
Economic Shock Simulation Model using Mesa Framework.

This is a reference/fallback model for simulating economic scenarios
based on interest rates, inflation, and market sentiment.

Agents:
- Investors: React to interest rates and sentiment
- Consumers: Spending behavior based on inflation and sentiment
- Firms: Production decisions based on all factors

Output: Probability of positive economic outcome (binary for Monte Carlo)
"""

import random
from mesa import Agent, Model
from mesa.datacollection import DataCollector


class InvestorAgent(Agent):
    """Investor agent that makes investment decisions based on interest rates and sentiment."""

    def __init__(self, unique_id: int, model: "EconomicModel"):
        super().__init__(model)
        self.unique_id = unique_id
        self.wealth = random.uniform(50, 150)
        self.invested = 0
        self.risk_tolerance = random.uniform(0.3, 0.9)

    def step(self):
        # Higher interest rates reduce investment appetite
        rate_effect = 1 - (self.model.interest_rate / 20)  # Normalize to 0-1 range

        # Positive sentiment increases investment
        sentiment_effect = (self.model.sentiment + 1) / 2  # Normalize -1 to 1 -> 0 to 1

        # Investment decision
        invest_probability = rate_effect * sentiment_effect * self.risk_tolerance

        if random.random() < invest_probability:
            # Invest portion of wealth
            investment = self.wealth * random.uniform(0.1, 0.3)
            self.invested += investment
            self.wealth -= investment
            self.model.total_investment += investment
        else:
            # Disinvest if conditions are poor
            if self.invested > 0 and random.random() > invest_probability:
                disinvest = self.invested * random.uniform(0.1, 0.2)
                self.invested -= disinvest
                self.wealth += disinvest
                self.model.total_investment -= disinvest


class ConsumerAgent(Agent):
    """Consumer agent that decides spending based on inflation and sentiment."""

    def __init__(self, unique_id: int, model: "EconomicModel"):
        super().__init__(model)
        self.unique_id = unique_id
        self.income = random.uniform(30, 100)
        self.savings = random.uniform(10, 50)
        self.spending_propensity = random.uniform(0.4, 0.8)

    def step(self):
        # Higher inflation reduces real purchasing power
        inflation_effect = 1 - (self.model.inflation / 20)  # High inflation = less spending

        # Positive sentiment increases spending
        sentiment_effect = (self.model.sentiment + 1) / 2

        # Spending decision
        spend_amount = self.income * self.spending_propensity * inflation_effect * sentiment_effect

        if spend_amount > 0:
            self.model.total_consumption += spend_amount
            # Save the rest
            savings_amount = self.income - spend_amount
            self.savings += savings_amount * 0.1


class FirmAgent(Agent):
    """Firm agent that makes production decisions based on economic conditions."""

    def __init__(self, unique_id: int, model: "EconomicModel"):
        super().__init__(model)
        self.unique_id = unique_id
        self.production_capacity = random.uniform(50, 150)
        self.inventory = random.uniform(10, 30)
        self.employees = random.randint(5, 20)

    def step(self):
        # Lower interest rates encourage borrowing for production
        rate_effect = 1 - (self.model.interest_rate / 15)

        # Higher inflation may encourage production to meet demand
        inflation_effect = 0.5 + (self.model.inflation / 20)

        # Positive sentiment increases production
        sentiment_effect = (self.model.sentiment + 1) / 2

        # Production decision
        production_factor = rate_effect * inflation_effect * sentiment_effect
        production = self.production_capacity * production_factor

        self.model.total_production += production
        self.inventory += production * 0.1

        # Hiring/firing based on production
        if production_factor > 0.6:
            self.employees += random.randint(0, 2)
            self.model.employment_change += 1
        elif production_factor < 0.4:
            fired = min(self.employees, random.randint(0, 2))
            self.employees -= fired
            self.model.employment_change -= 1


def compute_economic_health(model):
    """Compute overall economic health indicator."""
    if len(model.agents) == 0:
        return 0

    # Weighted combination of economic indicators (scaled for ~100 agents)
    investment_score = min(model.total_investment / 500, 1)
    consumption_score = min(model.total_consumption / 1500, 1)
    production_score = min(model.total_production / 2000, 1)
    employment_score = (model.employment_change + 20) / 40  # Normalize

    health = (
        0.3 * investment_score +
        0.3 * consumption_score +
        0.25 * production_score +
        0.15 * employment_score
    )

    return min(max(health, 0), 1)


class EconomicModel(Model):
    """
    Main economic simulation model.

    Parameters:
        interest_rate: Central bank interest rate (0-20%)
        inflation: Current inflation rate (0-20%)
        sentiment: Market sentiment (-1 to 1)
        num_investors: Number of investor agents
        num_consumers: Number of consumer agents
        num_firms: Number of firm agents
    """

    def __init__(
        self,
        interest_rate: float = 5.0,
        inflation: float = 3.0,
        sentiment: float = 0.0,
        num_investors: int = 30,
        num_consumers: int = 50,
        num_firms: int = 20,
        seed: int = None
    ):
        super().__init__()

        if seed is not None:
            random.seed(seed)

        self.interest_rate = interest_rate
        self.inflation = inflation
        self.sentiment = sentiment

        # Aggregate metrics
        self.total_investment = 0
        self.total_consumption = 0
        self.total_production = 0
        self.employment_change = 0

        # Create agents (Mesa 3.x auto-registers agents)
        for i in range(num_investors):
            InvestorAgent(i, self)

        for i in range(num_consumers):
            ConsumerAgent(num_investors + i, self)

        for i in range(num_firms):
            FirmAgent(num_investors + num_consumers + i, self)

        # Data collection
        self.datacollector = DataCollector(
            model_reporters={
                "Economic_Health": compute_economic_health,
                "Total_Investment": lambda m: m.total_investment,
                "Total_Consumption": lambda m: m.total_consumption,
                "Total_Production": lambda m: m.total_production,
                "Employment_Change": lambda m: m.employment_change,
            }
        )

    def step(self):
        """Advance the model by one step."""
        # Reset step counters
        self.total_investment = 0
        self.total_consumption = 0
        self.total_production = 0
        self.employment_change = 0

        # Run all agents in random order (Mesa 3.x)
        self.agents.shuffle_do("step")

        # Collect data after step
        self.datacollector.collect(self)

    def get_results(self) -> dict:
        """Get simulation results as a dictionary."""
        df = self.datacollector.get_model_vars_dataframe()

        if len(df) == 0:
            return {
                "final_health": 0,
                "avg_health": 0,
                "time_series": [],
            }

        return {
            "final_health": df["Economic_Health"].iloc[-1] if len(df) > 0 else 0,
            "avg_health": df["Economic_Health"].mean(),
            "max_health": df["Economic_Health"].max(),
            "min_health": df["Economic_Health"].min(),
            "time_series": df["Economic_Health"].tolist(),
            "final_investment": df["Total_Investment"].iloc[-1] if len(df) > 0 else 0,
            "final_consumption": df["Total_Consumption"].iloc[-1] if len(df) > 0 else 0,
            "final_production": df["Total_Production"].iloc[-1] if len(df) > 0 else 0,
        }

    def run_trial(self, threshold: float = 0.5) -> bool:
        """
        Run a single trial and return binary outcome.

        Args:
            threshold: Health threshold for positive outcome

        Returns:
            True if economic health exceeds threshold, False otherwise
        """
        # Run for 100 steps
        for _ in range(100):
            self.step()

        results = self.get_results()
        return results["final_health"] > threshold


def run_monte_carlo(
    interest_rate: float = 5.0,
    inflation: float = 3.0,
    sentiment: float = 0.0,
    n_runs: int = 200,
    threshold: float = 0.5
) -> dict:
    """
    Run Monte Carlo simulation for probability estimation.

    Args:
        interest_rate: Interest rate parameter
        inflation: Inflation parameter
        sentiment: Sentiment parameter (-1 to 1)
        n_runs: Number of simulation runs
        threshold: Threshold for positive outcome

    Returns:
        Dictionary with probability and confidence interval
    """
    results = []

    for seed in range(n_runs):
        model = EconomicModel(
            interest_rate=interest_rate,
            inflation=inflation,
            sentiment=sentiment,
            seed=seed
        )
        outcome = model.run_trial(threshold)
        results.append(1 if outcome else 0)

    probability = sum(results) / len(results)
    ci_95 = 1.96 * (probability * (1 - probability) / n_runs) ** 0.5

    return {
        "probability": probability,
        "n_runs": n_runs,
        "results": results,
        "ci_95": ci_95,
        "parameters": {
            "interest_rate": interest_rate,
            "inflation": inflation,
            "sentiment": sentiment,
            "threshold": threshold,
        }
    }


# Example usage and testing
if __name__ == "__main__":
    print("Testing Economic Shock Model...")
    print("=" * 50)

    # Single model test
    model = EconomicModel(
        interest_rate=5.5,
        inflation=3.2,
        sentiment=0.2,
        num_investors=30,
        num_consumers=50,
        num_firms=20
    )

    print(f"Parameters: rate={model.interest_rate}%, inflation={model.inflation}%, sentiment={model.sentiment}")
    print(f"Agents: {len(model.agents)}")

    # Run simulation
    for _ in range(100):
        model.step()

    results = model.get_results()
    print(f"\nSingle Run Results:")
    print(f"  Final Health: {results['final_health']:.3f}")
    print(f"  Avg Health: {results['avg_health']:.3f}")
    print(f"  Final Investment: {results['final_investment']:.1f}")
    print(f"  Final Consumption: {results['final_consumption']:.1f}")
    print(f"  Final Production: {results['final_production']:.1f}")

    # Monte Carlo test (small run for quick test)
    print("\n" + "=" * 50)
    print("Monte Carlo Test (50 runs)...")

    mc_results = run_monte_carlo(
        interest_rate=5.5,
        inflation=3.2,
        sentiment=0.2,
        n_runs=50,
        threshold=0.25
    )

    print(f"\nMonte Carlo Results:")
    print(f"  Probability: {mc_results['probability']:.1%}")
    print(f"  95% CI: ±{mc_results['ci_95']:.1%}")
    print(f"  Runs: {mc_results['n_runs']}")

    print("\n✓ Model test complete!")
