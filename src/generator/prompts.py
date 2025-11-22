"""
Prompts for LLM model generation with template-based approach.
"""

# Fixed template - LLM only fills in the marked sections
MODEL_TEMPLATE = '''import random
import json
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

# ============== LLM GENERATED CODE START ==============
{agent_code}
# ============== LLM GENERATED CODE END ==============

class SimulationModel(Model):
    def __init__(self, seed=None):
        super().__init__()

        if seed is not None:
            random.seed(seed)

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
            model_reporters={{"Outcome": compute_outcome}}
        )

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

    def get_results(self):
        data = self.datacollector.get_model_vars_dataframe()
        return {{
            "final_outcome": data["Outcome"].iloc[-1] if len(data) > 0 else 0,
            "history": data["Outcome"].tolist()
        }}

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

    return {{
        "probability": probability,
        "n_runs": n_runs,
        "results": results,
        "ci_95": ci_95
    }}

if __name__ == "__main__":
    results = run_monte_carlo(n_runs=200, threshold=THRESHOLD)
    print(json.dumps(results))
'''

SYSTEM_PROMPT = """You are an expert agent-based modeling scientist. Generate ONLY the agent classes and configuration for a Mesa 2.1.5 simulation.

## CRITICAL: Mesa 2.x Syntax (NOT Mesa 3.x!)

⚠️ WARNING: We use Mesa 2.1.5, NOT Mesa 3.x! The syntax is DIFFERENT.

### Required imports (already provided):
```python
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import numpy as np
```

### Agent Pattern - MUST follow exactly:
```python
class MyAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)  # Mesa 2.x: MUST pass BOTH unique_id AND model
        # your attributes here
        self.some_value = np.random.uniform(0, 1)

    def step(self):
        # agent behavior - access model via self.model
        self.some_value += self.model.some_param * 0.1
```

### WRONG (Mesa 3.x - DO NOT USE):
```python
super().__init__(model)  # ❌ WRONG - missing unique_id
```

### CORRECT (Mesa 2.x):
```python
super().__init__(unique_id, model)  # ✅ CORRECT
```

## Your Output Format

You must return EXACTLY this structure (no markdown, no explanations):

```
# Agent classes
class Agent1(Agent):
    ...

class Agent2(Agent):
    ...

# Outcome computation
def compute_outcome(model):
    # Return float 0-1 representing probability of "Yes" outcome
    ...

# Configuration
AGENT_CONFIG = {
    Agent1: 10,
    Agent2: 5,
}

MODEL_PARAMS = {
    "param1": 0.5,
    "param2": 0.8,
}

THRESHOLD = 0.5  # Outcome > threshold means "Yes"
```

## Rules
- Create 2-4 agent types representing key actors
- Each agent must have __init__ and step methods
- compute_outcome returns 0-1 (higher = more likely "Yes")
- Keep it simple - max 50 agents total
- Access model state via self.model.param_name
"""

USER_PROMPT_TEMPLATE = """## Prediction Market Question
{question}

## Current Market Odds
- Yes: {yes_odds:.0%}
- No: {no_odds:.0%}

## Research Data
{research}

## Your Task
Generate agent classes that model this scenario. Consider:
1. Who are the key actors? (2-4 agent types)
2. What behaviors influence the outcome?
3. How to compute whether "Yes" wins?

Return ONLY the code (agents, compute_outcome, AGENT_CONFIG, MODEL_PARAMS, THRESHOLD).
No explanations, no markdown blocks.
"""


def create_generation_prompt(question: str, yes_odds: float, research: str) -> str:
    """Create the user prompt for model generation."""
    return USER_PROMPT_TEMPLATE.format(
        question=question,
        yes_odds=yes_odds,
        no_odds=1 - yes_odds,
        research=research
    )


def assemble_code(agent_code: str) -> str:
    """Combine LLM-generated agent code with the fixed template."""
    return MODEL_TEMPLATE.format(agent_code=agent_code)
