## **High-Level Tech Overview (for colleague)**

### **LLM Prediction Arena \- 1 Pager**

**What is it?**

A benchmark that tests how well different AI models can write code, fix their own errors, and make accurate predictions.

**How it works:**

1. We give AI models real prediction questions from Polymarket (betting market) that have already resolved \- so we know the right answer.  
2. Each model runs inside a secure sandbox (E2B) and tries two approaches:  
   * **Direct:** Just think and predict  
   * **Simulation:** Write Python code to simulate/model the outcome  
3. When code fails (missing library, bug, etc.), the model must recognize the error and fix it. We call this "self-healing."  
4. We use Claude's Agent SDK as the scaffolding, but swap the underlying model via proxy (Claude, GPT-4, Gemini, DeepSeek).

**What we measure:**

| Metric | What it tells us |
| ----- | ----- |
| Brier Score | How accurate are predictions vs reality |
| First-try Rate | How often code runs without errors |
| Heal Rate | How often model recovers from errors |
| Attempts | How many tries needed to get working code |

**Tech stack:**

* **E2B** \- Secure sandbox to run AI-generated code  
* **Claude Agent SDK** \- Agent framework (tool use, loops)  
* **Castari Proxy** \- Routes to different LLM providers (or @musistudio/claude-code-router)  
* **Polymarket data** \- Ground truth for predictions

**Output:**

Leaderboard showing which model performs best across all metrics.

```
╔═══════════════╦═══════════════╗
║ Model           ║ Brier║ First-try % ║ Heal Rate ║
╠═══════════════╬═══════════════╣
║ Claude Sonnet   ║0.12  ║    72%      ║    94%    ║
║ GPT-4o          ║0.15  ║    68%      ║    89%    ║
║ Gemini 1.5 Pro  ║0.18  ║    61%      ║    82%    ║
╚═══════════════╩════════╩══════╝
```

---

## 

## **LLM Prediction Arena \- Requirements & Modules**

**Purpose:** Handoff document for AI engineer to build PRD **Status:** Draft for review

---

### **Why**

We want to answer: **"Same agentic scaffolding, which model brain performs best?"**

No existing benchmark combines:

* Agentic code generation  
* Self-healing (fixing own errors)  
* Real-world prediction accuracy  
* Multi-model comparison on identical tasks

Polymarket resolved questions give us ground truth to measure against.

---

### **What**

An arena where Claude Agent SDK runs prediction tasks using different underlying models (via proxy \- @musistudio/claude-code-router or other). Each model attempts two approaches per question:

1. **Direct** \- Reason and predict (no code)  
2. **Simulation** \- Write code, execute, predict from results

We measure: prediction accuracy, code quality, self-healing success.

---

### **High-Level Flow**

```
Human runs command locally
        │
        ▼
┌─────────────────┐
│  Orchestrator      │  ← Spawns E2B sandbox, uploads arena code
└────────┬────────┘
         │
         ▼
┌───────────────────────────────────────────────────────────────────────┐
│              E2B Sandbox                                                           │
│                                                                                    │
│   Claude Agent SDK                                                                 │
│      │                                                                             │
│      ├──→ Castari Proxy (@musistudio/claude-code-router) ──→ Any LLM            │
│      │                                                                             │
│      └──→ Tools: execute_code, submit_result                                      │
│                                                                                    │
│   Agent loops until prediction submitted                                           │
│                                                                                    │                                  
└───────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Results JSON      │  ← Collected locally
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Scorer           │  ← Generates leaderboard
└─────────────────┘
```

---

### **Modules**

#### **1\. Orchestrator (Local)**

**Why:** Need something to spawn sandboxes, upload code, collect results.

**What:**

* Reads question file  
* Spins up vanilla E2B sandbox  
* Uploads arena code  
* Passes config (model, question, API keys)  
* Runs arena\_runner  
* Collects result JSON  
* Saves to local results folder

**How:**

```
load question from file
create e2b sandbox (vanilla)
upload arena/ folder to sandbox
set environment variables (API keys)
run "python arena_runner.py <input_json>"
capture output JSON
save to results/{question_id}_{model}.json
destroy sandbox
```

---

#### **2\. Arena Runner (E2B)**

**Why:** Entry point inside sandbox. Orchestrates the agent run.

**What:**

