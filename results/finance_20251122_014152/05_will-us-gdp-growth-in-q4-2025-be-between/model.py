import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class ConsumerAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.spending_confidence = np.random.uniform(0.3, 0.7)
        self.income_growth = np.random.uniform(-0.02, 0.03)
        
    def step(self):
        interest_rate_impact = -self.model.interest_rate_level * 0.15
        shutdown_impact = -self.model.government_shutdown_severity * 0.1
        self.spending_confidence += interest_rate_impact + shutdown_impact + self.income_growth * 0.5
        self.spending_confidence = np.clip(self.spending_confidence, 0, 1)


class BusinessAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.investment_rate = np.random.uniform(0.4, 0.8)
        self.financing_cost_sensitivity = np.random.uniform(0.5, 1.0)
        
    def step(self):
        cost_impact = -self.model.interest_rate_level * self.financing_cost_sensitivity * 0.12
        policy_uncertainty_impact = -self.model.policy_uncertainty * 0.08
        global_demand_impact = self.model.global_demand_strength * 0.06
        self.investment_rate += cost_impact + policy_uncertainty_impact + global_demand_impact
        self.investment_rate = np.clip(self.investment_rate, 0, 1)


class GovernmentAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.spending_capacity = np.random.uniform(0.5, 0.9)
        
    def step(self):
        shutdown_drag = -self.model.government_shutdown_severity * 0.25
        self.spending_capacity += shutdown_drag
        self.spending_capacity = np.clip(self.spending_capacity, 0, 1)


class FederalReserveAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.monetary_stimulus = np.random.uniform(0.2, 0.5)
        
    def step(self):
        if self.model.interest_rate_level > 0.6:
            self.monetary_stimulus -= 0.02
        else:
            self.monetary_stimulus += 0.01
        self.monetary_stimulus = np.clip(self.monetary_stimulus, 0, 1)


# Outcome computation
def compute_outcome(model):
    consumers = [a for a in model.schedule.agents if isinstance(a, ConsumerAgent)]
    businesses = [a for a in model.schedule.agents if isinstance(a, BusinessAgent)]
    government = [a for a in model.schedule.agents if isinstance(a, GovernmentAgent)]
    fed = [a for a in model.schedule.agents if isinstance(a, FederalReserveAgent)]
    
    avg_consumer_spending = np.mean([c.spending_confidence for c in consumers]) if consumers else 0.5
    avg_business_investment = np.mean([b.investment_rate for b in businesses]) if businesses else 0.6
    avg_govt_spending = np.mean([g.spending_capacity for g in government]) if government else 0.7
    avg_fed_stimulus = np.mean([f.monetary_stimulus for f in fed]) if fed else 0.35
    
    consumer_weight = 0.45
    business_weight = 0.30
    government_weight = 0.15
    fed_weight = 0.10
    
    gdp_indicator = (
        avg_consumer_spending * consumer_weight +
        avg_business_investment * business_weight +
        avg_govt_spending * government_weight +
        avg_fed_stimulus * fed_weight
    )
    
    baseline_growth = 0.017
    growth_multiplier = 0.025
    estimated_gdp_growth = baseline_growth + (gdp_indicator - 0.5) * growth_multiplier
    
    lower_bound = 0.015
    upper_bound = 0.020
    
    if lower_bound <= estimated_gdp_growth <= upper_bound:
        in_range_score = 1.0
    else:
        distance = min(abs(estimated_gdp_growth - lower_bound), abs(estimated_gdp_growth - upper_bound))
        in_range_score = max(0, 1 - distance * 50)
    
    return in_range_score


# Configuration
AGENT_CONFIG = {
    ConsumerAgent: 20,
    BusinessAgent: 15,
    GovernmentAgent: 3,
    FederalReserveAgent: 2,
}

MODEL_PARAMS = {
    "interest_rate_level": 0.65,
    "government_shutdown_severity": 0.35,
    "policy_uncertainty": 0.55,
    "global_demand_strength": 0.45,
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

def run_monte_carlo(n_runs: int = 200, threshold: float = 0.5, mode: str = "threshold"):
    results = []
    outcomes = []

    for seed in range(n_runs):
        model = SimulationModel(seed=seed)

        # Run simulation
        for _ in range(100):
            model.step()
        model_results = model.get_results()
        outcome_value = model_results["final_outcome"]
        outcomes.append(outcome_value)

        if mode == "probability":
            # Use outcome directly as probability, sample from it
            success = np.random.random() < outcome_value
        else:
            # Traditional threshold mode
            success = outcome_value > threshold

        results.append(1 if success else 0)

    probability = sum(results) / len(results)
    ci_95 = 1.96 * (probability * (1 - probability) / n_runs) ** 0.5

    return {
        "probability": probability,
        "n_runs": n_runs,
        "results": results,
        "ci_95": ci_95,
        "outcome_mean": float(np.mean(outcomes)),
        "outcome_std": float(np.std(outcomes)),
        "outcome_min": float(np.min(outcomes)),
        "outcome_max": float(np.max(outcomes)),
    }

if __name__ == "__main__":
    import os
    mode = os.getenv("SIMULATION_MODE", "threshold")
    results = run_monte_carlo(n_runs=200, threshold=THRESHOLD, mode=mode)
    print(json.dumps(results))
