import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class VoterAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.candidate_preference = np.random.choice(['asfura', 'nasralla', 'moncada'], 
                                                      p=[0.40, 0.40, 0.20])
        self.turnout_probability = np.random.uniform(0.6, 0.95)
        self.susceptibility_to_influence = np.random.uniform(0.0, 0.3)
        self.voted = False
        self.final_vote = None

    def step(self):
        if not self.voted:
            influence_effect = self.model.foreign_influence * self.susceptibility_to_influence
            fraud_effect = self.model.fraud_level * np.random.uniform(0, 0.15)
            
            if self.candidate_preference == 'asfura':
                stay_probability = 0.85 + influence_effect + fraud_effect
            elif self.candidate_preference == 'nasralla':
                stay_probability = 0.85 - fraud_effect
            else:
                stay_probability = 0.80
            
            if np.random.random() > stay_probability:
                if self.candidate_preference == 'moncada':
                    self.candidate_preference = np.random.choice(['asfura', 'nasralla'])
                elif self.candidate_preference == 'nasralla' and influence_effect > 0.05:
                    self.candidate_preference = 'asfura'
            
            if np.random.random() < self.turnout_probability:
                self.voted = True
                self.final_vote = self.candidate_preference


class ElectoralOfficialAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.integrity = np.random.uniform(0.3, 0.9)
        self.votes_processed = 0
        self.asfura_boost = 0.0

    def step(self):
        fraud_pressure = self.model.fraud_level * (1 - self.integrity)
        if fraud_pressure > 0.3:
            self.asfura_boost = fraud_pressure * 0.05
        self.votes_processed += 1


class InternationalObserverAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.vigilance = np.random.uniform(0.5, 1.0)
        self.fraud_detected = 0.0

    def step(self):
        if self.model.fraud_level > 0.4:
            detection_chance = self.vigilance * 0.7
            if np.random.random() < detection_chance:
                self.fraud_detected += 0.1
                self.model.fraud_level *= 0.95


class CampaignOperativeAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.candidate = np.random.choice(['asfura', 'nasralla'], p=[0.55, 0.45])
        self.effectiveness = np.random.uniform(0.4, 0.9)
        self.resources = np.random.uniform(0.5, 1.0)

    def step(self):
        if self.candidate == 'asfura':
            boost = self.effectiveness * self.resources * self.model.foreign_influence * 0.01
            self.model.asfura_campaign_strength += boost
        else:
            boost = self.effectiveness * self.resources * 0.008
            self.model.nasralla_campaign_strength += boost


# Outcome computation
def compute_outcome(model):
    voters = [a for a in model.schedule.agents if isinstance(a, VoterAgent)]
    officials = [a for a in model.schedule.agents if isinstance(a, ElectoralOfficialAgent)]
    
    total_votes = sum(1 for v in voters if v.voted)
    if total_votes == 0:
        return 0.40
    
    asfura_votes = sum(1 for v in voters if v.voted and v.final_vote == 'asfura')
    nasralla_votes = sum(1 for v in voters if v.voted and v.final_vote == 'nasralla')
    
    official_boost = sum(o.asfura_boost for o in officials) / len(officials) if officials else 0.0
    asfura_votes *= (1 + official_boost)
    
    campaign_effect = (model.asfura_campaign_strength - model.nasralla_campaign_strength) * 0.5
    asfura_votes += campaign_effect * total_votes
    
    asfura_share = asfura_votes / (asfura_votes + nasralla_votes) if (asfura_votes + nasralla_votes) > 0 else 0.40
    
    base_probability = asfura_share
    fraud_penalty = max(0, (model.fraud_level - 0.5) * 0.1)
    
    final_probability = np.clip(base_probability - fraud_penalty, 0.3, 0.75)
    
    return final_probability


# Configuration
AGENT_CONFIG = {
    VoterAgent: 100,
    ElectoralOfficialAgent: 8,
    InternationalObserverAgent: 5,
    CampaignOperativeAgent: 12,
}

MODEL_PARAMS = {
    "foreign_influence": 0.35,
    "fraud_level": 0.45,
    "asfura_campaign_strength": 0.0,
    "nasralla_campaign_strength": 0.0,
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
