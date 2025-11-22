"""
LLM-based Mesa model generator using Claude.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

from .prompts import SYSTEM_PROMPT, create_generation_prompt

load_dotenv()


def generate_model(
    question: str,
    yes_odds: float,
    research: str,
    model: str = "claude-sonnet-4-20250514"
) -> str:
    """
    Generate a Mesa simulation model using Claude.

    Args:
        question: The prediction market question
        yes_odds: Current market odds for Yes (0-1)
        research: Research data from Perplexity
        model: Claude model to use

    Returns:
        Complete Python code as string
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    user_prompt = create_generation_prompt(question, yes_odds, research)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    # Extract the code from response
    code = response.content[0].text

    # Clean up if wrapped in markdown code blocks
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    return code.strip()


async def generate_model_async(
    question: str,
    yes_odds: float,
    research: str,
    model: str = "claude-sonnet-4-20250514"
) -> str:
    """
    Async version of generate_model.
    """
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    user_prompt = create_generation_prompt(question, yes_odds, research)

    response = await client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    code = response.content[0].text

    # Clean up markdown
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    return code.strip()
