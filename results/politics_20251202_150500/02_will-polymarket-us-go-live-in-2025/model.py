import json
import numpy as np
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
# Agent classes
class RegulatoryAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.approval_progress = np.random.uniform(0.7, 0.9)
        self.compliance_strength = np.random.uniform(0.7, 0.95)
        
    def step(self):
        if self.approval_progress < 1.0:
            progress_rate = self.model.regulatory_efficiency * 0.15
            self.approval_progress = min(1.0, self.approval_progress + progress_rate)
        
        if self.model.competitive_pressure > 0.7:
            self.approval_progress += 0.05

class PolymarketTeamAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.technical_readiness = np.random.uniform(0.75, 0.95)
        self.execution_capability = np.random.uniform(0.7, 0.9)
        
    def step(self):
        if self.technical_readiness < 1.0:
            progress = self.model.funding_strength * 0.1 * self.execution_capability
            self.technical_readiness = min(1.0, self.technical_readiness + progress)
        
        regulatory_agents = [a for a in self.model.schedule.agents if isinstance(a, RegulatoryAgent)]
        if regulatory_agents:
            avg_regulatory = np.mean([a.approval_progress for a in regulatory_agents])
            if avg_regulatory > 0.85:
                self.technical_readiness += 0.03

class CompetitorAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.market_pressure = np.random.uniform(0.6, 0.9)
        self.launch_urgency = np.random.uniform(0.5, 0.8)
        
    def step(self):
        self.market_pressure += np.random.uniform(-0.05, 0.1)
        self.market_pressure = np.clip(self.market_pressure, 0, 1)
        
        if self.market_pressure > 0.75:
            self.model.competitive_pressure = min(1.0, self.model.competitive_pressure + 0.08)

class InvestorAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.confidence = np.random.uniform(0.8, 0.95)
        self.funding_support = np.random.uniform(0.85, 1.0)
        
    def step(self):
        team_agents = [a for a in self.model.schedule.agents if isinstance(a, PolymarketTeamAgent)]
        regulatory_agents = [a for a in self.model.schedule.agents if isinstance(a, RegulatoryAgent)]
        
        if team_agents and regulatory_agents:
            avg_team_readiness = np.mean([a.technical_readiness for a in team_agents])
            avg_regulatory = np.mean([a.approval_progress for a in regulatory_agents])
            
            combined_progress = (avg_team_readiness + avg_regulatory) / 2
            
            if combined_progress > 0.8:
                self.confidence = min(1.0, self.confidence + 0.05)
                self.model.funding_strength = min(1.0, self.model.funding_strength + 0.03)

# Outcome computation
def compute_outcome(model):
    regulatory_agents = [a for a in model.schedule.agents if isinstance(a, RegulatoryAgent)]
    team_agents = [a for a in model.schedule.agents if isinstance(a, PolymarketTeamAgent)]
    investor_agents = [a for a in model.schedule.agents if isinstance(a, InvestorAgent)]
    
    if not regulatory_agents or not team_agents or not investor_agents:
        return 0.5
    
    avg_regulatory_approval = np.mean([a.approval_progress for a in regulatory_agents])
    avg_regulatory_compliance = np.mean([a.compliance_strength for a in regulatory_agents])
    
    avg_technical_readiness = np.mean([a.technical_readiness for a in team_agents])
    avg_execution = np.mean([a.execution_capability for a in team_agents])
    
    avg_investor_confidence = np.mean([a.confidence for a in investor_agents])
    avg_funding_support = np.mean([a.funding_support for a in investor_agents])
    
    regulatory_score = (avg_regulatory_approval * 0.7 + avg_regulatory_compliance * 0.3)
    technical_score = (avg_technical_readiness * 0.6 + avg_execution * 0.4)
    financial_score = (avg_investor_confidence * 0.5 + avg_funding_support * 0.5)
    
    launch_probability = (
        regulatory_score * 0.40 +
        technical_score * 0.35 +
        financial_score * 0.15 +
        model.competitive_pressure * 0.10
    )
    
    return launch_probability

# Configuration
AGENT_CONFIG = {
    RegulatoryAgent: 3,
    PolymarketTeamAgent: 8,
    CompetitorAgent: 5,
    InvestorAgent: 4,
}

MODEL_PARAMS = {
    "regulatory_efficiency": 0.85,
    "funding_strength": 0.90,
    "competitive_pressure": 0.75,
}

THRESHOLD = 0.88
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
