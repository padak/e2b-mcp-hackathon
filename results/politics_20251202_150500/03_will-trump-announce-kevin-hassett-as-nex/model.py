import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class TrumpDecisionMaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.hassett_support = np.random.uniform(0.7, 0.85)
        self.market_sensitivity = np.random.uniform(0.6, 0.9)
        self.loyalty_weight = np.random.uniform(0.7, 0.9)
        
    def step(self):
        market_avg = np.mean([a.market_confidence for a in self.model.schedule.agents if isinstance(a, MarketActor)])
        advisor_avg = np.mean([a.hassett_endorsement for a in self.model.schedule.agents if isinstance(a, WhiteHouseAdvisor)])
        
        self.hassett_support += (market_avg - 0.5) * self.market_sensitivity * 0.05
        self.hassett_support += (advisor_avg - 0.5) * self.loyalty_weight * 0.05
        self.hassett_support = np.clip(self.hassett_support, 0.4, 0.95)


class WhiteHouseAdvisor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.hassett_endorsement = np.random.uniform(0.6, 0.85)
        self.alternative_preference = np.random.uniform(0.1, 0.4)
        
    def step(self):
        trump_support = [a.hassett_support for a in self.model.schedule.agents if isinstance(a, TrumpDecisionMaker)]
        if trump_support:
            avg_trump_support = np.mean(trump_support)
            self.hassett_endorsement += (avg_trump_support - self.hassett_endorsement) * 0.1
        
        if np.random.random() < 0.1:
            self.alternative_preference += np.random.uniform(-0.05, 0.05)
            self.alternative_preference = np.clip(self.alternative_preference, 0.0, 0.5)
        
        self.hassett_endorsement = np.clip(self.hassett_endorsement, 0.3, 0.9)


class MarketActor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.market_confidence = np.random.uniform(0.65, 0.85)
        self.hassett_credibility = np.random.uniform(0.7, 0.9)
        
    def step(self):
        other_markets = [a.market_confidence for a in self.model.schedule.agents if isinstance(a, MarketActor) and a != self]
        if other_markets:
            avg_confidence = np.mean(other_markets)
            self.market_confidence += (avg_confidence - self.market_confidence) * 0.15
        
        self.market_confidence += (self.hassett_credibility - 0.5) * self.model.market_momentum * 0.05
        self.market_confidence = np.clip(self.market_confidence, 0.5, 0.95)


class CompetingCandidate(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.support_level = np.random.uniform(0.1, 0.35)
        self.campaign_strength = np.random.uniform(0.2, 0.5)
        
    def step(self):
        hassett_momentum = np.mean([a.hassett_support for a in self.model.schedule.agents if isinstance(a, TrumpDecisionMaker)])
        
        if hassett_momentum > 0.75:
            self.support_level -= np.random.uniform(0.01, 0.03)
        else:
            self.support_level += self.campaign_strength * 0.03
        
        self.support_level = np.clip(self.support_level, 0.05, 0.45)


# Outcome computation
def compute_outcome(model):
    trump_agents = [a for a in model.schedule.agents if isinstance(a, TrumpDecisionMaker)]
    advisor_agents = [a for a in model.schedule.agents if isinstance(a, WhiteHouseAdvisor)]
    market_agents = [a for a in model.schedule.agents if isinstance(a, MarketActor)]
    candidate_agents = [a for a in model.schedule.agents if isinstance(a, CompetingCandidate)]
    
    trump_support = np.mean([a.hassett_support for a in trump_agents]) if trump_agents else 0.7
    advisor_support = np.mean([a.hassett_endorsement for a in advisor_agents]) if advisor_agents else 0.7
    market_support = np.mean([a.market_confidence for a in market_agents]) if market_agents else 0.75
    competitor_strength = np.mean([a.support_level for a in candidate_agents]) if candidate_agents else 0.25
    
    timeline_factor = min(1.0, model.schedule.steps / 50.0)
    
    outcome = (trump_support * 0.5 + 
               advisor_support * 0.2 + 
               market_support * 0.15 + 
               (1 - competitor_strength) * 0.15) * (0.9 + timeline_factor * 0.1)
    
    return outcome


# Configuration
AGENT_CONFIG = {
    TrumpDecisionMaker: 1,
    WhiteHouseAdvisor: 8,
    MarketActor: 15,
    CompetingCandidate: 4,
}

MODEL_PARAMS = {
    "market_momentum": 0.75,
}

THRESHOLD = 0.70
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
