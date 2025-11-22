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
        self.willingness_to_negotiate = np.random.uniform(0.2, 0.4)
        self.territorial_demands_met = 0.0
        self.pressure_from_military_losses = np.random.uniform(0.3, 0.5)
        
    def step(self):
        # Russia becomes more willing if territorial demands partially met or facing pressure
        self.territorial_demands_met = self.model.territorial_control * 0.3
        
        # Western aid reduces willingness, military pressure increases it
        western_aid_effect = -self.model.western_military_aid * 0.4
        pressure_effect = self.pressure_from_military_losses * 0.2
        
        self.willingness_to_negotiate = np.clip(
            self.willingness_to_negotiate + western_aid_effect + pressure_effect + self.territorial_demands_met,
            0.0, 1.0
        )
        
        # Russia demands preconditions
        if self.model.western_military_aid > 0.6:
            self.willingness_to_negotiate *= 0.5

class UkrainianLeadership(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.willingness_to_negotiate = np.random.uniform(0.3, 0.5)
        self.sovereignty_requirement = 0.9
        self.war_fatigue = np.random.uniform(0.4, 0.6)
        
    def step(self):
        # Ukraine willing to negotiate only if sovereignty maintained and has support
        support_effect = self.model.western_military_aid * 0.3
        territorial_loss_effect = -(1.0 - self.model.territorial_control) * 0.4
        
        self.war_fatigue += 0.01
        fatigue_effect = self.war_fatigue * 0.15
        
        self.willingness_to_negotiate = np.clip(
            self.willingness_to_negotiate + support_effect + territorial_loss_effect + fatigue_effect,
            0.0, 1.0
        )
        
        # Ukraine demands full ceasefire, not partial
        if self.model.territorial_control < 0.7:
            self.willingness_to_negotiate *= 0.7

class InternationalMediator(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.diplomatic_pressure = np.random.uniform(0.4, 0.6)
        self.negotiation_momentum = 0.3
        
    def step(self):
        # Mediators push for talks when humanitarian crisis worsens
        humanitarian_pressure = self.model.humanitarian_crisis * 0.25
        
        # Momentum builds with ongoing talks
        if self.model.active_negotiations:
            self.negotiation_momentum += 0.05
        else:
            self.negotiation_momentum *= 0.9
            
        self.diplomatic_pressure = np.clip(
            self.diplomatic_pressure + humanitarian_pressure + self.negotiation_momentum * 0.1,
            0.0, 1.0
        )

class MilitaryCommander(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.side = np.random.choice(['russia', 'ukraine'])
        self.battlefield_intensity = np.random.uniform(0.6, 0.9)
        self.stalemate_perception = np.random.uniform(0.3, 0.5)
        
    def step(self):
        # Military stalemate increases pressure for ceasefire
        if self.model.territorial_control > 0.45 and self.model.territorial_control < 0.55:
            self.stalemate_perception += 0.03
        else:
            self.stalemate_perception *= 0.95
            
        # Continued fighting reduces ceasefire likelihood
        self.battlefield_intensity = np.random.uniform(0.5, 0.9)
        
        self.stalemate_perception = np.clip(self.stalemate_perception, 0.0, 1.0)

# Outcome computation
def compute_outcome(model):
    russian_agents = [a for a in model.schedule.agents if isinstance(a, RussianLeadership)]
    ukrainian_agents = [a for a in model.schedule.agents if isinstance(a, UkrainianLeadership)]
    mediator_agents = [a for a in model.schedule.agents if isinstance(a, InternationalMediator)]
    military_agents = [a for a in model.schedule.agents if isinstance(a, MilitaryCommander)]
    
    # Average willingness from both sides
    russian_willingness = np.mean([a.willingness_to_negotiate for a in russian_agents]) if russian_agents else 0.0
    ukrainian_willingness = np.mean([a.willingness_to_negotiate for a in ukrainian_agents]) if ukrainian_agents else 0.0
    
    # Diplomatic pressure
    diplomatic_push = np.mean([a.diplomatic_pressure for a in mediator_agents]) if mediator_agents else 0.0
    
    # Military stalemate factor
    stalemate_pressure = np.mean([a.stalemate_perception for a in military_agents]) if military_agents else 0.0
    
    # Reduce by battlefield intensity
    avg_intensity = np.mean([a.battlefield_intensity for a in military_agents]) if military_agents else 0.8
    
    # Key incompatible demands reduce probability dramatically
    territorial_compatibility = 1.0 - abs(0.85 - model.territorial_control)
    precondition_penalty = model.western_military_aid * 0.3
    
    # Ceasefire probability formula
    base_probability = (
        russian_willingness * 0.25 +
        ukrainian_willingness * 0.25 +
        diplomatic_push * 0.15 +
        stalemate_pressure * 0.15 +
        territorial_compatibility * 0.1 +
        (1.0 - avg_intensity) * 0.1
    )
    
    # Apply penalties for incompatible positions
    final_probability = base_probability * (1.0 - precondition_penalty)
    
    # Account for fundamental disagreements
    if model.territorial_control < 0.7 or model.western_military_aid > 0.6:
        final_probability *= 0.6
    
    return np.clip(final_probability, 0.0, 1.0)

# Configuration
AGENT_CONFIG = {
    RussianLeadership: 3,
    UkrainianLeadership: 3,
    InternationalMediator: 4,
    MilitaryCommander: 12,
}

MODEL_PARAMS = {
    "territorial_control": 0.75,
    "western_military_aid": 0.7,
    "humanitarian_crisis": 0.8,
    "active_negotiations": True,
}

THRESHOLD = 0.18
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
