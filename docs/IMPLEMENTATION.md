# Implementation Checklist - News Scenario Simulator

## Prerequisites (User Action Required)

### API Keys needed in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...      # Claude API
E2B_API_KEY=e2b_...               # E2B sandbox
PERPLEXITY_API_KEY=pplx-...       # Perplexity (used via MCP in E2B)
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
  ├── mcp/           # MCP client wrapper
  ├── generator/     # LLM model generation
  ├── sandbox/       # E2B execution
  ├── viz/           # Visualization
  └── cli.py         # Entry point
  ```

- [ ] **1.2** Create `requirements.txt`
  ```
  anthropic
  e2b
  mcp
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

## Phase 2: E2B Sandbox with MCP Gateway

- [ ] **2.1** Create `src/sandbox/runner.py`
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

- [ ] **2.2** Test E2B + MCP connection
  ```python
  # Get MCP URL and token
  mcp_url = sbx.get_mcp_url()
  mcp_token = await sbx.get_mcp_token()
  print(f"MCP Gateway: {mcp_url}")
  ```

- [ ] **2.3** Test code execution in sandbox
  ```python
  result = await sbx.run_python('print("Hello from E2B")')
  # Should print "Hello from E2B"
  ```

- [ ] **2.4** Test Mesa in sandbox
  ```python
  await sbx.run_python('!pip install mesa plotly pandas')
  result = await sbx.run_python('''
  from mesa import Agent, Model
  print("Mesa works!")
  ''')
  ```

---

## Phase 3: Perplexity MCP Client

- [ ] **3.1** Create `src/mcp/client.py`
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

- [ ] **3.2** Create wrapper for Perplexity search
  - Function: `search(query: str) -> str`
  - Call `perplexity_ask` tool via MCP

- [ ] **3.3** Test Perplexity via MCP
  ```python
  result = await search("Fed interest rate decision December 2024")
  # Should return relevant news/data from Perplexity
  ```

---

## Phase 4: Polymarket Client

- [ ] **4.1** Create `src/mcp/polymarket.py`
  - Function: `get_markets() -> list[Market]`
  - Function: `get_market_details(market_id: str) -> MarketDetails`
  - Use httpx for API calls (no auth needed)
  ```python
  # Polymarket CLOB API
  BASE_URL = "https://clob.polymarket.com"

  async def get_markets():
      async with httpx.AsyncClient() as client:
          resp = await client.get(f"{BASE_URL}/markets")
          return resp.json()
  ```

- [ ] **4.2** Test Polymarket API
  ```python
  markets = await get_markets()
  # Should return list of active prediction markets
  print(f"Found {len(markets)} markets")
  ```

- [ ] **4.3** Create market selector
  - Filter by volume, category
  - Extract: question, odds, deadline
  - Format for display and LLM

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
  result = await sbx.run_python(code + "\n\n# Run simulation\n...")
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
  - Function: `execute_with_retry(sbx, code: str, max_retries: int = 5) -> Result`
  - On error: send error + code to LLM for fix
  - Return success result or fallback to reference model

- [ ] **7.2** Create `src/generator/fixer.py`
  - Function: `fix_code(code: str, error: str) -> str`
  - LLM analyzes error and fixes code

- [ ] **7.3** Test retry loop
  ```python
  # Intentionally broken code
  broken = "import mesa\nprint(undefined_var)"
  result = await execute_with_retry(sbx, broken)
  # Should fix and return working result (or fallback)
  ```

---

## Phase 8: Visualization

- [ ] **8.1** Create `src/viz/plotter.py`
  - Function: `create_chart(simulation: dict) -> str`
  - Plotly chart showing simulation distribution
  - Returns HTML string

- [ ] **8.2** Test visualization
  ```python
  html = create_chart(
      simulation={"mean": 0.65, "std": 0.1, "samples": [...]}
  )
  # Should create HTML file with interactive chart
  ```

---

## Phase 9: Orchestrator

- [ ] **9.1** Create `src/orchestrator.py`
  - Connects all components
  - Flow: Polymarket → Perplexity Research → Generate → Execute → Visualize

- [ ] **9.2** Create `src/cli.py`
  - Interactive CLI with Rich
  - Input topic/question
  - Display progress
  - Open visualization

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

- [ ] **11.1** Cache Perplexity responses for demo reliability

- [ ] **11.2** Pre-select good Polymarket topic for demo

- [ ] **11.3** Test full flow 3 times without errors

- [ ] **11.4** Record demo video

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
