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

class InstitutionalInvestor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.googl_allocation = np.random.uniform(0.1, 0.3)
        self.ai_sentiment = np.random.uniform(0.6, 0.9)
        self.risk_tolerance = np.random.uniform(0.5, 0.8)
        
    def step(self):
        ai_boost = self.model.gemini_performance * self.ai_sentiment
        cloud_boost = self.model.cloud_growth * 0.3
        regulatory_relief = self.model.antitrust_resolution * 0.2
        
        self.googl_allocation += (ai_boost + cloud_boost + regulatory_relief) * self.risk_tolerance * 0.1
        self.googl_allocation = np.clip(self.googl_allocation, 0.05, 0.5)

class RetailTrader(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.googl_position = np.random.uniform(0.05, 0.15)
        self.momentum_sensitivity = np.random.uniform(0.7, 1.0)
        self.news_impact = np.random.uniform(0.5, 0.9)
        
    def step(self):
        ytd_momentum = self.model.ytd_performance * self.momentum_sensitivity * 0.15
        product_news = self.model.product_launches * self.news_impact * 0.1
        
        self.googl_position += (ytd_momentum + product_news) * 0.08
        self.googl_position = np.clip(self.googl_position, 0.02, 0.3)

class TechAnalyst(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.googl_rating = np.random.uniform(0.6, 0.85)
        self.ai_expertise = np.random.uniform(0.7, 0.95)
        self.earnings_weight = np.random.uniform(0.6, 0.9)
        
    def step(self):
        ai_assessment = self.model.gemini_performance * self.ai_expertise * 0.2
        earnings_impact = self.model.earnings_strength * self.earnings_weight * 0.15
        competitive_position = (1.0 - self.model.nvidia_pullback) * 0.1
        
        self.googl_rating += (ai_assessment + earnings_impact + competitive_position) * 0.12
        self.googl_rating = np.clip(self.googl_rating, 0.3, 1.0)

class HedgeFundManager(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.googl_weight = np.random.uniform(0.15, 0.35)
        self.diversification_factor = np.random.uniform(0.5, 0.8)
        self.macro_sensitivity = np.random.uniform(0.6, 0.9)
        
    def step(self):
        business_strength = (self.model.cloud_growth + self.model.earnings_strength) / 2.0 * 0.2
        regulatory_clarity = self.model.antitrust_resolution * self.macro_sensitivity * 0.15
        ai_leadership = self.model.gemini_performance * 0.18
        
        adjustment = (business_strength + regulatory_clarity + ai_leadership) * self.diversification_factor
        self.googl_weight += adjustment * 0.1
        self.googl_weight = np.clip(self.googl_weight, 0.08, 0.45)

def compute_outcome(model):
    institutional_avg = np.mean([a.googl_allocation for a in model.schedule.agents if isinstance(a, InstitutionalInvestor)])
    retail_avg = np.mean([a.googl_position for a in model.schedule.agents if isinstance(a, RetailTrader)])
    analyst_avg = np.mean([a.googl_rating for a in model.schedule.agents if isinstance(a, TechAnalyst)])
    hedgefund_avg = np.mean([a.googl_weight for a in model.schedule.agents if isinstance(a, HedgeFundManager)])
    
    base_score = (institutional_avg * 0.35 + retail_avg * 0.15 + analyst_avg * 0.25 + hedgefund_avg * 0.25)
    
    fundamental_boost = (model.gemini_performance * 0.15 + 
                        model.cloud_growth * 0.12 + 
                        model.earnings_strength * 0.13 +
                        model.ytd_performance * 0.10 +
                        model.antitrust_resolution * 0.08 +
                        model.product_launches * 0.07)
    
    competitive_advantage = (1.0 - model.nvidia_pullback) * 0.10
    
    total_score = base_score + fundamental_boost + competitive_advantage
    
    return np.clip(total_score, 0.0, 1.0)

AGENT_CONFIG = {
    InstitutionalInvestor: 15,
    RetailTrader: 20,
    TechAnalyst: 8,
    HedgeFundManager: 7,
}

MODEL_PARAMS = {
    "gemini_performance": 0.88,
    "cloud_growth": 0.82,
    "earnings_strength": 0.85,
    "ytd_performance": 0.80,
    "antitrust_resolution": 0.75,
    "product_launches": 0.78,
    "nvidia_pullback": 0.15,
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
