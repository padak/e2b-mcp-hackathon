import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class FedPolicymaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.dovish_tendency = np.random.uniform(0.3, 0.7)
        self.inflation_concern = np.random.uniform(0.4, 0.8)
        self.labor_concern = np.random.uniform(0.3, 0.7)
        self.vote_for_cut = 0.0
        
    def step(self):
        inflation_pressure = self.model.core_pce_inflation - 2.0
        labor_weakness = max(0, 4.5 - self.model.unemployment_rate)
        
        cut_score = (
            self.dovish_tendency * 0.3 +
            (1 - self.inflation_concern) * (inflation_pressure / 2.0) * 0.4 +
            self.labor_concern * labor_weakness * 0.3
        )
        
        self.vote_for_cut = min(1.0, max(0.0, cut_score))

class MarketTrader(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.risk_tolerance = np.random.uniform(0.2, 0.8)
        self.expectation_cut = np.random.uniform(0.5, 0.8)
        
    def step(self):
        fed_signals = np.mean([agent.vote_for_cut for agent in self.model.schedule.agents 
                               if isinstance(agent, FedPolicymaker)])
        
        economic_strength = (self.model.gdp_growth / 2.0) * 0.5 + (1 - self.model.core_pce_inflation / 4.0) * 0.5
        
        adjustment = (fed_signals - 0.5) * 0.3 + (economic_strength - 0.5) * 0.2
        self.expectation_cut = np.clip(self.expectation_cut + adjustment * self.risk_tolerance, 0.0, 1.0)

class Economist(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.inflation_weight = np.random.uniform(0.4, 0.7)
        self.growth_weight = 1 - self.inflation_weight
        self.forecast_no_change = 0.0
        
    def step(self):
        inflation_stable = 1 - abs(self.model.core_pce_inflation - 2.0) / 2.0
        growth_strong = self.model.gdp_growth / 3.0
        
        stability_score = (
            inflation_stable * self.inflation_weight +
            growth_strong * self.growth_weight
        )
        
        self.forecast_no_change = np.clip(stability_score, 0.0, 1.0)

class BusinessLeader(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.investment_sensitivity = np.random.uniform(0.3, 0.8)
        self.preference_stable_rates = 0.0
        
    def step(self):
        market_uncertainty = 1 - np.mean([agent.expectation_cut for agent in self.model.schedule.agents 
                                          if isinstance(agent, MarketTrader)])
        
        growth_outlook = min(1.0, self.model.gdp_growth / 2.0)
        
        self.preference_stable_rates = (
            market_uncertainty * 0.4 +
            growth_outlook * 0.6
        ) * self.investment_sensitivity

# Outcome computation
def compute_outcome(model):
    fed_votes = [agent.vote_for_cut for agent in model.schedule.agents 
                 if isinstance(agent, FedPolicymaker)]
    fed_avg_cut = np.mean(fed_votes) if fed_votes else 0.5
    
    market_expectations = [agent.expectation_cut for agent in model.schedule.agents 
                           if isinstance(agent, MarketTrader)]
    market_avg_cut = np.mean(market_expectations) if market_expectations else 0.65
    
    economist_forecasts = [agent.forecast_no_change for agent in model.schedule.agents 
                           if isinstance(agent, Economist)]
    economist_avg_no_change = np.mean(economist_forecasts) if economist_forecasts else 0.35
    
    business_preferences = [agent.preference_stable_rates for agent in model.schedule.agents 
                            if isinstance(agent, BusinessLeader)]
    business_avg_stable = np.mean(business_preferences) if business_preferences else 0.4
    
    inflation_factor = max(0, (model.core_pce_inflation - 2.0) / 2.0)
    growth_factor = min(1.0, model.gdp_growth / 2.0)
    
    prob_no_change = (
        (1 - fed_avg_cut) * 0.45 +
        (1 - market_avg_cut) * 0.15 +
        economist_avg_no_change * 0.20 +
        business_avg_stable * 0.10 +
        inflation_factor * 0.05 +
        growth_factor * 0.05
    )
    
    return prob_no_change

# Configuration
AGENT_CONFIG = {
    FedPolicymaker: 12,
    MarketTrader: 20,
    Economist: 10,
    BusinessLeader: 8,
}

MODEL_PARAMS = {
    "core_pce_inflation": 2.6,
    "unemployment_rate": 4.1,
    "gdp_growth": 1.5,
}

THRESHOLD = 0.35
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
