"""
Phase 4 Tests: Polymarket Client

Tests for the Polymarket API client using Gamma API.
"""

import pytest
import sys
import os
import importlib.util

# Load polymarket module directly to avoid conflict with mcp package
spec = importlib.util.spec_from_file_location(
    "polymarket",
    os.path.join(os.path.dirname(__file__), '..', 'src', 'mcp', 'polymarket.py')
)
polymarket = importlib.util.module_from_spec(spec)
spec.loader.exec_module(polymarket)

get_markets = polymarket.get_markets
format_for_llm = polymarket.format_for_llm
select_high_volume_markets = polymarket.select_high_volume_markets
format_markets_for_display = polymarket.format_markets_for_display


class TestPolymarketClient:
    """Test Polymarket client functions."""

    def test_get_markets_returns_list(self):
        """Test that get_markets returns a list of markets."""
        markets = get_markets(limit=5)
        assert isinstance(markets, list)
        assert len(markets) > 0
        assert len(markets) <= 5

    def test_markets_have_required_fields(self):
        """Test that markets have the required fields."""
        markets = get_markets(limit=1)
        market = markets[0]

        # Check required fields exist
        assert "question" in market
        assert "outcomePrices" in market or "tokens" in market
        assert "volumeNum" in market or "volume" in market

    def test_markets_sorted_by_volume(self):
        """Test that markets are sorted by volume descending."""
        markets = get_markets(limit=10)

        volumes = []
        for m in markets:
            vol = float(m.get("volumeNum") or m.get("volume") or 0)
            volumes.append(vol)

        # Check volumes are in descending order
        for i in range(len(volumes) - 1):
            assert volumes[i] >= volumes[i + 1], f"Markets not sorted by volume at index {i}"

    def test_format_for_llm(self):
        """Test formatting market data for LLM."""
        markets = get_markets(limit=1)
        formatted = format_for_llm(markets[0])

        # Check required fields
        assert "question" in formatted
        assert "yes_odds" in formatted
        assert "no_odds" in formatted
        assert "volume" in formatted
        assert "condition_id" in formatted

        # Check types
        assert isinstance(formatted["question"], str)
        assert isinstance(formatted["yes_odds"], float)
        assert isinstance(formatted["no_odds"], float)
        assert isinstance(formatted["volume"], float)

        # Check odds are valid probabilities
        assert 0 <= formatted["yes_odds"] <= 1
        assert 0 <= formatted["no_odds"] <= 1

    def test_select_high_volume_markets(self):
        """Test filtering markets by volume."""
        markets = get_markets(limit=20)

        # Filter with different thresholds
        high_vol = select_high_volume_markets(markets, min_volume=100000)
        low_vol = select_high_volume_markets(markets, min_volume=1)

        assert len(high_vol) <= len(low_vol)

        # Check all returned markets meet threshold
        for m in high_vol:
            vol = float(m.get("volumeNum") or m.get("volume") or 0)
            assert vol >= 100000

    def test_format_markets_for_display(self):
        """Test formatting markets for display."""
        markets = get_markets(limit=5)
        display = format_markets_for_display(markets, max_display=3)

        assert isinstance(display, str)
        assert len(display) > 0

        # Check format includes expected elements
        assert "1." in display
        assert "Yes:" in display
        assert "Volume:" in display


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_market_format(self):
        """Test formatting an empty market dict."""
        formatted = format_for_llm({})

        assert formatted["question"] == "Unknown"
        assert formatted["yes_odds"] == 0.5
        assert formatted["no_odds"] == 0.5
        assert formatted["volume"] == 0

    def test_select_with_zero_threshold(self):
        """Test selecting markets with zero volume threshold."""
        markets = get_markets(limit=10)
        filtered = select_high_volume_markets(markets, min_volume=0)

        # Should return all markets
        assert len(filtered) == len(markets)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
