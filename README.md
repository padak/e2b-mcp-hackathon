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

### v1.0 MVP (7-Day Plan) - Codex Reviewed

#### Day 1: Data Collection
- [ ] Fetch 75-100 resolved Polymarket questions via polymarket-downloader
- [ ] Filter: volume >$100k, binary, resolved after Oct 2024
- [ ] Add difficulty categorization by final price spread:
  - Easy: >0.85 or <0.15 (strong consensus)
  - Medium: 0.15-0.35 or 0.65-0.85
  - Hard: 0.35-0.65 (uncertain)

#### Day 2: Reproducibility Infrastructure
- [ ] Add `temperature=0` for deterministic runs (single trial, not 3)
- [ ] Add leakage guard in prompts ("as of [date]" cutoff)
- [ ] Pin dependencies (`requirements.lock`)
- [ ] Add metadata to results (git commit, Python version, prompt version)

#### Day 2.5: Pilot Run
- [ ] Run pilot on 10 questions before full sweep
- [ ] Validate cost estimates and runtime
- [ ] Adjust if variance too high

#### Day 3-4: Full Evaluation
- [ ] Run 675-900 evals (75-100 questions × 3 models × 3 modes × 1 trial)
- [ ] Estimated cost: $40-55

#### Day 5: Analysis & Scoring
- [ ] Add baseline comparisons:
  - Trivial: always 0.5 → Brier = 0.25
  - Market: use final Polymarket price as prediction
- [ ] Use Wilcoxon signed-rank test (not paired t-test)
- [ ] Bootstrap 95% CI (10k resamples)
- [ ] Multiple comparison correction (Holm-Bonferroni)
- [ ] Report Brier by difficulty category (easy/medium/hard)

#### Day 6: Documentation
- [ ] Create `docs/METHODOLOGY.md` with full prompts
- [ ] Create CHANGELOG.md
- [ ] Add LICENSE (MIT)
- [ ] Create CITATION.cff

#### Day 7: Publication
- [ ] Git tag v1.0.0
- [ ] GitHub release with results bundle
- [ ] Announcements (HN, Twitter, Reddit) - after peer review

---

### v1.1 Roadmap (Post-Publication)

Based on community feedback:
- [ ] Expand to 200+ questions
- [ ] Add train/test split
- [ ] Add calibration curves
- [ ] Interactive leaderboard
- [ ] Additional models (Llama, Mistral)
- [ ] Price evolution analysis (volatility over time)
- [ ] CI/CD pipeline

---

### Technical Debt (Lower Priority)

#### Testing & CI
- [ ] Add unit tests for parsing, normalization, scoring
- [ ] Add integration test running all modes on fixture data
- [ ] Set up CI pipeline with test gate

#### Simulation Validity
- [ ] Add sanity tests for Mesa model correctness
- [ ] Add convergence checks for Monte Carlo
- [ ] Add diagnostic plots for simulation outputs

#### Production Hardening
- [ ] Document timeouts, rate limits, sandbox lifecycle
- [ ] Add guardrails for infinite loops and runaway costs

---

## Legacy: WorldSim Markets

This project evolved from WorldSim Markets, which used E2B sandboxes + Perplexity MCP for full simulation pipelines. The Arena module focuses specifically on LLM evaluation/benchmarking.

See `src/cli.py` for the original WorldSim implementation.