* Receives question \+ model config  
* Installs base dependencies  
* Creates Claude Agent with specified model (via proxy)  
* Gives agent the task (direct mode first, then simulation)  
* Wraps tool calls with logging  
* Returns structured result

**How:**

```
parse input config
install dependencies (anthropic, etc.)

# Direct mode
agent = create_agent(model, tools=[submit_prediction])
direct_result = agent.run(direct_task_prompt)

# Simulation mode  
agent = create_agent(model, tools=[execute_code, submit_prediction])
simulation_result = agent.run(simulation_task_prompt)

return {
    question_id,
    model,
    direct: direct_result,
    simulation: simulation_result
}
```

---

#### **3\. Agent Tools (E2B)**

**Why:** Agent needs capabilities. Tools define what agent can do.

**What:** Three tools the agent can call:

| Tool | Purpose |
| ----- | ----- |
| `execute_code` | Run Python code, return stdout/stderr |
| `install_package` | pip install, return success/fail |
| `submit_prediction` | Final answer, ends the loop |

**How:**

**execute\_code**

```
receive code string
write to temp file
run with timeout (90s)
capture stdout, stderr, exit code
return {output, error, success}
```

**install\_package**

```
receive package name
run pip install
return success/fail
```

**submit\_prediction**

```
receive prediction (0-1), reasoning, optional fields
validate prediction is float 0-1
validate reasoning exists
mark task complete
return validated result
```

---

#### **4\. Tool Logger (E2B)**

**Why:** Need tracking of attempts without controlling the loop.

**What:** Wraps each tool call to capture:

* Timestamp  
* Tool name  
* Input  
* Output  
* Success/fail  
* Duration

Agent SDK handles retry decisions. We just observe.

**How:**

```
wrap each tool function:
    before: log {timestamp, tool, input}
    call actual tool
    after: log {output, success, duration_ms}
    append to attempt_log list
```

This gives us:

* Number of execute\_code attempts (self-heal metric)  
* Error messages encountered  
* Time spent

---

#### **5\. Prompts (E2B)**

**Why:** Define the task clearly for agent.

**What:** Two task prompts:

**Direct Mode Prompt**

```
You are predicting the outcome of a real event.

Question: {question_text}

Analyze this question using your knowledge. Consider relevant factors,
historical precedents, and logical reasoning.

When ready, use submit_prediction tool with:
- prediction: probability 0.0 to 1.0
- reasoning: brief explanation of your analysis

Do not write code. Use only your reasoning.
```

**Simulation Mode Prompt**

```
You are predicting the outcome of a real event by building a simulation.

Question: {question_text}

Build a predictive model or simulation in Python. You can:
- Use execute_code to run Python code
- Use install_package if you need libraries
- Use any approach: Monte Carlo, agent-based (Mesa), Bayesian, etc.

Run your simulation and analyze the results.

When ready, use submit_prediction tool with:
- prediction: probability 0.0 to 1.0
- reasoning: explanation of your approach and results
- approach: name of method used (e.g., "monte_carlo", "mesa_abm")
- num_runs: number of simulation runs (if applicable)
```

---

#### **6\. Validator (E2B)**

**Why:** Ensure output is usable regardless of model quirks.

**What:** Checks submit\_prediction input:

* prediction is float  
* prediction between 0.0 and 1.0  
* reasoning is non-empty string  
* optional fields have correct types if present

**How:**

```
if prediction not float: reject
if prediction < 0 or > 1: reject
if reasoning empty: reject
return validated result
```

---

#### **7\. Scorer (Local)**

**Why:** Compare results across models.

**What:** Reads all result JSONs, computes metrics, outputs leaderboard.

**Metrics:**

| Metric | What | Formula |
| ----- | ----- | ----- |
| Brier Score | Prediction accuracy | mean((prediction \- outcome)²) |
| First-try Rate | Code quality | % of simulations with 1 execute\_code call |
| Heal Rate | Recovery ability | % of simulations that eventually succeeded |
| Avg Attempts | Efficiency | mean(execute\_code calls per simulation) |

**How:**

```
load all result JSONs
load questions (for resolved outcomes)

for each model:
    collect all predictions
    compute brier score vs outcomes
    compute first-try rate from attempt logs
    compute heal rate
    compute avg attempts

output leaderboard table
output per-question breakdown (optional)
```

---

### **Data Contracts**

**Question Input**

