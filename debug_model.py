import random
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
from mesa import Agent
import random

class MaduroRegime(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.control_strength = 0.85
        self.military_loyalty = 0.80
        self.repression_capacity = 0.75
        
    def step(self):
        # Regime adapts to pressure by increasing repression
        external_pressure = self.model.us_pressure + self.model.intl_sanctions
        self.repression_capacity = min(0.95, self.repression_capacity + external_pressure * 0.02)
        
        # Military loyalty can erode under sustained pressure and economic collapse
        if self.model.economic_collapse > 0.7 and random.random() < 0.1:
            self.military_loyalty *= 0.95
        
        # Control strength is composite of military and repression
        self.control_strength = (self.military_loyalty * 0.6 + self.repression_capacity * 0.4)
        
        # Small chance of elite defection if control weakens significantly
        if self.control_strength < 0.5 and random.random() < 0.15:
            self.control_strength *= 0.8

class Opposition(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.mobilization = 0.35
        self.international_support = 0.40
        self.unity = 0.45
        
    def step(self):
        # Mobilization increases with economic collapse and international support
        self.mobilization = min(0.9, self.mobilization + 
                               self.model.economic_collapse * 0.03 + 
                               self.international_support * 0.02)
        
        # Repression dampens mobilization
        regime_agents = [a for a in self.model.agents if isinstance(a, MaduroRegime)]
        if regime_agents:
            avg_repression = sum(r.repression_capacity for r in regime_agents) / len(regime_agents)
            self.mobilization *= (1 - avg_repression * 0.15)
        
        # International support increases with US pressure
        self.international_support = min(0.85, self.international_support + 
                                        self.model.us_pressure * 0.05)
        
        # Unity fluctuates but trends up with external support
        if random.random() < 0.3:
            self.unity = min(0.8, self.unity + random.uniform(0, 0.1))
        else:
            self.unity *= random.uniform(0.95, 1.0)

class USIntervention(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.covert_ops_intensity = 0.30
        self.military_threat_level = 0.15
        self.diplomatic_pressure = 0.50
        
    def step(self):
        # US escalates based on regime strength and policy
        regime_agents = [a for a in self.model.agents if isinstance(a, MaduroRegime)]
        if regime_agents:
            avg_control = sum(r.control_strength for r in regime_agents) / len(regime_agents)
            
            # Higher regime control may trigger more intervention
            if avg_control > 0.75:
                self.covert_ops_intensity = min(0.7, self.covert_ops_intensity + 0.05)
                if random.random() < self.model.intervention_probability:
                    self.military_threat_level = min(0.5, self.military_threat_level + 0.08)
        
        # Update model pressure
        self.model.us_pressure = (self.covert_ops_intensity * 0.4 + 
                                 self.military_threat_level * 0.4 + 
                                 self.diplomatic_pressure * 0.2)

class Military(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.loyalty_to_maduro = 0.75
        self.economic_satisfaction = 0.50
        self.coup_risk = 0.10
        
    def step(self):
        # Economic collapse erodes military satisfaction
        self.economic_satisfaction = max(0.1, self.economic_satisfaction - 
                                        self.model.economic_collapse * 0.04)
        
        # US pressure and low satisfaction increase coup risk
        if self.economic_satisfaction < 0.3 and self.model.us_pressure > 0.4:
            self.coup_risk = min(0.6, self.coup_risk + 0.08)
        
        # Loyalty erodes with low satisfaction and high coup risk
        if self.economic_satisfaction < 0.4:
            self.loyalty_to_maduro *= 0.98
        
        # Catastrophic loyalty collapse triggers potential coup
        if self.loyalty_to_maduro < 0.4 and random.random() < self.coup_risk:
            self.loyalty_to_maduro *= 0.5
            self.coup_risk = min(0.9, self.coup_risk * 1.5)

def compute_outcome(model):
    regime_agents = [a for a in model.agents if isinstance(a, MaduroRegime)]
    opposition_agents = [a for a in model.agents if isinstance(a, Opposition)]
    us_agents = [a for a in model.agents if isinstance(a, USIntervention)]
    military_agents = [a for a in model.agents if isinstance(a, Military)]
    
    if not regime_agents:
        return 0.5
    
    # Average regime control strength (inverse for ouster probability)
    avg_regime_control = sum(r.control_strength for r in regime_agents) / len(regime_agents)
    
    # Opposition strength
    avg_opposition_strength = 0
    if opposition_agents:
        avg_opposition_strength = sum((o.mobilization * 0.4 + o.unity * 0.3 + 
                                       o.international_support * 0.3) 
                                      for o in opposition_agents) / len(opposition_agents)
    
    # US intervention impact
    avg_us_impact = 0
    if us_agents:
        avg_us_impact = sum((u.covert_ops_intensity * 0.3 + 
                            u.military_threat_level * 0.5 + 
                            u.diplomatic_pressure * 0.2) 
                           for u in us_agents) / len(us_agents)
    
    # Military defection risk
    avg_military_defection = 0
    if military_agents:
        avg_military_defection = sum((1 - m.loyalty_to_maduro) * 0.6 + m.coup_risk * 0.4 
                                     for m in military_agents) / len(military_agents)
    
    # Combined probability of Maduro being ousted
    ouster_probability = (
        (1 - avg_regime_control) * 0.35 +
        avg_opposition_strength * 0.20 +
        avg_us_impact * 0.25 +
        avg_military_defection * 0.20
    )
    
    # Cap probability realistically given current odds
    return min(0.40, max(0.05, ouster_probability))

AGENT_CONFIG = {
    MaduroRegime: 1,
    Opposition: 8,
    USIntervention: 2,
    Military: 5,
}

MODEL_PARAMS = {
    "us_pressure": 0.35,
    "intl_sanctions": 0.60,
    "economic_collapse": 0.75,
    "intervention_probability": 0.12,
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
