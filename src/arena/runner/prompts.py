"""Prompts for arena evaluation modes.

Three modes:
1. Direct Mode: LLM makes prediction based on reasoning alone (no code)
2. Simulation Mode: LLM builds Mesa agent-based simulations with calibration + Monte Carlo
3. Reasoning Mode: LLM uses Python freely (numpy, scipy, etc.) to compute predictions
"""

# ==============================================================================
# DIRECT MODE PROMPTS
# ==============================================================================

DIRECT_MODE_PROMPT = """You are a prediction analyst evaluating a prediction market question.

## Your Task
Analyze the following prediction market question and submit your probability estimate.

## Question
{question}

## Description
{description}

## Market Context
- Market ID: {market_id}
- Trading Volume: ${volume:,.0f}
- Market Closed: {closed_time}

## Instructions
1. Reason carefully about the question
2. Consider multiple perspectives and scenarios
3. Estimate the probability that the answer is "Yes"
4. Submit your prediction using the submit_prediction tool

## Important
- Your prediction must be between 0.0 (definitely No) and 1.0 (definitely Yes)
- Be calibrated: 0.5 means you're completely uncertain
- Provide clear reasoning for your prediction
- You have ONE chance to submit - make it count

Think step by step, then submit your prediction."""


SYSTEM_PROMPT_DIRECT = """You are a prediction analyst. You analyze prediction market questions and provide calibrated probability estimates.

You have access to these tools:
- submit_prediction: Submit your final probability (0.0 to 1.0) with reasoning

Guidelines:
- Think carefully before submitting
- Consider base rates and reference classes
- Account for your uncertainty
- Provide clear, concise reasoning
- Submit exactly one prediction"""


# ==============================================================================
# REASONING MODE PROMPTS (Free Python computation)
# ==============================================================================

REASONING_MODE_PROMPT = """You are a quantitative analyst using Python to predict outcomes.

## Your Task
Use Python code to analyze this prediction market question and compute a probability estimate.

## Question
{question}

## Description
{description}

## Market Context
- Market ID: {market_id}
- Trading Volume: ${volume:,.0f}
- Market Closed: {closed_time}

## Environment
- You have access to Python with numpy, scipy, pandas, and other scientific libraries
- NO internet access - you cannot fetch external data
- You must work with your knowledge and computational reasoning only

## Approach Options
Choose the approach that best fits the question:

1. **Monte Carlo Simulation**: Model uncertainty with random sampling
   ```python
   import numpy as np
   n_simulations = 10000
   outcomes = np.random.binomial(1, base_probability, n_simulations)
   probability = outcomes.mean()
   ```

2. **Bayesian Estimation**: Use prior knowledge and update beliefs
   ```python
   from scipy import stats
   prior = stats.beta(a, b)  # Prior belief
   # Update based on reasoning
   posterior_mean = prior.mean()
   ```

3. **Statistical Modeling**: Build a simple model of the scenario
   ```python
   # Model factors that influence the outcome
   factor1_effect = 0.6
   factor2_effect = 0.3
   probability = factor1_effect * weight1 + factor2_effect * weight2
   ```

4. **Decision Tree / Scenario Analysis**: Enumerate possible outcomes
   ```python
   scenarios = [
       (0.4, 0.8),  # (scenario_prob, outcome_if_scenario)
       (0.6, 0.3),
   ]
   probability = sum(p * o for p, o in scenarios)
   ```

## Process
1. Analyze the question - what factors determine the outcome?
2. Choose an appropriate computational approach
3. Write and execute Python code to compute your estimate
4. Review the output and refine if needed
5. Submit your final prediction with reasoning

## Tools Available
- **execute_code**: Run Python code (numpy, scipy, pandas available)
- **install_package**: Install additional packages if needed
- **submit_prediction**: Submit your final probability (0.0 to 1.0)

## Important
- Your code should print the computed probability
- Consider uncertainty - don't be overconfident
- You can run multiple code iterations to refine your estimate
- Submit exactly ONE final prediction

Start by analyzing the question, then write code to compute your probability estimate."""


