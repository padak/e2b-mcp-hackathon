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


class CongressMember(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.party = np.random.choice(['democrat', 'republican'], p=[0.48, 0.52])
        self.support_extension = 1.0 if self.party == 'democrat' else 0.1
        self.budget_concern = np.random.uniform(0.3, 0.9)
        self.constituent_pressure = np.random.uniform(0, 1)
        
    def step(self):
        budget_impact = self.model.deficit_concern * self.budget_concern
        affordability_pressure = self.model.affordability_crisis * self.constituent_pressure
        
        if self.party == 'democrat':
            self.support_extension = min(1.0, 0.8 + affordability_pressure * 0.3 - budget_impact * 0.1)
        else:
            self.support_extension = max(0.0, 0.1 + affordability_pressure * 0.4 - budget_impact * 0.5)
        
        if self.model.enrollment_gains > 0.7:
            self.support_extension += 0.1
        
        self.support_extension = np.clip(self.support_extension, 0, 1)


class HealthcareAdvocate(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.lobbying_strength = np.random.uniform(0.5, 1.0)
        self.public_awareness = 0.4
        
    def step(self):
        if self.model.premium_increase_threat > 0.6:
            self.public_awareness = min(1.0, self.public_awareness + 0.15)
        
        total_lobbying = 0
        for agent in self.model.schedule.agents:
            if isinstance(agent, CongressMember):
                total_lobbying += 1
        
        if total_lobbying > 0:
            impact = (self.lobbying_strength * self.public_awareness) / total_lobbying
            for agent in self.model.schedule.agents:
                if isinstance(agent, CongressMember):
                    agent.constituent_pressure = min(1.0, agent.constituent_pressure + impact * 0.3)


class BudgetHawk(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.fiscal_pressure = np.random.uniform(0.6, 1.0)
        self.influence = np.random.uniform(0.3, 0.8)
        
    def step(self):
        deficit_messaging = self.fiscal_pressure * self.model.deficit_concern
        
        for agent in self.model.schedule.agents:
            if isinstance(agent, CongressMember):
                if agent.party == 'republican':
                    agent.budget_concern = min(1.0, agent.budget_concern + deficit_messaging * self.influence * 0.15)
                else:
                    agent.budget_concern = min(1.0, agent.budget_concern + deficit_messaging * self.influence * 0.05)


class ACABeneficiary(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.subsidy_reliance = np.random.uniform(0.7, 1.0)
        self.political_engagement = np.random.uniform(0.2, 0.8)
        self.contacted_representative = False
        
    def step(self):
        threat_perception = self.model.premium_increase_threat * self.subsidy_reliance
        
        if threat_perception > 0.5 and not self.contacted_representative:
            if np.random.random() < self.political_engagement * 0.4:
                self.contacted_representative = True
                for agent in self.model.schedule.agents:
                    if isinstance(agent, CongressMember):
                        agent.constituent_pressure = min(1.0, agent.constituent_pressure + 0.02)


def compute_outcome(model):
    congress_members = [agent for agent in model.schedule.agents if isinstance(agent, CongressMember)]
    
    if len(congress_members) == 0:
        return 0.25
    
    total_support = sum(agent.support_extension for agent in congress_members)
    avg_support = total_support / len(congress_members)
    
    democrat_support = sum(agent.support_extension for agent in congress_members if agent.party == 'democrat')
    democrat_count = sum(1 for agent in congress_members if agent.party == 'democrat')
    republican_support = sum(agent.support_extension for agent in congress_members if agent.party == 'republican')
    republican_count = sum(1 for agent in congress_members if agent.party == 'republican')
    
    democrat_avg = democrat_support / democrat_count if democrat_count > 0 else 0
    republican_avg = republican_support / republican_count if republican_count > 0 else 0
    
    bipartisan_factor = min(democrat_avg, republican_avg) * 0.5
    
    advocates = [agent for agent in model.schedule.agents if isinstance(agent, HealthcareAdvocate)]
    advocacy_boost = np.mean([agent.public_awareness * agent.lobbying_strength for agent in advocates]) * 0.15 if advocates else 0
    
    beneficiaries = [agent for agent in model.schedule.agents if isinstance(agent, ACABeneficiary)]
    grassroots_pressure = sum(1 for agent in beneficiaries if agent.contacted_representative) / len(beneficiaries) * 0.1 if beneficiaries else 0
    
    outcome_score = avg_support * 0.6 + bipartisan_factor + advocacy_boost + grassroots_pressure
    
    deadline_urgency = model.time_to_deadline * 0.05
    outcome_score += deadline_urgency
    
    return np.clip(outcome_score, 0, 1)


AGENT_CONFIG = {
    CongressMember: 30,
    HealthcareAdvocate: 5,
    BudgetHawk: 3,
    ACABeneficiary: 12,
}

MODEL_PARAMS = {
    "deficit_concern": 0.75,
    "affordability_crisis": 0.8,
    "premium_increase_threat": 0.85,
    "enrollment_gains": 0.75,
    "time_to_deadline": 0.3,
}

THRESHOLD = 0.45
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
