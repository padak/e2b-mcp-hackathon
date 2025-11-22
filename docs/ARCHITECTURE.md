# Architecture - News Scenario Simulator

## High-Level Workflow

```mermaid
flowchart TD
    subgraph CLI["CLI Interface"]
        A[User selects category/markets]
    end

    subgraph Polymarket["Polymarket API"]
        B[Fetch markets by category/volume/search]
    end

    subgraph Batch["Batch Processing"]
        C[Create results directory]
        D[Run markets in parallel]
    end

    subgraph SingleMarket["Per-Market Pipeline"]
        E[Create E2B Sandbox with MCP]
        F[Perplexity Research via MCP Gateway]
        G[Claude generates Mesa model]
        H[Execute in E2B Sandbox]
        I{Success?}
        J[Claude fixes code]
        K[Calibration: 50 runs to find threshold]
        K2{Variance OK?}
        K3[Claude fixes variance]
        L[Monte Carlo: 200 runs]
        M[Create Plotly dashboard]
        N2[Save results]
    end

    subgraph Results["Output"]
        N[Individual result.html per market]
        O[Batch summary.html]
        P[batch_report.json]
    end

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I -->|Error max 5x| J
    J --> H
    I -->|Success| K
    K --> K2
    K2 -->|Low variance| K3
    K3 --> K
    K2 -->|OK| L
    L --> M
    M --> N2
    N2 --> N
    D -->|All complete| O
    O --> P
```

## Component Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI (cli.py)
    participant PM as Polymarket API
    participant E2B as E2B Sandbox
    participant MCP as MCP Gateway
    participant Perplexity
    participant Claude
    participant Mesa as Mesa Simulation

    User->>CLI: Select category
    CLI->>PM: Fetch markets
    PM-->>CLI: Market list

    User->>CLI: Confirm batch run

    loop For each market (parallel)
        CLI->>E2B: Create sandbox with MCP
        E2B-->>CLI: Sandbox ready

        CLI->>MCP: Research query
        MCP->>Perplexity: Ask
        Perplexity-->>MCP: Research data
        MCP-->>CLI: Research results

        CLI->>Claude: Generate Mesa model
        Claude-->>CLI: Python code

        CLI->>E2B: Execute code

        alt Execution fails
            E2B-->>CLI: Error
            CLI->>Claude: Fix code
            Claude-->>CLI: Fixed code
            CLI->>E2B: Retry execution
        end

        E2B->>Mesa: Run 200 trials
        Mesa-->>E2B: Results
        E2B-->>CLI: Monte Carlo output

        CLI->>CLI: Generate Plotly chart
        CLI->>CLI: Save result.html
    end

    CLI->>CLI: Generate summary.html
    CLI-->>User: Results directory
```

## Key Components

| Component | File | Purpose |
|-----------|------|---------|
| CLI | `src/cli.py` | Interactive menu, batch orchestration |
| Polymarket Client | `src/mcp_clients/polymarket.py` | Fetch prediction markets |
| MCP Client | `src/mcp_clients/perplexity_client.py` | Research via E2B MCP Gateway |
| Model Generator | `src/generator/generator.py` | Claude generates Mesa code |
| Sandbox Runner | `src/sandbox/runner.py` | E2B execution environment |
| Retry Loop | `src/sandbox/retry.py` | Self-fixing with error feedback |
| Visualization | `src/viz/plotter.py` | Plotly dashboards |

## Data Flow

```
Polymarket API
    ↓
[Markets with odds, volume]
    ↓
E2B Sandbox + MCP Gateway
    ↓
Perplexity Research
    ↓
[Context, news, statistics]
    ↓
Claude (Anthropic)
    ↓
[Mesa simulation code]
    ↓
E2B Execution (with retry)
    ↓
[Monte Carlo results]
    ↓
Plotly Visualization
    ↓
[HTML dashboard comparing simulation vs market]
```

## Self-Fixing Loop

The retry mechanism in `src/sandbox/retry.py`:

1. Execute generated code in E2B
2. If error occurs, send error + code to Claude
3. Claude analyzes and fixes the code
4. Retry execution (max 5 attempts)
5. If all retries fail, use fallback model

## Calibration & Simulation Modes

### Auto-Calibration (50 runs)

Before running the full Monte Carlo, the system runs 50 calibration trials to:

1. **Determine optimal threshold** - Sets threshold = mean of outcomes
2. **Check variance** - If std ≈ 0, model is deterministic (bad)
3. **Fix low variance** - Claude adjusts model to increase randomness

```python
calibration = {
    "min": 0.45,
    "max": 0.78,
    "mean": 0.62,      # → becomes THRESHOLD
    "std": 0.08        # must be > 0 for valid simulation
}
```

### Simulation Modes

**Threshold Mode** (default):
```python
success = outcome_value > threshold
# Binary: outcome above threshold = YES
```

**Probability Mode**:
```python
success = random.random() < outcome_value
# Treats outcome as probability, samples from it
```

Probability mode is useful when the model outputs a direct probability estimate rather than a score to threshold.

## Output Structure

```
results/
└── {category}_{timestamp}/
    ├── summary.html          # Batch overview
    ├── batch_report.json     # Full results data
    └── {market_slug}/
        ├── result.html       # Individual dashboard
        ├── model.py          # Generated Mesa code
        ├── research.txt      # Perplexity research
        └── execution.log     # Debug log
```
