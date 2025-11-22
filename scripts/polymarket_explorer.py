#!/usr/bin/env python3
"""
Mockup script to explore Polymarket API data structure.
See what fields are available for filtering (tags, categories, etc.)
"""

import httpx
import json
from collections import Counter

GAMMA_API_URL = "https://gamma-api.polymarket.com"


def fetch_markets(limit: int = 100) -> list:
    """Fetch markets from Gamma API."""
    params = {
        "limit": limit,
        "active": "true",
        "closed": "false",
    }

    with httpx.Client() as client:
        response = client.get(f"{GAMMA_API_URL}/markets", params=params)
        response.raise_for_status()
        return response.json()


def explore_market_structure(markets: list):
    """Show all available fields in market objects."""
    if not markets:
        print("No markets found!")
        return

    # Get all unique keys across all markets
    all_keys = set()
    for m in markets:
        all_keys.update(m.keys())

    print("=" * 60)
    print("AVAILABLE FIELDS IN MARKET OBJECTS")
    print("=" * 60)
    for key in sorted(all_keys):
        print(f"  - {key}")

    print("\n" + "=" * 60)
    print("SAMPLE MARKET (FULL DATA)")
    print("=" * 60)
    print(json.dumps(markets[0], indent=2, default=str))


def analyze_tags(markets: list):
    """Analyze tags/categories in markets."""
    print("\n" + "=" * 60)
    print("TAGS ANALYSIS")
    print("=" * 60)

    tag_counter = Counter()
    markets_with_tags = 0

    for m in markets:
        tags = m.get("tags", [])
        if tags:
            markets_with_tags += 1
            # Tags might be string or list
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = [tags]
            for tag in tags:
                if isinstance(tag, dict):
                    tag_counter[tag.get("label", tag.get("slug", str(tag)))] += 1
                else:
                    tag_counter[str(tag)] += 1

    print(f"\nMarkets with tags: {markets_with_tags}/{len(markets)}")
    print("\nTop 20 tags:")
    for tag, count in tag_counter.most_common(20):
        print(f"  {tag}: {count}")


def analyze_categories(markets: list):
    """Look for category-like fields."""
    print("\n" + "=" * 60)
    print("CATEGORY-LIKE FIELDS")
    print("=" * 60)

    # Check various fields that might indicate category
    category_fields = ["category", "slug", "groupSlug", "groupItemTitle"]

    for field in category_fields:
        values = Counter()
        for m in markets:
            val = m.get(field)
            if val:
                values[str(val)[:50]] += 1

        if values:
            print(f"\n{field}:")
            for val, count in values.most_common(10):
                print(f"  {val}: {count}")


def show_top_by_volume(markets: list, n: int = 10):
    """Show top N markets by volume."""
    print("\n" + "=" * 60)
    print(f"TOP {n} MARKETS BY VOLUME")
    print("=" * 60)

    # Sort by volume
    sorted_markets = sorted(
        markets,
        key=lambda m: float(m.get("volumeNum") or m.get("volume") or 0),
        reverse=True
    )

    for i, m in enumerate(sorted_markets[:n], 1):
        question = m.get("question", "Unknown")[:60]
        volume = float(m.get("volumeNum") or m.get("volume") or 0)
        tags = m.get("tags", [])

        # Parse tags
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []

        tag_str = ", ".join([
            t.get("label", str(t)) if isinstance(t, dict) else str(t)
            for t in tags[:3]
        ]) if tags else "No tags"

        print(f"\n{i}. {question}...")
        print(f"   Volume: ${volume:,.0f}")
        print(f"   Tags: {tag_str}")


def test_api_params():
    """Test different API parameters."""
    print("\n" + "=" * 60)
    print("TESTING TAG FILTERING")
    print("=" * 60)

    # Test various tags
    tags_to_test = [
        "politics", "crypto", "sports", "finance", "world",
        "entertainment", "science", "tech", "elections", "bitcoin",
        "ethereum", "nfl", "nba", "soccer", "ai", "stocks",
        "breaking", "trending", "popular", "new"
    ]

    results = []
    with httpx.Client() as client:
        for tag in tags_to_test:
            params = {"limit": 50, "active": "true", "tag": tag}
            try:
                response = client.get(f"{GAMMA_API_URL}/markets", params=params)
                markets = response.json() if response.status_code == 200 else []
                count = len(markets) if isinstance(markets, list) else 0
                if count > 0:
                    results.append((tag, count))
            except Exception as e:
                pass

    # Sort by count
    results.sort(key=lambda x: x[1], reverse=True)
    print("\nTags with markets:")
    for tag, count in results:
        print(f"  {tag}: {count}")


def show_markets_by_tag(tag: str, limit: int = 5):
    """Show sample markets for a specific tag."""
    print(f"\n" + "=" * 60)
    print(f"SAMPLE MARKETS FOR TAG: {tag}")
    print("=" * 60)

    params = {"limit": limit, "active": "true", "tag": tag}
    with httpx.Client() as client:
        response = client.get(f"{GAMMA_API_URL}/markets", params=params)
        markets = response.json() if response.status_code == 200 else []

    for i, m in enumerate(markets, 1):
        question = m.get("question", "Unknown")[:70]
        volume = float(m.get("volumeNum") or m.get("volume") or 0)
        print(f"\n{i}. {question}")
        print(f"   Volume: ${volume:,.0f}")