SYSTEM_PROMPT_REASONING = """You are a quantitative analyst who uses Python to make predictions.

You have access to these tools:
- execute_code: Run Python code (numpy, scipy, pandas, etc. available)
- install_package: Install packages if needed
- submit_prediction: Submit your final probability (0.0 to 1.0) with reasoning

Environment constraints:
- NO internet access - cannot fetch external data
- Must rely on computational reasoning and your knowledge

Guidelines:
- Use appropriate statistical/computational methods for the question
- Consider Monte Carlo, Bayesian methods, or scenario analysis
- Print intermediate results to understand your computation
- Be calibrated - account for uncertainty
- Submit exactly one prediction based on your analysis"""


# ==============================================================================
# SIMULATION MODE PROMPTS (MESA Agent-Based Modeling)
# ==============================================================================

# Fixed Mesa 2.x template - LLM fills in agent_code section
MESA_MODEL_TEMPLATE = '''import json
import numpy as np
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

def run_calibration(n_runs: int = 50):
    """Run calibration to determine threshold."""
    outcomes = []
    for seed in range(n_runs):
        model = SimulationModel(seed=seed)
        for _ in range(100):
            model.step()
        results = model.get_results()
        outcomes.append(results["final_outcome"])

    # Clamp threshold to [0.05, 0.95] to avoid degenerate predictions
    # (threshold=1.0 means 0% always, threshold=0.0 means 100% always)
    raw_threshold = np.median(outcomes)
    threshold = np.clip(raw_threshold, 0.05, 0.95)

    return {{
        "outcomes": outcomes,
        "mean": np.mean(outcomes),
        "std": np.std(outcomes),
        "min": np.min(outcomes),
        "max": np.max(outcomes),
        "threshold": threshold
    }}

def run_monte_carlo(n_runs: int = 200, threshold: float = 0.5):
    """Run Monte Carlo simulation with given threshold."""
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
        "ci_95": ci_95,
        "threshold": threshold
    }}

if __name__ == "__main__":
    # Phase 1: Calibration
    cal = run_calibration(n_runs=50)
    print(f"CALIBRATION: mean={{cal['mean']:.4f}}, std={{cal['std']:.4f}}, threshold={{cal['threshold']:.4f}}")

    # Check for low variance
    if cal['std'] < 0.001:
        print("ERROR: Low variance detected - model produces constant outputs")
        print(json.dumps({{"error": "low_variance", "calibration": cal}}))
    else:
        # Phase 2: Monte Carlo
        mc = run_monte_carlo(n_runs=200, threshold=cal['threshold'])
        print(f"MONTE_CARLO: probability={{mc['probability']:.4f}}, ci_95={{mc['ci_95']:.4f}}")
        print(json.dumps({{"calibration": cal, "monte_carlo": mc}}))
'''


