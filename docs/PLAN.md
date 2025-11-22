# News Scenario Simulator

AI-powered tool that generates and runs simulations based on prediction markets and news. Uses LLMs to dynamically generate complete Mesa simulation models, executes them in E2B sandboxes, and compares results with Polymarket odds.

## Core Concept

```
Polymarket → Pick topic with real odds
                    ↓
         Perplexity → Research context
                    ↓
         LLM → Generate Mesa simulation
                    ↓
         E2B → Execute Monte Carlo runs
                    ↓
         Viz → Compare simulation vs market odds
```

**Key Innovation**: LLM generates entire simulation code on-the-fly, not just parameters. Compares AI simulation with crowd wisdom (Polymarket).

## Architecture

### Data Sources
- **Polymarket API** - Active prediction markets with real odds
- **Perplexity** - Research and context for simulation parameters

### Core Components
- **E2B Sandbox** - Secure execution of generated code
- **LLM Generator** - Claude generates complete Mesa models
- **Retry Loop** - Self-healing with error feedback (max 5 attempts)
- **Reference Model** - Economic Shock fallback when generation fails

### Output
- **Plotly Chart** - Simulation distribution vs Polymarket odds
- **HTML Export** - Embeddable visualization

## Technical Flow

### 1. Topic Selection (Polymarket)
```python
# Get active markets
markets = polymarket.get_markets()

# Select high-volume market
market = select_market(markets)
# Returns: question, odds, deadline, volume
```

### 2. Research (Perplexity)
```python
# Get context for simulation
research = perplexity.research(market.question, [
    "current relevant data",
    "historical trends",
    "key factors"
])
```

### 3. Model Generation (LLM)
```python
# Generate complete Mesa model
code = generator.generate_model(
    topic=market.question,
    market_odds=market.odds,
    research=research
)
# Returns: Python code with Mesa agents, behaviors, metrics
```

### 4. Execution (E2B)
```python
# Run with retry loop
result = sandbox.execute_with_retry(
    code=code,
    max_retries=5,
    fallback=reference_model
)
# Returns: simulation results or fallback
```

### 5. Visualization
```python
# Compare simulation vs market
html = viz.create_comparison(
    simulation=result.distribution,
    market_odds=market.odds,
    title=market.question
)
```

## Components

### Polymarket Client
- `get_markets()` - List active prediction markets
- `get_market_details(id)` - Get odds, volume, deadline
- Filter by volume, category, deadline

### Perplexity Client
- `search(query)` - News and current data
- `research(topic, questions)` - Structured research
- Response caching for reliability

### LLM Generator
- System prompt with Mesa examples
- Output format: complete runnable Python
- Constraints: max 500 agents, required metrics
- Error fixing capability

### E2B Runner
- Code execution with timeout (30s)
- Capture stdout, stderr, files
- Retry loop with error feedback
- Fallback to reference model

### Visualization
- Plotly histogram: simulation distribution
- Overlay: Polymarket odds as vertical line
- Export: HTML for embedding

## Reference Model

Economic Shock model as fallback:
- Agents: Investors, Consumers, Firms
- Parameters: interest_rate, inflation, sentiment
- Output: probability distribution

Used when LLM generation fails after 5 retries.

## File Structure

```
src/
├── mcp/
│   ├── polymarket.py    # Polymarket API client
│   └── perplexity.py    # Perplexity research
├── generator/
│   ├── prompts.py       # System prompts
│   ├── generator.py     # Model generation
│   └── fixer.py         # Error fixing
├── sandbox/
│   ├── runner.py        # E2B execution
│   └── retry.py         # Retry loop
├── models/
│   └── economic_shock.py # Reference fallback
├── viz/
│   └── plotter.py       # Plotly charts
├── orchestrator.py      # Main pipeline
└── cli.py               # Entry point
```

## Dependencies

```python
# Core
anthropic              # Claude API
e2b                    # Sandbox execution
mcp                    # MCP client
httpx                  # HTTP client

# Simulation
mesa                   # Agent-based modeling
numpy                  # Numerical computing
pandas                 # Data manipulation

# Visualization
plotly                 # Interactive charts

# Utilities
pydantic               # Data validation
rich                   # CLI formatting
python-dotenv          # Environment
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM generates buggy code | Retry loop with error feedback |
| Model doesn't converge | Max iterations, E2B timeout |
| All retries fail | Fallback to reference model |
| Perplexity rate limits | Response caching |
| Polymarket API issues | Cached market data |

## Success Criteria

1. **Works end-to-end** - Polymarket → Simulation → Visualization
2. **Self-healing** - Retry loop fixes LLM errors
3. **Meaningful output** - Simulation vs market comparison
4. **Reliable demo** - Fallback ensures it always works

## Demo Flow

1. Select Polymarket topic (e.g., "Fed rate cut December")
2. Show market odds (e.g., 72% Yes)
3. Research context via Perplexity
4. Generate Mesa simulation
5. Run Monte Carlo in E2B
6. Display: "Simulation: 65% ± 8% vs Market: 72%"
7. Discuss difference

## Competitive Advantages

1. **Dynamic generation** - LLM creates custom simulations
2. **Market validation** - Compare with real prediction markets
3. **Self-healing** - AI fixes its own bugs
4. **Safe execution** - E2B sandbox isolation

## Extensions

- Multiple markets comparison
- Historical backtesting
- Sensitivity analysis
- Automated reporting
- API endpoint
