import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class Policymaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.uncertainty_contribution = np.random.uniform(0.3, 0.7)
        self.stimulus_inclination = np.random.uniform(0.4, 0.8)
        
    def step(self):
        # Policymakers respond to economic weakness by adjusting stimulus
        avg_consumer_confidence = np.mean([a.confidence for a in self.model.schedule.agents if isinstance(a, Consumer)])
        avg_business_sentiment = np.mean([a.sentiment for a in self.model.schedule.agents if isinstance(a, Business)])
        
        if avg_consumer_confidence < 0.4 or avg_business_sentiment < 0.4:
            self.stimulus_inclination = min(0.9, self.stimulus_inclination + 0.05)
        
        # Policy uncertainty creates volatility
        if np.random.random() < self.model.policy_volatility:
            self.uncertainty_contribution += np.random.uniform(-0.1, 0.1)
            self.uncertainty_contribution = np.clip(self.uncertainty_contribution, 0.2, 0.8)

class Consumer(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.confidence = np.random.uniform(0.3, 0.6)
        self.spending_rate = np.random.uniform(0.4, 0.7)
        
    def step(self):
        # Consumer confidence responds to policy uncertainty and business sentiment
        avg_policy_uncertainty = np.mean([a.uncertainty_contribution for a in self.model.schedule.agents if isinstance(a, Policymaker)])
        avg_business_sentiment = np.mean([a.sentiment for a in self.model.schedule.agents if isinstance(a, Business)])
        
        # High policy uncertainty reduces confidence
        self.confidence -= avg_policy_uncertainty * 0.1
        
        # Business sentiment influences consumer confidence
        self.confidence += (avg_business_sentiment - 0.5) * 0.05
        
        # Fed rate impact
        if self.model.fed_rate_high:
            self.confidence -= 0.02
        
        # Spending responds to confidence
        self.spending_rate = 0.3 + self.confidence * 0.6
        
        self.confidence = np.clip(self.confidence, 0.1, 0.9)
        self.spending_rate = np.clip(self.spending_rate, 0.2, 0.9)

class Business(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.sentiment = np.random.uniform(0.4, 0.7)
        self.investment_rate = np.random.uniform(0.3, 0.6)
        
    def step(self):
        # Business sentiment responds to tariff risk, consumer spending, and policy
        avg_consumer_spending = np.mean([a.spending_rate for a in self.model.schedule.agents if isinstance(a, Consumer)])
        avg_stimulus = np.mean([a.stimulus_inclination for a in self.model.schedule.agents if isinstance(a, Policymaker)])
        
        # Tariff uncertainty hurts sentiment
        self.sentiment -= self.model.tariff_risk * 0.08
        
        # Consumer spending drives business optimism
        self.sentiment += (avg_consumer_spending - 0.5) * 0.1
        
        # Stimulus helps sentiment
        self.sentiment += avg_stimulus * 0.03
        
        # AI productivity boost (speculative upside)
        if np.random.random() < self.model.ai_adoption_rate:
            self.sentiment += 0.05
        
        self.investment_rate = 0.2 + self.sentiment * 0.7
        
        self.sentiment = np.clip(self.sentiment, 0.1, 0.9)
        self.investment_rate = np.clip(self.investment_rate, 0.1, 0.8)

class FinancialInstitution(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.stability = np.random.uniform(0.6, 0.9)
        self.risk_exposure = np.random.uniform(0.3, 0.6)
        
    def step(self):
        # Financial stability responds to asset valuations and economic conditions
        avg_business_sentiment = np.mean([a.sentiment for a in self.model.schedule.agents if isinstance(a, Business)])
        avg_consumer_confidence = np.mean([a.confidence for a in self.model.schedule.agents if isinstance(a, Consumer)])
        
        # Elevated asset valuations create vulnerability
        if self.model.asset_valuations_high:
            self.risk_exposure += 0.02
            self.stability -= 0.03
        
        # Weak economy increases risk
        if avg_business_sentiment < 0.4 or avg_consumer_confidence < 0.4:
            self.stability -= 0.04
        
        # Fed policy support
        if not self.model.fed_rate_high:
            self.stability += 0.02
        
        self.stability = np.clip(self.stability, 0.2, 0.95)
        self.risk_exposure = np.clip(self.risk_exposure, 0.1, 0.8)

# Outcome computation
def compute_outcome(model):
    # Gather agent states
    consumer_confidence = np.mean([a.confidence for a in model.schedule.agents if isinstance(a, Consumer)])
    consumer_spending = np.mean([a.spending_rate for a in model.schedule.agents if isinstance(a, Consumer)])
    business_sentiment = np.mean([a.sentiment for a in model.schedule.agents if isinstance(a, Business)])
    business_investment = np.mean([a.investment_rate for a in model.schedule.agents if isinstance(a, Business)])
    financial_stability = np.mean([a.stability for a in model.schedule.agents if isinstance(a, FinancialInstitution)])
    policy_uncertainty = np.mean([a.uncertainty_contribution for a in model.schedule.agents if isinstance(a, Policymaker)])
    
    # Compute recession probability (higher value = more likely recession = "Yes")
    recession_score = 0.0
    
    # Low consumer metrics increase recession risk
    recession_score += (0.5 - consumer_confidence) * 0.4
    recession_score += (0.5 - consumer_spending) * 0.3
    
    # Low business metrics increase recession risk
    recession_score += (0.5 - business_sentiment) * 0.35
    recession_score += (0.5 - business_investment) * 0.25
    
    # Financial instability increases recession risk
    recession_score += (0.7 - financial_stability) * 0.4
    
    # Policy uncertainty increases recession risk
    recession_score += policy_uncertainty * 0.3
    
    # External factors
    recession_score += model.tariff_risk * 0.25
    if model.fed_rate_high:
        recession_score += 0.08
    if model.asset_valuations_high:
        recession_score += 0.06
    
    # AI adoption reduces recession risk
    recession_score -= model.ai_adoption_rate * 0.15
    
    # Normalize to 0-1 range (calibrate to match ~22-40% base probability)
    recession_probability = np.clip(recession_score * 0.5 + 0.1, 0.0, 1.0)
    
    return recession_probability

# Configuration
AGENT_CONFIG = {
    Policymaker: 3,
    Consumer: 20,
    Business: 15,
    FinancialInstitution: 4,
}

MODEL_PARAMS = {
    "policy_volatility": 0.35,
    "tariff_risk": 0.45,
    "fed_rate_high": False,
    "asset_valuations_high": True,
    "ai_adoption_rate": 0.15,
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
