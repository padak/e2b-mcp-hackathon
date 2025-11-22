import random
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np

class MilitaryAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.loyalty_to_maduro = np.random.uniform(0.7, 0.95)
        self.economic_pressure_sensitivity = np.random.uniform(0.3, 0.7)
        
    def step(self):
        economic_impact = self.model.economic_crisis * self.economic_pressure_sensitivity
        international_impact = self.model.international_pressure * 0.3
        
        self.loyalty_to_maduro -= (economic_impact * 0.1 + international_impact * 0.05)
        self.loyalty_to_maduro = max(0.0, min(1.0, self.loyalty_to_maduro))
        
        if self.loyalty_to_maduro < 0.4 and np.random.random() < 0.1:
            self.loyalty_to_maduro = 0.2

class OppositionAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.mobilization_capacity = np.random.uniform(0.5, 0.8)
        self.international_support = np.random.uniform(0.6, 0.9)
        
    def step(self):
        self.mobilization_capacity += self.model.international_pressure * 0.05
        self.mobilization_capacity = min(1.0, self.mobilization_capacity)
        
        if self.model.popular_protest_level > 0.7:
            self.mobilization_capacity += 0.03
            self.mobilization_capacity = min(1.0, self.mobilization_capacity)

class RegimeEliteAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.regime_loyalty = np.random.uniform(0.6, 0.9)
        self.corruption_benefit = np.random.uniform(0.5, 0.9)
        
    def step(self):
        avg_military_loyalty = np.mean([a.loyalty_to_maduro for a in self.model.schedule.agents if isinstance(a, MilitaryAgent)])
        
        if avg_military_loyalty < 0.5:
            self.regime_loyalty -= 0.15
        
        economic_loss = self.model.economic_crisis * 0.4
        self.regime_loyalty -= economic_loss * 0.08
        self.regime_loyalty = max(0.0, min(1.0, self.regime_loyalty))

class InternationalActorAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.intervention_willingness = np.random.uniform(0.2, 0.5)
        self.sanction_strength = np.random.uniform(0.4, 0.7)
        
    def step(self):
        avg_opposition_strength = np.mean([a.mobilization_capacity for a in self.model.schedule.agents if isinstance(a, OppositionAgent)])
        
        if avg_opposition_strength > 0.7:
            self.intervention_willingness += 0.02
            self.sanction_strength += 0.03
        
        self.intervention_willingness = min(0.6, self.intervention_willingness)
        self.sanction_strength = min(1.0, self.sanction_strength)

def compute_outcome(model):
    military_agents = [a for a in model.schedule.agents if isinstance(a, MilitaryAgent)]
    opposition_agents = [a for a in model.schedule.agents if isinstance(a, OppositionAgent)]
    regime_agents = [a for a in model.schedule.agents if isinstance(a, RegimeEliteAgent)]
    international_agents = [a for a in model.schedule.agents if isinstance(a, InternationalActorAgent)]
    
    avg_military_loyalty = np.mean([a.loyalty_to_maduro for a in military_agents]) if military_agents else 0.8
    avg_opposition_strength = np.mean([a.mobilization_capacity for a in opposition_agents]) if opposition_agents else 0.5
    avg_regime_loyalty = np.mean([a.regime_loyalty for a in regime_agents]) if regime_agents else 0.7
    avg_international_pressure = np.mean([a.sanction_strength for a in international_agents]) if international_agents else 0.5
    
    military_defection_prob = 1.0 - avg_military_loyalty
    regime_collapse_prob = 1.0 - avg_regime_loyalty
    opposition_success_prob = avg_opposition_strength
    international_impact = avg_international_pressure * 0.5
    
    maduro_ouster_probability = (
        military_defection_prob * 0.45 +
        regime_collapse_prob * 0.25 +
        opposition_success_prob * 0.20 +
        international_impact * 0.10
    )
    
    return maduro_ouster_probability

AGENT_CONFIG = {
    MilitaryAgent: 15,
    OppositionAgent: 12,
    RegimeEliteAgent: 10,
    InternationalActorAgent: 8,
}

MODEL_PARAMS = {
    "economic_crisis": 0.75,
    "international_pressure": 0.65,
    "popular_protest_level": 0.60,
}

THRESHOLD = 0.92
# ============== LLM GENERATED CODE END ==============

class SimulationModel(Model):
    def __init__(self, seed=None):
        super().__init__()

        if seed is not None:
            random.seed(seed)

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
