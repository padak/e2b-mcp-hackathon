import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class UkraineAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.ceasefire_willingness = 0.2
        self.territorial_demands = 0.9
        self.trust_in_russia = 0.1
        self.western_support = np.random.uniform(0.7, 0.9)
        
    def step(self):
        battlefield_pressure = self.model.russian_military_pressure
        diplomatic_pressure = self.model.international_mediation
        
        if battlefield_pressure > 0.7:
            self.ceasefire_willingness += 0.05
        if self.western_support > 0.7:
            self.ceasefire_willingness -= 0.02
            self.territorial_demands = min(1.0, self.territorial_demands + 0.01)
        
        if diplomatic_pressure > 0.6:
            self.ceasefire_willingness += 0.03
            
        if self.model.russia_offers_full_ceasefire:
            self.ceasefire_willingness += 0.1
            if self.trust_in_russia > 0.3:
                self.ceasefire_willingness += 0.1
        
        self.ceasefire_willingness = np.clip(self.ceasefire_willingness, 0, 1)
        self.territorial_demands = np.clip(self.territorial_demands, 0, 1)


class RussiaAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.ceasefire_willingness = 0.15
        self.territorial_demands = 0.95
        self.sanctions_pressure = np.random.uniform(0.5, 0.8)
        self.willing_to_offer_full = False
        
    def step(self):
        battlefield_success = self.model.russian_military_pressure
        economic_pressure = self.sanctions_pressure * self.model.sanctions_intensity
        
        if battlefield_success > 0.6:
            self.ceasefire_willingness -= 0.02
            self.territorial_demands = min(1.0, self.territorial_demands + 0.01)
        else:
            self.ceasefire_willingness += 0.03
            
        if economic_pressure > 0.7:
            self.ceasefire_willingness += 0.05
            self.willing_to_offer_full = np.random.random() < 0.15
        
        if self.model.western_arms_flow < 0.3:
            self.ceasefire_willingness += 0.08
            self.willing_to_offer_full = np.random.random() < 0.25
        
        self.model.russia_offers_full_ceasefire = self.willing_to_offer_full
        self.ceasefire_willingness = np.clip(self.ceasefire_willingness, 0, 1)


class WesternMediatorAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.mediation_intensity = np.random.uniform(0.4, 0.7)
        self.arms_support = np.random.uniform(0.7, 0.9)
        self.sanctions_enforcement = np.random.uniform(0.6, 0.9)
        
    def step(self):
        ukraine_agents = [a for a in self.model.schedule.agents if isinstance(a, UkraineAgent)]
        russia_agents = [a for a in self.model.schedule.agents if isinstance(a, RussiaAgent)]
        
        if ukraine_agents and russia_agents:
            avg_ukraine_will = np.mean([a.ceasefire_willingness for a in ukraine_agents])
            avg_russia_will = np.mean([a.ceasefire_willingness for a in russia_agents])
            
            if avg_ukraine_will > 0.4 and avg_russia_will > 0.4:
                self.mediation_intensity = min(1.0, self.mediation_intensity + 0.1)
            else:
                self.mediation_intensity = max(0.2, self.mediation_intensity - 0.02)
            
            if avg_ukraine_will < 0.3:
                self.arms_support = min(1.0, self.arms_support + 0.05)
            
            if avg_russia_will < 0.2:
                self.sanctions_enforcement = min(1.0, self.sanctions_enforcement + 0.05)
        
        self.model.international_mediation = self.mediation_intensity
        self.model.western_arms_flow = self.arms_support
        self.model.sanctions_intensity = self.sanctions_enforcement


class DomesticPressureAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.russia_domestic_pressure = np.random.uniform(0.3, 0.6)
        self.ukraine_domestic_pressure = np.random.uniform(0.4, 0.7)
        
    def step(self):
        if self.model.russian_military_pressure < 0.4:
            self.russia_domestic_pressure += 0.05
        
        time_factor = self.model.schedule.steps / 365.0
        self.ukraine_domestic_pressure += time_factor * 0.01
        
        russia_agents = [a for a in self.model.schedule.agents if isinstance(a, RussiaAgent)]
        ukraine_agents = [a for a in self.model.schedule.agents if isinstance(a, UkraineAgent)]
        
        if russia_agents:
            for agent in russia_agents:
                agent.ceasefire_willingness += self.russia_domestic_pressure * 0.02
        
        if ukraine_agents:
            for agent in ukraine_agents:
                if self.ukraine_domestic_pressure > 0.7:
                    agent.ceasefire_willingness += 0.03
        
        self.russia_domestic_pressure = np.clip(self.russia_domestic_pressure, 0, 1)
        self.ukraine_domestic_pressure = np.clip(self.ukraine_domestic_pressure, 0, 1)


# Outcome computation
def compute_outcome(model):
    ukraine_agents = [a for a in model.schedule.agents if isinstance(a, UkraineAgent)]
    russia_agents = [a for a in model.schedule.agents if isinstance(a, RussiaAgent)]
    
    if not ukraine_agents or not russia_agents:
        return 0.0
    
    avg_ukraine_will = np.mean([a.ceasefire_willingness for a in ukraine_agents])
    avg_russia_will = np.mean([a.ceasefire_willingness for a in russia_agents])
    avg_ukraine_demands = np.mean([a.territorial_demands for a in ukraine_agents])
    avg_russia_demands = np.mean([a.territorial_demands for a in russia_agents])
    
    territorial_gap = abs(avg_ukraine_demands - avg_russia_demands)
    willingness_product = avg_ukraine_will * avg_russia_will
    mediation_factor = model.international_mediation
    
    russia_offers_full = model.russia_offers_full_ceasefire
    
    base_probability = willingness_product * 0.4
    mediation_boost = mediation_factor * 0.2
    territorial_penalty = territorial_gap * 0.3
    russia_full_offer_boost = 0.15 if russia_offers_full else 0.0
    
    outcome = base_probability + mediation_boost - territorial_penalty + russia_full_offer_boost
    
    return np.clip(outcome, 0, 1)


# Configuration
AGENT_CONFIG = {
    UkraineAgent: 8,
    RussiaAgent: 8,
    WesternMediatorAgent: 6,
    DomesticPressureAgent: 4,
}

MODEL_PARAMS = {
    "russian_military_pressure": 0.6,
    "international_mediation": 0.5,
    "western_arms_flow": 0.8,
    "sanctions_intensity": 0.7,
    "russia_offers_full_ceasefire": False,
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
