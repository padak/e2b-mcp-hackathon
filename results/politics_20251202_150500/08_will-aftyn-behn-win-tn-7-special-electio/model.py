import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

class RepublicanVoter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.turnout_likelihood = np.random.uniform(0.65, 0.85)
        self.van_epps_support = np.random.uniform(0.85, 0.98)
        self.will_vote = False
        
    def step(self):
        turnout_modifier = self.model.republican_enthusiasm * 1.2
        self.will_vote = np.random.random() < (self.turnout_likelihood * turnout_modifier)

class DemocraticVoter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.turnout_likelihood = np.random.uniform(0.55, 0.75)
        self.behn_support = np.random.uniform(0.80, 0.95)
        self.will_vote = False
        
    def step(self):
        turnout_modifier = self.model.democratic_enthusiasm * 1.1
        self.will_vote = np.random.random() < (self.turnout_likelihood * turnout_modifier)

class SwingVoter(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.turnout_likelihood = np.random.uniform(0.45, 0.65)
        self.behn_lean = np.random.uniform(0.35, 0.55)
        self.will_vote = False
        self.votes_behn = False
        
    def step(self):
        self.will_vote = np.random.random() < self.turnout_likelihood
        
        behn_appeal = self.model.behn_campaign_strength * 0.8
        van_epps_appeal = self.model.van_epps_campaign_strength * 0.9
        
        base_lean = self.behn_lean
        adjusted_lean = base_lean + (behn_appeal - van_epps_appeal) * 0.3
        adjusted_lean = np.clip(adjusted_lean, 0, 1)
        
        if self.will_vote:
            self.votes_behn = np.random.random() < adjusted_lean

class IndependentCandidate(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.vote_share = np.random.uniform(0.005, 0.015)
        
    def step(self):
        pass

def compute_outcome(model):
    republican_votes = sum(1 for agent in model.schedule.agents 
                          if isinstance(agent, RepublicanVoter) and agent.will_vote)
    
    democratic_votes = sum(1 for agent in model.schedule.agents 
                          if isinstance(agent, DemocraticVoter) and agent.will_vote)
    
    swing_votes_behn = sum(1 for agent in model.schedule.agents 
                          if isinstance(agent, SwingVoter) and agent.will_vote and agent.votes_behn)
    
    swing_votes_van_epps = sum(1 for agent in model.schedule.agents 
                               if isinstance(agent, SwingVoter) and agent.will_vote and not agent.votes_behn)
    
    independent_vote_drain = sum(agent.vote_share for agent in model.schedule.agents 
                                if isinstance(agent, IndependentCandidate))
    
    total_behn = democratic_votes + swing_votes_behn
    total_van_epps = republican_votes + swing_votes_van_epps
    
    total_votes = total_behn + total_van_epps
    
    if total_votes == 0:
        return 0.11
    
    behn_vote_share = total_behn / total_votes
    behn_vote_share_adjusted = behn_vote_share * (1 - independent_vote_drain)
    
    return behn_vote_share_adjusted

AGENT_CONFIG = {
    RepublicanVoter: 28,
    DemocraticVoter: 22,
    SwingVoter: 12,
    IndependentCandidate: 4,
}

MODEL_PARAMS = {
    "republican_enthusiasm": 0.85,
    "democratic_enthusiasm": 0.78,
    "behn_campaign_strength": 0.68,
    "van_epps_campaign_strength": 0.74,
}

THRESHOLD = 0.48
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
