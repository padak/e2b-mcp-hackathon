"""Model configurations for OpenRouter-based LLM routing."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """Configuration for an LLM model via OpenRouter.

    Attributes:
        id: OpenRouter model ID (e.g., "openai/gpt-4o")
        name: Human-readable name
        provider: Provider name (openai, anthropic, google)
        router_id: Full router ID for claude-code-router (e.g., "openrouter,openai/gpt-4o")
        input_price: Price per 1M input tokens in USD
        output_price: Price per 1M output tokens in USD
        context_length: Maximum context length
        supports_tools: Whether model supports tool/function calling
    """

    id: str
    name: str
    provider: str
    router_id: str
    input_price: float  # USD per 1M input tokens
    output_price: float  # USD per 1M output tokens
    context_length: int
    supports_tools: bool = True

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a given number of tokens.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.input_price
        output_cost = (output_tokens / 1_000_000) * self.output_price
        return input_cost + output_cost


# OpenRouter model configurations
# Prices from https://openrouter.ai/models (as of Dec 2024)

MODELS = {
    # OpenAI models
    "gpt-4o": ModelConfig(
        id="openai/gpt-4o",
        name="GPT-4o",
        provider="openai",
        router_id="openrouter,openai/gpt-4o",
        input_price=2.50,  # $2.50 per 1M input tokens
        output_price=10.00,  # $10.00 per 1M output tokens
        context_length=128_000,
        supports_tools=True,
    ),
    "gpt-4o-mini": ModelConfig(
        id="openai/gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        router_id="openrouter,openai/gpt-4o-mini",
        input_price=0.15,
        output_price=0.60,
        context_length=128_000,
        supports_tools=True,
    ),
    # Anthropic models
    "claude-sonnet-4": ModelConfig(
        id="anthropic/claude-sonnet-4",
        name="Claude Sonnet 4",
        provider="anthropic",
        router_id="openrouter,anthropic/claude-sonnet-4",
        input_price=3.00,
        output_price=15.00,
        context_length=200_000,
        supports_tools=True,
    ),
    "claude-3.5-sonnet": ModelConfig(
        id="anthropic/claude-3.5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        router_id="openrouter,anthropic/claude-3.5-sonnet",
        input_price=3.00,
        output_price=15.00,
        context_length=200_000,
        supports_tools=True,
    ),
    # Google models
    "gemini-2.0-flash": ModelConfig(
        id="google/gemini-2.0-flash-exp:free",
        name="Gemini 2.0 Flash",
        provider="google",
        router_id="openrouter,google/gemini-2.0-flash-exp:free",
        input_price=0.0,  # Free tier
        output_price=0.0,
        context_length=1_000_000,
        supports_tools=True,
    ),
    "gemini-pro": ModelConfig(
        id="google/gemini-pro-1.5",
        name="Gemini Pro 1.5",
        provider="google",
        router_id="openrouter,google/gemini-pro-1.5",
        input_price=1.25,
        output_price=5.00,
        context_length=2_000_000,
        supports_tools=True,
    ),
}

# Default models for arena evaluation
DEFAULT_MODELS = ["gpt-4o", "claude-sonnet-4", "gemini-2.0-flash"]

# Budget-friendly models for testing
BUDGET_MODELS = ["gpt-4o-mini", "gemini-2.0-flash"]


def get_model(model_key: str) -> ModelConfig:
    """Get model configuration by key.

    Args:
        model_key: Model key (e.g., "gpt-4o", "claude-sonnet-4")

    Returns:
        ModelConfig instance

    Raises:
        KeyError: If model not found
    """
    if model_key not in MODELS:
        raise KeyError(f"Unknown model: {model_key}. Available: {list(MODELS.keys())}")
    return MODELS[model_key]


def get_all_models() -> list[ModelConfig]:
    """Get all available model configurations."""
    return list(MODELS.values())


def get_default_models() -> list[ModelConfig]:
    """Get default models for arena evaluation."""
    return [MODELS[key] for key in DEFAULT_MODELS]


def get_budget_models() -> list[ModelConfig]:
    """Get budget-friendly models for testing."""
    return [MODELS[key] for key in BUDGET_MODELS]


def estimate_arena_cost(
    n_questions: int,
    n_models: int = 3,
    n_modes: int = 2,
    n_trials: int = 3,
    avg_input_tokens: int = 5000,
    avg_output_tokens: int = 2000,
) -> dict:
    """Estimate total arena cost.

    Args:
        n_questions: Number of questions to evaluate
        n_models: Number of models (default 3)
        n_modes: Number of modes (direct + simulation = 2)
        n_trials: Trials per model/question (default 3)
        avg_input_tokens: Average input tokens per run
        avg_output_tokens: Average output tokens per run

    Returns:
        Dict with cost breakdown
    """
    total_runs = n_questions * n_models * n_modes * n_trials

    costs = {}
    for model_key in DEFAULT_MODELS:
        model = MODELS[model_key]
        model_cost = model.estimate_cost(avg_input_tokens, avg_output_tokens)
        model_runs = n_questions * n_modes * n_trials
        costs[model_key] = model_cost * model_runs

    return {
        "total_runs": total_runs,
        "per_model_costs": costs,
        "total_estimated": sum(costs.values()),
        "assumptions": {
            "n_questions": n_questions,
            "n_models": n_models,
            "n_modes": n_modes,
            "n_trials": n_trials,
            "avg_input_tokens": avg_input_tokens,
            "avg_output_tokens": avg_output_tokens,
        },
    }
