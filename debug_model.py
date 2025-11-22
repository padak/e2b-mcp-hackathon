import random
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

class RussianGovernment(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.territorial_control = 0.85
        self.willingness_to_negotiate = 0.25
        self.military_position = 0.70
        self.preconditions_flexibility = 0.15
        
    def step(self):
        war_exhaustion = self.model.war_exhaustion_factor
        international_pressure = self.model.international_pressure
        
        if self.military_position > 0.6:
            self.willingness_to_negotiate = max(0.1, self.willingness_to_negotiate - 0.02)
        else:
            self.willingness_to_negotiate = min(0.5, self.willingness_to_negotiate + 0.05)
        
        self.preconditions_flexibility += (war_exhaustion * 0.03 + international_pressure * 0.02)
        self.preconditions_flexibility = np.clip(self.preconditions_flexibility, 0.1, 0.6)
        
        self.military_position *= (1 - war_exhaustion * 0.01)

class UkrainianGovernment(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.territorial_integrity_stance = 0.95
        self.willingness_to_negotiate = 0.60
        self.western_support_level = 0.75
        self.humanitarian_pressure = 0.70
        
    def step(self):
        war_exhaustion = self.model.war_exhaustion_factor
        western_backing = self.model.western_support_strength
        
        self.western_support_level = 0.5 + western_backing * 0.5
        
        if self.humanitarian_pressure > 0.8:
            self.territorial_integrity_stance = max(0.70, self.territorial_integrity_stance - 0.03)
        
        self.willingness_to_negotiate = 0.5 + war_exhaustion * 0.3 + self.humanitarian_pressure * 0.2
        self.willingness_to_negotiate = np.clip(self.willingness_to_negotiate, 0.4, 0.9)
        
        self.humanitarian_pressure += war_exhaustion * 0.05
        self.humanitarian_pressure = np.clip(self.humanitarian_pressure, 0.5, 1.0)

class InternationalMediators(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.mediation_effectiveness = 0.40
        self.trust_building = 0.30
        self.pressure_capacity = 0.50
        
    def step(self):
        russia_agents = [a for a in self.model.schedule.agents if isinstance(a, RussianGovernment)]
        ukraine_agents = [a for a in self.model.schedule.agents if isinstance(a, UkrainianGovernment)]
        
        if russia_agents and ukraine_agents:
            russia = russia_agents[0]
            ukraine = ukraine_agents[0]
            
            negotiation_gap = abs(russia.willingness_to_negotiate - ukraine.willingness_to_negotiate)
            
            if negotiation_gap < 0.3:
                self.trust_building = min(0.7, self.trust_building + 0.05)
                self.mediation_effectiveness = min(0.7, self.mediation_effectiveness + 0.04)
            else:
                self.trust_building = max(0.2, self.trust_building - 0.02)
            
            if russia.willingness_to_negotiate < 0.3:
                self.model.international_pressure = min(0.8, self.model.international_pressure + 0.03)

class WarfareConditions(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.military_stalemate_level = 0.75
        self.civilian_impact = 0.80
        self.battlefield_momentum = 0.50
        
    def step(self):
        russia_agents = [a for a in self.model.schedule.agents if isinstance(a, RussianGovernment)]
        ukraine_agents = [a for a in self.model.schedule.agents if isinstance(a, UkrainianGovernment)]
        
        if russia_agents and ukraine_agents:
            russia = russia_agents[0]
            ukraine = ukraine_agents[0]
            
            if self.military_stalemate_level > 0.7:
                self.model.war_exhaustion_factor = min(0.9, self.model.war_exhaustion_factor + 0.02)
            
            self.civilian_impact += 0.01
            self.civilian_impact = np.clip(self.civilian_impact, 0.7, 1.0)
            
            if ukraine.western_support_level < 0.5:
                self.battlefield_momentum = max(0.3, self.battlefield_momentum - 0.03)
            else:
                self.battlefield_momentum = min(0.7, self.battlefield_momentum + 0.02)

def compute_outcome(model):
    russia_agents = [a for a in model.schedule.agents if isinstance(a, RussianGovernment)]
    ukraine_agents = [a for a in model.schedule.agents if isinstance(a, UkrainianGovernment)]
    mediator_agents = [a for a in model.schedule.agents if isinstance(a, InternationalMediators)]
    warfare_agents = [a for a in model.schedule.agents if isinstance(a, WarfareConditions)]
    
    if not (russia_agents and ukraine_agents and mediator_agents and warfare_agents):
        return 0.14
    
    russia = russia_agents[0]
    ukraine = ukraine_agents[0]
    mediators = mediator_agents[0]
    warfare = warfare_agents[0]
    
    russia_readiness = (russia.willingness_to_negotiate * 0.4 + 
                       russia.preconditions_flexibility * 0.6)
    
    ukraine_readiness = (ukraine.willingness_to_negotiate * 0.5 + 
                        (1 - ukraine.territorial_integrity_stance) * 0.3 +
                        ukraine.humanitarian_pressure * 0.2)
    
    negotiation_alignment = 1.0 - abs(russia_readiness - ukraine_readiness)
    
    mediation_factor = (mediators.mediation_effectiveness * 0.5 + 
                       mediators.trust_building * 0.5)
    
    stalemate_pressure = (warfare.military_stalemate_level * 0.4 + 
                         warfare.civilian_impact * 0.3 +
                         model.war_exhaustion_factor * 0.3)
    
    territorial_compromise_gap = russia.territorial_control * ukraine.territorial_integrity_stance
    territorial_barrier = np.exp(-territorial_compromise_gap * 2)
    
    western_support_barrier = ukraine.western_support_level * 0.3
    
    ceasefire_probability = (
        russia_readiness * 0.20 +
        ukraine_readiness * 0.20 +
        negotiation_alignment * 0.15 +
        mediation_factor * 0.15 +
        stalemate_pressure * 0.15 +
        territorial_barrier * 0.10 +
        (1 - western_support_barrier) * 0.05
    )
    
    return np.clip(ceasefire_probability, 0.0, 1.0)

AGENT_CONFIG = {
    RussianGovernment: 1,
    UkrainianGovernment: 1,
    InternationalMediators: 3,
    WarfareConditions: 1,
}

MODEL_PARAMS = {
    "war_exhaustion_factor": 0.55,
    "international_pressure": 0.45,
    "western_support_strength": 0.70,
}

THRESHOLD = 0.50
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
