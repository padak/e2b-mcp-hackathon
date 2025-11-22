"""
Polymarket CLOB API client for fetching prediction markets.
"""

import os
import json
from typing import Optional
import httpx
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

load_dotenv()

# Gamma API for better market queries
GAMMA_API_URL = "https://gamma-api.polymarket.com"


def create_client() -> ClobClient:
    """Create and return a Polymarket CLOB client.

    For read-only operations (get_markets), no authentication is needed.
    For trading operations, a private key and API credentials are required.
    """
    # For read-only operations, we don't need authentication
    client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,  # Polygon
    )
    return client


# Global client instance (lazy initialization)
_client: Optional[ClobClient] = None


def get_client() -> ClobClient:
    """Get or create the global Polymarket client."""
    global _client
    if _client is None:
        _client = create_client()
    return _client


def get_markets(limit: int = 100, active_only: bool = True) -> list:
    """
    Fetch prediction markets from Polymarket using Gamma API.

    Args:
        limit: Maximum number of markets to return
        active_only: If True, only return active (open) markets

    Returns:
        List of market objects sorted by volume (descending)
    """
    # Use Gamma API for better filtering
    # Fetch more markets to sort properly, then limit
    fetch_limit = min(limit * 3, 500)
    params = {
        "limit": fetch_limit,
        "active": "true" if active_only else "false",
        "closed": "false" if active_only else "true",
    }

    with httpx.Client() as client:
        response = client.get(f"{GAMMA_API_URL}/markets", params=params)
        response.raise_for_status()
        markets = response.json()

    if not isinstance(markets, list):
        return []

    # Sort by volumeNum (numeric) descending
    markets.sort(key=lambda m: float(m.get("volumeNum") or m.get("volume") or 0), reverse=True)

    return markets[:limit]


def get_markets_clob(limit: int = 100) -> list:
    """
    Fetch markets using the CLOB API (includes closed markets).

    Args:
        limit: Maximum number of markets to return

    Returns:
        List of market objects
    """
    client = get_client()
    result = client.get_markets()
    # API returns {'data': [...], 'next_cursor': ...}
    markets = result.get("data", []) if isinstance(result, dict) else result
    return markets[:limit] if limit else markets


def get_market_details(condition_id: str) -> dict:
    """
    Get detailed information about a specific market.

    Args:
        condition_id: The market's condition ID

    Returns:
        Market details dictionary
    """
    client = get_client()
    return client.get_market(condition_id)


def select_high_volume_markets(markets: list, min_volume: float = 10000) -> list:
    """
    Filter markets by minimum trading volume.

    Args:
        markets: List of market objects
        min_volume: Minimum volume threshold

    Returns:
        Filtered list of high-volume markets
    """
    filtered = []
    for m in markets:
        try:
            volume = float(m.get("volume", 0) or 0)
            if volume >= min_volume:
                filtered.append(m)
        except (TypeError, ValueError):
            continue
    return filtered


def format_for_llm(market: dict) -> dict:
    """
    Format market data for LLM consumption.

    Args:
        market: Raw market object from API (supports both CLOB and Gamma formats)

    Returns:
        Formatted dictionary with key market info
    """
    yes_price = 0.5
    no_price = 0.5

    # Try Gamma API format first (outcomePrices as JSON string or list)
    outcome_prices = market.get("outcomePrices", [])
    # Parse if it's a JSON string
    if isinstance(outcome_prices, str):
        try:
            outcome_prices = json.loads(outcome_prices)
        except json.JSONDecodeError:
            outcome_prices = []

    if outcome_prices and len(outcome_prices) >= 2:
        try:
            yes_price = float(outcome_prices[0])
            no_price = float(outcome_prices[1])
        except (ValueError, TypeError):
            pass
    else:
        # Fall back to CLOB API format (tokens array)
        tokens = market.get("tokens", [])
        for token in tokens:
            outcome = token.get("outcome", "").lower()
            price = float(token.get("price", 0.5))
            if outcome == "yes":
                yes_price = price
            elif outcome == "no":
                no_price = price

    # Get volume (handle both formats)
    volume = market.get("volumeNum") or market.get("volume") or 0
    try:
        volume = float(volume)
    except (ValueError, TypeError):
        volume = 0

    return {
        "question": market.get("question", "Unknown"),
        "condition_id": market.get("conditionId") or market.get("condition_id", ""),
        "yes_odds": yes_price,
        "no_odds": no_price,
        "volume": volume,
        "end_date": market.get("endDateIso") or market.get("end_date_iso", ""),
        "description": market.get("description", ""),
    }


def format_markets_for_display(markets: list, max_display: int = 10) -> str:
    """
    Format markets list for CLI display.

    Args:
        markets: List of market objects
        max_display: Maximum number to display

    Returns:
        Formatted string for display
    """
    lines = []
    for i, m in enumerate(markets[:max_display], 1):
        formatted = format_for_llm(m)
        question = formatted["question"][:60] + "..." if len(formatted["question"]) > 60 else formatted["question"]
        yes_pct = formatted["yes_odds"] * 100
        volume = formatted["volume"]
        lines.append(f"{i}. {question}")
        lines.append(f"   Yes: {yes_pct:.0f}% | Volume: ${volume:,.0f}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Quick test
    print("Testing Polymarket client...")

    try:
        markets = get_markets(limit=20)
        print(f"Found {len(markets)} markets")

        high_volume = select_high_volume_markets(markets, min_volume=10000)
        print(f"High volume markets (>$10k): {len(high_volume)}")

        if high_volume:
            print("\nTop markets:")
            print(format_markets_for_display(high_volume, max_display=5))

            # Show first market details
            first = high_volume[0]
            formatted = format_for_llm(first)
            print(f"\nFirst market details:")
            print(f"  Question: {formatted['question']}")
            print(f"  Yes odds: {formatted['yes_odds']:.1%}")
            print(f"  Volume: ${formatted['volume']:,.0f}")
    except Exception as e:
        print(f"Error: {e}")
