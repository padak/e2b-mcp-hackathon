"""LLM Prediction Arena - Benchmark LLMs on prediction tasks.

Usage:
    python -m arena run --models gpt-4o-mini --max-questions 2
    python -m arena quick-test
    python -m arena score results/arena/results.json
    python -m arena list-models
"""

__version__ = "0.1.0"

from .orchestrator import ArenaOrchestrator, RunConfig, run_arena
from .scoring import score_results, score_results_file, ArenaScores
from .data.questions import Question
from .data.loader import load_questions, load_sample_questions
from .models.config import get_model, get_all_models, MODELS

__all__ = [
    "ArenaOrchestrator",
    "RunConfig",
    "run_arena",
    "score_results",
    "score_results_file",
    "ArenaScores",
    "Question",
    "load_questions",
    "load_sample_questions",
    "get_model",
    "get_all_models",
    "MODELS",
]
