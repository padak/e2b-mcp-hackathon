"""
LLM-based code fixer for failed simulations.
"""

import os
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL")
if not DEFAULT_MODEL:
    raise ValueError("ANTHROPIC_MODEL environment variable is required")

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
- "TypeError: __init__() takes 2 positional arguments but 3 were given" -> You used Mesa 3.x syntax, change to super().__init__(unique_id, model)
- ModuleNotFoundError -> Keep all imports, don't remove them

Rules:
- Return ONLY the fixed Python code, no explanations
- Do not wrap in markdown code blocks
- Preserve the original structure and logic as much as possible
- Fix only the specific error, don't refactor unnecessarily
- Make sure all imports are included (mesa, numpy, etc.)
- Use Mesa 2.x API with RandomActivation scheduler
"""


async def fix_code(code: str, error: str, model: str = None) -> str:
    """
    Fix broken Python code using Claude.

    Args:
        code: The broken Python code
        error: The error message
        model: Claude model to use

    Returns:
        Fixed Python code
    """
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    user_prompt = f"""Fix this Python code that produced an error.

## Original Code:
```python
{code}
```

## Error:
```
{error}
```

Return the fixed code:"""

    response = await client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=4096,
        system=FIXER_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    fixed_code = response.content[0].text

    # Clean up markdown if present
    if fixed_code.startswith("```python"):
        fixed_code = fixed_code[9:]
    elif fixed_code.startswith("```"):
        fixed_code = fixed_code[3:]
    if fixed_code.endswith("```"):
        fixed_code = fixed_code[:-3]

    return fixed_code.strip()


def fix_code_sync(code: str, error: str, model: str = None) -> str:
    """
    Synchronous version of fix_code.
    """
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    user_prompt = f"""Fix this Python code that produced an error.

## Original Code:
```python
{code}
```

## Error:
```
{error}
```

Return the fixed code:"""

    response = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=4096,
        system=FIXER_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    fixed_code = response.content[0].text

    # Clean up markdown
    if fixed_code.startswith("```python"):
        fixed_code = fixed_code[9:]
    elif fixed_code.startswith("```"):
        fixed_code = fixed_code[3:]
    if fixed_code.endswith("```"):
        fixed_code = fixed_code[:-3]

    return fixed_code.strip()


VARIANCE_FIXER_PROMPT = """You are an expert at fixing agent-based models that produce degenerate outputs.

The model's compute_outcome function produces constant values with no variance across different random seeds.
This makes the Monte Carlo simulation useless.

## Problem Analysis
Calibration results show:
- min={min}, max={max}, mean={mean}, std={std}

This typically happens when:
1. Multipliers push values above 1.0 before clamping
2. Agent behaviors don't create enough variation
3. The outcome formula uses fixed MODEL_PARAMS instead of actual agent states
4. Coefficients dominate over agent-derived values

## Your Task - CRITICAL

The outcome MUST vary based on random seed. Each seed creates different agent initial values via np.random.uniform().
Your compute_outcome function MUST use these agent values, not fixed constants.

### DO THIS:
```python
def compute_outcome(model):
    agents = [a for a in model.schedule.agents if isinstance(a, SomeAgent)]
    # USE actual agent state values that were randomly initialized
    avg_value = np.mean([a.some_attribute for a in agents])
    # Combine multiple agent attributes for variance
    outcome = avg_value * 0.5 + other_agent_value * 0.3 + np.random.uniform(-0.05, 0.05)
    return np.clip(outcome, 0, 1)
```

### DO NOT DO THIS:
```python
def compute_outcome(model):
    # BAD: Using fixed model params or constants
    outcome = model.some_param * 0.8 + 0.1  # This is constant!
    return outcome
```

## Specific Fixes Required:
1. Replace any fixed constants with agent-derived values
2. Use np.mean([a.attribute for a in agents]) to get varying values
3. Add small random noise: np.random.uniform(-0.05, 0.05)
4. Keep coefficients small (0.1-0.5) to avoid saturation
5. The formula should produce values roughly in 0.2-0.8 range

Rules:
- Return ONLY the fixed Python code, no explanations
- Do not wrap in markdown code blocks
- Keep all agent classes and their logic
- Focus on fixing compute_outcome to use agent states
- Add np.random.uniform() noise as a last resort if needed
"""


def fix_model_variance_sync(code: str, cal_data: dict, model: str = None) -> str:
    """
    Fix model that produces constant outcomes with no variance.

    Args:
        code: The model code
        cal_data: Calibration results with min, max, mean, std
        model: Claude model to use

    Returns:
        Fixed Python code with better variance
    """
    from anthropic import Anthropic

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system_prompt = VARIANCE_FIXER_PROMPT.format(
        min=cal_data['min'],
        max=cal_data['max'],
        mean=cal_data['mean'],
        std=cal_data['std']
    )

    user_prompt = f"""Fix this model to produce meaningful variance in outcomes:

```python
{code}
```

Return the fixed code:"""

    response = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    fixed_code = response.content[0].text

    # Clean up markdown
    if fixed_code.startswith("```python"):
        fixed_code = fixed_code[9:]
    elif fixed_code.startswith("```"):
        fixed_code = fixed_code[3:]
    if fixed_code.endswith("```"):
        fixed_code = fixed_code[:-3]

    return fixed_code.strip()
