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
        self.buying_power = np.random.uniform(0.5, 1.0)
        self.risk_tolerance = np.random.uniform(0.3, 0.8)
        self.sentiment = np.random.uniform(0.4, 0.7)
        self.accumulated_position = 0.0
        
    def step(self):
        market_momentum = self.model.price_momentum
        macro_conditions = self.model.macro_environment
        
        if macro_conditions > 0.6 and market_momentum > 0.5:
            buy_signal = self.risk_tolerance * self.buying_power * (macro_conditions + market_momentum) / 2
            self.accumulated_position += buy_signal * 0.1
            self.sentiment = min(1.0, self.sentiment + 0.05)
        else:
            self.sentiment = max(0.0, self.sentiment - 0.03)
            
        if self.accumulated_position > 0.8:
            self.accumulated_position *= 0.95

class RetailTrader(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.fomo_level = np.random.uniform(0.3, 0.9)
        self.capital = np.random.uniform(0.1, 0.5)
        self.sentiment = np.random.uniform(0.3, 0.8)
        self.position = 0.0
        
    def step(self):
        price_momentum = self.model.price_momentum
        social_sentiment = self.model.social_media_buzz
        
        if price_momentum > 0.6 and social_sentiment > 0.6:
            fomo_buy = self.fomo_level * self.capital * (price_momentum + social_sentiment) / 2
            self.position += fomo_buy * 0.15
            self.sentiment = min(1.0, self.sentiment + 0.08)
        elif price_momentum < 0.4:
            self.position *= 0.9
            self.sentiment = max(0.2, self.sentiment - 0.05)
        else:
            self.sentiment = self.sentiment * 0.98 + 0.02 * social_sentiment

class MarketMaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.liquidity_provision = np.random.uniform(0.7, 1.0)
        self.price_efficiency = np.random.uniform(0.6, 0.9)
        self.volatility_tolerance = np.random.uniform(0.4, 0.8)
        
    def step(self):
        current_volatility = self.model.volatility
        demand_pressure = self.model.demand_pressure
        
        if current_volatility < self.volatility_tolerance:
            self.liquidity_provision = min(1.0, self.liquidity_provision + 0.03)
        else:
            self.liquidity_provision = max(0.5, self.liquidity_provision - 0.05)
            
        self.price_efficiency = 0.7 * self.price_efficiency + 0.3 * (1.0 - current_volatility)

class WhaleInvestor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.capital = np.random.uniform(0.8, 1.0)
        self.strategic_patience = np.random.uniform(0.6, 0.9)
        self.market_impact = np.random.uniform(0.7, 1.0)
        self.position_size = 0.0
        self.entry_threshold = np.random.uniform(0.5, 0.7)
        
    def step(self):
        macro_env = self.model.macro_environment
        time_remaining = self.model.time_remaining
        
        if macro_env > self.entry_threshold and time_remaining > 0.3:
            buy_amount = self.capital * self.market_impact * 0.08
            self.position_size += buy_amount
            self.model.demand_pressure = min(1.0, self.model.demand_pressure + buy_amount * 0.2)
        elif time_remaining < 0.2 and self.position_size > 0.5:
            self.position_size *= 0.85

def compute_outcome(model):
    institutional_sentiment = np.mean([agent.sentiment for agent in model.schedule.agents if isinstance(agent, InstitutionalInvestor)])
    retail_sentiment = np.mean([agent.sentiment for agent in model.schedule.agents if isinstance(agent, RetailTrader)])
    whale_positions = np.mean([agent.position_size for agent in model.schedule.agents if isinstance(agent, WhaleInvestor)])
    
    institutional_positions = np.mean([agent.accumulated_position for agent in model.schedule.agents if isinstance(agent, InstitutionalInvestor)])
    retail_positions = np.mean([agent.position for agent in model.schedule.agents if isinstance(agent, RetailTrader)])
    
    price_momentum = model.price_momentum
    macro_env = model.macro_environment
    time_factor = model.time_remaining
    
    momentum_component = price_momentum * 0.25
    sentiment_component = (institutional_sentiment * 0.3 + retail_sentiment * 0.15 + whale_positions * 0.25)
    position_component = (institutional_positions * 0.25 + retail_positions * 0.15 + whale_positions * 0.2) * 0.3
    macro_component = macro_env * 0.2
    time_penalty = max(0.3, time_factor) * 0.2
    
    outcome_probability = (momentum_component + sentiment_component + position_component + macro_component) * time_penalty
    
    return min(1.0, max(0.0, outcome_probability))

AGENT_CONFIG = {
    InstitutionalInvestor: 8,
    RetailTrader: 20,
    MarketMaker: 4,
    WhaleInvestor: 3,
}

MODEL_PARAMS = {
    "price_momentum": 0.55,
    "macro_environment": 0.60,
    "social_media_buzz": 0.65,
    "volatility": 0.45,
    "demand_pressure": 0.50,
    "time_remaining": 0.15,
}

THRESHOLD = 0.12
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
