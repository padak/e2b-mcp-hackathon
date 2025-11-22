import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class RussianLeadership(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.territorial_satisfaction = np.random.uniform(0.6, 0.8)
        self.sanction_pressure = np.random.uniform(0.3, 0.5)
        self.domestic_support = np.random.uniform(0.6, 0.8)
        self.willingness_to_negotiate = 0.2
        
    def step(self):
        battlefield_advantage = self.model.russian_territorial_control
        sanction_impact = self.sanction_pressure * self.model.western_unity
        
        if battlefield_advantage < 0.6 or sanction_impact > 0.6:
            self.willingness_to_negotiate += 0.05
        
        if self.domestic_support < 0.5:
            self.willingness_to_negotiate += 0.08
            
        self.willingness_to_negotiate = min(0.9, self.willingness_to_negotiate)


class UkrainianLeadership(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.territorial_integrity_demand = np.random.uniform(0.8, 0.95)
        self.western_support_confidence = np.random.uniform(0.6, 0.8)
        self.war_fatigue = np.random.uniform(0.3, 0.5)
        self.willingness_to_negotiate = 0.15
        
    def step(self):
        support_level = self.western_support_confidence * self.model.western_unity
        battlefield_status = 1.0 - self.model.russian_territorial_control
        
        if support_level < 0.4 or self.war_fatigue > 0.7:
            self.willingness_to_negotiate += 0.06
            
        if battlefield_status < 0.3:
            self.willingness_to_negotiate += 0.07
            
        self.willingness_to_negotiate = min(0.8, self.willingness_to_negotiate)


class WesternPowers(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.support_commitment = np.random.uniform(0.6, 0.8)
        self.domestic_pressure = np.random.uniform(0.3, 0.5)
        self.ceasefire_preference = np.random.uniform(0.4, 0.6)
        
    def step(self):
        war_duration_factor = self.model.schedule.steps / 100.0
        self.domestic_pressure += war_duration_factor * 0.02
        
        if self.domestic_pressure > 0.7:
            self.ceasefire_preference += 0.05
            self.support_commitment -= 0.03
            
        self.ceasefire_preference = min(0.9, self.ceasefire_preference)
        self.support_commitment = max(0.2, self.support_commitment)
        
        western_agents = [a for a in self.model.schedule.agents if isinstance(a, WesternPowers)]
        if western_agents:
            avg_commitment = np.mean([a.support_commitment for a in western_agents])
            self.model.western_unity = avg_commitment


class InternationalMediators(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.mediation_effectiveness = np.random.uniform(0.2, 0.4)
        self.trust_building = 0.1
        
    def step(self):
        russian_agents = [a for a in self.model.schedule.agents if isinstance(a, RussianLeadership)]
        ukrainian_agents = [a for a in self.model.schedule.agents if isinstance(a, UkrainianLeadership)]
        
        if russian_agents and ukrainian_agents:
            avg_russian_will = np.mean([a.willingness_to_negotiate for a in russian_agents])
            avg_ukrainian_will = np.mean([a.willingness_to_negotiate for a in ukrainian_agents])
            
            if avg_russian_will > 0.4 and avg_ukrainian_will > 0.4:
                self.trust_building += 0.08 * self.mediation_effectiveness
                
                for agent in russian_agents:
                    agent.willingness_to_negotiate += 0.02 * self.trust_building
                    
                for agent in ukrainian_agents:
                    agent.willingness_to_negotiate += 0.02 * self.trust_building
                    
        self.trust_building = min(0.6, self.trust_building)


# Outcome computation
def compute_outcome(model):
    russian_agents = [a for a in model.schedule.agents if isinstance(a, RussianLeadership)]
    ukrainian_agents = [a for a in model.schedule.agents if isinstance(a, UkrainianLeadership)]
    western_agents = [a for a in model.schedule.agents if isinstance(a, WesternPowers)]
    mediator_agents = [a for a in model.schedule.agents if isinstance(a, InternationalMediators)]
    
    if not russian_agents or not ukrainian_agents:
        return 0.0
        
    avg_russian_will = np.mean([a.willingness_to_negotiate for a in russian_agents])
    avg_ukrainian_will = np.mean([a.willingness_to_negotiate for a in ukrainian_agents])
    
    territorial_gap = abs(model.russian_territorial_control - 0.3)
    
    western_pressure = 0.0
    if western_agents:
        western_pressure = np.mean([a.ceasefire_preference for a in western_agents])
        
    mediation_factor = 0.0
    if mediator_agents:
        mediation_factor = np.mean([a.trust_building for a in mediator_agents])
    
    negotiation_alignment = min(avg_russian_will, avg_ukrainian_will)
    
    territorial_penalty = territorial_gap * 1.5
    
    ceasefire_probability = (
        negotiation_alignment * 0.4 +
        western_pressure * 0.2 +
        mediation_factor * 0.2 +
        (1.0 - territorial_penalty) * 0.2
    )
    
    ceasefire_probability = max(0.0, min(1.0, ceasefire_probability))
    
    return ceasefire_probability


# Configuration
AGENT_CONFIG = {
    RussianLeadership: 3,
    UkrainianLeadership: 3,
    WesternPowers: 8,
    InternationalMediators: 2,
}

MODEL_PARAMS = {
    "russian_territorial_control": 0.65,
    "western_unity": 0.7,
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
