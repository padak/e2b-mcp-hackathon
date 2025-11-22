# Demo Script (< 2 minutes)

## Pre-Demo Setup
- Have terminal ready with venv activated
- Have `.env` configured
- Have browser ready to show result

---

## Demo Flow

### 0:00-0:10 - Intro (10s)
> "News Scenario Simulator - comparing prediction market odds with AI-generated Monte Carlo simulations"

Show terminal, run:
```bash
python src/cli.py
```

### 0:10-0:25 - Market Selection (15s)
> "We fetch live markets from Polymarket - real money, real odds"

- Option 1: List markets
- Show table with questions, odds, volume
- Select a market (pick something interesting - political, economic)

### 0:25-0:45 - Research Phase (20s)
> "Perplexity researches the topic via MCP running inside E2B sandbox"

- Watch "Researching with Perplexity..." spinner
- Briefly mention: "This is MCP from Docker Hub, hosted in E2B"

### 0:45-1:05 - Code Generation (20s)
> "Claude generates a complete Mesa simulation - not just parameters, but actual agent classes"

- Watch "Generating simulation model..." spinner
- Mention: "It creates custom agents for this specific question - investors, policymakers, whatever fits"

### 1:05-1:35 - Monte Carlo Execution (30s)
> "E2B sandbox executes 200 Monte Carlo runs with auto-calibration"

- Watch "Running Monte Carlo (200 runs)..." progress
- Mention: "The simulation runs in a secure E2B sandbox with self-healing - if code fails, it retries with error feedback"

### 1:35-1:55 - Results (20s)
> "And here's the comparison"

- Show the result panel in terminal (Simulation % vs Market %)
- Open the HTML result in browser
- Point out:
  - Convergence chart (confidence narrows over runs)
  - Final comparison: Simulation vs Polymarket
  - Difference in percentage points

### 1:55-2:00 - Wrap-up (5s)
> "AI simulation meets crowd wisdom - all running in E2B with Perplexity MCP"

---

## Key Points to Hit

1. **E2B Sandbox** - "Code executes securely in E2B"
2. **MCP from Docker Hub** - "Perplexity via MCP Gateway"
3. **Dynamic Generation** - "LLM writes entire simulation, not just config"
4. **Self-Healing** - "Retry loop fixes errors automatically"
5. **Real Data** - "Live Polymarket odds, real money at stake"

## Backup Plans

If something fails during demo:
- Show pre-recorded results in `results/` folder
- Open existing `result.html` to show visualization
- Explain the architecture from README

## Best Markets for Demo

Pick markets that are:
- Easy to understand (Fed rates, elections, crypto)
- High volume (>$100k)
- Not too long question text
- Binary outcome (Yes/No)
