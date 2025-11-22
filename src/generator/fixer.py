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

FIXER_SYSTEM_PROMPT = """You are a Python code debugger specializing in Mesa 3.x agent-based simulations.

Your task is to fix Python code that failed to execute. You will receive:
1. The original code
2. The error message

## CRITICAL Mesa 3.x Requirements:

Every Agent subclass MUST call super().__init__(model):
```python
class MyAgent(Agent):
    def __init__(self, unique_id: int, model):
        super().__init__(model)  # REQUIRED - only model, not unique_id!
        self.unique_id = unique_id
```

Common errors:
- "TypeError: __init__() missing 1 required positional argument: 'model'" -> super().__init__() forgot to pass model
- "TypeError: __init__() takes 2 positional arguments but 3 were given" -> super().__init__(unique_id, model) is WRONG

Rules:
- Return ONLY the fixed Python code, no explanations
- Do not wrap in markdown code blocks
- Preserve the original structure and logic as much as possible
- Fix only the specific error, don't refactor unnecessarily
- Make sure all imports are included
- Use Mesa 3.x API (no schedule, use model.agents.shuffle_do("step"))
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
