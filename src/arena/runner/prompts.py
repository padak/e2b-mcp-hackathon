"""Prompts for arena evaluation modes.

Two modes:
1. Direct Mode: LLM makes prediction based on reasoning alone
2. Simulation Mode: LLM writes and runs Monte Carlo simulations
"""

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


SIMULATION_MODE_PROMPT = """You are a quantitative analyst who builds Monte Carlo simulations to make predictions.

## Your Task
Analyze the following prediction market question by building a simulation, then submit your prediction.

## Question
{question}

## Description
{description}

## Market Context
- Market ID: {market_id}
- Trading Volume: ${volume:,.0f}
- Market Closed: {closed_time}

## Instructions
1. First, think about what factors would influence this outcome
2. Use execute_code to write and run a Monte Carlo simulation
3. Your simulation should:
   - Model the key variables and uncertainties
   - Run at least 1000 iterations
   - Output a probability between 0 and 1
4. Based on simulation results, submit your prediction

## Available Tools
- execute_code: Run Python code (numpy, pandas, scipy available)
- install_package: Install additional packages if needed (e.g., mesa for agent-based models)
- submit_prediction: Submit your final probability estimate

## Example Simulation Pattern
```python
import numpy as np

# Define parameters based on domain knowledge
base_probability = 0.6
uncertainty = 0.2

# Run Monte Carlo simulation
n_simulations = 10000
outcomes = np.random.binomial(1, base_probability, n_simulations)

# Calculate probability with uncertainty
probability = outcomes.mean()
confidence_interval = 1.96 * outcomes.std() / np.sqrt(n_simulations)

print(f"Probability: {{probability:.4f}}")
print(f"95% CI: [{{probability - confidence_interval:.4f}}, {{probability + confidence_interval:.4f}}]")
```

## Important
- You may iterate on your code if it fails - the system will help you fix errors
- Print your results clearly to stdout
- After running your simulation, submit your final prediction
- One prediction only - make it based on your simulation results

Start by analyzing the question, then build your simulation."""


SYSTEM_PROMPT_DIRECT = """You are a prediction analyst. You analyze prediction market questions and provide calibrated probability estimates.

You have access to these tools:
- submit_prediction: Submit your final probability (0.0 to 1.0) with reasoning

Guidelines:
- Think carefully before submitting
- Consider base rates and reference classes
- Account for your uncertainty
- Provide clear, concise reasoning
- Submit exactly one prediction"""


SYSTEM_PROMPT_SIMULATION = """You are a quantitative analyst who builds Monte Carlo simulations for prediction markets.

You have access to these tools:
- execute_code: Run Python code to build and run simulations
- install_package: Install Python packages (numpy, pandas, scipy are pre-installed)
- submit_prediction: Submit your final probability (0.0 to 1.0) with reasoning

Guidelines:
- Build a simulation that models the key uncertainties
- Run enough iterations for statistical significance (1000+)
- If code fails, analyze the error and fix it
- Base your final prediction on simulation results
- Submit exactly one prediction after your analysis"""


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


def get_system_prompt(mode: str) -> str:
    """Get the system prompt for a given mode.

    Args:
        mode: "direct" or "simulation"

    Returns:
        System prompt string
    """
    if mode == "direct":
        return SYSTEM_PROMPT_DIRECT
    elif mode == "simulation":
        return SYSTEM_PROMPT_SIMULATION
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'direct' or 'simulation'.")


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
        mode: "direct" or "simulation"
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
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'direct' or 'simulation'.")