def test_events_endpoint():
    """Test the events endpoint which might have better categorization."""
    print("\n" + "=" * 60)
    print("TESTING EVENTS ENDPOINT")
    print("=" * 60)

    with httpx.Client() as client:
        # Try events endpoint
        response = client.get(f"{GAMMA_API_URL}/events", params={"limit": 20, "active": "true"})
        events = response.json() if response.status_code == 200 else []

    if events:
        print(f"\nFound {len(events)} events")
        print("\nSample events:")
        for i, e in enumerate(events[:10], 1):
            title = e.get("title", "Unknown")[:60]
            slug = e.get("slug", "")
            markets_count = len(e.get("markets", []))
            print(f"\n{i}. {title}")
            print(f"   Slug: {slug}")
            print(f"   Markets: {markets_count}")

        # Show full structure of first event
        print("\n\nFirst event full structure:")
        print(json.dumps(events[0], indent=2, default=str)[:2000])


def filter_by_keywords(markets: list, keywords: list[str], limit: int = 10) -> list:
    """Filter markets by keywords in question/description."""
    filtered = []
    for m in markets:
        question = m.get("question", "").lower()
        description = m.get("description", "").lower()
        text = question + " " + description

        if any(kw.lower() in text for kw in keywords):
            filtered.append(m)

    # Sort by volume
    filtered.sort(key=lambda x: float(x.get("volumeNum") or 0), reverse=True)
    return filtered[:limit]


def show_keyword_filtering():
    """Demonstrate keyword-based filtering as alternative to tags."""
    print("\n" + "=" * 60)
    print("KEYWORD-BASED FILTERING (Alternative to tags)")
    print("=" * 60)

    # Fetch more markets
    markets = fetch_markets(limit=300)

    categories = {
        "Politics": ["trump", "biden", "election", "congress", "senate", "government", "president"],
        "Crypto": ["bitcoin", "ethereum", "crypto", "btc", "eth", "defi", "token"],
        "Finance": ["fed", "rate", "recession", "stock", "market cap", "gdp", "inflation"],
        "Sports": ["nfl", "nba", "soccer", "football", "championship", "super bowl"],
        "Tech": ["ai", "openai", "google", "apple", "microsoft", "tesla"],
    }

    for category, keywords in categories.items():
        filtered = filter_by_keywords(markets, keywords)
        if filtered:
            print(f"\n{category} ({len(filtered)} markets):")
            for i, m in enumerate(filtered[:3], 1):
                question = m.get("question", "")[:60]
                volume = float(m.get("volumeNum") or 0)
                print(f"  {i}. {question}... (${volume:,.0f})")


def fetch_tags():
    """Fetch available tags from the API."""
    print("\n" + "=" * 60)
    print("AVAILABLE TAGS (from /tags endpoint)")
    print("=" * 60)

    with httpx.Client() as client:
        # Fetch more tags
        response = client.get(f"{GAMMA_API_URL}/tags", params={"limit": 1000})
        tags = response.json() if response.status_code == 200 else []

    if tags:
        print(f"\nFound {len(tags)} tags total\n")

        # Search for key category tags
        search_terms = ["politic", "crypto", "bitcoin", "sport", "finance", "tech", "ai", "election", "nfl", "nba"]

        print("Key category tags found:")
        for term in search_terms:
            matches = [t for t in tags if term in t.get("label", "").lower() or term in t.get("slug", "").lower()]
            if matches:
                for t in matches[:3]:
                    print(f"  '{term}' -> ID: {t.get('id'):6} | {t.get('label', t.get('slug'))}")

        return tags
    return []


def test_tag_id_filtering(tags: list):
    """Test filtering by tag_id."""
    print("\n" + "=" * 60)
    print("TESTING tag_id FILTERING")
    print("=" * 60)

    # Find some interesting tags
    tag_map = {t.get("label", t.get("slug", "")).lower(): t.get("id") for t in tags}

    test_tags = ["politics", "crypto", "sports", "ai", "elections"]

    with httpx.Client() as client:
        for tag_name in test_tags:
            tag_id = tag_map.get(tag_name)
            if not tag_id:
                # Try partial match
                for label, tid in tag_map.items():
                    if tag_name in label:
                        tag_id = tid
                        break

            if tag_id:
                params = {"tag_id": tag_id, "closed": "false", "limit": 5}
                response = client.get(f"{GAMMA_API_URL}/markets", params=params)
                markets = response.json() if response.status_code == 200 else []

                if markets:
                    print(f"\n{tag_name.upper()} (tag_id={tag_id}):")
                    for i, m in enumerate(markets[:3], 1):
                        question = m.get("question", "")[:60]
                        volume = float(m.get("volumeNum") or 0)
                        print(f"  {i}. {question}... (${volume:,.0f})")
            else:
                print(f"\n{tag_name}: tag not found")


def test_sports_endpoint():
    """Test the /sports endpoint."""
    print("\n" + "=" * 60)
    print("SPORTS ENDPOINT")
    print("=" * 60)

    with httpx.Client() as client:
        response = client.get(f"{GAMMA_API_URL}/sports")
        sports = response.json() if response.status_code == 200 else []

    if sports:
        print(f"\nFound {len(sports)} sports\n")
        for s in sports[:10]:
            print(f"  ID: {s.get('id'):6} | {s.get('label', s.get('slug'))}")
            if s.get('tag_id'):
                print(f"         tag_id: {s.get('tag_id')}")


def main():
    print("Fetching markets from Polymarket...")
    markets = fetch_markets(limit=100)
    print(f"Fetched {len(markets)} markets\n")

    show_top_by_volume(markets, n=10)
    test_sports_endpoint()
    show_keyword_filtering()

    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    print("""
Tag-based filtering (tag_id) exists but tags are too specific.
RECOMMENDED: Use keyword-based filtering on fetched markets.

Implementation for V2:
1. Fetch 500 markets sorted by volume
2. Filter locally by keywords in question/description
3. Categories: Politics, Crypto, Finance, Sports, Tech
""")


if __name__ == "__main__":
    main()
