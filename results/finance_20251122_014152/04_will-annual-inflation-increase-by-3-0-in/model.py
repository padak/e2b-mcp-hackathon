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

class EconomicDataAnalyst(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.inflation_estimate = np.random.uniform(2.96, 3.10)
        self.confidence = np.random.uniform(0.7, 0.95)
        
    def step(self):
        energy_effect = self.model.energy_price_volatility * np.random.uniform(-0.05, 0.05)
        tariff_effect = self.model.tariff_impact * np.random.uniform(0, 0.03)
        
        self.inflation_estimate += energy_effect + tariff_effect
        self.inflation_estimate = np.clip(self.inflation_estimate, 2.85, 3.20)
        
        uncertainty_factor = 1 - self.model.data_delay_uncertainty
        self.confidence *= uncertainty_factor

class CentralBankOfficial(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.inflation_forecast = 3.0
        self.policy_bias = np.random.uniform(-0.02, 0.02)
        
    def step(self):
        avg_analyst_estimate = np.mean([a.inflation_estimate for a in self.model.schedule.agents if isinstance(a, EconomicDataAnalyst)])
        
        self.inflation_forecast = 0.7 * self.inflation_forecast + 0.3 * avg_analyst_estimate
        self.inflation_forecast += self.policy_bias * self.model.monetary_policy_stance

class MarketTrader(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.belief_inflation_at_3 = np.random.uniform(0.85, 1.0)
        self.risk_tolerance = np.random.uniform(0.3, 0.9)
        
    def step(self):
        analyst_avg = np.mean([a.inflation_estimate for a in self.model.schedule.agents if isinstance(a, EconomicDataAnalyst)])
        cb_avg = np.mean([a.inflation_forecast for a in self.model.schedule.agents if isinstance(a, CentralBankOfficial)])
        
        combined_signal = 0.6 * analyst_avg + 0.4 * cb_avg
        
        if abs(combined_signal - 3.0) < 0.02:
            self.belief_inflation_at_3 += self.risk_tolerance * 0.05
        elif combined_signal > 3.02:
            self.belief_inflation_at_3 += self.risk_tolerance * 0.08
        elif combined_signal < 2.98:
            self.belief_inflation_at_3 -= self.risk_tolerance * 0.08
        else:
            self.belief_inflation_at_3 += np.random.uniform(-0.02, 0.02)
        
        self.belief_inflation_at_3 = np.clip(self.belief_inflation_at_3, 0.0, 1.0)

class EnergyMarketSpecialist(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.energy_price_trend = np.random.uniform(-0.02, 0.04)
        self.inflation_impact_estimate = 3.0
        
    def step(self):
        self.energy_price_trend += np.random.normal(0, 0.01)
        self.energy_price_trend = np.clip(self.energy_price_trend, -0.05, 0.08)
        
        energy_contribution = self.energy_price_trend * self.model.energy_price_volatility * 2.0
        self.inflation_impact_estimate = 3.0 + energy_contribution

def compute_outcome(model):
    analysts = [a for a in model.schedule.agents if isinstance(a, EconomicDataAnalyst)]
    cb_officials = [a for a in model.schedule.agents if isinstance(a, CentralBankOfficial)]
    traders = [a for a in model.schedule.agents if isinstance(a, MarketTrader)]
    energy_specialists = [a for a in model.schedule.agents if isinstance(a, EnergyMarketSpecialist)]
    
    if not analysts or not traders:
        return 0.5
    
    analyst_avg = np.mean([a.inflation_estimate for a in analysts])
    analyst_confidence = np.mean([a.confidence for a in analysts])
    
    cb_avg = np.mean([a.inflation_forecast for a in cb_officials]) if cb_officials else 3.0
    
    trader_belief = np.mean([t.belief_inflation_at_3 for t in traders])
    
    energy_avg = np.mean([e.inflation_impact_estimate for e in energy_specialists]) if energy_specialists else 3.0
    
    fundamental_estimate = 0.4 * analyst_avg + 0.25 * cb_avg + 0.2 * energy_avg + 0.15 * 3.0
    
    prob_at_or_above_3 = 0.0
    if fundamental_estimate >= 3.0:
        prob_at_or_above_3 = 0.5 + (fundamental_estimate - 3.0) * 5.0
    else:
        prob_at_or_above_3 = 0.5 - (3.0 - fundamental_estimate) * 5.0
    
    prob_at_or_above_3 = np.clip(prob_at_or_above_3, 0.0, 1.0)
    
    final_probability = 0.5 * prob_at_or_above_3 + 0.3 * trader_belief + 0.2 * analyst_confidence
    
    return np.clip(final_probability, 0.0, 1.0)

AGENT_CONFIG = {
    EconomicDataAnalyst: 15,
    CentralBankOfficial: 5,
    MarketTrader: 20,
    EnergyMarketSpecialist: 8,
}

MODEL_PARAMS = {
    "energy_price_volatility": 0.6,
    "tariff_impact": 0.5,
    "data_delay_uncertainty": 0.3,
    "monetary_policy_stance": 0.2,
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
