"""Scoring module for arena evaluation.

Metrics:
- Brier Score: mean((prediction - outcome)²) - lower is better
- First-try Rate: % of runs where first execute_code succeeded
- Heal Rate: % of runs that recovered after initial failure
- Valid Rate: % of runs producing valid predictions
- Avg Attempts: mean execute_code calls per run
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelScore:
    """Scores for a single model."""

    model_id: str
    mode: str
    n_runs: int
    n_valid: int
    brier_score: Optional[float]  # None if no valid predictions
    first_try_rate: Optional[float]
    heal_rate: Optional[float]
    avg_attempts: float
    valid_rate: float

    def to_dict(self) -> dict:
        return {
            "model_id": self.model_id,
            "mode": self.mode,
            "n_runs": self.n_runs,
            "n_valid": self.n_valid,
            "brier_score": self.brier_score,
            "first_try_rate": self.first_try_rate,
            "heal_rate": self.heal_rate,
            "avg_attempts": self.avg_attempts,
            "valid_rate": self.valid_rate,
        }


@dataclass
class ArenaScores:
    """Complete scores for an arena run."""

    model_scores: list[ModelScore]
    overall_brier: Optional[float]
    overall_valid_rate: float
    n_total_runs: int
    n_valid_predictions: int

    def to_dict(self) -> dict:
        return {
            "model_scores": [s.to_dict() for s in self.model_scores],
            "overall_brier": self.overall_brier,
            "overall_valid_rate": self.overall_valid_rate,
            "n_total_runs": self.n_total_runs,
            "n_valid_predictions": self.n_valid_predictions,
        }

    def print_summary(self) -> None:
        """Print a formatted summary of scores."""
        print("\n" + "=" * 70)
        print("ARENA SCORES")
        print("=" * 70)

        print(f"\nTotal runs: {self.n_total_runs}")
        print(f"Valid predictions: {self.n_valid_predictions} ({self.overall_valid_rate:.1%})")
        if self.overall_brier is not None:
            print(f"Overall Brier Score: {self.overall_brier:.4f}")

        print("\n" + "-" * 70)
        print(f"{'Model':<30} {'Mode':<12} {'Brier':<10} {'Valid%':<10} {'1st-try%':<10}")
        print("-" * 70)

        for score in sorted(self.model_scores, key=lambda s: (s.model_id, s.mode)):
            brier_str = f"{score.brier_score:.4f}" if score.brier_score is not None else "N/A"
            first_try_str = f"{score.first_try_rate:.1%}" if score.first_try_rate is not None else "N/A"
            print(
                f"{score.model_id:<30} {score.mode:<12} {brier_str:<10} "
                f"{score.valid_rate:.1%}      {first_try_str}"
            )

        print("=" * 70)


def compute_brier_score(predictions: list[float], outcomes: list[float]) -> float:
    """Compute Brier score.

    Brier score = mean((prediction - outcome)²)
    Lower is better. Perfect = 0, worst = 1.

    Args:
        predictions: List of predicted probabilities (0-1)
        outcomes: List of actual outcomes (0 or 1)

    Returns:
        Brier score
    """
    if len(predictions) != len(outcomes):
        raise ValueError("Predictions and outcomes must have same length")
    if len(predictions) == 0:
        return None

    squared_errors = [(p - o) ** 2 for p, o in zip(predictions, outcomes)]
    return sum(squared_errors) / len(squared_errors)


def score_results(results: list[dict]) -> ArenaScores:
    """Score arena results.

    Args:
        results: List of result dictionaries from orchestrator

    Returns:
        ArenaScores object
    """
    # Group by (model, mode)
    groups = {}
    for r in results:
        key = (r["model_id"], r["mode"])
        if key not in groups:
            groups[key] = []
        groups[key].append(r)

    model_scores = []
    all_predictions = []
    all_outcomes = []

    for (model_id, mode), group_results in groups.items():
        n_runs = len(group_results)

        # Extract valid predictions
        valid_results = [
            r for r in group_results
            if r.get("prediction") and r["prediction"].get("valid", True)
            and r.get("resolved_outcome") is not None
        ]
        n_valid = len(valid_results)

        # Brier score
        if valid_results:
            predictions = [r["prediction"]["probability"] for r in valid_results]
            outcomes = [r["resolved_outcome"] for r in valid_results]
            brier = compute_brier_score(predictions, outcomes)

            all_predictions.extend(predictions)
            all_outcomes.extend(outcomes)
        else:
            brier = None

        # First-try rate (simulation mode only)
        if mode == "simulation":
            first_try_results = [
                r for r in group_results
                if r.get("metrics", {}).get("first_try_success") is not None
            ]
            if first_try_results:
                first_try_rate = sum(
                    1 for r in first_try_results
                    if r["metrics"]["first_try_success"]
                ) / len(first_try_results)
            else:
                first_try_rate = None
        else:
            first_try_rate = None

        # Heal rate
        heal_results = [
            r for r in group_results
            if r.get("metrics", {}).get("heal_rate") is not None
        ]
        if heal_results:
            heal_rate = sum(r["metrics"]["heal_rate"] for r in heal_results) / len(heal_results)
        else:
            heal_rate = None

        # Avg attempts
        attempt_results = [
            r for r in group_results
            if r.get("metrics", {}).get("execute_code_calls") is not None
        ]
        if attempt_results:
            avg_attempts = sum(
                r["metrics"]["execute_code_calls"] for r in attempt_results
            ) / len(attempt_results)
        else:
            avg_attempts = 0

        model_scores.append(
            ModelScore(
                model_id=model_id,
                mode=mode,
                n_runs=n_runs,
                n_valid=n_valid,
                brier_score=brier,
                first_try_rate=first_try_rate,
                heal_rate=heal_rate,
                avg_attempts=avg_attempts,
                valid_rate=n_valid / n_runs if n_runs > 0 else 0,
            )
        )

    # Overall scores
    n_total = len(results)
    n_valid_total = len(all_predictions)
    overall_brier = compute_brier_score(all_predictions, all_outcomes) if all_predictions else None

    return ArenaScores(
        model_scores=model_scores,
        overall_brier=overall_brier,
        overall_valid_rate=n_valid_total / n_total if n_total > 0 else 0,
        n_total_runs=n_total,
        n_valid_predictions=n_valid_total,
    )


def score_results_file(results_path: str) -> ArenaScores:
    """Score results from a JSON file.

    Args:
        results_path: Path to results JSON file

    Returns:
        ArenaScores object
    """
    with open(results_path) as f:
        data = json.load(f)

    results = data.get("results", [])
    return score_results(results)


def compare_models(scores: ArenaScores) -> dict:
    """Compare models and rank by Brier score.

    Args:
        scores: ArenaScores object

    Returns:
        Dictionary with rankings
    """
    # Separate by mode
    direct_scores = [s for s in scores.model_scores if s.mode == "direct"]
    sim_scores = [s for s in scores.model_scores if s.mode == "simulation"]

    def rank_by_brier(model_scores: list[ModelScore]) -> list[dict]:
        valid = [s for s in model_scores if s.brier_score is not None]
        ranked = sorted(valid, key=lambda s: s.brier_score)
        return [
            {
                "rank": i + 1,
                "model_id": s.model_id,
                "brier_score": s.brier_score,
                "valid_rate": s.valid_rate,
            }
            for i, s in enumerate(ranked)
        ]

    return {
        "direct_ranking": rank_by_brier(direct_scores),
        "simulation_ranking": rank_by_brier(sim_scores),
        "overall_ranking": rank_by_brier(scores.model_scores),
    }
