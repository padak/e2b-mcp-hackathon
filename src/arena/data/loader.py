"""Load questions from polymarket-downloader JSON format."""

import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .questions import Question

logger = logging.getLogger(__name__)


def load_questions(
    markets_path: str,
    only_resolved: bool = True,
    min_volume: float = 0,
    max_questions: Optional[int] = None,
    after_date: Optional[str] = None,
) -> list[Question]:
    """Load questions from polymarket-downloader markets.json.

    Args:
        markets_path: Path to markets.json file
        only_resolved: Only include resolved markets (default True)
        min_volume: Minimum trading volume filter
        max_questions: Maximum number of questions to return
        after_date: Only include markets closed after this date (ISO format)

    Returns:
        List of Question objects

    Example:
        questions = load_questions("data/markets.json", max_questions=10)
    """
    path = Path(markets_path)
    if not path.exists():
        raise FileNotFoundError(f"Markets file not found: {markets_path}")

    with open(path, "r", encoding="utf-8") as f:
        markets = json.load(f)

    # Handle both list and dict formats
    if isinstance(markets, dict):
        # Some exports have {"markets": [...]}
        markets = markets.get("markets", [])

    questions = []
    for market in markets:
        # Filter by resolution status
        if only_resolved:
            status = market.get("umaResolutionStatus", "")
            if status != "resolved":
                continue

        # Filter by volume
        volume = float(market.get("volume", 0))
        if volume < min_volume:
            continue

        # Filter by date
        if after_date:
            closed_time = market.get("closedTime", "")
            if closed_time and closed_time < after_date:
                continue

        try:
            question = Question.from_polymarket_json(market)
            questions.append(question)
        except Exception as e:
            logger.warning(f"Failed to parse market {market.get('id', 'unknown')}: {e}")
            continue

        # Limit results
        if max_questions and len(questions) >= max_questions:
            break

    logger.info(f"Loaded {len(questions)} questions from {markets_path}")
    return questions


def load_questions_from_list(data: list[dict]) -> list[Question]:
    """Load questions from a list of market dicts.

    Args:
        data: List of market dictionaries in polymarket format

    Returns:
        List of Question objects
    """
    questions = []
    for market in data:
        try:
            question = Question.from_polymarket_json(market)
            questions.append(question)
        except Exception as e:
            logger.warning(f"Failed to parse market: {e}")
    return questions


def save_questions(questions: list[Question], output_path: str) -> None:
    """Save questions to JSON file.

    Args:
        questions: List of Question objects
        output_path: Path to output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = [q.to_dict() for q in questions]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved {len(questions)} questions to {output_path}")


def filter_recent_questions(
    questions: list[Question],
    after_date: str,
) -> list[Question]:
    """Filter questions to only include those resolved after a date.

    This helps mitigate data leakage by excluding questions that might
    be in model training data.

    Args:
        questions: List of Question objects
        after_date: ISO format date string (e.g., "2024-01-01")

    Returns:
        Filtered list of questions
    """
    filtered = []
    for q in questions:
        if q.closed_time and q.closed_time >= after_date:
            filtered.append(q)
        elif not q.closed_time:
            # Include if no closed_time (can't filter)
            filtered.append(q)
    return filtered


# Sample data for testing without external data
SAMPLE_QUESTIONS = [
    {
        "id": "sample-1",
        "conditionId": "cond-1",
        "question": "Will the Federal Reserve cut interest rates in December 2024?",
        "slug": "fed-rate-cut-dec-2024",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["1", "0"],  # Yes won
        "umaResolutionStatus": "resolved",
        "volume": "5000000",
        "startDate": "2024-11-01T00:00:00Z",
        "endDate": "2024-12-31T23:59:59Z",
        "closedTime": "2024-12-18T00:00:00Z",
        "description": "This market resolves Yes if the Federal Reserve cuts the federal funds rate at its December 2024 FOMC meeting.",
    },
    {
        "id": "sample-2",
        "conditionId": "cond-2",
        "question": "Will Bitcoin reach $100,000 before 2025?",
        "slug": "bitcoin-100k-2025",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["1", "0"],  # Yes won
        "umaResolutionStatus": "resolved",
        "volume": "10000000",
        "startDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-12-31T23:59:59Z",
        "closedTime": "2024-12-05T00:00:00Z",
        "description": "This market resolves Yes if Bitcoin's price reaches or exceeds $100,000 USD on any major exchange before January 1, 2025.",
    },
    {
        "id": "sample-3",
        "conditionId": "cond-3",
        "question": "Will SpaceX successfully catch Starship booster with chopsticks in 2024?",
        "slug": "spacex-starship-catch-2024",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["1", "0"],  # Yes won
        "umaResolutionStatus": "resolved",
        "volume": "2000000",
        "startDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-12-31T23:59:59Z",
        "closedTime": "2024-10-13T00:00:00Z",
        "description": "This market resolves Yes if SpaceX successfully catches a Starship Super Heavy booster using the launch tower ('chopsticks') in 2024.",
    },
    {
        "id": "sample-4",
        "conditionId": "cond-4",
        "question": "Will Donald Trump win the 2024 US Presidential Election?",
        "slug": "trump-wins-2024",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["1", "0"],  # Yes won
        "umaResolutionStatus": "resolved",
        "volume": "50000000",
        "startDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-11-05T23:59:59Z",
        "closedTime": "2024-11-06T00:00:00Z",
        "description": "This market resolves Yes if Donald Trump wins the 2024 US Presidential Election.",
    },
    {
        "id": "sample-5",
        "conditionId": "cond-5",
        "question": "Will the US unemployment rate exceed 5% in 2024?",
        "slug": "us-unemployment-5pct-2024",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0", "1"],  # No won
        "umaResolutionStatus": "resolved",
        "volume": "1500000",
        "startDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-12-31T23:59:59Z",
        "closedTime": "2024-12-31T00:00:00Z",
        "description": "This market resolves Yes if the US unemployment rate exceeds 5% at any point in 2024.",
    },
]


def load_sample_questions() -> list[Question]:
    """Load sample questions for testing.

    Returns:
        List of 5 sample Question objects
    """
    return load_questions_from_list(SAMPLE_QUESTIONS)
