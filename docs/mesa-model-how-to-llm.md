# Mesa 3.x Model Generation Guide for LLM

## Mesa 3.x API (CRITICAL)

### Agent Creation
```python
from mesa import Agent, Model
from mesa.datacollection import DataCollector

class MyAgent(Agent):
    def __init__(self, unique_id: int, model: "MyModel"):
        super().__init__(model)  # Mesa 3.x: only model, no unique_id
        self.unique_id = unique_id  # store it yourself
        # your attributes here

    def step(self):
        # agent behavior
        pass
```

### Model Creation
```python
class MyModel(Model):
    def __init__(self, param1, param2, seed=None):
        super().__init__()

        if seed is not None:
            random.seed(seed)

        # Store parameters
        self.param1 = param1

        # Create agents (auto-registered in Mesa 3.x)
        for i in range(num_agents):
            MyAgent(i, self)

        # Data collection
        self.datacollector = DataCollector(
            model_reporters={"Metric": compute_metric}
        )

    def step(self):
        # Run all agents randomly
        self.agents.shuffle_do("step")
        self.datacollector.collect(self)
```

## Common Mistakes to Avoid

1. **DO NOT use RandomActivation** - removed in Mesa 3.x
   ```python
   # WRONG
   from mesa.time import RandomActivation
   self.schedule = RandomActivation(self)

   # CORRECT
   self.agents.shuffle_do("step")
   ```

2. **DO NOT pass unique_id to super().__init__**
   ```python
   # WRONG (Mesa 2.x style)
   super().__init__(unique_id, model)

   # CORRECT (Mesa 3.x)
   super().__init__(model)
   ```

3. **DO NOT use self.schedule.add()** - agents auto-register
   ```python
   # WRONG
   agent = MyAgent(i, self)
   self.schedule.add(agent)

   # CORRECT
   MyAgent(i, self)  # automatically added to self.agents
   ```

4. **Collect data AFTER agents step, not before**

## Monte Carlo Pattern

```python
def run_trial(self, threshold: float = 0.5) -> bool:
    """Single trial returning binary outcome."""
    for _ in range(100):
        self.step()
    results = self.get_results()
    return results["metric"] > threshold

def run_monte_carlo(params, n_runs=200, threshold=0.5):
    results = []
    for seed in range(n_runs):
        model = MyModel(**params, seed=seed)
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
```

## Required Output Structure

Model must return dict with:
```python
{
    "probability": float,  # 0-1
    "n_runs": int,
    "results": list[int],  # binary outcomes [0,1,1,0,...]
    "ci_95": float  # 95% confidence interval
}
```

## Agent Design Patterns

### Economic Agents
- **Investors**: wealth, risk_tolerance, invested amount
- **Consumers**: income, savings, spending_propensity
- **Firms**: production_capacity, inventory, employees

### Behavior Pattern
```python
def step(self):
    # 1. Calculate effects from model parameters
    effect = self.calculate_effect(self.model.param)

    # 2. Probabilistic decision
    if random.random() < effect:
        self.do_action()

    # 3. Update model aggregates
    self.model.total_metric += value
```

## Health/Outcome Calculation

```python
def compute_health(model):
    if len(model.agents) == 0:
        return 0

    # Normalize metrics to 0-1 range
    score1 = min(model.metric1 / expected_max, 1)
    score2 = min(model.metric2 / expected_max, 1)

    # Weighted combination
    health = 0.5 * score1 + 0.5 * score2
    return min(max(health, 0), 1)
```

## Parameter Normalization

Input parameters should be normalized for agent decisions:
```python
# Interest rate 0-20% -> 0-1 effect (inverse)
rate_effect = 1 - (self.model.interest_rate / 20)

# Sentiment -1 to 1 -> 0-1 effect
sentiment_effect = (self.model.sentiment + 1) / 2

# Inflation 0-20% -> 0-1 effect (inverse for spending)
inflation_effect = 1 - (self.model.inflation / 20)
```

## Execution Environment

- Python 3.12+ in E2B sandbox
- Mesa 3.3.1
- Dependencies: mesa, numpy, pandas, plotly
- Timeout: 60 seconds for model run
- Max agents: ~100 (for performance)
- Steps per trial: ~100

## Template Structure

```python
import random
from mesa import Agent, Model
from mesa.datacollection import DataCollector

# Agent classes here

def compute_outcome(model):
    # outcome calculation
    pass

class SimulationModel(Model):
    def __init__(self, **params, seed=None):
        # initialization
        pass

    def step(self):
        # step logic
        pass

    def get_results(self):
        # return results dict
        pass

    def run_trial(self, threshold=0.5):
        # single trial
        pass

def run_monte_carlo(**params, n_runs=200):
    # monte carlo wrapper
    pass

if __name__ == "__main__":
    results = run_monte_carlo(**params)
    print(f"Probability: {results['probability']:.1%}")
    print(f"CI: ±{results['ci_95']:.1%}")
```
