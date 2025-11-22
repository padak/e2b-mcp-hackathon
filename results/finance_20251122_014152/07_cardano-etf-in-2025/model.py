import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class SECRegulator(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.approval_stance = np.random.uniform(0.3, 0.7)
        self.delay_tendency = np.random.uniform(0.2, 0.6)
        
    def step(self):
        institutional_pressure = np.mean([a.demand_level for a in self.model.schedule.agents if isinstance(a, InstitutionalInvestor)])
        precedent_effect = self.model.btc_eth_etf_success
        
        self.approval_stance += institutional_pressure * 0.03
        self.approval_stance += precedent_effect * 0.02
        self.approval_stance -= self.model.regulatory_uncertainty * 0.04
        self.approval_stance = np.clip(self.approval_stance, 0, 1)
        
        if np.random.random() < self.model.regulatory_uncertainty:
            self.delay_tendency += 0.05
        else:
            self.delay_tendency -= 0.02
        self.delay_tendency = np.clip(self.delay_tendency, 0, 1)


class InstitutionalInvestor(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.demand_level = np.random.uniform(0.5, 0.9)
        self.accumulation = np.random.uniform(0.3, 0.7)
        
    def step(self):
        sec_confidence = np.mean([a.approval_stance for a in self.model.schedule.agents if isinstance(a, SECRegulator)])
        foundation_progress = np.mean([a.development_progress for a in self.model.schedule.agents if isinstance(a, CardanoFoundation)])
        
        if sec_confidence > 0.5 and foundation_progress > 0.6:
            self.demand_level += 0.04
            self.accumulation += 0.03
        else:
            self.demand_level -= 0.01
            
        self.demand_level = np.clip(self.demand_level, 0, 1)
        self.accumulation = np.clip(self.accumulation, 0, 1)


class CardanoFoundation(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.development_progress = np.random.uniform(0.6, 0.8)
        self.issuer_partnerships = np.random.uniform(0.4, 0.7)
        
    def step(self):
        institutional_demand = np.mean([a.demand_level for a in self.model.schedule.agents if isinstance(a, InstitutionalInvestor)])
        
        self.development_progress += 0.03
        self.development_progress += institutional_demand * 0.02
        self.issuer_partnerships += 0.025
        
        if self.model.regulatory_uncertainty > 0.6:
            self.development_progress -= 0.02
            
        self.development_progress = np.clip(self.development_progress, 0, 1)
        self.issuer_partnerships = np.clip(self.issuer_partnerships, 0, 1)


class FundIssuer(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.filing_readiness = np.random.uniform(0.4, 0.7)
        self.competitive_urgency = np.random.uniform(0.5, 0.8)
        
    def step(self):
        foundation_progress = np.mean([a.development_progress for a in self.model.schedule.agents if isinstance(a, CardanoFoundation)])
        sec_approval = np.mean([a.approval_stance for a in self.model.schedule.agents if isinstance(a, SECRegulator)])
        
        self.filing_readiness += foundation_progress * 0.03
        self.filing_readiness += sec_approval * 0.02
        
        self.competitive_urgency += self.model.btc_eth_etf_success * 0.03
        
        if sec_approval > 0.6:
            self.filing_readiness += 0.04
            
        self.filing_readiness = np.clip(self.filing_readiness, 0, 1)
        self.competitive_urgency = np.clip(self.competitive_urgency, 0, 1)


# Outcome computation
def compute_outcome(model):
    sec_agents = [a for a in model.schedule.agents if isinstance(a, SECRegulator)]
    institutional_agents = [a for a in model.schedule.agents if isinstance(a, InstitutionalInvestor)]
    foundation_agents = [a for a in model.schedule.agents if isinstance(a, CardanoFoundation)]
    issuer_agents = [a for a in model.schedule.agents if isinstance(a, FundIssuer)]
    
    if not sec_agents or not institutional_agents or not foundation_agents or not issuer_agents:
        return 0.16
    
    sec_approval = np.mean([a.approval_stance for a in sec_agents])
    sec_delay = np.mean([a.delay_tendency for a in sec_agents])
    
    institutional_demand = np.mean([a.demand_level for a in institutional_agents])
    accumulation = np.mean([a.accumulation for a in institutional_agents])
    
    foundation_progress = np.mean([a.development_progress for a in foundation_agents])
    partnerships = np.mean([a.issuer_partnerships for a in foundation_agents])
    
    issuer_readiness = np.mean([a.filing_readiness for a in issuer_agents])
    urgency = np.mean([a.competitive_urgency for a in issuer_agents])
    
    approval_probability = (
        sec_approval * 0.35 +
        (1 - sec_delay) * 0.15 +
        institutional_demand * 0.15 +
        foundation_progress * 0.15 +
        issuer_readiness * 0.10 +
        model.btc_eth_etf_success * 0.10
    )
    
    approval_probability -= model.regulatory_uncertainty * 0.2
    approval_probability += accumulation * 0.05
    approval_probability += urgency * 0.05
    
    return np.clip(approval_probability, 0, 1)


# Configuration
AGENT_CONFIG = {
    SECRegulator: 3,
    InstitutionalInvestor: 15,
    CardanoFoundation: 2,
    FundIssuer: 5,
}

MODEL_PARAMS = {
    "btc_eth_etf_success": 0.75,
    "regulatory_uncertainty": 0.45,
}

THRESHOLD = 0.42
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
