"""Tests for arena data layer."""

import json
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from arena.data.questions import Question
from arena.data.loader import (
    load_questions,
    load_questions_from_list,
    load_sample_questions,
    save_questions,
    filter_recent_questions,
    SAMPLE_QUESTIONS,
)
from arena.models.config import (
    get_model,
    get_all_models,
    get_default_models,
    estimate_arena_cost,
    MODELS,
)


class TestQuestion:
    """Tests for Question dataclass."""

    def test_from_polymarket_json_yes_resolved(self):
        """Test parsing a market where Yes won."""
        data = {
            "id": "test-1",
            "conditionId": "cond-1",
            "question": "Will X happen?",
            "slug": "will-x-happen",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["1", "0"],
            "umaResolutionStatus": "resolved",
            "volume": "1000000",
        }

        q = Question.from_polymarket_json(data)

        assert q.id == "test-1"
        assert q.question == "Will X happen?"
        assert q.resolved_outcome == 1.0
        assert q.resolved_yes is True
        assert q.is_resolved is True

    def test_from_polymarket_json_no_resolved(self):
        """Test parsing a market where No won."""
        data = {
            "id": "test-2",
            "conditionId": "cond-2",
            "question": "Will Y happen?",
            "slug": "will-y-happen",
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0", "1"],
            "umaResolutionStatus": "resolved",
            "volume": "500000",
        }

        q = Question.from_polymarket_json(data)

        assert q.resolved_outcome == 0.0
        assert q.resolved_yes is False

    def test_to_dict_roundtrip(self):
        """Test that to_dict produces valid data."""
        data = SAMPLE_QUESTIONS[0]
        q = Question.from_polymarket_json(data)
        d = q.to_dict()

        assert d["id"] == data["id"]
        assert d["question"] == data["question"]
        assert d["resolved_outcome"] == 1.0


class TestLoader:
    """Tests for data loader."""

    def test_load_sample_questions(self):
        """Test loading built-in sample questions."""
        questions = load_sample_questions()

        assert len(questions) == 5
        assert all(isinstance(q, Question) for q in questions)
        assert all(q.is_resolved for q in questions)

    def test_load_questions_from_file(self):
        """Test loading questions from JSON file."""
        questions = load_questions("data/arena/sample_questions.json")

        assert len(questions) == 8
        assert questions[0].question == "Will the Federal Reserve cut interest rates in December 2024?"

    def test_load_questions_with_filters(self):
        """Test loading with volume filter."""
        questions = load_questions(
            "data/arena/sample_questions.json",
            min_volume=5000000,
        )

        # Should only include high-volume markets
        assert all(q.volume >= 5000000 for q in questions)

    def test_load_questions_max_limit(self):
        """Test max_questions limit."""
        questions = load_questions(
            "data/arena/sample_questions.json",
            max_questions=3,
        )

        assert len(questions) == 3

    def test_save_and_load_questions(self):
        """Test saving and reloading questions."""
        original = load_sample_questions()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            save_questions(original, f.name)
            loaded = load_questions(f.name, only_resolved=False)

        assert len(loaded) == len(original)
        assert loaded[0].id == original[0].id

    def test_filter_recent_questions(self):
        """Test filtering by date."""
        questions = load_sample_questions()
        filtered = filter_recent_questions(questions, "2024-11-01")

        # Should include questions closed after Nov 1, 2024
        assert all(
            q.closed_time is None or q.closed_time >= "2024-11-01"
            for q in filtered
        )


class TestModelConfig:
    """Tests for model configuration."""

    def test_get_model(self):
        """Test getting model by key."""
        model = get_model("gpt-4o")

        assert model.id == "openai/gpt-4o"
        assert model.provider == "openai"
        assert model.supports_tools is True

    def test_get_model_invalid(self):
        """Test getting unknown model raises error."""
        with pytest.raises(KeyError):
            get_model("unknown-model")

    def test_get_all_models(self):
        """Test getting all models."""
        models = get_all_models()

        assert len(models) >= 3
        assert all(hasattr(m, "router_id") for m in models)

    def test_get_default_models(self):
        """Test getting default models."""
        models = get_default_models()

        assert len(models) == 3
        providers = {m.provider for m in models}
        assert "openai" in providers
        assert "anthropic" in providers
        assert "google" in providers

    def test_estimate_cost(self):
        """Test cost estimation for a model."""
        model = get_model("gpt-4o")

        # 1000 input + 500 output tokens
        cost = model.estimate_cost(1000, 500)

        # Should be (1000/1M * 2.50) + (500/1M * 10.00)
        expected = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)
        assert abs(cost - expected) < 0.0001

    def test_estimate_arena_cost(self):
        """Test arena cost estimation."""
        estimate = estimate_arena_cost(
            n_questions=5,
            n_models=3,
            n_modes=2,
            n_trials=3,
        )

        assert estimate["total_runs"] == 5 * 3 * 2 * 3  # 90 runs
        assert "total_estimated" in estimate
        assert estimate["total_estimated"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