SIMULATION_MODE_PROMPT = """You are an expert Mesa agent-based modeling scientist who builds simulations to predict outcomes.

## Your Task
Build a Mesa 2.x agent-based simulation to model this prediction market, then submit your prediction.

## Question
{question}

## Description
{description}

## Market Context
- Market ID: {market_id}
- Trading Volume: ${volume:,.0f}
- Market Closed: {closed_time}

## CRITICAL: Mesa 2.x Syntax (NOT Mesa 3.x!)

⚠️ WARNING: We use Mesa 2.1.5, NOT Mesa 3.x! The syntax is DIFFERENT.

### Agent Pattern - MUST follow exactly:
```python
class MyAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)  # Mesa 2.x: MUST pass BOTH unique_id AND model
        # Initialize agent attributes with randomness
        self.belief = np.random.uniform(0, 1)
        self.influence = np.random.uniform(0.1, 0.5)

    def step(self):
        # Agent behavior - access model via self.model
        self.belief += np.random.normal(0, 0.05)
        self.belief = np.clip(self.belief, 0, 1)
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

Use generate_mesa_model to submit your agent code. You must provide EXACTLY this structure:

```python
# Agent classes (2-4 types)
class PolicyMaker(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.hawkish = np.random.uniform(0, 1)

    def step(self):
        # Update behavior based on model state
        pass

class MarketParticipant(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        self.expectation = np.random.uniform(0.3, 0.7)

    def step(self):
        pass

# Outcome computation - MUST use agent states for variance
def compute_outcome(model):
    agents = model.schedule.agents
    # Aggregate agent states to compute outcome (0-1)
    avg_expectation = np.mean([a.expectation for a in agents if hasattr(a, 'expectation')])
    return np.clip(avg_expectation + np.random.uniform(-0.05, 0.05), 0, 1)

# Configuration
AGENT_CONFIG = {{
    PolicyMaker: 5,
    MarketParticipant: 20,
}}

MODEL_PARAMS = {{
    "base_rate": 0.5,
    "volatility": 0.1,
}}

THRESHOLD = 0.5  # Outcome > threshold means "Yes"
```

## Available Tools
1. **generate_mesa_model**: Submit your agent code (agents, compute_outcome, AGENT_CONFIG, MODEL_PARAMS, THRESHOLD)
   - The system will run calibration (50 runs) and Monte Carlo (200 runs)
   - If there's an error, fix and resubmit
   - If variance is too low, add more randomness to agents

2. **submit_prediction**: After seeing simulation results, submit your final probability

## Process
1. Analyze the question - who are the key actors?
2. Design 2-4 agent types that model the scenario
3. Call generate_mesa_model with your code
4. Review calibration/Monte Carlo results
5. Fix any errors (Mesa syntax, low variance, etc.)
6. Submit your prediction based on simulation results

## Important
- Each agent's __init__ MUST initialize random attributes
- compute_outcome MUST aggregate agent states (not use constants)
- Variance check: if std < 0.001, add more randomness
- You may iterate if the code fails - analyze errors carefully
- Submit exactly ONE prediction after successful simulation

Start by analyzing the question, then build your Mesa model."""


SYSTEM_PROMPT_SIMULATION = """You are an expert Mesa agent-based modeling scientist for prediction markets.

You have access to these tools:
- generate_mesa_model: Submit Mesa agent code (agents, compute_outcome, config)
- install_package: Install packages if needed (mesa is pre-installed)
- submit_prediction: Submit your final probability (0.0 to 1.0) with reasoning

## CRITICAL Mesa 2.x Requirements:
Every Agent subclass MUST call super().__init__(unique_id, model):
```python
class MyAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)  # Mesa 2.x: BOTH args required
```

Guidelines:
- Build Mesa agent-based simulations (not simple numpy Monte Carlo)
- Design 2-4 agent types representing key actors
- compute_outcome MUST use agent states for variance
- If code fails, analyze the error (often Mesa syntax)
- If variance too low (std < 0.001), add randomness to agents
- Submit prediction based on Monte Carlo probability"""


# ==============================================================================
# SELF-HEALING PROMPTS
# ==============================================================================

FIXER_SYSTEM_PROMPT = """You are a Python code debugger specializing in Mesa 2.1.5 agent-based simulations.

Your task is to fix Python code that failed to execute. You will receive:
1. The original code
2. The error message

## CRITICAL Mesa 2.x Requirements:

⚠️ We use Mesa 2.1.5, NOT Mesa 3.x! The syntax is DIFFERENT.

Every Agent subclass MUST call super().__init__(unique_id, model):
```python
class MyAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)  # Mesa 2.x: MUST pass BOTH unique_id AND model
        # your attributes here
```

### WRONG (Mesa 3.x - DO NOT USE):
```python
super().__init__(model)  # ❌ WRONG - missing unique_id
```

### CORRECT (Mesa 2.x):
```python
super().__init__(unique_id, model)  # ✅ CORRECT
```

Common errors:
- "TypeError: __init__() takes 2 positional arguments but 3 were given" -> Use super().__init__(unique_id, model)
- ModuleNotFoundError -> Ensure all imports are present
- AttributeError -> Check attribute names match between classes

Rules:
- Return ONLY the fixed agent code section, no explanations
- Do not include the template boilerplate (SimulationModel, run_monte_carlo, etc.)
- Preserve the original structure and logic as much as possible
- Fix only the specific error, don't refactor unnecessarily"""


