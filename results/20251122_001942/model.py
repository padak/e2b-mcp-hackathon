import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np

class Household(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.spending_confidence = np.random.uniform(0.3, 0.7)
        self.employment_status = np.random.choice([True, False], p=[0.96, 0.04])
        
    def step(self):
        # Spending confidence influenced by policy uncertainty and inflation
        policy_impact = -self.model.policy_uncertainty * 0.15
        inflation_impact = -self.model.inflation_rate * 0.1
        
        # Unemployment affects confidence
        if not self.employment_status:
            self.spending_confidence *= 0.9
        
        # Update confidence
        self.spending_confidence += policy_impact + inflation_impact
        self.spending_confidence = np.clip(self.spending_confidence, 0.1, 1.0)
        
        # Employment can change based on economic conditions
        if self.model.gdp_growth < 0.005:
            if np.random.random() < 0.02:
                self.employment_status = False

class Corporation(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.profit_margin = np.random.uniform(0.4, 0.8)
        self.investment_rate = np.random.uniform(0.3, 0.7)
        
    def step(self):
        # Profits affected by GDP growth and consumer spending
        avg_household_spending = np.mean([a.spending_confidence for a in self.model.schedule.agents if isinstance(a, Household)])
        
        growth_impact = self.model.gdp_growth * 10
        demand_impact = avg_household_spending * 0.3
        
        self.profit_margin += (growth_impact + demand_impact - 0.5) * 0.1
        self.profit_margin = np.clip(self.profit_margin, 0.2, 1.0)
        
        # Investment decisions based on profitability and policy certainty
        if self.profit_margin > 0.6 and self.model.policy_uncertainty < 0.5:
            self.investment_rate += 0.05
        else:
            self.investment_rate -= 0.03
            
        self.investment_rate = np.clip(self.investment_rate, 0.1, 0.9)

class FederalReserve(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.interest_rate_sentiment = 0.5
        
    def step(self):
        # Fed responds to inflation and growth
        if self.model.inflation_rate > 0.03:
            self.interest_rate_sentiment += 0.05
        elif self.model.gdp_growth < 0.01:
            self.interest_rate_sentiment -= 0.05
            
        self.interest_rate_sentiment = np.clip(self.interest_rate_sentiment, 0.0, 1.0)
        
        # Fed policy affects GDP and inflation
        if self.interest_rate_sentiment > 0.6:
            self.model.gdp_growth *= 0.95
            self.model.inflation_rate *= 0.98
        elif self.interest_rate_sentiment < 0.4:
            self.model.gdp_growth *= 1.02
            self.model.inflation_rate *= 1.01

class PolicyMaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.fiscal_stimulus = np.random.uniform(0.2, 0.6)
        
    def step(self):
        # Policy makers respond to economic weakness
        unemployment_rate = 1.0 - np.mean([a.employment_status for a in self.model.schedule.agents if isinstance(a, Household)])
        
        if unemployment_rate > 0.06 or self.model.gdp_growth < 0.005:
            self.fiscal_stimulus += 0.05
        else:
            self.fiscal_stimulus -= 0.02
            
        self.fiscal_stimulus = np.clip(self.fiscal_stimulus, 0.1, 0.8)
        
        # Fiscal stimulus affects GDP but increases policy uncertainty temporarily
        self.model.gdp_growth += self.fiscal_stimulus * 0.01
        if self.fiscal_stimulus > 0.5:
            self.model.policy_uncertainty = min(0.8, self.model.policy_uncertainty + 0.05)

def compute_outcome(model):
    # Recession indicators: negative GDP, high unemployment, low corporate health
    households = [a for a in model.schedule.agents if isinstance(a, Household)]
    corporations = [a for a in model.schedule.agents if isinstance(a, Corporation)]
    
    unemployment_rate = 1.0 - np.mean([h.employment_status for h in households])
    avg_spending = np.mean([h.spending_confidence for h in households])
    avg_profit = np.mean([c.profit_margin for c in corporations])
    avg_investment = np.mean([c.investment_rate for c in corporations])
    
    # Recession probability increases with:
    # - Negative/low GDP growth
    # - High unemployment
    # - Low consumer spending
    # - Low corporate profits and investment
    
    gdp_factor = max(0, 1.0 - (model.gdp_growth / 0.02))  # Higher when GDP is low/negative
    unemployment_factor = unemployment_rate / 0.08  # Normalized by recession threshold
    spending_factor = 1.0 - avg_spending
    corporate_factor = (1.0 - avg_profit + 1.0 - avg_investment) / 2.0
    
    recession_probability = (
        gdp_factor * 0.35 +
        unemployment_factor * 0.25 +
        spending_factor * 0.20 +
        corporate_factor * 0.20
    )
    
    return np.clip(recession_probability, 0.0, 1.0)

AGENT_CONFIG = {
    Household: 25,
    Corporation: 15,
    FederalReserve: 1,
    PolicyMaker: 3,
}

MODEL_PARAMS = {
    "gdp_growth": 0.0025,
    "inflation_rate": 0.025,
    "policy_uncertainty": 0.45,
}

THRESHOLD = 0.5
# ============== LLM GENERATED CODE END ==============

class SimulationModel(Model):
    def __init__(self, seed=None):
        super().__init__()

        if seed is not None:
            np.random.seed(seed)

        # Initialize model state
        for key, value in MODEL_PARAMS.items():
            setattr(self, key, value)

        # Create scheduler (Mesa 2.x)
        self.schedule = RandomActivation(self)

        # Create agents from config
        agent_id = 0
        for agent_class, count in AGENT_CONFIG.items():
            for _ in range(count):
                agent = agent_class(agent_id, self)
                self.schedule.add(agent)
                agent_id += 1

        self.datacollector = DataCollector(
            model_reporters={"Outcome": compute_outcome}
        )

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def get_results(self):
        data = self.datacollector.get_model_vars_dataframe()
        return {
            "final_outcome": data["Outcome"].iloc[-1] if len(data) > 0 else 0,
            "history": data["Outcome"].tolist()
        }

    def run_trial(self, threshold: float = 0.5) -> bool:
        for _ in range(100):
            self.step()
        results = self.get_results()
        return results["final_outcome"] > threshold

def run_monte_carlo(n_runs: int = 200, threshold: float = 0.5):
    results = []
    for seed in range(n_runs):
        model = SimulationModel(seed=seed)
        outcome = model.run_trial(threshold)
        results.append(1 if outcome else 0)

    probability = sum(results) / len(results)
    ci_95 = 1.96 * (probability * (1 - probability) / n_runs) ** 0.5

    return {
        "probability": probability,
        "n_runs": n_runs,
        "results": results,
        "ci_95": ci_95
    }

if __name__ == "__main__":
    results = run_monte_carlo(n_runs=200, threshold=THRESHOLD)
    print(json.dumps(results))
