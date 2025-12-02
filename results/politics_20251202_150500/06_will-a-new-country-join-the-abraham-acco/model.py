import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class RegionalCountry(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.join_likelihood = np.random.uniform(0.1, 0.4)
        self.diplomatic_pressure = np.random.uniform(0.0, 0.3)
        self.domestic_support = np.random.uniform(0.2, 0.6)
        self.economic_incentive = np.random.uniform(0.1, 0.5)
        
    def step(self):
        # Influenced by US diplomatic efforts
        us_agents = [a for a in self.model.schedule.agents if isinstance(a, USDiplomacy)]
        if us_agents:
            self.diplomatic_pressure += us_agents[0].push_intensity * 0.15
        
        # Influenced by regional stability
        if self.model.regional_stability > 0.6:
            self.domestic_support += 0.05
        else:
            self.domestic_support -= 0.05
        
        # Economic incentives matter
        self.join_likelihood = (
            0.4 * self.diplomatic_pressure +
            0.3 * self.domestic_support +
            0.3 * self.economic_incentive
        )
        
        self.join_likelihood = np.clip(self.join_likelihood, 0.0, 1.0)
        self.domestic_support = np.clip(self.domestic_support, 0.0, 1.0)
        self.diplomatic_pressure = np.clip(self.diplomatic_pressure, 0.0, 1.0)


class USDiplomacy(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.push_intensity = np.random.uniform(0.5, 0.8)
        self.effectiveness = np.random.uniform(0.4, 0.7)
        
    def step(self):
        # Trump administration priority
        self.push_intensity = self.model.us_priority * 0.7 + np.random.uniform(0.0, 0.3)
        
        # Effectiveness based on regional stability
        if self.model.regional_stability > 0.5:
            self.effectiveness += 0.05
        else:
            self.effectiveness -= 0.03
            
        self.effectiveness = np.clip(self.effectiveness, 0.0, 1.0)
        self.push_intensity = np.clip(self.push_intensity, 0.0, 1.0)


class IsraeliDiplomacy(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.outreach_level = np.random.uniform(0.4, 0.7)
        self.credibility = np.random.uniform(0.3, 0.6)
        
    def step(self):
        # Outreach influenced by ceasefire status
        if self.model.ceasefire_active:
            self.outreach_level += 0.08
            self.credibility += 0.05
        else:
            self.outreach_level -= 0.05
            self.credibility -= 0.08
        
        # Boost to regional countries
        regional_agents = [a for a in self.model.schedule.agents if isinstance(a, RegionalCountry)]
        for country in regional_agents:
            country.diplomatic_pressure += self.outreach_level * 0.1
            
        self.outreach_level = np.clip(self.outreach_level, 0.0, 1.0)
        self.credibility = np.clip(self.credibility, 0.0, 1.0)


class ExistingMember(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.advocacy_strength = np.random.uniform(0.3, 0.6)
        self.satisfaction = np.random.uniform(0.4, 0.8)
        
    def step(self):
        # Satisfied members advocate more
        self.advocacy_strength = self.satisfaction * 0.7 + np.random.uniform(0.0, 0.3)
        
        # Influence regional countries
        regional_agents = [a for a in self.model.schedule.agents if isinstance(a, RegionalCountry)]
        for country in regional_agents:
            country.economic_incentive += self.advocacy_strength * 0.08
            
        # Satisfaction influenced by regional stability
        if self.model.regional_stability > 0.6:
            self.satisfaction += 0.03
        else:
            self.satisfaction -= 0.02
            
        self.advocacy_strength = np.clip(self.advocacy_strength, 0.0, 1.0)
        self.satisfaction = np.clip(self.satisfaction, 0.0, 1.0)


# Outcome computation
def compute_outcome(model):
    regional_agents = [a for a in model.schedule.agents if isinstance(a, RegionalCountry)]
    
    if not regional_agents:
        return 0.15
    
    # Average join likelihood weighted by diplomatic support
    join_scores = []
    for country in regional_agents:
        # Account for US and Israeli diplomatic efforts
        us_boost = model.us_priority * 0.2
        ceasefire_boost = 0.15 if model.ceasefire_active else 0.0
        stability_boost = model.regional_stability * 0.15
        
        total_score = (
            country.join_likelihood * 0.6 +
            us_boost +
            ceasefire_boost +
            stability_boost
        )
        join_scores.append(total_score)
    
    # Take maximum likelihood (most likely country to join)
    max_likelihood = max(join_scores)
    
    # Add variance for existing member influence
    existing_agents = [a for a in model.schedule.agents if isinstance(a, ExistingMember)]
    if existing_agents:
        avg_advocacy = np.mean([a.advocacy_strength for a in existing_agents])
        max_likelihood += avg_advocacy * 0.1
    
    return np.clip(max_likelihood, 0.0, 1.0)


# Configuration
AGENT_CONFIG = {
    RegionalCountry: 8,
    USDiplomacy: 2,
    IsraeliDiplomacy: 2,
    ExistingMember: 5,
}

MODEL_PARAMS = {
    "us_priority": 0.75,
    "ceasefire_active": 1.0,
    "regional_stability": 0.65,
}

THRESHOLD = 0.50
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
