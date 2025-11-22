# PolyFuture: Future Predictions for Nerds, Normies & Agents

### Get rich overnight: Know the future and bet safely on Polymarket

**"What if we could simulate the world 200 times before placing a bet?"**

AI world simulator: **Polymarket crowd odds** vs **AI-generated Monte Carlo forecasts**. Claude writes entire agent-based simulations from scratch, executes them in E2B sandboxes, compares results.

## The Pivot Story

Started as n8n → E2B workflow migration tool. OAuth hell killed that in 2 hours. New idea: **if we can run arbitrary code in E2B, why not run entire simulated worlds?**

## How It Works

```
┌─────────────────────────── ALL IN E2B SANDBOX ───────────────────────────┐
│                                                                          │
│  1. RESEARCH        Perplexity MCP → current events, key actors, data    │
│         ↓                                                                │
│  2. GENERATE        Claude Agent → writes complete Mesa simulation       │
│         ↓                                                                │
│  3. SELF-HEAL       Error? → Claude fixes code → retry (up to 5x)        │
│         ↓                                                                │
│  4. CALIBRATE       50 runs → find optimal threshold, fix low variance   │
│         ↓                                                                │
│  5. SIMULATE        200 Monte Carlo runs → probability distribution      │
│         ↓                                                                │
│  6. VISUALS         Show results, go bet a fortune                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
         ↓
    Compare with Polymarket odds → Interactive Plotly dashboard
```

**Key insight**: Claude doesn't tweak parameters—it writes **complete simulation code** with custom agents, behaviors, and outcome logic for each question. Runs them safely in sandboxes.

## Example: Ukraine-Russia Ceasefire

**Market**: "Ceasefire by end of 2025?" — Polymarket: 14%

**Step 1 - Perplexity MCP researches**:
> "Frontline status stalled. Trump administration pushing for negotiations. EU fatigue increasing. Russia holding occupied territories. Ukraine dependent on Western support..."

**Step 2 - Claude generates agents based on research**:
```python
class UkraineAgent:
    ceasefire_willingness = 0.2      # Low - wants territory back
    territorial_stance = 0.95        # High - won't concede
    western_support_dependency = 0.85

class RussiaAgent:
    ceasefire_willingness = 0.35     # Moderate - wants to lock gains
    territorial_demands = 0.85       # High
    military_position = 0.6

class WesternPowerAgent:
    support_level = 0.7              # Declining
    fatigue = 0.4                    # Rising
    pressure_for_ceasefire = 0.4     # Increasing

class InternationalMediatorAgent:
    diplomatic_pressure = 0.5
    negotiation_progress = 0.2
```

**Step 3 - Calibration** (50 runs): find optimal threshold

**Step 4 - Monte Carlo** (200 runs): **41% ± 7%**

**Result**: Simulation **+26.5pp** more optimistic than Polymarket crowd

📊 [View interactive result](results/20251121_214251/result.html) | 🐍 [View generated model](results/20251121_214251/model.py)

## Why This Matters

| Use Case | Value |
|----------|-------|
| **Safe execution** | LLM-generated code runs only in E2B sandbox, never locally |
| **Blueprint for more** | Same stack → benchmark builder, NPC tuner, scenario planner |

## Tech Stack

| Layer | Tech |
|-------|------|
| Sandbox | **E2B** (`sim-z-gateway` template) |
| MCP | **Perplexity** via E2B MCP Gateway (Docker HUB ) |
| LLM | **Claude** + **Claude Agent SDK** (Anthropic) |
| Simulation | **Mesa 2.1.5** (agent-based modeling) |
| Data | **Polymarket** Gamma/CLOB API |
| Viz | **Plotly** + **Rich** CLI |

## Self-Healing Loop

Generated code breaks? Autonomous fix cycle:

```
Execute → Error? → Claude analyzes stacktrace → Generates fix → Retry
                              ↑                              │
                              └──────── up to 5x ────────────┘
                                            │
                              Fallback to reference model if all fail
```

**Result**: Closed-loop autonomous code-generation + execution, not fire-and-pray.

## Quick Start

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add: ANTHROPIC_API_KEY, E2B_API_KEY, PERPLEXITY_API_KEY
python src/cli.py
```
> **Note:** You need an E2B template with MCP gateway pre-installed.

## Future Extensions
- **NPC tuner**: same stack for game AI (NPC) behavior optimization
- **Benchmark builder**: build benchmarks using AI generated code plus static data
- **Code evolution, arena**: Let Claude Agent optimize code and then let various versions compete against each other in sandboxes
