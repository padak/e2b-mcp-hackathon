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

class YoungVoter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.enthusiasm = np.random.uniform(0.6, 0.95)
        self.will_vote = np.random.random() < 0.28
        self.mamdani_support = np.random.random() < 0.75
        
    def step(self):
        if self.model.youth_mobilization > 0.6:
            self.will_vote = True
            self.enthusiasm = min(1.0, self.enthusiasm + 0.1)
        
        if self.will_vote and self.enthusiasm > 0.7:
            self.mamdani_support = np.random.random() < 0.80

class TraditionalVoter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.party_loyalty = np.random.uniform(0.4, 0.8)
        self.will_vote = np.random.random() < 0.65
        self.mamdani_support = np.random.random() < 0.35
        
    def step(self):
        cuomo_strength = self.model.cuomo_appeal
        if cuomo_strength > 0.5:
            self.mamdani_support = np.random.random() < (0.30 - cuomo_strength * 0.2)
        else:
            self.mamdani_support = np.random.random() < 0.40

class MinorityVoter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.progressive_affinity = np.random.uniform(0.6, 0.9)
        self.will_vote = np.random.random() < 0.70
        self.mamdani_support = np.random.random() < 0.65
        
    def step(self):
        if self.model.affordability_focus > 0.7:
            self.mamdani_support = np.random.random() < 0.75
            self.will_vote = True
        
        if self.progressive_affinity > 0.75:
            self.mamdani_support = np.random.random() < 0.82

class SwingVoter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.economic_concern = np.random.uniform(0.5, 1.0)
        self.will_vote = np.random.random() < 0.55
        self.mamdani_support = np.random.random() < 0.45
        
    def step(self):
        campaign_momentum = self.model.youth_mobilization * self.model.affordability_focus
        if campaign_momentum > 0.5:
            self.mamdani_support = np.random.random() < (0.45 + campaign_momentum * 0.15)
        
        if self.economic_concern > 0.75 and self.model.affordability_focus > 0.7:
            self.mamdani_support = np.random.random() < 0.60

def compute_outcome(model):
    total_votes = 0
    mamdani_votes = 0
    other_votes = 0
    
    for agent in model.schedule.agents:
        if agent.will_vote:
            total_votes += 1
            if agent.mamdani_support:
                mamdani_votes += 1
            else:
                other_votes += 1
    
    if total_votes == 0:
        return 0.0
    
    mamdani_percentage = mamdani_votes / total_votes
    other_percentage = other_votes / total_votes
    
    margin = mamdani_percentage - other_percentage
    
    margin_probability = (margin - 0.05) / 0.25
    margin_probability = max(0.0, min(1.0, margin_probability))
    
    return margin_probability

AGENT_CONFIG = {
    YoungVoter: 180,
    TraditionalVoter: 400,
    MinorityVoter: 250,
    SwingVoter: 170,
}

MODEL_PARAMS = {
    "youth_mobilization": 0.75,
    "affordability_focus": 0.80,
    "cuomo_appeal": 0.45,
}

THRESHOLD = 0.52
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

        # Report progress every 10 runs
        if (seed + 1) % 10 == 0 or seed == n_runs - 1:
            print(f"PROGRESS:{seed + 1}/{n_runs}", flush=True)

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
