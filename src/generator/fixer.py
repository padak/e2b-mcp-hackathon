"""
LLM-based code fixer for failed simulations.
"""

import os
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

FIXER_SYSTEM_PROMPT = """You are a Python code debugger specializing in Mesa agent-based simulations.

Your task is to fix Python code that failed to execute. You will receive:
1. The original code
2. The error message

Rules:
- Return ONLY the fixed Python code, no explanations
- Do not wrap in markdown code blocks
- Preserve the original structure and logic as much as possible
- Fix only the specific error, don't refactor unnecessarily
- Ensure the run_trial(seed: int) -> bool function signature is preserved
- Make sure all imports are included
- Use Mesa 3.x API (Model.steps instead of schedule, model.agents property)
"""


async def fix_code(code: str, error: str, model: str = "claude-sonnet-4-20250514") -> str:
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
        model=model,
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


def fix_code_sync(code: str, error: str, model: str = "claude-sonnet-4-20250514") -> str:
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
        model=model,
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