VARIANCE_FIXER_PROMPT = """You are an expert at fixing agent-based models that produce degenerate outputs.

The model's compute_outcome function produces constant values with no variance across different random seeds.
This makes the Monte Carlo simulation useless.

## Problem Analysis
Calibration results show:
- min={min}, max={max}, mean={mean}, std={std}

This typically happens when:
1. Agent __init__ doesn't initialize random attributes
2. compute_outcome uses fixed MODEL_PARAMS instead of agent states
3. Coefficients or clamping eliminates variance
4. Agent step() doesn't update state meaningfully

## Your Task - CRITICAL

The outcome MUST vary based on random seed. Each seed creates different agent initial values via np.random.uniform().
Your compute_outcome function MUST use these agent values, not fixed constants.

### DO THIS:
```python
class MyAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(unique_id, model)
        # RANDOM initialization creates variance
        self.belief = np.random.uniform(0.2, 0.8)
        self.confidence = np.random.uniform(0.1, 0.5)

def compute_outcome(model):
    agents = model.schedule.agents
    # USE actual agent state values that were randomly initialized
    avg_belief = np.mean([a.belief for a in agents])
    avg_confidence = np.mean([a.confidence for a in agents])
    # Add small noise for extra variance
    outcome = avg_belief * avg_confidence + np.random.uniform(-0.05, 0.05)
    return np.clip(outcome, 0, 1)
```

### DO NOT DO THIS:
```python
def compute_outcome(model):
    # BAD: Using fixed model params or constants
    outcome = model.base_rate * 0.8 + 0.1  # This is constant!
    return outcome
```

## Specific Fixes Required:
1. Ensure all agents initialize attributes with np.random.uniform()
2. compute_outcome MUST aggregate agent states: np.mean([a.attr for a in agents])
3. Add small random noise: np.random.uniform(-0.05, 0.05)
4. Keep coefficients moderate (0.1-0.5) to avoid saturation at 0 or 1

Rules:
- Return ONLY the fixed agent code section
- Do not include SimulationModel or run_monte_carlo
- Keep all agent classes and their basic logic
- Focus on making compute_outcome use agent states"""


def format_direct_prompt(
    question: str,
    description: str,
    market_id: str,
    volume: float,
    closed_time: str,
) -> str:
    """Format the direct mode user prompt.

    Args:
        question: The prediction market question
        description: Detailed description of resolution criteria
        market_id: Market identifier
        volume: Trading volume in USD
        closed_time: When the market closed

    Returns:
        Formatted prompt string
    """
    return DIRECT_MODE_PROMPT.format(
        question=question,
        description=description or "No additional description provided.",
        market_id=market_id,
        volume=volume,
        closed_time=closed_time or "Unknown",
    )


def format_simulation_prompt(
    question: str,
    description: str,
    market_id: str,
    volume: float,
    closed_time: str,
) -> str:
    """Format the simulation mode user prompt.

    Args:
        question: The prediction market question
        description: Detailed description of resolution criteria
        market_id: Market identifier
        volume: Trading volume in USD
        closed_time: When the market closed

    Returns:
        Formatted prompt string
    """
    return SIMULATION_MODE_PROMPT.format(
        question=question,
        description=description or "No additional description provided.",
        market_id=market_id,
        volume=volume,
        closed_time=closed_time or "Unknown",
    )


