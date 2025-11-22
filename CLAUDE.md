# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WorldSim Markets** - AI world simulator that compares Polymarket crowd odds vs AI-generated Monte Carlo forecasts.

**Flow** (all in E2B sandbox):
1. Perplexity MCP → research current events
2. Claude Agent → generate Mesa simulation code
3. Calibration (50 runs) → find threshold
4. Monte Carlo (200 runs) → probability distribution
5. Self-healing → fix errors, retry up to 5x

## Commands

```bash
# Setup
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run CLI
python src/cli.py

# Run tests
pytest                                    # All tests
pytest tests/test_phase6_generator.py    # Single test file
pytest -k "test_name"                    # Single test by name

# Quick test of orchestrator
python src/orchestrator.py
```

## Required Environment Variables

Create `.env` with:
```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514  # or other model
E2B_API_KEY=e2b_...
PERPLEXITY_API_KEY=pplx-...
POLYMARKET_API_KEY=...
POLYMARKET_SECRET=...
POLYMARKET_PASSPHRASE=...
```

## Architecture

```
src/
├── cli.py                    # Entry point - Rich-based interactive menu
├── orchestrator.py           # Main pipeline: Market → Research → Generate → Execute → Viz
├── mcp_clients/
│   ├── perplexity_client.py  # Perplexity search via E2B MCP gateway
│   └── polymarket.py         # Polymarket API (py-clob-client)
├── generator/
│   ├── prompts.py            # System prompts for Mesa code generation
│   ├── generator.py          # Claude generates complete Mesa models
│   └── fixer.py              # LLM fixes code errors (retry loop)
├── sandbox/
│   ├── runner.py             # E2B sandbox creation + Monte Carlo execution
│   └── retry.py              # Retry loop with error feedback
├── models/
│   └── economic_shock.py     # Fallback reference model
└── viz/
    └── plotter.py            # Plotly charts (simulation vs market odds)
```

## Key Patterns

### E2B Sandbox with MCP
- Uses custom E2B template `sim-zpicena-gateway` with Perplexity MCP pre-configured
- `create_sandbox()` returns sandbox with MCP gateway for Perplexity searches
- Code execution uses `sbx.run_code()` from e2b-code-interpreter

### LLM Model Generation
- `generate_model_async()` creates complete Mesa simulations from market questions
- Generated code must define `SimulationModel` class with `get_results()` and `run_monte_carlo()`
- `ANTHROPIC_MODEL` env var controls which Claude model to use

### Monte Carlo with Auto-Calibration
- Calibration pass (50 runs) determines threshold before full Monte Carlo
- Results return probability, 95% CI, and raw binary outcomes
- Fallback to `economic_shock.py` if generation fails after 5 retries

### Results
- Saved to `results/{timestamp}/` with `result.html` and `model.py`
- HTML contains interactive Plotly chart comparing simulation vs market odds