```
{
  "id": "q123",
  "question": "Will X happen by Y?",
  "resolved_outcome": 1.0
}
```

**Arena Result Output**

```
{
  "question_id": "q123",
  "model": "openai/gpt-4o",
  
  "direct": {
    "success": true,
    "prediction": 0.42,
    "reasoning": "...",
    "time_ms": 1500,
    "tool_log": [...]
  },
  
  "simulation": {
    "success": true,
    "prediction": 0.38,
    "reasoning": "...",
    "approach": "monte_carlo",
    "num_runs": 200,
    "time_ms": 45000,
    "tool_log": [
      {"tool": "execute_code", "success": false, "error": "No module mesa"},
      {"tool": "install_package", "input": "mesa", "success": true},
      {"tool": "execute_code", "success": true},
      {"tool": "submit_prediction", "prediction": 0.38}
    ]
  }
}
```

---

### **Model Configuration**

Via Castari Proxy, agent uses:

```
model="anthropic/claude-sonnet-4-5-20250929"
model="openai/gpt-4o"
model="google/gemini-1.5-pro"
model="deepseek/deepseek-chat"
```

Models configurable in config file. Easy to add/remove.

---

### **CLI**

```shell
# Run single question, single model
python main.py --question q1.json --model openai/gpt-4o

# Run single question, all configured models
python main.py --question q1.json

# Generate leaderboard
python scorer.py
```

---

### **Success Criteria**

* \[ \] Agent SDK runs in E2B with proxy routing to different models  
* \[ \] Both modes complete: direct and simulation  
* \[ \] Tool calls logged without interfering with agent loop  
* \[ \] Results JSON captured locally  
* \[ \] Scorer produces leaderboard with Brier score \+ attempt metrics

---

### **Risks & Mitigations**

| Risk | Mitigation |
| ----- | ----- |
| Proxy adds latency/failures | Retry at orchestrator level, log proxy errors |
| Agent loops forever | Global timeout at orchestrator (5 min per mode) |
| Models refuse task | Log refusal as failure, continue |
| Inconsistent output format | Validator rejects, logged as failure |

---

### **Out of Scope (Future)**

* Perplexity research integration  
* Parallel execution  
* Real-time dashboard  
* Cost tracking  
* Error type classification

---

### **Questions for AI Engineer**

1. Castari proxy setup \- any auth/config needed beyond model string?  
2. Claude Agent SDK \- confirm tool definition format  
3. E2B vanilla image \- Python version, pre-installed packages?  
4. Timeout handling \- SDK native or wrapper needed?

---

## **\!\! Self-Healing: How It Works**

The healing happens **inside the Agent SDK loop** \- not our code.

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agent SDK Loop                              │
│                                                                 │
│   Agent receives task: "Build simulation, predict outcome"      │
│                              │                                  │
│                              ▼                                  │
│   Agent decides: "I'll write Mesa simulation"                   │
│                              │                                  │
│                              ▼                                  │
│   Agent calls: execute_code(mesa_code)                          │
│                              │                                  │
│                              ▼                                  │
│   Tool returns: ❌ "ModuleNotFoundError: mesa"                  │
│                              │                                  │
│         ┌────────────────────┴────────────────────┐             │
│         │   Agent SEES the error in response      │             │
│         │   Agent DECIDES to fix it               │  ← HEALING  │
│         │   (This is model reasoning, not our code)             │
│         └────────────────────┬────────────────────┘             │
│                              │                                  │
│                              ▼                                  │
│   Agent calls: install_package("mesa")                          │
│                              │                                  │
│                              ▼                                  │
│   Tool returns: ✅ "Successfully installed"                     │
│                              │                                  │
│                              ▼                                  │
│   Agent calls: execute_code(mesa_code)  ← retry                 │
│                              │                                  │
│                              ▼                                  │
│   Tool returns: ✅ output with results                          │
│                              │                                  │
│                              ▼                                  │
│   Agent calls: submit_prediction(0.41, reasoning="...")         │
│                              │                                  │
│                              ▼                                  │
│   Loop ends                                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**What we measure:**

* Tool Logger captures every tool call  
* Count `execute_code` calls \= attempt count  
* First call success \= first-try rate  
* Eventually succeeded \= heal rate

**What models must do themselves:**

* Recognize the error  
* Decide how to fix (install package? rewrite code? different approach?)  
* Try again

This is the benchmark: **which model brain is best at recovering?**