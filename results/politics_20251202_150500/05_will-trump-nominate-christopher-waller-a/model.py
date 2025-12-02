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

class TrumpAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.preference_for_waller = 0.15
        self.preference_for_hassett = 0.70
        self.influence_from_advisors = 0.0
        
    def step(self):
        advisor_support = np.mean([a.waller_support for a in self.model.schedule.agents if isinstance(a, AdvisorAgent)])
        self.influence_from_advisors = advisor_support * self.model.advisor_influence_weight
        
        hassett_momentum = np.mean([c.hassett_strength for c in self.model.schedule.agents if isinstance(c, CompetitorAgent)])
        self.preference_for_hassett = min(0.90, 0.70 + hassett_momentum * 0.3)
        
        waller_dovish_boost = np.mean([w.dovish_positioning for w in self.model.schedule.agents if isinstance(w, WallerAgent)])
        self.preference_for_waller = 0.15 + waller_dovish_boost * 0.25 + self.influence_from_advisors * 0.15

class WallerAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.dovish_positioning = np.random.uniform(0.6, 0.8)
        self.fed_experience = 0.85
        self.public_engagement = np.random.uniform(0.4, 0.6)
        self.hawkish_history_penalty = -0.3
        
    def step(self):
        self.dovish_positioning = min(0.9, self.dovish_positioning + np.random.uniform(-0.05, 0.10))
        self.public_engagement = min(0.8, self.public_engagement + np.random.uniform(-0.02, 0.08))
        
        if self.model.schedule.steps > 5:
            self.dovish_positioning = min(0.95, self.dovish_positioning + 0.05)

class AdvisorAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.waller_support = np.random.uniform(0.1, 0.4)
        self.hassett_support = np.random.uniform(0.5, 0.8)
        self.influence_on_trump = np.random.uniform(0.3, 0.7)
        
    def step(self):
        waller_agents = [w for w in self.model.schedule.agents if isinstance(w, WallerAgent)]
        if waller_agents:
            avg_waller_performance = np.mean([w.dovish_positioning * w.fed_experience for w in waller_agents])
            self.waller_support = min(0.5, self.waller_support + avg_waller_performance * 0.05)
        
        competitor_agents = [c for c in self.model.schedule.agents if isinstance(c, CompetitorAgent)]
        if competitor_agents:
            avg_hassett_strength = np.mean([c.hassett_strength for c in competitor_agents])
            self.hassett_support = min(0.9, self.hassett_support + avg_hassett_strength * 0.03)

class CompetitorAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.hassett_strength = np.random.uniform(0.65, 0.80)
        self.loyalty_factor = np.random.uniform(0.7, 0.9)
        self.policy_alignment = np.random.uniform(0.75, 0.90)
        
    def step(self):
        self.hassett_strength = min(0.90, self.hassett_strength + np.random.uniform(-0.02, 0.05))
        self.policy_alignment = min(0.95, self.policy_alignment + np.random.uniform(0.0, 0.03))

def compute_outcome(model):
    trump_agents = [a for a in model.schedule.agents if isinstance(a, TrumpAgent)]
    waller_agents = [a for a in model.schedule.agents if isinstance(a, WallerAgent)]
    advisor_agents = [a for a in model.schedule.agents if isinstance(a, AdvisorAgent)]
    competitor_agents = [a for a in model.schedule.agents if isinstance(a, CompetitorAgent)]
    
    if not trump_agents or not waller_agents:
        return 0.04
    
    trump_pref = trump_agents[0].preference_for_waller
    trump_hassett_pref = trump_agents[0].preference_for_hassett
    
    waller_score = np.mean([w.dovish_positioning * w.fed_experience * w.public_engagement for w in waller_agents])
    waller_penalty = np.mean([w.hawkish_history_penalty for w in waller_agents])
    
    advisor_support = np.mean([a.waller_support * a.influence_on_trump for a in advisor_agents])
    
    hassett_dominance = np.mean([c.hassett_strength * c.loyalty_factor * c.policy_alignment for c in competitor_agents])
    
    waller_probability = (
        trump_pref * 0.40 +
        waller_score * 0.25 +
        advisor_support * 0.15 +
        waller_penalty * 0.05 -
        hassett_dominance * 0.30 +
        (1 - trump_hassett_pref) * 0.15
    )
    
    waller_probability = max(0.0, min(1.0, waller_probability))
    
    return waller_probability

AGENT_CONFIG = {
    TrumpAgent: 1,
    WallerAgent: 3,
    AdvisorAgent: 8,
    CompetitorAgent: 12,
}

MODEL_PARAMS = {
    "advisor_influence_weight": 0.35,
}

THRESHOLD = 0.15
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
