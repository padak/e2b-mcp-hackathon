# Frontend PRD - WorldSim Markets Web UI

## Overview

Web interface for WorldSim Markets - an AI world simulator comparing Polymarket odds with Monte Carlo simulations.

**Goal**: Simple, light UI enabling users to try simulations without technical knowledge.

**Deployment**: Vercel (TypeScript only)

---

## Architecture

```
┌─────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│   Vercel    │────▶│  E2B Sandbox #1      │────▶│  E2B Sandbox #2  │
│  (Frontend) │     │  (Backend API)       │     │  (Per-simulation) │
│  Next.js    │     │  Python + FastAPI    │     │  Isolated Mesa    │
│  TypeScript │     │  HTTPS exposed       │     │  Monte Carlo      │
└─────────────┘     │  (shared instance)   │     └──────────────────┘
                    └──────────────────────┘              ↓
                                                  E2B Sandbox #3
                                                  (another user)
                                                         ↓
                                                       ...
```

### Why This Architecture

- Vercel only supports TypeScript/Node.js
- Python backend runs in E2B sandbox (shared API instance)
- E2B can expose HTTPS URL externally
- Each simulation runs in isolated E2B sandbox (supports concurrent users)
- Multiple users = multiple simulation sandboxes running in parallel

### Secrets Management

- All API keys (Anthropic, E2B, Perplexity) stored in Vercel environment variables
- Frontend calls Vercel API routes (never external APIs directly)
- Vercel API routes communicate with E2B backend
- No secrets exposed to browser

---

## Core Features

### 1. URL Import (Primary Input)

User pastes Polymarket URL and the system:
- Parses URL → extracts event slug
- Fetches market data
- Validates:
  - ✅ Active (end_date > now)
  - ✅ Binary (YES/NO)
  - ❌ Multi-outcome (sport scores)

**Supported Formats:**

| Type | Pattern | Simulatable |
|------|---------|-------------|
| Event (YES/NO) | `/event/{slug}` | ✅ |
| Sports game | `/sports/.../games/...` | ❌ |
| Multi-outcome | `/event/{slug}` with >2 outcomes | ❌ |

### 2. Market Browser (Secondary)

- Categories: Politics, World, Sports, Crypto, Finance, Tech, Culture
- Top 10 by Volume
- Custom Search

### 3. Simulation Runner

Progress tracking with live updates:
1. Research (Perplexity) - 5-10s
2. Generate (Claude) - 10-20s
3. Calibrate (50 runs) - 15-30s
4. Simulate (200 runs) - 30-60s

**Total: ~2-3 minutes per market**

### 4. Results Dashboard

- Interactive Plotly chart
- Trading signal (BUY YES / BUY NO / HOLD)
- Expected value calculation
- Model Explainer (see below)

### 5. Model Explainer (Key Feature)

Transparent simulation explanation for laypeople:

