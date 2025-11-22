#!/usr/bin/env python3
"""
Batch CLI Mockup - Simulation of the V2 batch mode interface.
This is a mockup to test the UX before implementing the real thing.
"""

import httpx
import sys
from datetime import datetime

GAMMA_API_URL = "https://gamma-api.polymarket.com"


def get_markets_by_volume(limit: int = 10) -> list:
    """Fetch top markets by volume."""
    params = {"limit": limit * 3, "active": "true", "closed": "false"}
    with httpx.Client() as client:
        response = client.get(f"{GAMMA_API_URL}/markets", params=params)
        markets = response.json() if response.status_code == 200 else []

    markets.sort(key=lambda m: float(m.get("volumeNum") or 0), reverse=True)
    return markets[:limit]


def get_biggest_movers(category: str, limit: int = 10) -> list:
    """Get biggest movers (breaking news) by category."""
    with httpx.Client() as client:
        response = client.get(
            f"https://polymarket.com/api/biggest-movers",
            params={"category": category}
        )
        data = response.json() if response.status_code == 200 else {}

    markets = data.get("markets", [])
    return markets[:limit]


def search_markets(query: str, limit: int = 10) -> list:
    """Search markets using public search API."""
    with httpx.Client() as client:
        response = client.get(
            f"{GAMMA_API_URL}/public-search",
            params={
                "q": query,
                "limit_per_type": 50,
            }
        )
        data = response.json() if response.status_code == 200 else {}

    # Extract active markets from events
    markets = []
    for event in data.get("events", []):
        for market in event.get("markets", []):
            if not market.get("closed", False):
                markets.append(market)

    # Dedupe and sort by volume
    seen = set()
    unique = []
    for m in markets:
        mid = m.get("id")
        if mid not in seen:
            seen.add(mid)
            unique.append(m)

    unique.sort(key=lambda m: float(m.get("volumeNum") or 0), reverse=True)
    return unique[:limit]


def display_markets(markets: list, title: str, show_change: bool = False):
    """Display markets in a nice format."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}\n")

    if not markets:
        print("  No markets found.\n")
        return

    for i, m in enumerate(markets, 1):
        question = m.get("question", "Unknown")
        if len(question) > 55:
            question = question[:52] + "..."

        slug = m.get("slug", "")

        # Get odds
        outcome_prices = m.get("outcomePrices", [])
        if isinstance(outcome_prices, str):
            import json
            try:
                outcome_prices = json.loads(outcome_prices)
            except:
                outcome_prices = []

        yes_odds = float(outcome_prices[0]) * 100 if outcome_prices else 50

        print(f"  {i:2}. {question}")

        if show_change:
            change = m.get("oneDayPriceChange", 0) * 100
            print(f"      Yes: {yes_odds:.0f}% | 24h: {change:+.0f}%")
        else:
            volume = float(m.get("volumeNum") or m.get("volume") or 0)
            print(f"      Yes: {yes_odds:.0f}% | Volume: ${volume:,.0f}")

        # Get event slug for URL
        events = m.get("events", [])
        event_slug = events[0].get("slug", "") if events else ""
        if event_slug and slug:
            print(f"      https://polymarket.com/event/{event_slug}/{slug}")
        elif slug:
            print(f"      https://polymarket.com/event/{slug}")
        print()


def show_menu():
    """Display the main menu."""
    print("\n" + "=" * 60)
    print(" NEWS SCENARIO SIMULATOR - Batch Mode (MOCKUP)")
    print("=" * 60)
    print("""
  Breaking News Categories:
  1. Politics
  2. World
  3. Sports
  4. Crypto
  5. Finance
  6. Tech
  7. Culture

  Other:
  8. Top 10 by Volume
  9. Custom Search
  0. Quit
""")


def simulate_batch_run(markets: list, batch_name: str):
    """Simulate what a batch run would look like."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"results/{batch_name}_{timestamp}"

    print(f"\n{'=' * 60}")
    print(f" BATCH SIMULATION PREVIEW")
    print(f"{'=' * 60}")
    print(f"\n  Output directory: {results_dir}/")
    print(f"  Markets to simulate: {len(markets)}")
    print(f"\n  Would create:")
    print(f"    - {results_dir}/summary.html")
    print(f"    - {results_dir}/batch_report.json")

    for m in markets:
        question = m.get("question", "Unknown")[:40]
        slug = question.lower().replace(" ", "-").replace("?", "")[:30]
        print(f"    - {results_dir}/{slug}/")
        print(f"        model.py, result.html")

    print(f"\n  Estimated time: ~{len(markets) * 3} minutes (parallel execution)")
    print(f"\n  [MOCKUP - No actual simulation will run]")


def main():
    """Main CLI loop."""
    print("\n  Loading Polymarket data...")

    while True:
        show_menu()

        try:
            choice = input("  Select option (0-9): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Goodbye!\n")
            break

        if choice == "1":
            print("\n  Fetching politics markets (biggest movers)...")
            markets = get_biggest_movers("politics", 10)
            display_markets(markets, "POLITICS - Breaking", show_change=True)
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "politics")

        elif choice == "2":
            print("\n  Fetching world markets (biggest movers)...")
            markets = get_biggest_movers("world", 10)
            display_markets(markets, "WORLD - Breaking", show_change=True)
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "world")

        elif choice == "3":
            print("\n  Fetching sports markets (biggest movers)...")
            markets = get_biggest_movers("sports", 10)
            display_markets(markets, "SPORTS - Breaking", show_change=True)
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "sports")

        elif choice == "4":
            print("\n  Fetching crypto markets (biggest movers)...")
            markets = get_biggest_movers("crypto", 10)
            display_markets(markets, "CRYPTO - Breaking", show_change=True)
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "crypto")

        elif choice == "5":
            print("\n  Fetching finance markets (biggest movers)...")
            markets = get_biggest_movers("finance", 10)
            display_markets(markets, "FINANCE - Breaking", show_change=True)
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "finance")

        elif choice == "6":
            print("\n  Fetching tech markets (biggest movers)...")
            markets = get_biggest_movers("tech", 10)
            display_markets(markets, "TECH - Breaking", show_change=True)
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "tech")

        elif choice == "7":
            print("\n  Fetching culture markets (biggest movers)...")
            markets = get_biggest_movers("culture", 10)
            display_markets(markets, "CULTURE - Breaking", show_change=True)
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "culture")

        elif choice == "8":
            print("\n  Fetching top markets by volume...")
            markets = get_markets_by_volume(10)
            display_markets(markets, "TOP 10 BY VOLUME")
            if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                simulate_batch_run(markets, "top10_volume")

        elif choice == "9":
            query = input("\n  Enter search query: ").strip()
            if query:
                print(f"\n  Searching for '{query}'...")
                markets = search_markets(query, 10)
                display_markets(markets, f"SEARCH: {query.upper()}")
                if markets and input("  Run batch simulation? (y/n): ").lower() == 'y':
                    safe_name = query.lower().replace(" ", "_")[:20]
                    simulate_batch_run(markets, f"custom_{safe_name}")

        elif choice == "0":
            print("\n  Goodbye!\n")
            break

        else:
            print("\n  Invalid option. Please select 0-9.\n")


if __name__ == "__main__":
    main()
