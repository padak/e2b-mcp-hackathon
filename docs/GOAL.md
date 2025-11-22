# News Scenario Simulator

AI agent that generates simulations from prediction markets and compares results with crowd wisdom.

## Concept

**Input**: Polymarket prediction market (e.g., "Will Fed cut rates in December?")
**Output**: Monte Carlo simulation vs market odds visualization

## Flow

```
Polymarket → Pick market with real $ odds
                    ↓
         Perplexity → Research context/data
                    ↓
         Claude → Generate Mesa simulation code
                    ↓
         E2B → Execute simulation (retry if fails)
                    ↓
         Plotly → Compare: Simulation dist vs Market odds
```

## Key Features

1. **Dynamic Code Generation** - LLM writes complete Mesa simulations
2. **Self-Healing** - Retry loop with error feedback
3. **Market Comparison** - AI prediction vs crowd wisdom
4. **Safe Execution** - E2B sandbox isolation

## Tech Stack

- **Data**: Polymarket API, Perplexity MCP
- **AI**: Claude (Anthropic)
- **Simulation**: Mesa (agent-based modeling)
- **Execution**: E2B sandbox
- **Viz**: Plotly

## Example Output

```
Topic: "Fed rate cut December 2024"

Polymarket odds: 72% Yes

Simulation result:
  Mean: 65%
  Std: 8%
  Range: [48%, 82%]

→ Market is slightly more bullish than simulation
```
