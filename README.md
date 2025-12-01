# LLM Prediction Arena

**Benchmark LLMs on prediction market questions across three evaluation modes.**

Compare GPT-4o, Claude, Gemini on code generation, self-healing, and prediction accuracy against resolved Polymarket outcomes.

## Three Evaluation Modes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MODE           DESCRIPTION                         TOOLS AVAILABLE         │
├─────────────────────────────────────────────────────────────────────────────┤
│  direct         LLM predicts from knowledge alone   submit_prediction only  │
│                                                                             │
│  reasoning      Free Python computation             execute_code            │
│                 (math, statistics, heuristics)      install_package         │
│                                                     submit_prediction       │
│                                                                             │
│  simulation     Mesa agent-based modeling           generate_mesa_model     │
│                 with Monte Carlo + calibration      execute_code            │
│                                                     install_package         │
│                                                     submit_prediction       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Architecture

```
LOCAL MACHINE
├── Orchestrator (Python)
│   ├── Load questions from polymarket-downloader JSON
│   ├── For each (question, model, mode, trial):
│   │   1. Run arena_runner with OpenRouter API
│   │   2. Collect result JSON with metrics
│   │   3. Score with Brier Score
│   └── Save results + summary
│
└── OpenRouter API
    └── Routes to GPT-4o, Claude Sonnet, Gemini Flash

EVALUATION LOOP
├── Arena Runner
│   ├── System prompt (mode-specific)
│   ├── Tools: execute_code, install_package, submit_prediction
│   │   └── + generate_mesa_model (simulation mode only)
│   ├── Agent loop (up to 10 turns)
│   └── Metrics collection (tokens, cost, tool calls)
│
└── Self-Healing
    └── Model fixes own errors, retries up to 5x
```

## Metrics

| Metric | Description |
|--------|-------------|
| **Brier Score** | `(prediction - actual)²` — lower is better |
| **First-try Rate** | % where first execute_code succeeded |
| **Heal Rate** | % that succeeded after ≥1 failure |
| **Valid Rate** | % producing valid submit_prediction |
| **Avg Attempts** | Mean execute_code calls |
| **Cost** | Estimated USD from token usage |

## Quick Start

```bash
# Setup
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add: OPENROUTER_API_KEY

# Run quick test
PYTHONPATH=src python -m arena quick-test

# Run full evaluation
PYTHONPATH=src python -m arena run --models gpt-4o-mini --modes direct,reasoning,simulation

# Score existing results
PYTHONPATH=src python -m arena score results/arena/arena_results_*.json
```

## CLI Commands

```bash
# List available models
python -m arena list-models

# Run with specific models and modes
python -m arena run --models gpt-4o-mini,claude-sonnet-4 --modes simulation --trials 3

# Run with custom questions
python -m arena run --questions data/questions.json --max-questions 10
```

## Example Output

```
============================================================
ARENA SCORES
============================================================

MODEL: openai/gpt-4o-mini

  MODE: reasoning
    Runs: 1 (1 valid)
    Brier Score: 0.4356
    First-try Rate: 100.00%
    Avg Attempts: 2.0
    Avg Cost: $0.0010

  MODE: simulation
    Runs: 1 (1 valid)
    Brier Score: 0.2025
    First-try Rate: 100.00%
    Mesa Heal Rate: N/A
    Avg Attempts: 8.0
    Avg Cost: $0.0117
```

## Tech Stack

| Layer | Tech |
|-------|------|
| LLM Routing | **OpenRouter** (GPT-4o, Claude, Gemini) |
| Simulation | **Mesa 2.1.5** (agent-based modeling) |
| Data | **Polymarket** resolved outcomes |
| CLI | **Rich** + **argparse** |

## Project Structure

```
src/arena/
├── cli.py              # Entry point
├── orchestrator.py     # Main evaluation loop
├── scoring.py          # Brier score + metrics
├── models/
│   └── config.py       # Model definitions
└── runner/
    ├── arena_runner.py # Agent loop + OpenAI SDK
    ├── tools.py        # Tool definitions + handlers
    ├── hooks.py        # Metrics collection
    └── prompts.py      # Mode-specific prompts
```

---

## Roadmap / TODO

> **Status**: Early prototype. Not ready for production or public benchmarking claims.

The following items were identified as necessary before this can be considered a rigorous benchmark:

### Documentation & Methodology
- [ ] Document prompt formats, temperature, seeds for reproducibility
- [ ] Specify retry scoring rules and handling of non-numeric outputs
- [ ] Add methodology section explaining how predictions are elicited
- [ ] Create CHANGELOG tracking version history

### Data & Validity
- [ ] Expand question set from 5 to dozens+ with selection criteria
- [ ] Document question sourcing and resolution policy
- [ ] Publish full question list with resolution sources/timestamps
- [ ] Add held-out test split to prevent overfitting

### Metrics & Statistics
- [ ] Add confidence intervals / error bars to all metrics
- [ ] Report per-mode variability across trials
- [ ] Add calibration plots
- [ ] Define all metric thresholds precisely

### Testing & CI
- [ ] Add unit tests for parsing, normalization, scoring
- [ ] Add integration test running all modes on fixture data
- [ ] Set up CI pipeline with test gate
- [ ] Test retry logic edge cases

### Simulation Validity
- [ ] Add sanity tests for Mesa model correctness
- [ ] Add convergence checks for Monte Carlo
- [ ] Add baseline comparisons (naive, market-based)
- [ ] Add diagnostic plots for simulation outputs

### Production Hardening
- [ ] Document timeouts, rate limits, sandbox lifecycle
- [ ] Add health checks and fallback handling
- [ ] Document secrets management
- [ ] Add guardrails for infinite loops and runaway costs

### Reproducibility
- [ ] Pin all dependencies with lockfile
- [ ] Include exact model versions in results
- [ ] Seed all randomness
- [ ] Publish run scripts and artifact bundles

---

## Legacy: WorldSim Markets

This project evolved from WorldSim Markets, which used E2B sandboxes + Perplexity MCP for full simulation pipelines. The Arena module focuses specifically on LLM evaluation/benchmarking.

See `src/cli.py` for the original WorldSim implementation.