```
┌─────────────────────────────────────────────────┐
│  📊 How We Simulated This                       │
├─────────────────────────────────────────────────┤
│                                                 │
│  Research Insights                              │
│  ─────────────────                              │
│  • "Fed likely to cut rates" - Reuters          │
│  • Current inflation: 3.2%                      │
│  • Market expects 65% chance                    │
│                                                 │
│  ↓ This informed our agent design ↓             │
│                                                 │
│  Agent-Based Model                              │
│  ─────────────────                              │
│                                                 │
│  🏦 Fed Officials (12)                          │
│     Why: FOMC has 12 voting members             │
│     Behavior: Weighs inflation vs employment    │
│     Initial bias: 65% dovish (from research)    │
│                                                 │
│  📈 Market Traders (50)                         │
│     Why: Markets price in expectations          │
│     Behavior: React to Fed signals              │
│                                                 │
│  Simulation Logic                               │
│  ────────────────                               │
│  1. Each step = 1 day                           │
│  2. Indicators update randomly                  │
│  3. Agents interact and shift positions         │
│  4. After 100 steps: count outcomes             │
│  5. Ran 200x with different seeds               │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Explanation Generation** - Claude also creates:

```python
MODEL_EXPLANATION = {
    "research_highlights": [...],
    "agents": {
        "AgentType": {
            "count": 12,
            "why": "reason for this agent",
            "behavior": "what it does",
            "initial_state": "based on research"
        }
    },
    "simulation_logic": [...],
    "outcome_interpretation": "..."
}
```

---

## UI Design

### Principles

- **Light theme** - clean, minimalist
- **Simple** - minimum clicks to result
- **Transparent** - user sees what's happening
- **Educational** - explains simulation principles

### Main Screens

#### 1. Landing / Input

```
┌─────────────────────────────────────────┐
│  WorldSim Markets              [Menu]   │
├─────────────────────────────────────────┤
│                                         │
│  Paste Polymarket URL                   │
│  ┌───────────────────────────────────┐  │
│  │ https://polymarket.com/event/...  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  [Simulate]                             │
│                                         │
│  ── or browse markets ──                │
│                                         │
│  [Politics] [World] [Sports] [Crypto]   │
│  [Finance] [Tech] [Culture] [Top 10]    │
│                                         │
└─────────────────────────────────────────┘
```

#### 2. Market Validation

```
┌─────────────────────────────────────────┐
│  ✅ Valid market detected               │
│                                         │
│  "Will the Fed cut rates in December?"  │
│                                         │
│  Current odds: 65% Yes                  │
│  Volume: $125,000                       │
│  Ends: Dec 18, 2024                     │
│                                         │
│  Monte Carlo runs: [200 ▼]              │
│                                         │
│  [Run Simulation]                       │
└─────────────────────────────────────────┘
```

#### 3. Simulation Progress

```
┌─────────────────────────────────────────┐
│  Simulating...                          │
├─────────────────────────────────────────┤
│                                         │
│  ✅ Research         (12s)              │
│  ✅ Generate Model   (18s)              │
│  🔄 Calibrating...   (50 runs)          │
│  ○  Monte Carlo      (200 runs)         │
│                                         │
│  Live Log:                              │
│  ┌───────────────────────────────────┐  │
│  │ [14:32:05] Calibration run 23/50 │  │
│  │ [14:32:04] Testing threshold...  │  │
│  │ [14:32:01] Model compiled OK     │  │
│  └───────────────────────────────────┘  │
│                                         │
│  [Cancel]                               │
└─────────────────────────────────────────┘
```

#### 4. Results

```
┌─────────────────────────────────────────┐
│  Results                           [↓]  │
├─────────────────────────────────────────┤
│                                         │
│  "Will the Fed cut rates in December?"  │
│                                         │
│  ┌─────────┐  ┌─────────┐               │
│  │   72%   │  │   65%   │               │
│  │Simulation│  │ Market │               │
│  └─────────┘  └─────────┘               │
│                                         │
│  Signal: BUY YES (+7pp)                 │
│  Confidence: ±6.7pp (95% CI)            │
│                                         │
│  [View Chart] [How We Simulated This ▼] │
│                                         │
└─────────────────────────────────────────┘
```

---

## API Endpoints

### Market Management

```
GET /api/markets/from-url?url={encoded}
  → {valid, simulatable, market, reason}

GET /api/markets?category=&search=&limit=10
  → [{question, yes_odds, volume, slug}]

GET /api/markets/categories
  → {politics: [...], world: [...], ...}
```

### Simulation Control

```
POST /api/simulations
  Body: {market_url, n_runs}
  → {simulation_id, status}

GET /api/simulations/:id
  → {status, progress, result}

WS /api/ws/simulations/:id
  Events:
    {type: "phase", phase: "research|generate|calibrate|simulate"}
    {type: "log", message: "..."}
    {type: "progress", current: 50, total: 200}
    {type: "complete", result: {...}}
    {type: "error", error: "..."}
```

### Results

```
GET /api/simulations/:id/result
  → {
      probability, ci_95, n_runs,
      market_odds, difference,
      signal, expected_value,
      model_explanation,
      chart_html
    }

GET /api/simulations/:id/model
  → {code, explanation}
