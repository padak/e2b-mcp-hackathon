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

class UkraineAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.ceasefire_willingness = 0.2
        self.territorial_stance = 0.95
        self.western_support_dependency = 0.85
        
    def step(self):
        russia_agents = [a for a in self.model.schedule.agents if isinstance(a, RussiaAgent)]
        western_agents = [a for a in self.model.schedule.agents if isinstance(a, WesternPowerAgent)]
        
        if russia_agents:
            avg_russia_territorial = np.mean([a.territorial_demands for a in russia_agents])
            if avg_russia_territorial > 0.7:
                self.ceasefire_willingness = max(0.1, self.ceasefire_willingness - 0.05)
            else:
                self.ceasefire_willingness = min(0.6, self.ceasefire_willingness + 0.03)
        
        if western_agents:
            avg_western_support = np.mean([a.support_level for a in western_agents])
            self.western_support_dependency = avg_western_support
            if avg_western_support < 0.5:
                self.ceasefire_willingness = min(0.7, self.ceasefire_willingness + 0.08)
        
        self.ceasefire_willingness *= (1 + np.random.uniform(-0.05, 0.05))
        self.ceasefire_willingness = np.clip(self.ceasefire_willingness, 0, 1)

class RussiaAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.ceasefire_willingness = 0.35
        self.territorial_demands = 0.85
        self.military_position = 0.6
        
    def step(self):
        ukraine_agents = [a for a in self.model.schedule.agents if isinstance(a, UkraineAgent)]
        mediator_agents = [a for a in self.model.schedule.agents if isinstance(a, InternationalMediatorAgent)]
        
        if self.military_position < 0.4:
            self.ceasefire_willingness = min(0.65, self.ceasefire_willingness + 0.06)
            self.territorial_demands = max(0.5, self.territorial_demands - 0.05)
        elif self.military_position > 0.7:
            self.territorial_demands = min(0.95, self.territorial_demands + 0.03)
            self.ceasefire_willingness = max(0.2, self.ceasefire_willingness - 0.04)
        
        if mediator_agents:
            avg_mediator_pressure = np.mean([a.diplomatic_pressure for a in mediator_agents])
            if avg_mediator_pressure > 0.6:
                self.ceasefire_willingness = min(0.7, self.ceasefire_willingness + 0.04)
        
        self.military_position += np.random.uniform(-0.08, 0.05)
        self.military_position = np.clip(self.military_position, 0, 1)
        self.ceasefire_willingness *= (1 + np.random.uniform(-0.05, 0.05))
        self.ceasefire_willingness = np.clip(self.ceasefire_willingness, 0, 1)

class WesternPowerAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.support_level = np.random.uniform(0.6, 0.85)
        self.pressure_for_ceasefire = np.random.uniform(0.3, 0.5)
        self.fatigue = 0.4
        
    def step(self):
        self.fatigue += self.model.war_duration_effect * 0.02
        self.fatigue = np.clip(self.fatigue, 0, 1)
        
        if self.fatigue > 0.6:
            self.support_level = max(0.3, self.support_level - 0.06)
            self.pressure_for_ceasefire = min(0.8, self.pressure_for_ceasefire + 0.07)
        
        ukraine_agents = [a for a in self.model.schedule.agents if isinstance(a, UkraineAgent)]
        if ukraine_agents:
            avg_ukraine_will = np.mean([a.ceasefire_willingness for a in ukraine_agents])
            if avg_ukraine_will > 0.4:
                self.pressure_for_ceasefire = min(0.9, self.pressure_for_ceasefire + 0.05)
        
        self.support_level *= (1 + np.random.uniform(-0.04, 0.04))
        self.support_level = np.clip(self.support_level, 0, 1)

class InternationalMediatorAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.diplomatic_pressure = np.random.uniform(0.4, 0.6)
        self.negotiation_progress = 0.2
        
    def step(self):
        ukraine_agents = [a for a in self.model.schedule.agents if isinstance(a, UkraineAgent)]
        russia_agents = [a for a in self.model.schedule.agents if isinstance(a, RussiaAgent)]
        western_agents = [a for a in self.model.schedule.agents if isinstance(a, WesternPowerAgent)]
        
        if ukraine_agents and russia_agents:
            avg_ukraine_will = np.mean([a.ceasefire_willingness for a in ukraine_agents])
            avg_russia_will = np.mean([a.ceasefire_willingness for a in russia_agents])
            avg_russia_demands = np.mean([a.territorial_demands for a in russia_agents])
            
            gap = abs(avg_ukraine_will - avg_russia_will)
            territorial_gap = avg_russia_demands - 0.5
            
            if gap < 0.3 and territorial_gap < 0.3:
                self.negotiation_progress = min(0.8, self.negotiation_progress + 0.08)
                self.diplomatic_pressure = min(0.85, self.diplomatic_pressure + 0.06)
            else:
                self.negotiation_progress = max(0.1, self.negotiation_progress - 0.03)
        
        if western_agents:
            avg_western_pressure = np.mean([a.pressure_for_ceasefire for a in western_agents])
            self.diplomatic_pressure = 0.7 * self.diplomatic_pressure + 0.3 * avg_western_pressure
        
        self.diplomatic_pressure *= (1 + np.random.uniform(-0.05, 0.05))
        self.diplomatic_pressure = np.clip(self.diplomatic_pressure, 0, 1)

def compute_outcome(model):
    ukraine_agents = [a for a in model.schedule.agents if isinstance(a, UkraineAgent)]
    russia_agents = [a for a in model.schedule.agents if isinstance(a, RussiaAgent)]
    mediator_agents = [a for a in model.schedule.agents if isinstance(a, InternationalMediatorAgent)]
    western_agents = [a for a in model.schedule.agents if isinstance(a, WesternPowerAgent)]
    
    if not ukraine_agents or not russia_agents:
        return 0.14
    
    avg_ukraine_will = np.mean([a.ceasefire_willingness for a in ukraine_agents])
    avg_russia_will = np.mean([a.ceasefire_willingness for a in russia_agents])
    avg_russia_demands = np.mean([a.territorial_demands for a in russia_agents])
    
    avg_mediator_progress = np.mean([a.negotiation_progress for a in mediator_agents]) if mediator_agents else 0.2
    avg_western_pressure = np.mean([a.pressure_for_ceasefire for a in western_agents]) if western_agents else 0.4
    
    willingness_alignment = 1 - abs(avg_ukraine_will - avg_russia_will)
    territorial_compatibility = 1 - max(0, avg_russia_demands - 0.6)
    
    base_probability = (
        0.30 * avg_ukraine_will +
        0.30 * avg_russia_will +
        0.15 * willingness_alignment +
        0.10 * territorial_compatibility +
        0.10 * avg_mediator_progress +
        0.05 * avg_western_pressure
    )
    
    if avg_russia_demands > 0.75:
        base_probability *= 0.6
    
    if avg_ukraine_will < 0.3 or avg_russia_will < 0.3:
        base_probability *= 0.7
    
    return np.clip(base_probability, 0, 1)

AGENT_CONFIG = {
    UkraineAgent: 8,
    RussiaAgent: 8,
    WesternPowerAgent: 12,
    InternationalMediatorAgent: 5,
}

MODEL_PARAMS = {
    "war_duration_effect": 0.8,
}

THRESHOLD = 0.5
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
