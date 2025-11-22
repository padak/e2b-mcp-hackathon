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

class MaduroRegime(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.control_strength = np.random.uniform(0.7, 0.9)
        self.elite_loyalty = np.random.uniform(0.6, 0.85)
        self.repression_capacity = np.random.uniform(0.65, 0.85)
        
    def step(self):
        foreign_pressure = np.mean([agent.pressure_level for agent in self.model.schedule.agents if isinstance(agent, ForeignActor)])
        domestic_threat = np.mean([agent.opposition_strength for agent in self.model.schedule.agents if isinstance(agent, DomesticOpposition)])
        
        self.control_strength -= (foreign_pressure * 0.15 + domestic_threat * 0.08)
        self.control_strength = max(0.0, min(1.0, self.control_strength))
        
        if domestic_threat > 0.4:
            self.elite_loyalty -= np.random.uniform(0.02, 0.05)
        else:
            self.elite_loyalty += np.random.uniform(0.0, 0.02)
        self.elite_loyalty = max(0.0, min(1.0, self.elite_loyalty))
        
        self.repression_capacity = self.control_strength * 0.7 + self.elite_loyalty * 0.3

class ForeignActor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.pressure_level = np.random.uniform(0.3, 0.6)
        self.intervention_willingness = np.random.uniform(0.05, 0.2)
        self.escalation_threshold = np.random.uniform(0.6, 0.8)
        
    def step(self):
        regime = [agent for agent in self.model.schedule.agents if isinstance(agent, MaduroRegime)][0]
        
        if self.model.us_military_tensions > 0.5:
            self.pressure_level += np.random.uniform(0.05, 0.15)
            self.intervention_willingness += np.random.uniform(0.02, 0.08)
        
        if regime.control_strength < 0.4:
            self.intervention_willingness += np.random.uniform(0.03, 0.1)
        
        if self.pressure_level > self.escalation_threshold:
            self.intervention_willingness += np.random.uniform(0.05, 0.12)
        
        self.pressure_level = max(0.0, min(1.0, self.pressure_level))
        self.intervention_willingness = max(0.0, min(1.0, self.intervention_willingness))

class DomesticOpposition(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.opposition_strength = np.random.uniform(0.15, 0.35)
        self.mobilization_capacity = np.random.uniform(0.1, 0.25)
        self.international_support = np.random.uniform(0.2, 0.4)
        
    def step(self):
        regime = [agent for agent in self.model.schedule.agents if isinstance(agent, MaduroRegime)][0]
        foreign_support = np.mean([agent.pressure_level for agent in self.model.schedule.agents if isinstance(agent, ForeignActor)])
        
        self.international_support = foreign_support * 0.6 + self.international_support * 0.4
        
        if regime.repression_capacity > 0.7:
            self.opposition_strength -= np.random.uniform(0.03, 0.08)
            self.mobilization_capacity -= np.random.uniform(0.02, 0.06)
        else:
            self.opposition_strength += np.random.uniform(0.02, 0.07)
            self.mobilization_capacity += np.random.uniform(0.01, 0.05)
        
        if self.international_support > 0.5:
            self.opposition_strength += np.random.uniform(0.02, 0.06)
        
        self.opposition_strength = max(0.0, min(1.0, self.opposition_strength))
        self.mobilization_capacity = max(0.0, min(1.0, self.mobilization_capacity))

class MilitaryElite(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.regime_loyalty = np.random.uniform(0.65, 0.85)
        self.defection_risk = np.random.uniform(0.05, 0.15)
        self.self_interest = np.random.uniform(0.6, 0.9)
        
    def step(self):
        regime = [agent for agent in self.model.schedule.agents if isinstance(agent, MaduroRegime)][0]
        foreign_intervention = np.mean([agent.intervention_willingness for agent in self.model.schedule.agents if isinstance(agent, ForeignActor)])
        domestic_pressure = np.mean([agent.opposition_strength for agent in self.model.schedule.agents if isinstance(agent, DomesticOpposition)])
        
        if regime.control_strength < 0.4 or foreign_intervention > 0.5:
            self.defection_risk += np.random.uniform(0.05, 0.15)
            self.regime_loyalty -= np.random.uniform(0.05, 0.12)
        
        if domestic_pressure > 0.4:
            self.defection_risk += np.random.uniform(0.02, 0.07)
        
        if regime.elite_loyalty < 0.5:
            self.defection_risk += np.random.uniform(0.08, 0.18)
        
        self.regime_loyalty = max(0.0, min(1.0, self.regime_loyalty))
        self.defection_risk = max(0.0, min(1.0, self.defection_risk))

def compute_outcome(model):
    regime_agents = [agent for agent in model.schedule.agents if isinstance(agent, MaduroRegime)]
    foreign_agents = [agent for agent in model.schedule.agents if isinstance(agent, ForeignActor)]
    opposition_agents = [agent for agent in model.schedule.agents if isinstance(agent, DomesticOpposition)]
    military_agents = [agent for agent in model.schedule.agents if isinstance(agent, MilitaryElite)]
    
    if not regime_agents:
        return 0.5
    
    regime = regime_agents[0]
    
    avg_foreign_intervention = np.mean([agent.intervention_willingness for agent in foreign_agents]) if foreign_agents else 0.0
    avg_opposition_strength = np.mean([agent.opposition_strength for agent in opposition_agents]) if opposition_agents else 0.0
    avg_military_defection = np.mean([agent.defection_risk for agent in military_agents]) if military_agents else 0.0
    
    regime_weakness = 1.0 - regime.control_strength
    elite_disloyalty = 1.0 - regime.elite_loyalty
    
    removal_probability = (
        avg_foreign_intervention * 0.40 +
        avg_military_defection * 0.30 +
        regime_weakness * 0.15 +
        avg_opposition_strength * 0.10 +
        elite_disloyalty * 0.05
    )
    
    return min(1.0, max(0.0, removal_probability))

AGENT_CONFIG = {
    MaduroRegime: 1,
    ForeignActor: 8,
    DomesticOpposition: 12,
    MilitaryElite: 6,
}

MODEL_PARAMS = {
    "us_military_tensions": 0.55,
}

THRESHOLD = 0.5
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
