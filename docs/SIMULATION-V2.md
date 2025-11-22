# Simulation V2 - Batch Processing

## Current Workflow (cli.py)

1. Main menu → List/Run/Quit
2. Fetch top 50 markets, filter by volume (>$10k)
3. Display 15 markets
4. User selects ONE market
5. Run pipeline: Research → Generate Model → Monte Carlo → Visualization
6. Save results to `results/{session_id}/`

## Proposed V2 Changes

### New Menu Structure

```
News Scenario Simulator - Batch Mode

Options:
  1. Top 10 by Volume
  2. Top 10 Trending
  3. Breaking News Categories
     - Politics (10)
     - World (10)
     - Sports (10)
     - Crypto (10)
     - Finance (10)
  4. Custom Selection (manual pick N markets)
  5. Single Market (legacy mode)
  6. Quit
```

### Polymarket API Integration

Need to investigate:
- **Categories endpoint**: Does Polymarket expose category filtering?
- **Trending/Breaking**: https://polymarket.com/breaking - scrape or API?
- **Tags**: Markets have tags we can filter by

Likely approach:
```python
# Current: get_markets(limit=50) returns all active

# V2 additions needed in src/mcp_clients/polymarket.py:
def get_markets_by_category(category: str, limit: int = 10) -> list
def get_trending_markets(limit: int = 10) -> list
def get_breaking_news(category: str, limit: int = 10) -> list
```

### Batch Execution Flow

```python
async def run_single_market(market: dict, results_dir: Path) -> dict:
    """Run one simulation in its own sandbox."""
    sbx = await create_sandbox()
    try:
        research = await search(sbx, market['question'])
        code = await generate_model_async(...)
        result = await execute_monte_carlo(...)

        # Save immediately to local results
        market_dir = results_dir / slugify(market['question'][:50])
        market_dir.mkdir(parents=True, exist_ok=True)
        (market_dir / "model.py").write_text(code)
        (market_dir / "result.html").write_text(create_dashboard(...))

        return {'market': market, 'result': result, 'code': code}
    finally:
        sbx.kill()

async def run_batch_simulation(markets: list[dict], batch_name: str):
    """Run simulations in parallel - each in its own E2B sandbox."""

    # 1. Create results directory with clear name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("results") / f"{batch_name}_{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)

    # 2. Run ALL simulations in parallel (each gets own sandbox)
    tasks = [
        run_single_market(market, results_dir)
        for market in markets
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Generate batch summary dashboard
    batch_html = create_batch_dashboard(results)
    (results_dir / "summary.html").write_text(batch_html)

    # 4. Save batch metadata
    save_batch_report(results_dir, results)
```

### Results Structure

```
results/
  top10_volume_20241121_143022/
    summary.html                              # Overview of all 10 simulations
    batch_report.json                         # Machine-readable results
    will-trump-win-election/
      result.html
      model.py
    bitcoin-above-100k-by-december/
      result.html
      model.py
    fed-rate-cut-january/
      result.html
      model.py
    ...
```

Directory names use slugified question (first 50 chars) for clarity.

### Batch Dashboard

New visualization showing:
- Table of all markets with: Question | Market Odds | Simulation | Diff
- Sorted by largest discrepancy (potential alpha)
- Individual links to detailed views
- Summary stats: avg diff, biggest outliers

### Implementation Steps

1. **Phase 1: Polymarket Categories**
   - Investigate Polymarket API for categories/tags
   - Add filtering functions to `polymarket.py`
   - Test with manual category mapping if needed

2. **Phase 2: Batch Execution**
   - Modify `run_simulation()` → `run_batch_simulation()`
   - Add progress tracking for batch (1/10, 2/10, etc.)
   - Implement sandbox reuse across markets

3. **Phase 3: Batch Visualization**
   - Create `create_batch_dashboard()` in `viz/plotter.py`
   - Summary table with sortable columns
   - Aggregate statistics

4. **Phase 4: New CLI Menu**
   - Replace current menu with category-based options
   - Keep "single market" as legacy option
   - Add batch size configuration

### Parallel Execution

**Each market gets its own E2B sandbox:**
- True parallelism - all 10 run simultaneously
- ~3-5 min total for batch of 10 (vs 30 min sequential)
- Each sandbox isolated - no cross-contamination
- Results saved immediately as each completes
- Higher E2B cost but much faster turnaround

**Considerations:**
- Perplexity API rate limits (may need small delays)
- Anthropic API concurrent requests
- `asyncio.gather()` with `return_exceptions=True` for fault tolerance

### Configuration

```python
# src/config.py (new)
BATCH_CONFIG = {
    "default_batch_size": 10,
    "n_runs_batch_mode": 100,  # Fewer runs per market in batch
    "n_runs_single_mode": 200,
    "categories": {
        "politics": ["election", "government", "congress"],
        "crypto": ["bitcoin", "ethereum", "defi"],
        "sports": ["nfl", "nba", "soccer"],
        # ... tag mappings
    }
}
```

### Open Questions

1. Does Polymarket API support category filtering directly?
2. Do we need to scrape /breaking page for categories?
3. Should batch mode use fewer Monte Carlo runs per market (speed vs accuracy)?
4. Parallel sandbox execution worth the complexity?

### Next Steps

1. [ ] Research Polymarket API for categories/trending
2. [ ] Add batch execution to orchestrator
3. [ ] Create batch dashboard visualization
4. [ ] Update CLI with new menu
5. [ ] Test with batch of 10 markets
