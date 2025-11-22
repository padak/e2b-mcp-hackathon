import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class FedOfficial(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.rate_cut_preference = np.random.uniform(1.5, 3.5)
        self.inflation_sensitivity = np.random.uniform(0.6, 1.0)
        self.labor_sensitivity = np.random.uniform(0.6, 1.0)

    def step(self):
        inflation_factor = (3.0 - self.model.inflation_level) * self.inflation_sensitivity
        labor_factor = (self.model.unemployment_rate - 4.0) * self.labor_sensitivity
        
        self.rate_cut_preference += (inflation_factor * 0.15 + labor_factor * 0.2)
        self.rate_cut_preference = np.clip(self.rate_cut_preference, 0, 5)


class MarketParticipant(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.cut_expectation = np.random.uniform(1.8, 3.2)
        self.confidence = np.random.uniform(0.5, 0.9)

    def step(self):
        fed_avg = np.mean([agent.rate_cut_preference for agent in self.model.schedule.agents if isinstance(agent, FedOfficial)])
        
        adjustment = (fed_avg - self.cut_expectation) * 0.1 * self.confidence
        self.cut_expectation += adjustment
        
        economic_signal = (self.model.gdp_growth - 2.0) * 0.2
        self.cut_expectation -= economic_signal
        
        self.cut_expectation = np.clip(self.cut_expectation, 0, 5)


class BankEconomist(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.forecast = np.random.uniform(1.5, 3.0)
        self.dovish_bias = np.random.uniform(-0.3, 0.3)

    def step(self):
        if self.model.inflation_level > 2.5:
            self.forecast -= 0.1
        elif self.model.inflation_level < 2.0:
            self.forecast += 0.15
        
        if self.model.unemployment_rate > 4.5:
            self.forecast += 0.2
        elif self.model.unemployment_rate < 3.8:
            self.forecast -= 0.1
        
        self.forecast += self.dovish_bias * 0.05
        self.forecast = np.clip(self.forecast, 0, 5)


class PolicyMaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.fiscal_stance = np.random.choice(['expansionary', 'neutral', 'restrictive'])
        self.influence = np.random.uniform(0.3, 0.7)

    def step(self):
        if self.fiscal_stance == 'expansionary':
            self.model.inflation_level += 0.02 * self.influence
        elif self.fiscal_stance == 'restrictive':
            self.model.inflation_level -= 0.01 * self.influence
        
        self.model.gdp_growth += np.random.uniform(-0.05, 0.05) * self.influence


# Outcome computation
def compute_outcome(model):
    fed_officials = [agent for agent in model.schedule.agents if isinstance(agent, FedOfficial)]
    market_participants = [agent for agent in model.schedule.agents if isinstance(agent, MarketParticipant)]
    economists = [agent for agent in model.schedule.agents if isinstance(agent, BankEconomist)]
    
    fed_avg_cuts = np.mean([agent.rate_cut_preference for agent in fed_officials])
    market_avg_cuts = np.mean([agent.cut_expectation for agent in market_participants])
    economist_avg_cuts = np.mean([agent.forecast for agent in economists])
    
    weighted_avg = (fed_avg_cuts * 0.5 + market_avg_cuts * 0.25 + economist_avg_cuts * 0.25)
    
    inflation_penalty = max(0, model.inflation_level - 2.5) * 0.15
    unemployment_boost = max(0, model.unemployment_rate - 4.2) * 0.2
    
    adjusted_cuts = weighted_avg - inflation_penalty + unemployment_boost
    
    probability = 1 / (1 + np.exp(-2 * (adjusted_cuts - 2.5)))
    
    return probability


# Configuration
AGENT_CONFIG = {
    FedOfficial: 12,
    MarketParticipant: 20,
    BankEconomist: 8,
    PolicyMaker: 5,
}

MODEL_PARAMS = {
    "inflation_level": 2.3,
    "unemployment_rate": 4.1,
    "gdp_growth": 2.2,
}

THRESHOLD = 0.65
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
