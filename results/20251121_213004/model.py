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

class RussianNegotiator(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.territorial_demands = np.random.uniform(0.7, 0.95)
        self.flexibility = np.random.uniform(0.05, 0.20)
        self.domestic_pressure = np.random.uniform(0.6, 0.9)
        self.willingness_to_negotiate = 0.3
        
    def step(self):
        military_stalemate_effect = self.model.military_stalemate * 0.15
        mediation_effect = self.model.international_mediation * 0.1
        
        self.willingness_to_negotiate += (military_stalemate_effect + mediation_effect - self.domestic_pressure * 0.05)
        self.willingness_to_negotiate = np.clip(self.willingness_to_negotiate, 0, 1)
        
        if self.model.western_support > 0.7:
            self.territorial_demands = min(0.95, self.territorial_demands + 0.02)
        
        if self.willingness_to_negotiate > 0.5:
            self.flexibility = min(0.4, self.flexibility + 0.01)

class UkrainianNegotiator(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.sovereignty_priority = np.random.uniform(0.8, 0.95)
        self.flexibility = np.random.uniform(0.05, 0.15)
        self.resistance_capacity = np.random.uniform(0.6, 0.85)
        self.willingness_to_negotiate = 0.4
        
    def step(self):
        western_support_effect = self.model.western_support * 0.2
        humanitarian_pressure = (1 - self.model.humanitarian_crisis) * 0.1
        
        self.resistance_capacity = 0.5 + western_support_effect
        self.willingness_to_negotiate += (humanitarian_pressure - self.sovereignty_priority * 0.03)
        self.willingness_to_negotiate = np.clip(self.willingness_to_negotiate, 0, 1)
        
        if self.model.international_mediation > 0.6 and self.resistance_capacity > 0.6:
            self.flexibility = min(0.3, self.flexibility + 0.01)

class InternationalMediator(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.leverage = np.random.uniform(0.3, 0.6)
        self.credibility = np.random.uniform(0.4, 0.7)
        self.pressure_effectiveness = 0.3
        
    def step(self):
        russian_agents = [a for a in self.model.schedule.agents if isinstance(a, RussianNegotiator)]
        ukrainian_agents = [a for a in self.model.schedule.agents if isinstance(a, UkrainianNegotiator)]
        
        if russian_agents and ukrainian_agents:
            avg_russian_willingness = np.mean([a.willingness_to_negotiate for a in russian_agents])
            avg_ukrainian_willingness = np.mean([a.willingness_to_negotiate for a in ukrainian_agents])
            
            gap = abs(avg_russian_willingness - avg_ukrainian_willingness)
            
            if gap < 0.3:
                self.pressure_effectiveness += 0.05
            else:
                self.pressure_effectiveness = max(0.1, self.pressure_effectiveness - 0.02)
        
        self.leverage = min(0.8, self.leverage + self.model.international_mediation * 0.02)
        self.pressure_effectiveness = np.clip(self.pressure_effectiveness, 0, 1)

class DomesticPopulation(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.war_fatigue = np.random.uniform(0.4, 0.7)
        self.nationalist_sentiment = np.random.uniform(0.5, 0.8)
        self.country = "russia" if np.random.random() < 0.5 else "ukraine"
        
    def step(self):
        self.war_fatigue += self.model.humanitarian_crisis * 0.03
        self.war_fatigue = min(0.95, self.war_fatigue)
        
        if self.model.military_stalemate > 0.6:
            self.war_fatigue += 0.02
            self.nationalist_sentiment = max(0.3, self.nationalist_sentiment - 0.01)

def compute_outcome(model):
    russian_agents = [a for a in model.schedule.agents if isinstance(a, RussianNegotiator)]
    ukrainian_agents = [a for a in model.schedule.agents if isinstance(a, UkrainianNegotiator)]
    mediator_agents = [a for a in model.schedule.agents if isinstance(a, InternationalMediator)]
    population_agents = [a for a in model.schedule.agents if isinstance(a, DomesticPopulation)]
    
    if not russian_agents or not ukrainian_agents:
        return 0.14
    
    avg_russian_willingness = np.mean([a.willingness_to_negotiate for a in russian_agents])
    avg_ukrainian_willingness = np.mean([a.willingness_to_negotiate for a in ukrainian_agents])
    avg_russian_flexibility = np.mean([a.flexibility for a in russian_agents])
    avg_ukrainian_flexibility = np.mean([a.flexibility for a in ukrainian_agents])
    avg_russian_demands = np.mean([a.territorial_demands for a in russian_agents])
    avg_ukrainian_sovereignty = np.mean([a.sovereignty_priority for a in ukrainian_agents])
    
    mediator_effectiveness = np.mean([a.pressure_effectiveness for a in mediator_agents]) if mediator_agents else 0.3
    
    avg_war_fatigue = np.mean([a.war_fatigue for a in population_agents]) if population_agents else 0.5
    
    negotiation_alignment = 1 - abs(avg_russian_willingness - avg_ukrainian_willingness)
    flexibility_score = (avg_russian_flexibility + avg_ukrainian_flexibility) / 2
    demands_gap = avg_russian_demands - (1 - avg_ukrainian_sovereignty)
    
    ceasefire_probability = (
        negotiation_alignment * 0.25 +
        flexibility_score * 0.20 +
        mediator_effectiveness * 0.15 +
        avg_war_fatigue * 0.15 +
        (1 - abs(demands_gap)) * 0.15 +
        model.military_stalemate * 0.10
    )
    
    ceasefire_probability *= (1 - model.western_support * 0.3)
    ceasefire_probability *= (1 + model.international_mediation * 0.2)
    
    return np.clip(ceasefire_probability, 0, 1)

AGENT_CONFIG = {
    RussianNegotiator: 3,
    UkrainianNegotiator: 3,
    InternationalMediator: 4,
    DomesticPopulation: 20,
}

MODEL_PARAMS = {
    "military_stalemate": 0.75,
    "western_support": 0.80,
    "international_mediation": 0.50,
    "humanitarian_crisis": 0.70,
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
