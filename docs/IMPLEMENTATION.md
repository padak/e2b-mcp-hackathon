# Implementation Checklist - News Scenario Simulator

## Prerequisites (User Action Required)

### API Keys needed in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...      # Claude API
E2B_API_KEY=e2b_...               # E2B sandbox
PERPLEXITY_API_KEY=pplx-...       # Perplexity (used via MCP in E2B)
POLYMARKET_API_KEY=...            # Polymarket CLOB API
POLYMARKET_SECRET=...             # Polymarket secret
POLYMARKET_PASSPHRASE=...         # Polymarket passphrase
```

### Get API keys:
- **Anthropic**: https://console.anthropic.com/
- **E2B**: https://e2b.dev/dashboard
- **Perplexity**: https://www.perplexity.ai/settings/api
- **Polymarket**: https://polymarket.com/settings/api

---

## Phase 1: Project Setup

- [x] **1.1** Create project structure
  ```
  src/
  ├── mcp/           # MCP client wrapper
  ├── generator/     # LLM model generation
  ├── sandbox/       # E2B execution
  ├── viz/           # Visualization
  └── cli.py         # Entry point
  ```

- [x] **1.2** Create `requirements.txt`
  ```
  anthropic
  e2b
  mcp
  httpx
  pydantic
  plotly
  rich
  python-dotenv
  mesa
  numpy
  pandas
  py-clob-client
  ```

- [x] **1.3** Install dependencies in .venv
  ```bash
  pip install -r requirements.txt
  ```

- [x] **1.4** Verify `.env` has all API keys
  ```bash
  python -c "from dotenv import load_dotenv; import os; load_dotenv(); keys = ['ANTHROPIC_API_KEY', 'E2B_API_KEY', 'PERPLEXITY_API_KEY', 'POLYMARKET_API_KEY', 'POLYMARKET_SECRET', 'POLYMARKET_PASSPHRASE']; [print(f'{k}: {\"OK\" if os.getenv(k) else \"MISSING\"}') for k in keys]"
  ```

- [x] **1.5** Create `__init__.py` files for package imports
  ```bash
  touch src/__init__.py
  touch src/mcp/__init__.py
  touch src/generator/__init__.py
  touch src/sandbox/__init__.py
  touch src/viz/__init__.py
  touch src/models/__init__.py
  ```

---

## Phase 2: E2B Sandbox with MCP Gateway

- [x] **2.1** Create `src/sandbox/runner.py`
  - Create sandbox with Perplexity MCP enabled
  - Function: `create_sandbox() -> AsyncSandbox`
  ```python
  from e2b import AsyncSandbox

  sbx = await AsyncSandbox.create(
      mcp={
          "perplexityAsk": {
              "perplexityApiKey": os.getenv("PERPLEXITY_API_KEY"),
          },
      }
  )
  ```

- [x] **2.2** Test E2B + MCP connection
  ```python
  # Get MCP URL and token
  mcp_url = sbx.get_mcp_url()
  mcp_token = await sbx.get_mcp_token()
  print(f"MCP Gateway: {mcp_url}")
  ```

- [x] **2.3** Test code execution in sandbox
  ```python
  result = await sbx.commands.run('python3 -c "print(\'Hello from E2B\')"')
  # Should print "Hello from E2B"
  ```

- [x] **2.4** Test Mesa in sandbox
  ```python
  await sbx.commands.run('pip install mesa plotly pandas numpy')
  result = await sbx.commands.run('''python3 -c "
  from mesa import Agent, Model
  print('Mesa works!')
  "''')
  ```

---

## Phase 3: Perplexity MCP Client

- [x] **3.1** Create `src/mcp/client.py`
  - Connect to E2B MCP gateway from outside sandbox
  ```python
  from mcp.client.session import ClientSession
  from mcp.client.streamable_http import streamablehttp_client

  async with streamablehttp_client(
      url=sandbox.get_mcp_url(),
      headers={"Authorization": f"Bearer {await sandbox.get_mcp_token()}"},
  ) as (read_stream, write_stream, _):
      async with ClientSession(read_stream, write_stream) as session:
          await session.initialize()
          tools = await session.list_tools()
  ```

- [x] **3.2** Create wrapper for Perplexity search
  - Function: `search(query: str) -> str`
  - Call `perplexity-ask-perplexity_ask` tool via MCP

- [x] **3.3** Test Perplexity via MCP
  ```python
  result = await search(sbx, "Fed interest rate decision December 2024")
  # Should return relevant news/data from Perplexity
  ```

---

## Phase 4: Polymarket Client

- [x] **4.1** Create `src/mcp/polymarket.py`
  - Use official `py-clob-client`
  - Function: `get_markets() -> list[Market]`
  - Function: `get_market_details(condition_id: str) -> MarketDetails`
  ```python
  from py_clob_client.client import ClobClient
  from py_clob_client.clob_types import ApiCreds

  # Initialize client
  client = ClobClient(
      host="https://clob.polymarket.com",
      chain_id=137,  # Polygon
      key=os.getenv("POLYMARKET_API_KEY"),
      creds=ApiCreds(
          api_key=os.getenv("POLYMARKET_API_KEY"),
          api_secret=os.getenv("POLYMARKET_SECRET"),
          api_passphrase=os.getenv("POLYMARKET_PASSPHRASE"),
      )
  )

  def get_markets():
      return client.get_markets()

  def get_market_details(condition_id: str):
      return client.get_market(condition_id)
  ```

- [x] **4.2** Test Polymarket API
  ```python
  markets = get_markets()
  # Should return list of active prediction markets
  print(f"Found {len(markets)} markets")

  # Get specific market
  market = get_market_details("0x...")
  print(f"Question: {market.question}")
  print(f"Outcomes: {market.tokens}")  # Yes/No with prices
  ```

- [x] **4.3** Create market selector
  - Filter by volume, category
  - Extract: question, outcome prices (odds), deadline
  - Format for display and LLM
  ```python
  def select_high_volume_markets(markets, min_volume=10000):
      return [m for m in markets if m.volume >= min_volume]

  def format_for_llm(market):
      return {
          "question": market.question,
          "yes_odds": market.tokens[0].price,  # 0-1
          "no_odds": market.tokens[1].price,
          "volume": market.volume,
          "end_date": market.end_date_iso
      }
  ```

---

## Phase 5: Reference Model (Fallback)

- [x] **5.1** Create `src/models/economic_shock.py`
  - Complete Mesa model for economic simulation
  - Agents: Investors, Consumers, Firms
  - Parameters: interest_rate, inflation, sentiment
  - Output: time series + final distribution

- [x] **5.2** Test reference model locally
  ```python
  from models.economic_shock import EconomicModel
  model = EconomicModel(interest_rate=5.5, num_agents=100)
  for _ in range(100):
      model.step()
  print(model.get_results())
  ```

- [x] **5.3** Test reference model in E2B
  - Uses `code-interpreter-v1` template (Python 3.12)
  - Installs from requirements.txt
  ```python
  code = open("src/models/economic_shock.py").read()
  result = await sbx.run_python(code + "\n\n# Run simulation\n...")
  ```

---

## Phase 6: LLM Model Generator

- [x] **6.1** Create `src/generator/prompts.py`
  - System prompt with Mesa examples
  - Output format specification
  - Constraints (max agents, required outputs)

- [x] **6.2** Create `src/generator/generator.py`
  - Function: `generate_model(topic: str, research: dict) -> str`
  - Uses Claude to generate complete Mesa code
  - Returns Python code as string

- [x] **6.3** Test model generation
  ```python
  code = generate_model(
      topic="Fed rate hike impact",
      research={"current_rate": 5.5, "inflation": 3.2}
  )
  # Should return valid Python/Mesa code
  ```

---

## Phase 7: Retry Loop & Monte Carlo

- [x] **7.1** Create `src/sandbox/retry.py`
  - Function: `execute_with_retry(sbx, code: str, max_retries: int = 5) -> Result`
  - On error: send error + code to LLM for fix
  - Return success result or fallback to reference model

- [x] **7.2** Monte Carlo wrapper
  - LLM generates code with `run_trial(seed) -> bool` function
  - Wrapper runs 200 trials with different seeds
  - Aggregates binary results into probability
  ```python
  def run_monte_carlo(run_trial_func, n_runs=200):
      results = [run_trial_func(seed) for seed in range(n_runs)]
      probability = sum(results) / len(results)
      return {
          "probability": probability,
          "n_runs": n_runs,
          "results": results,  # raw [0,1,1,0,...]
          "ci_95": 1.96 * (probability * (1-probability) / n_runs) ** 0.5
      }
  ```

- [x] **7.3** Create `src/generator/fixer.py`
  - Function: `fix_code(code: str, error: str) -> str`
  - LLM analyzes error and fixes code

- [x] **7.4** Test retry loop
  ```python
  # Intentionally broken code
  broken = "import mesa\nprint(undefined_var)"
  result = await execute_with_retry(sbx, broken)
  # Should fix and return working result (or fallback)
  ```

- [x] **7.5** Auto-calibrate threshold
  - Run calibration pass (50 runs) before full Monte Carlo
  - Analyze distribution: min, max, mean, std
  - Set threshold = mean (ensures ~50% variance)
  - If user specifies threshold, use that instead
  ```python
  def calibrate_threshold(sandbox, code: str, n_calibration: int = 50) -> float:
      """Run calibration to find optimal threshold."""
      outcomes = []
      for seed in range(n_calibration):
          model = run_single_trial(sandbox, code, seed)
          outcomes.append(model.final_outcome)

      return {
          "min": min(outcomes),
          "max": max(outcomes),
          "mean": np.mean(outcomes),
          "std": np.std(outcomes),
          "suggested_threshold": np.mean(outcomes)
      }

  def run_monte_carlo_with_calibration(sandbox, code: str,
                                        n_runs: int = 200,
                                        user_threshold: float = None):
      # 1. Calibrate
      calibration = calibrate_threshold(sandbox, code)
      threshold = user_threshold or calibration["suggested_threshold"]

      # 2. Run full Monte Carlo with calibrated threshold
      results = run_monte_carlo(sandbox, code, n_runs, threshold)
      results["calibration"] = calibration
      results["threshold_used"] = threshold
      return results
  ```

---

## Phase 8: Visualization

- [ ] **8.1** Create `src/viz/plotter.py`
  - Function: `create_chart(simulation: dict, market_odds: float) -> str`
  - Returns interactive HTML string

  **Chart spec:**
  - Histogram of simulation results (200 binary outcomes)
  - Vertical dashed line = Polymarket odds (e.g., 72%)
  - Annotation: "Polymarket: 72%"
  - Summary box in corner:
    - Simulation: 65% ± 6%
    - Market: 72%
    - Difference: -7pp
  - Title: market question

  ```python
  import plotly.graph_objects as go

  def create_chart(simulation: dict, market_odds: float, title: str) -> str:
      prob = simulation["probability"]
      ci = simulation["ci_95"]

      fig = go.Figure()
      # Histogram of results
      fig.add_trace(go.Histogram(x=simulation["results"], nbinsx=2))
      # Market odds line
      fig.add_vline(x=market_odds, line_dash="dash",
                    annotation_text=f"Market: {market_odds:.0%}")
      # Summary annotation
      fig.add_annotation(
          text=f"Simulation: {prob:.0%} ± {ci:.0%}<br>Market: {market_odds:.0%}",
          xref="paper", yref="paper", x=0.95, y=0.95
      )
      return fig.to_html()
  ```

- [ ] **8.2** Test visualization
  ```python
  html = create_chart(
      simulation={"probability": 0.65, "ci_95": 0.06, "results": [...]},
      market_odds=0.72,
      title="Will Fed cut rates in December?"
  )
  # Should create interactive HTML with histogram + market line
  ```

---

## Phase 9: Orchestrator

- [x] **9.1** Create `src/orchestrator.py`
  - Connects all components
  - Flow: Polymarket → Perplexity Research → Generate → Execute → Visualize

- [x] **9.2** Create `src/cli.py`
  - Interactive CLI with Rich
  - Menu: list markets, select market, run simulation
  - Display progress with Rich spinners/progress bars
  - Show result URL from E2B sandbox
  ```python
  from rich.console import Console
  from rich.prompt import Prompt

  console = Console()

  # Main menu
  def main():
      console.print("[bold]News Scenario Simulator[/bold]")

      # 1. List markets
      markets = get_markets()
      for i, m in enumerate(markets[:10]):
          console.print(f"{i+1}. {m.question} ({m.volume})")

      # 2. Select market
      choice = Prompt.ask("Select market", default="1")
      market = markets[int(choice)-1]

      # 3. Run pipeline
      with console.status("Researching..."):
          research = await perplexity_search(market.question)

      with console.status("Generating simulation..."):
          code = generate_model(market, research)

      with console.status("Running Monte Carlo (200 runs)..."):
          result = await execute_with_retry(sandbox, code)

      # 4. Serve result from E2B
      html = create_chart(result, market.yes_odds, market.question)
      await sandbox.files.write('/tmp/result.html', html)
      sandbox.commands.run('python -m http.server 8080 -d /tmp', background=True)

      host = sandbox.get_host(8080)
      console.print(f"\n[green bold]Result:[/green bold] https://{host}/result.html")
  ```

---

## Phase 10: End-to-End Test

- [ ] **10.1** Run full pipeline
  ```bash
  python src/cli.py
  ```
  - Select Polymarket topic
  - See research results
  - Watch simulation generate
  - View comparison chart

- [ ] **10.2** Test with 3 different markets
  - Economic (Fed rates)
  - Political (elections)
  - Other (crypto, sports)

- [ ] **10.3** Verify fallback works
  - Force LLM to fail 5 times
  - Should use reference model

---

## Phase 11: Demo Prep

- [ ] **11.1** Pre-select good Polymarket topic for demo
  - High volume market (>$100k)
  - Clear Yes/No question
  - Interesting for audience (Fed rates, elections, crypto)

- [ ] **11.2** Test full flow 3 times without errors

- [ ] **11.3** Record demo video

- [ ] **11.4** (Optional) Web UI extension
  - Simple Flask/FastAPI served from E2B
  - Form for market selection
  - Real-time progress updates
  - Embedded Plotly chart

---

## Blocking Points (Need User Input)

| Phase | Blocker | Action Required |
|-------|---------|-----------------|
| 1.4 | Missing API keys | Add keys to `.env` |
| 3.3 | Perplexity rate limit | Check API quota |
| 4.2 | Polymarket API issues | Test API access |
| 10.1 | Demo market selection | User picks Polymarket market |

---

## Quick Commands

```bash
# Setup
pip install -r requirements.txt

