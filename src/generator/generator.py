"""
LLM-based Mesa model generator using Claude.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

from .prompts import SYSTEM_PROMPT, create_generation_prompt, assemble_code

load_dotenv()

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL")
if not DEFAULT_MODEL:
    raise ValueError("ANTHROPIC_MODEL environment variable is required")


def generate_model(
    question: str,
    yes_odds: float,
    research: str,
    model: str = None
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
        model=model or DEFAULT_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    # Extract the agent code from response
    agent_code = response.content[0].text

    # Clean up if wrapped in markdown code blocks
    if agent_code.startswith("```python"):
        agent_code = agent_code[9:]
    elif agent_code.startswith("```"):
        agent_code = agent_code[3:]
    if agent_code.endswith("```"):
        agent_code = agent_code[:-3]

    # Combine with template
    return assemble_code(agent_code.strip())


async def generate_model_async(
    question: str,
    yes_odds: float,
    research: str,
    model: str = None
) -> str:
    """
    Async version of generate_model.
    """
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    user_prompt = create_generation_prompt(question, yes_odds, research)

    response = await client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    agent_code = response.content[0].text

    # Clean up markdown
    if agent_code.startswith("```python"):
        agent_code = agent_code[9:]
    elif agent_code.startswith("```"):
        agent_code = agent_code[3:]
    if agent_code.endswith("```"):
        agent_code = agent_code[:-3]

    # Combine with template
    return assemble_code(agent_code.strip())
