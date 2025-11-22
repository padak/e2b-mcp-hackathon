import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

class MarketInvestor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.sentiment = np.random.uniform(0.3, 0.9)
        self.ai_optimism = np.random.uniform(0.5, 1.0)
        self.volatility_tolerance = np.random.uniform(0.3, 0.8)
        
    def step(self):
        sentiment_change = np.random.normal(0, 0.05)
        self.sentiment = np.clip(self.sentiment + sentiment_change * self.model.market_volatility, 0, 1)
        
        if self.model.ai_hype > 0.7:
            self.ai_optimism = np.clip(self.ai_optimism + 0.02, 0, 1)
        
        if self.model.market_volatility > 0.6:
            self.sentiment *= (1 - (1 - self.volatility_tolerance) * 0.1)

class TechAnalyst(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.alphabet_rating = np.random.uniform(0.5, 0.9)
        self.competitor_concern = np.random.uniform(0.2, 0.6)
        
    def step(self):
        earnings_impact = self.model.earnings_strength * 0.15
        self.alphabet_rating = np.clip(self.alphabet_rating + earnings_impact, 0, 1)
        
        if self.model.microsoft_momentum > 0.6:
            self.competitor_concern = np.clip(self.competitor_concern + 0.03, 0, 1)
            self.alphabet_rating *= 0.98
        
        ai_boost = self.model.ai_hype * 0.1
        self.alphabet_rating = np.clip(self.alphabet_rating + ai_boost, 0, 1)

class InstitutionalTrader(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.position_size = np.random.uniform(0.4, 0.9)
        self.rotation_probability = np.random.uniform(0.1, 0.4)
        self.confidence = np.random.uniform(0.5, 0.8)
        
    def step(self):
        if np.random.random() < self.rotation_probability * self.model.sector_rotation:
            self.position_size *= 0.95
        else:
            growth_factor = self.model.earnings_strength * 0.08
            self.position_size = np.clip(self.position_size + growth_factor, 0, 1)
        
        if self.model.market_volatility < 0.4:
            self.confidence = np.clip(self.confidence + 0.03, 0, 1)
        else:
            self.confidence = np.clip(self.confidence - 0.02, 0, 1)

class MacroeconomicActor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.policy_impact = np.random.uniform(0.3, 0.7)
        self.tech_favorability = np.random.uniform(0.5, 0.9)
        
    def step(self):
        policy_shift = np.random.normal(0, 0.03)
        self.policy_impact = np.clip(self.policy_impact + policy_shift, 0, 1)
        
        if self.model.market_volatility > 0.7:
            self.tech_favorability *= 0.97
        
        if self.model.earnings_strength > 0.7:
            self.tech_favorability = np.clip(self.tech_favorability + 0.02, 0, 1)

def compute_outcome(model):
    investors = [a for a in model.schedule.agents if isinstance(a, MarketInvestor)]
    analysts = [a for a in model.schedule.agents if isinstance(a, TechAnalyst)]
    traders = [a for a in model.schedule.agents if isinstance(a, InstitutionalTrader)]
    macro_actors = [a for a in model.schedule.agents if isinstance(a, MacroeconomicActor)]
    
    investor_score = np.mean([a.sentiment * a.ai_optimism for a in investors]) if investors else 0.5
    analyst_score = np.mean([a.alphabet_rating * (1 - a.competitor_concern * 0.5) for a in analysts]) if analysts else 0.5
    trader_score = np.mean([a.position_size * a.confidence for a in traders]) if traders else 0.5
    macro_score = np.mean([a.policy_impact * a.tech_favorability for a in macro_actors]) if macro_actors else 0.5
    
    base_probability = 0.66
    
    investor_weight = 0.25
    analyst_weight = 0.30
    trader_weight = 0.30
    macro_weight = 0.15
    
    outcome = (base_probability * 0.3 + 
              investor_score * investor_weight +
              analyst_score * analyst_weight +
              trader_score * trader_weight +
              macro_score * macro_weight)
    
    outcome *= (1 + model.ai_hype * 0.15)
    outcome *= (1 - model.microsoft_momentum * 0.1)
    outcome *= (1 + model.earnings_strength * 0.1)
    outcome *= (1 - model.market_volatility * 0.05)
    
    return np.clip(outcome, 0, 1)

AGENT_CONFIG = {
    MarketInvestor: 15,
    TechAnalyst: 8,
    InstitutionalTrader: 10,
    MacroeconomicActor: 5,
}

MODEL_PARAMS = {
    "ai_hype": 0.75,
    "market_volatility": 0.45,
    "earnings_strength": 0.70,
    "microsoft_momentum": 0.50,
    "sector_rotation": 0.35,
}

THRESHOLD = 0.65
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
