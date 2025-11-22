# Implementation Checklist - News Scenario Simulator

## Prerequisites (User Action Required)

### API Keys needed in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...      # Claude API
E2B_API_KEY=e2b_...               # E2B sandbox
PERPLEXITY_API_KEY=pplx-...       # Perplexity MCP
```

### Get API keys:
- **Anthropic**: https://console.anthropic.com/
- **E2B**: https://e2b.dev/dashboard
- **Perplexity**: https://www.perplexity.ai/settings/api

---

## Phase 1: Project Setup

- [ ] **1.1** Create project structure
  ```
  src/
  ├── mcp/           # MCP client
  ├── generator/     # LLM model generation
  ├── sandbox/       # E2B execution
  ├── viz/           # Visualization
  └── cli.py         # Entry point
  ```

- [ ] **1.2** Create `requirements.txt`
  ```
  anthropic
  e2b-code-interpreter
  httpx
  pydantic
  plotly
  rich
  python-dotenv
  ```

- [ ] **1.3** Install dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **1.4** Verify `.env` has all API keys
  ```bash
  python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('ANTHROPIC:', 'OK' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING'); print('E2B:', 'OK' if os.getenv('E2B_API_KEY') else 'MISSING'); print('PERPLEXITY:', 'OK' if os.getenv('PERPLEXITY_API_KEY') else 'MISSING')"
  ```

---

## Phase 2: E2B Sandbox Runner

- [ ] **2.1** Create `src/sandbox/runner.py`
  - Function: `run_code(code: str) -> ExecutionResult`
  - Install Mesa, Plotly, pandas in sandbox
  - Capture stdout, stderr, files
  - 30 second timeout

- [ ] **2.2** Test E2B connection
  ```python
  # Should print "Hello from E2B"
  result = run_code('print("Hello from E2B")')
  ```

- [ ] **2.3** Test Mesa in sandbox
  ```python
  # Should run without error
  result = run_code('''
  from mesa import Agent, Model
  print("Mesa works!")
  ''')
  ```

---

## Phase 3: Perplexity MCP Client

- [ ] **3.1** Create `src/mcp/perplexity.py`
  - Function: `search(query: str) -> str`
  - Function: `research(topic: str, questions: list) -> dict`
  - Use httpx for API calls

- [ ] **3.2** Test Perplexity search
  ```python
  result = search("Fed interest rate decision December 2024")
  # Should return relevant news/data
  ```

- [ ] **3.3** Test Perplexity research
  ```python
  result = research("interest rates", [
      "current federal funds rate",
      "inflation rate",
      "unemployment rate"
  ])
  # Should return structured data
  ```

---

## Phase 4: Polymarket Integration

- [ ] **4.1** Create `src/mcp/polymarket.py`
  - Function: `get_markets() -> list[Market]`
  - Function: `get_market_details(market_id: str) -> MarketDetails`
  - Parse odds, volume, deadline

- [ ] **4.2** Test Polymarket API
  ```python
  markets = get_markets()
  # Should return list of active prediction markets
  ```

- [ ] **4.3** Create topic selector
  - Pick market with high volume
  - Extract question, odds, deadline
  - Format for LLM

---

## Phase 5: Reference Model (Fallback)

- [ ] **5.1** Create `src/models/economic_shock.py`
  - Complete Mesa model for economic simulation
  - Agents: Investors, Consumers, Firms
  - Parameters: interest_rate, inflation, sentiment
  - Output: time series + final distribution

- [ ] **5.2** Test reference model locally
  ```python
  from models.economic_shock import EconomicModel
  model = EconomicModel(interest_rate=5.5, num_agents=100)
  for _ in range(100):
      model.step()
  print(model.get_results())
  ```

- [ ] **5.3** Test reference model in E2B
  ```python
  code = open("src/models/economic_shock.py").read()
  result = run_code(code + "\n\n# Run simulation\n...")
  ```

---

## Phase 6: LLM Model Generator

- [ ] **6.1** Create `src/generator/prompts.py`
  - System prompt with Mesa examples
  - Output format specification
  - Constraints (max agents, required outputs)

- [ ] **6.2** Create `src/generator/generator.py`
  - Function: `generate_model(topic: str, research: dict) -> str`
  - Uses Claude to generate complete Mesa code
  - Returns Python code as string

- [ ] **6.3** Test model generation
  ```python
  code = generate_model(
      topic="Fed rate hike impact",
      research={"current_rate": 5.5, "inflation": 3.2}
  )
  # Should return valid Python/Mesa code
  ```

---

## Phase 7: Retry Loop

- [ ] **7.1** Create `src/sandbox/retry.py`
  - Function: `execute_with_retry(code: str, max_retries: int = 5) -> Result`
  - On error: send error + code to LLM for fix
  - Return success result or fallback to reference model

- [ ] **7.2** Create `src/generator/fixer.py`
  - Function: `fix_code(code: str, error: str) -> str`
  - LLM analyzes error and fixes code

- [ ] **7.3** Test retry loop
  ```python
  # Intentionally broken code
  broken = "import mesa\nprint(undefined_var)"
  result = execute_with_retry(broken)
  # Should fix and return working result (or fallback)
  ```

---

## Phase 8: Visualization

- [ ] **8.1** Create `src/viz/plotter.py`
  - Function: `create_comparison_chart(simulation: dict, market_odds: float) -> str`
  - Plotly chart comparing simulation distribution vs Polymarket
  - Returns HTML string

- [ ] **8.2** Test visualization
  ```python
  html = create_comparison_chart(
      simulation={"mean": 0.65, "std": 0.1, "samples": [...]},
      market_odds=0.72
  )
  # Should create HTML file with interactive chart
  ```

---

## Phase 9: Orchestrator

- [ ] **9.1** Create `src/orchestrator.py`
  - Connects all components
  - Flow: Polymarket → Research → Generate → Execute → Visualize

- [ ] **9.2** Create `src/cli.py`
  - Interactive CLI with Rich
  - Show market selection
  - Display progress
  - Open visualization

---

## Phase 10: End-to-End Test

- [ ] **10.1** Run full pipeline
  ```bash
  python src/cli.py
  ```
  - Select a Polymarket topic
  - See research results
  - Watch simulation generate
  - View comparison chart

- [ ] **10.2** Test with 3 different topics
  - Economic (Fed rates)
  - Political (election)
  - Other (crypto, sports)

- [ ] **10.3** Verify fallback works
  - Force LLM to fail 5 times
  - Should use reference model

---

## Phase 11: Demo Prep

- [ ] **11.1** Cache Perplexity responses for demo reliability

- [ ] **11.2** Pre-select good Polymarket topic for demo

- [ ] **11.3** Test full flow 3 times without errors

- [ ] **11.4** Record 90-second demo video

---

## Blocking Points (Need User Input)

| Phase | Blocker | Action Required |
|-------|---------|-----------------|
| 1.4 | Missing API keys | Add keys to `.env` |
| 3.2 | Perplexity rate limit | Check API quota |
| 4.2 | Polymarket API issues | May need to scrape instead |
| 10.1 | Demo topic selection | User picks market |

---

## Quick Commands

```bash
# Setup
pip install -r requirements.txt

# Test E2B
python -c "from src.sandbox.runner import run_code; print(run_code('print(1+1)'))"

# Test Perplexity
python -c "from src.mcp.perplexity import search; print(search('test'))"

# Run full demo
python src/cli.py

# Run with specific topic
python src/cli.py --market "fed-rate-december"
```
