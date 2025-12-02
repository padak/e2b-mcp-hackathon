import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class SenateRaceAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.is_competitive = np.random.random() < 0.3
        self.republican_advantage = np.random.uniform(-0.1, 0.15)
        self.incumbent_boost = 0.05 if np.random.random() < 0.7 else 0
        
    def step(self):
        national_environment = self.model.national_swing
        candidate_quality = np.random.uniform(-0.05, 0.05)
        
        if self.is_competitive:
            self.republican_advantage += national_environment * 0.4 + candidate_quality
            self.republican_advantage += self.model.midterm_penalty * 0.3
        else:
            self.republican_advantage += national_environment * 0.1

class HouseDistrictAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.republican_lean = np.random.uniform(-0.2, 0.2)
        self.is_swing = abs(self.republican_lean) < 0.05
        
    def step(self):
        generic_ballot = self.model.generic_ballot_advantage
        turnout_effect = self.model.turnout_differential * np.random.uniform(0.5, 1.5)
        
        self.republican_lean += generic_ballot * 0.5
        self.republican_lean += self.model.midterm_penalty * 0.6
        self.republican_lean += turnout_effect * 0.3
        
        if self.is_swing:
            self.republican_lean += np.random.uniform(-0.08, 0.08)

class VoterMobilizationAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.party = "R" if np.random.random() < 0.48 else "D"
        self.enthusiasm = np.random.uniform(0.3, 0.8)
        
    def step(self):
        if self.party == "R":
            self.enthusiasm += self.model.republican_enthusiasm * 0.4
            self.enthusiasm -= self.model.midterm_penalty * 0.5
        else:
            self.enthusiasm += self.model.democratic_enthusiasm * 0.4
            self.enthusiasm += self.model.midterm_penalty * 0.3
        
        self.enthusiasm = np.clip(self.enthusiasm, 0, 1)

class NationalEnvironmentAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.economic_approval = np.random.uniform(0.35, 0.55)
        self.presidential_approval = np.random.uniform(0.38, 0.50)
        
    def step(self):
        shock = np.random.uniform(-0.03, 0.03)
        self.economic_approval += shock
        self.presidential_approval += shock * 0.8
        
        self.economic_approval = np.clip(self.economic_approval, 0.2, 0.7)
        self.presidential_approval = np.clip(self.presidential_approval, 0.25, 0.65)
        
        self.model.national_swing = (0.45 - self.presidential_approval) * 0.5

# Outcome computation
def compute_outcome(model):
    senate_races = [a for a in model.schedule.agents if isinstance(a, SenateRaceAgent)]
    house_districts = [a for a in model.schedule.agents if isinstance(a, HouseDistrictAgent)]
    voter_agents = [a for a in model.schedule.agents if isinstance(a, VoterMobilizationAgent)]
    
    republican_senate_seats = 40
    for race in senate_races:
        final_advantage = race.republican_advantage + race.incumbent_boost
        if final_advantage > 0:
            republican_senate_seats += 1
    
    senate_control = 1.0 if republican_senate_seats >= 51 else 0.0
    
    republican_house_seats = 0
    for district in house_districts:
        if district.republican_lean > 0:
            republican_house_seats += 1
    
    house_control = 1.0 if republican_house_seats >= 218 else 0.0
    
    r_enthusiasm = np.mean([v.enthusiasm for v in voter_agents if v.party == "R"])
    d_enthusiasm = np.mean([v.enthusiasm for v in voter_agents if v.party == "D"])
    enthusiasm_factor = (r_enthusiasm - d_enthusiasm + 1) / 2
    
    base_probability = senate_control * house_control
    adjusted_probability = base_probability * 0.7 + enthusiasm_factor * 0.3
    
    return np.clip(adjusted_probability, 0.0, 1.0)

# Configuration
AGENT_CONFIG = {
    SenateRaceAgent: 13,
    HouseDistrictAgent: 435,
    VoterMobilizationAgent: 30,
    NationalEnvironmentAgent: 1,
}

MODEL_PARAMS = {
    "national_swing": -0.04,
    "generic_ballot_advantage": -0.039,
    "midterm_penalty": -0.05,
    "turnout_differential": -0.02,
    "republican_enthusiasm": 0.45,
    "democratic_enthusiasm": 0.55,
}

THRESHOLD = 0.20
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