# Test E2B + MCP
python -c "
import asyncio
from e2b import AsyncSandbox
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    sbx = await AsyncSandbox.create(
        mcp={'perplexityAsk': {'perplexityApiKey': os.getenv('PERPLEXITY_API_KEY')}}
    )
    print('MCP URL:', sbx.get_mcp_url())
    result = await sbx.run_python('print(1+1)')
    print('Result:', result.text)
    await sbx.kill()

asyncio.run(test())
"

# Run full demo
python src/cli.py
```

---

## Architecture Notes

### E2B MCP Gateway
- Perplexity runs as MCP server INSIDE E2B sandbox
- We connect to it from OUTSIDE via `sandbox.get_mcp_url()`
- This satisfies hackathon requirement: "MCP from Docker Hub inside E2B sandbox"

### Flow
```
Outside E2B                    Inside E2B Sandbox
-----------                    ------------------

Polymarket API
    ↓
CLI → Orchestrator            Perplexity MCP Server
         ↓                           ↑
    MCP Client  ─────────────→  MCP Gateway
         ↓                           ↓
    LLM Generator              Mesa Simulation
         ↓                           ↓
    Code String  ─────────────→  run_python()
         ↓                           ↓
    Visualization  ←──────────  Results/Charts
    (Simulation vs Market Odds)
```
