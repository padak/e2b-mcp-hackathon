"""
Tests for Phase 6: LLM Model Generator
"""

import pytest
from src.generator import generate_model, create_generation_prompt, SYSTEM_PROMPT


class TestPrompts:
    """Test prompt generation."""

    def test_system_prompt_contains_mesa_spec(self):
        """System prompt should contain Mesa 2.x technical spec."""
        assert "Mesa 2.1.5" in SYSTEM_PROMPT or "Mesa 2.x" in SYSTEM_PROMPT
        assert "super().__init__(unique_id, model)" in SYSTEM_PROMPT
        assert "RandomActivation" in SYSTEM_PROMPT

    def test_system_prompt_contains_output_format(self):
        """System prompt should specify required output format."""
        assert "AGENT_CONFIG" in SYSTEM_PROMPT
        assert "MODEL_PARAMS" in SYSTEM_PROMPT
        assert "THRESHOLD" in SYSTEM_PROMPT
        assert "compute_outcome" in SYSTEM_PROMPT

    def test_create_generation_prompt(self):
        """Test user prompt creation."""
        prompt = create_generation_prompt(
            question="Will the Fed cut rates in December 2024?",
            yes_odds=0.72,
            research="Current rate is 5.5%. Inflation at 3.2%."
        )

        assert "Will the Fed cut rates" in prompt
        assert "72%" in prompt
        assert "28%" in prompt
        assert "Current rate is 5.5%" in prompt


class TestGenerator:
    """Test model generation with Claude."""

    @pytest.mark.slow
    def test_generate_model_basic(self):
        """Test basic model generation (requires API key)."""
        code = generate_model(
            question="Will Bitcoin exceed $100,000 by end of 2024?",
            yes_odds=0.35,
            research="""
            Current BTC price: $67,000
            Historical volatility: 60% annually
            Key factors: ETF inflows, halving effect, macro conditions
            Recent trend: sideways consolidation
            """
        )

        # Check code structure - generated code includes full template
        assert "from mesa import" in code
        assert "class" in code and "Agent" in code
        assert "def compute_outcome" in code
        assert "AGENT_CONFIG" in code
        assert "MODEL_PARAMS" in code
        assert "THRESHOLD" in code

        # Should use Mesa 2.x patterns (in template)
        assert "RandomActivation" in code
        assert "self.schedule.add" in code

    @pytest.mark.slow
    def test_generate_model_economic(self):
        """Test generation for economic scenario."""
        code = generate_model(
            question="Will the Fed cut rates in December 2024?",
            yes_odds=0.72,
            research="""
            Current federal funds rate: 5.25-5.50%
            November CPI: 3.1% YoY
            Unemployment: 3.7%
            Fed officials' recent statements suggest data-dependent approach
            Market expects 25bp cut with 72% probability
            """
        )

        # Generated code includes template with run_monte_carlo and SimulationModel
        assert "def run_monte_carlo" in code
        assert "SimulationModel" in code

    @pytest.mark.slow
    def test_generated_code_is_syntactically_valid(self):
        """Test that generated code can be compiled."""
        code = generate_model(
            question="Will it rain tomorrow in NYC?",
            yes_odds=0.60,
            research="Weather forecast shows 60% chance of rain."
        )

        # Should compile without syntax errors
        try:
            compile(code, "<generated>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")


if __name__ == "__main__":
    # Quick manual test
    print("Testing prompt creation...")
    prompt = create_generation_prompt(
        question="Test question?",
        yes_odds=0.5,
        research="Test research data"
    )
    print(f"Prompt length: {len(prompt)} chars")
    print("Prompt preview:", prompt[:200])

    print("\n" + "=" * 50)
    print("To run full tests with API calls:")
    print("  pytest tests/test_phase6_generator.py -v -m slow")
