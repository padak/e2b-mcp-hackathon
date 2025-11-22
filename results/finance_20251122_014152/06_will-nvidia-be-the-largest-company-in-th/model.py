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

class InstitutionalInvestor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.nvda_confidence = np.random.uniform(0.6, 0.95)
        self.risk_tolerance = np.random.uniform(0.3, 0.8)
        self.market_sentiment = np.random.uniform(0.5, 1.0)
        
    def step(self):
        # React to AI demand and competition
        ai_boost = self.model.ai_demand_strength * 0.15
        competition_pressure = self.model.competition_intensity * -0.1
        
        # Adjust confidence based on market conditions
        self.nvda_confidence += ai_boost + competition_pressure
        self.nvda_confidence = np.clip(self.nvda_confidence, 0.0, 1.0)
        
        # Update sentiment based on volatility
        volatility_impact = self.model.market_volatility * -0.05 * (1 - self.risk_tolerance)
        self.market_sentiment += volatility_impact + np.random.uniform(-0.02, 0.02)
        self.market_sentiment = np.clip(self.market_sentiment, 0.0, 1.0)

class TechAnalyst(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.nvda_outlook = np.random.uniform(0.65, 0.9)
        self.competitor_threat_assessment = np.random.uniform(0.2, 0.5)
        
    def step(self):
        # Analysts evaluate fundamentals and competitive position
        fundamental_strength = self.model.ai_demand_strength * 0.2
        competitive_dynamics = self.model.competition_intensity * 0.15
        
        # Update outlook
        self.nvda_outlook += fundamental_strength - competitive_dynamics
        self.nvda_outlook = np.clip(self.nvda_outlook, 0.0, 1.0)
        
        # Reassess competitor threats
        self.competitor_threat_assessment += competitive_dynamics + np.random.uniform(-0.03, 0.03)
        self.competitor_threat_assessment = np.clip(self.competitor_threat_assessment, 0.0, 1.0)

class MarketMaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.price_momentum = np.random.uniform(0.6, 0.85)
        self.volatility_factor = np.random.uniform(0.3, 0.7)
        
    def step(self):
        # Market makers respond to overall market conditions
        momentum_change = (self.model.ai_demand_strength - self.model.market_volatility) * 0.1
        self.price_momentum += momentum_change + np.random.uniform(-0.04, 0.04)
        self.price_momentum = np.clip(self.price_momentum, 0.0, 1.0)
        
        # Adjust for volatility
        self.volatility_factor = 0.7 * self.volatility_factor + 0.3 * self.model.market_volatility

class RegulatoryWatcher(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.regulatory_risk = np.random.uniform(0.1, 0.3)
        self.geopolitical_concern = np.random.uniform(0.15, 0.35)
        
    def step(self):
        # Monitor regulatory and geopolitical risks
        risk_change = self.model.regulatory_pressure * 0.08 + np.random.uniform(-0.02, 0.02)
        self.regulatory_risk += risk_change
        self.regulatory_risk = np.clip(self.regulatory_risk, 0.0, 1.0)
        
        # Geopolitical concerns vary with volatility
        self.geopolitical_concern += self.model.market_volatility * 0.05 + np.random.uniform(-0.015, 0.015)
        self.geopolitical_concern = np.clip(self.geopolitical_concern, 0.0, 1.0)

def compute_outcome(model):
    # Aggregate sentiment from different agent types
    institutional_avg = np.mean([agent.nvda_confidence * agent.market_sentiment 
                                  for agent in model.schedule.agents 
                                  if isinstance(agent, InstitutionalInvestor)])
    
    analyst_avg = np.mean([agent.nvda_outlook * (1 - agent.competitor_threat_assessment * 0.5)
                           for agent in model.schedule.agents 
                           if isinstance(agent, TechAnalyst)])
    
    market_maker_avg = np.mean([agent.price_momentum * (1 - agent.volatility_factor * 0.3)
                                for agent in model.schedule.agents 
                                if isinstance(agent, MarketMaker)])
    
    regulatory_drag = np.mean([1 - (agent.regulatory_risk * 0.4 + agent.geopolitical_concern * 0.3)
                               for agent in model.schedule.agents 
                               if isinstance(agent, RegulatoryWatcher)])
    
    # Weight different perspectives (institutional investors have most impact)
    base_probability = (institutional_avg * 0.40 + 
                       analyst_avg * 0.30 + 
                       market_maker_avg * 0.20 + 
                       regulatory_drag * 0.10)
    
    # Apply exogenous factors
    ai_boost = model.ai_demand_strength * 0.08
    competition_penalty = model.competition_intensity * 0.06
    volatility_penalty = model.market_volatility * 0.05
    
    outcome = base_probability + ai_boost - competition_penalty - volatility_penalty
    
    return np.clip(outcome, 0.0, 1.0)

AGENT_CONFIG = {
    InstitutionalInvestor: 20,
    TechAnalyst: 10,
    MarketMaker: 8,
    RegulatoryWatcher: 5,
}

MODEL_PARAMS = {
    "ai_demand_strength": 0.85,
    "competition_intensity": 0.35,
    "market_volatility": 0.25,
    "regulatory_pressure": 0.20,
}

THRESHOLD = 0.72
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
