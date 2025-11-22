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

class RussianLeadershipAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.territorial_demands = np.random.uniform(0.8, 1.0)
        self.sanctions_pressure = np.random.uniform(0.3, 0.6)
        self.willingness_to_negotiate = np.random.uniform(0.2, 0.4)
        
    def step(self):
        us_pressure = np.mean([a.pressure_on_russia for a in self.model.schedule.agents if isinstance(a, USAdministrationAgent)])
        eu_support = np.mean([a.support_for_ukraine for a in self.model.schedule.agents if isinstance(a, EuropeanLeaderAgent)])
        
        if us_pressure < 0.3:
            self.willingness_to_negotiate += 0.05
        
        self.sanctions_pressure = min(1.0, self.sanctions_pressure + eu_support * 0.02)
        
        if self.sanctions_pressure > 0.7:
            self.willingness_to_negotiate += 0.03
            self.territorial_demands = max(0.5, self.territorial_demands - 0.02)

class UkrainianLeadershipAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.territorial_integrity_demand = np.random.uniform(0.85, 1.0)
        self.security_guarantees_needed = np.random.uniform(0.8, 0.95)
        self.willingness_to_compromise = np.random.uniform(0.1, 0.3)
        
    def step(self):
        us_support = np.mean([a.support_for_ukraine for a in self.model.schedule.agents if isinstance(a, USAdministrationAgent)])
        eu_support = np.mean([a.support_for_ukraine for a in self.model.schedule.agents if isinstance(a, EuropeanLeaderAgent)])
        
        external_support = (us_support + eu_support) / 2
        
        if external_support < 0.5:
            self.willingness_to_compromise += 0.08
            self.territorial_integrity_demand = max(0.4, self.territorial_integrity_demand - 0.05)
        
        if external_support > 0.7:
            self.willingness_to_compromise = max(0.05, self.willingness_to_compromise - 0.02)

class USAdministrationAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.support_for_ukraine = np.random.uniform(0.3, 0.5)
        self.pressure_on_russia = np.random.uniform(0.2, 0.4)
        self.desire_for_deal = np.random.uniform(0.6, 0.8)
        
    def step(self):
        russian_flexibility = np.mean([a.willingness_to_negotiate for a in self.model.schedule.agents if isinstance(a, RussianLeadershipAgent)])
        ukrainian_flexibility = np.mean([a.willingness_to_compromise for a in self.model.schedule.agents if isinstance(a, UkrainianLeadershipAgent)])
        
        if self.model.trump_administration_factor > 0.7:
            self.pressure_on_russia = max(0.1, self.pressure_on_russia - 0.03)
            self.desire_for_deal += 0.04
            
            if ukrainian_flexibility < 0.4:
                self.support_for_ukraine = max(0.2, self.support_for_ukraine - 0.05)
        
        if russian_flexibility > 0.4 and ukrainian_flexibility > 0.3:
            self.desire_for_deal += 0.03

class EuropeanLeaderAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.support_for_ukraine = np.random.uniform(0.5, 0.8)
        self.economic_fatigue = np.random.uniform(0.4, 0.7)
        self.desire_for_ceasefire = np.random.uniform(0.5, 0.7)
        
    def step(self):
        self.economic_fatigue = min(1.0, self.economic_fatigue + self.model.conflict_duration_factor * 0.02)
        
        if self.economic_fatigue > 0.7:
            self.support_for_ukraine = max(0.3, self.support_for_ukraine - 0.04)
            self.desire_for_ceasefire += 0.05
        
        us_commitment = np.mean([a.support_for_ukraine for a in self.model.schedule.agents if isinstance(a, USAdministrationAgent)])
        
        if us_commitment < 0.4:
            self.support_for_ukraine = max(0.2, self.support_for_ukraine - 0.06)

def compute_outcome(model):
    russian_agents = [a for a in model.schedule.agents if isinstance(a, RussianLeadershipAgent)]
    ukrainian_agents = [a for a in model.schedule.agents if isinstance(a, UkrainianLeadershipAgent)]
    us_agents = [a for a in model.schedule.agents if isinstance(a, USAdministrationAgent)]
    eu_agents = [a for a in model.schedule.agents if isinstance(a, EuropeanLeaderAgent)]
    
    if not russian_agents or not ukrainian_agents:
        return 0.0
    
    russian_flexibility = np.mean([a.willingness_to_negotiate for a in russian_agents])
    russian_demands = np.mean([a.territorial_demands for a in russian_agents])
    
    ukrainian_flexibility = np.mean([a.willingness_to_compromise for a in ukrainian_agents])
    ukrainian_demands = np.mean([a.territorial_integrity_demand for a in ukrainian_agents])
    
    us_deal_desire = np.mean([a.desire_for_deal for a in us_agents]) if us_agents else 0.5
    us_support = np.mean([a.support_for_ukraine for a in us_agents]) if us_agents else 0.5
    
    eu_ceasefire_desire = np.mean([a.desire_for_ceasefire for a in eu_agents]) if eu_agents else 0.5
    
    negotiation_gap = abs(russian_demands - (1.0 - ukrainian_demands))
    
    flexibility_score = (russian_flexibility + ukrainian_flexibility) / 2
    
    international_pressure = (us_deal_desire * 0.4 + eu_ceasefire_desire * 0.3 + (1.0 - us_support) * 0.3)
    
    ceasefire_probability = (flexibility_score * 0.35 + 
                            (1.0 - negotiation_gap) * 0.30 + 
                            international_pressure * 0.35)
    
    ceasefire_probability *= model.trump_administration_factor
    ceasefire_probability *= (1.0 + model.conflict_duration_factor * 0.3)
    
    return min(1.0, max(0.0, ceasefire_probability))

AGENT_CONFIG = {
    RussianLeadershipAgent: 3,
    UkrainianLeadershipAgent: 3,
    USAdministrationAgent: 2,
    EuropeanLeaderAgent: 5,
}

MODEL_PARAMS = {
    "trump_administration_factor": 0.85,
    "conflict_duration_factor": 0.75,
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