```

---

## Technology Stack

### Frontend (Vercel)

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui or custom (TBD - design system)
- **Charts**: Plotly.js (react-plotly.js)
- **Real-time**: WebSocket / Server-Sent Events
- **State**: React Query / SWR

### Backend (E2B Sandbox)

- **Framework**: FastAPI
- **Existing code**: src/orchestrator.py, src/cli.py
- **Exposure**: E2B HTTPS URL

---

## Implementation Phases

### Phase 1: Foundation (MVP)

**Goal**: Basic flow - URL → Simulation → Result

**Scope**:
- [ ] Next.js project setup
- [ ] Landing page with URL input
- [ ] Market validation endpoint
- [ ] Backend API wrapper (FastAPI in E2B)
- [ ] E2B sandbox orchestration from Vercel
- [ ] Basic simulation trigger
- [ ] Results display (numbers only, no chart)
- [ ] Basic error handling

**Deliverables**:
- Working prototype on Vercel
- User can paste URL and get result

---

### Phase 2: Real-time & Visualization

**Goal**: Live progress and interactive visualization

**Scope**:
- [ ] WebSocket connection for live updates
- [ ] Progress stepper UI
- [ ] Live log stream
- [ ] Plotly chart integration
- [ ] Trading signal badge
- [ ] Confidence interval display
- [ ] Download result as JSON

**Deliverables**:
- User sees progress in real-time
- Interactive Plotly dashboard

---

### Phase 3: Model Explainer

**Goal**: Transparent simulation explanation

**Scope**:
- [ ] Extend Claude prompt with MODEL_EXPLANATION
- [ ] Research highlights extraction
- [ ] Agent cards with "why" and "behavior"
- [ ] Simulation logic steps
- [ ] Collapsible UI component
- [ ] Animated agent visualization (optional)

**Deliverables**:
- User understands how simulation works
- Sees connection: research → agents → outcome

---

### Phase 4: Market Browser

**Goal**: Alternative way to select markets

**Scope**:
- [ ] Category filtering
- [ ] Search functionality
- [ ] Top 10 by volume
- [ ] Market cards/table
- [ ] Sorting options
- [ ] Pagination

**Deliverables**:
- Browse markets without knowing URL
- Filtering and search

---

### Phase 5: Polish & Production

**Goal**: Production-ready application

**Scope**:
- [ ] Design system implementation
- [ ] Responsive design (mobile)
- [ ] Error states and recovery
- [ ] Loading skeletons
- [ ] SEO & meta tags
- [ ] Analytics integration
- [ ] Documentation

**Deliverables**:
- Polished, production-ready UI
- User documentation

---

### Phase 6: Advanced Features (Future)

**Possible extensions**:
- [ ] Batch simulation mode
- [ ] User accounts & history
- [ ] Compare multiple markets
- [ ] Custom model parameters
- [ ] Export to PDF/CSV
- [ ] Alerts on price changes
- [ ] API for third parties

---

## Decisions Made

- **Authentication** - Public demo, no login required
- **Rate limiting** - None (open access)
- **Persistence** - No storage, results are ephemeral (in-memory only)
- **Secrets** - All API keys in Vercel env vars, proxied through API routes

## Open Questions

### To Decide

1. **Design system** - shadcn/ui or custom?
2. **Domain** - worldsim.markets? other?

### Technical

1. **E2B sandbox lifecycle** - How long to keep backend sandbox alive?
2. **Cost management** - E2B pricing per sandbox minute
3. **Cold start** - How to handle first load (clone + install)?
4. **Fallback** - What if E2B is unavailable?

---

## Success Metrics

- **Time to result**: < 3 minutes from URL paste
- **Success rate**: > 90% simulations completed
- **User understanding**: User understands result (qualitative)
- **Error recovery**: Clear error messages with actions

---

## References

- [Polymarket API](https://docs.polymarket.com/)
- [E2B Documentation](https://e2b.dev/docs)
- [Mesa Documentation](https://mesa.readthedocs.io/)
- [Plotly.js](https://plotly.com/javascript/)