def format_reasoning_prompt(
    question: str,
    description: str,
    market_id: str,
    volume: float,
    closed_time: str,
) -> str:
    """Format the reasoning mode user prompt.

    Args:
        question: The prediction market question
        description: Detailed description of resolution criteria
        market_id: Market identifier
        volume: Trading volume in USD
        closed_time: When the market closed

    Returns:
        Formatted prompt string
    """
    return REASONING_MODE_PROMPT.format(
        question=question,
        description=description or "No additional description provided.",
        market_id=market_id,
        volume=volume,
        closed_time=closed_time or "Unknown",
    )


def get_system_prompt(mode: str) -> str:
    """Get the system prompt for a given mode.

    Args:
        mode: "direct", "simulation", or "reasoning"

    Returns:
        System prompt string
    """
    if mode == "direct":
        return SYSTEM_PROMPT_DIRECT
    elif mode == "simulation":
        return SYSTEM_PROMPT_SIMULATION
    elif mode == "reasoning":
        return SYSTEM_PROMPT_REASONING
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'direct', 'simulation', or 'reasoning'.")


def get_user_prompt(
    mode: str,
    question: str,
    description: str,
    market_id: str,
    volume: float,
    closed_time: str,
) -> str:
    """Get the user prompt for a given mode and question.

    Args:
        mode: "direct", "simulation", or "reasoning"
        question: The prediction market question
        description: Detailed description
        market_id: Market identifier
        volume: Trading volume
        closed_time: When market closed

    Returns:
        Formatted user prompt
    """
    if mode == "direct":
        return format_direct_prompt(question, description, market_id, volume, closed_time)
    elif mode == "simulation":
        return format_simulation_prompt(question, description, market_id, volume, closed_time)
    elif mode == "reasoning":
        return format_reasoning_prompt(question, description, market_id, volume, closed_time)
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'direct', 'simulation', or 'reasoning'.")


# ==============================================================================
# MESA MODEL HELPERS
# ==============================================================================


def assemble_mesa_code(agent_code: str) -> str:
    """Combine LLM-generated agent code with the fixed Mesa template.

    Args:
        agent_code: The agent classes, compute_outcome, AGENT_CONFIG, MODEL_PARAMS, THRESHOLD

    Returns:
        Complete executable Python code
    """
    return MESA_MODEL_TEMPLATE.format(agent_code=agent_code)


def format_fixer_prompt(code: str, error: str) -> str:
    """Format the error fixer user prompt.

    Args:
        code: The broken agent code
        error: The error message

    Returns:
        Formatted prompt for the fixer
    """
    return f"""Fix this Mesa agent code that produced an error.

## Original Agent Code:
```python
{code}
```

## Error:
```
{error}
```

Return ONLY the fixed agent code (classes, compute_outcome, AGENT_CONFIG, MODEL_PARAMS, THRESHOLD).
Do not include SimulationModel, run_monte_carlo, or any boilerplate."""


def format_variance_fixer_prompt(code: str, calibration: dict) -> str:
    """Format the variance fixer user prompt.

    Args:
        code: The agent code with low variance
        calibration: Calibration results with min, max, mean, std

    Returns:
        Formatted prompt for the variance fixer
    """
    return f"""Fix this Mesa agent code that produces constant outputs with no variance.

## Agent Code:
```python
{code}
```

## Calibration Results (showing low variance):
- min: {calibration.get('min', 0):.4f}
- max: {calibration.get('max', 0):.4f}
- mean: {calibration.get('mean', 0):.4f}
- std: {calibration.get('std', 0):.6f}

The std is too low ({calibration.get('std', 0):.6f} < 0.001). This means the model outputs the same value regardless of random seed.

Return ONLY the fixed agent code with proper variance from agent states.
Do not include SimulationModel, run_monte_carlo, or any boilerplate."""


def get_variance_fixer_system_prompt(calibration: dict) -> str:
    """Get the variance fixer system prompt with calibration data.

    Args:
        calibration: Dict with min, max, mean, std

    Returns:
        Formatted system prompt
    """
    return VARIANCE_FIXER_PROMPT.format(
        min=calibration.get('min', 0),
        max=calibration.get('max', 0),
        mean=calibration.get('mean', 0),
        std=calibration.get('std', 0),
    )
