# News Scenario Simulator - Implementation Plan

## Executive Summary

AI-powered tool that helps journalists explore "what-if" scenarios by automatically generating and running simulations based on current news topics. The system uses LLMs to extract simulation parameters from news articles and academic papers, then executes agent-based models in secure E2B sandboxes.

## Core Value Proposition

- **For Journalists**: Transform breaking news into interactive future scenarios
- **Data-Driven**: Parameters backed by academic research (ArXiv) and current data (Perplexity)
- **Visual Storytelling**: Generate embeddable visualizations for articles
- **Rapid Prototyping**: From news topic to simulation in minutes

## Technical Architecture

### Phase 1: Foundation (Hours 1-3)
```
1. Project Setup
   - Initialize Python project structure
   - Setup E2B SDK and API keys
   - Install Mesa, Plotly, and dependencies
   - Create base Agent classes

2. MCP Integration Layer
   - News fetching (Brave Search MCP)
   - Research retrieval (Perplexity MCP)
   - Academic papers (ArXiv API wrapper)
   - Create unified data interface

3. Basic E2B Sandbox Runner
   - Code execution wrapper
   - Error handling
   - Output capture
   - Result serialization
```

### Phase 2: Core Engine (Hours 4-8)
```
4. Topic Analyzer
   - News article parsing
   - Topic categorization
   - Simulatability scoring
   - Entity extraction

5. Parameter Extractor
   - LLM prompts for parameter identification
   - Research-based validation
   - Default value system
   - Confidence scoring

6. Model Generator
   - Mesa model templates (5-6 scenarios)
   - Dynamic agent generation
   - Parameter injection
   - Validation checks
```

### Phase 3: Simulation Templates (Hours 9-12)
```
7. Pre-built Scenarios:
   a) Economic Shock Model
      - Market agents, consumers, regulators
      - Parameters: inflation, interest rates, unemployment

   b) Disease Spread Model
      - Population agents with SEIR states
      - Parameters: R0, vaccination rate, mobility

   c) Social Opinion Dynamics
      - Agents with belief states
      - Parameters: influence radius, media impact

   d) Climate Event Impact
      - Geographic agents, infrastructure
      - Parameters: event severity, preparedness level

   e) Election/Political Model
      - Voter agents with preferences
      - Parameters: poll data, swing factors
```

### Phase 4: Integration & UI (Hours 13-16)
```
8. Orchestrator
   - Pipeline controller
   - State management
   - User approval flow
   - Progress tracking

9. Visualization Engine
   - Plotly dashboard generator
   - Time series animations
   - Export to HTML/JSON
   - Embeddable widgets

10. CLI Interface
    - Interactive prompts
    - Simulation review
    - Export options
    - Debug mode
```

## Implementation Details

### Topic Selection Algorithm
```python
def score_simulatability(topic):
    factors = {
        'has_numerical_data': 0.3,      # Stock prices, polls, rates
        'has_clear_agents': 0.3,        # People, companies, countries
        'has_predictable_rules': 0.2,   # Known dynamics
        'temporal_relevance': 0.2       # Ongoing/future event
    }
    return weighted_score(topic, factors)
```

### Prompt Templates

**Topic Analysis**:
```
Analyze this news article for simulation potential:
1. Identify key actors/agents
2. Extract measurable variables
3. Determine time horizon
4. Suggest simulation type from: [economic, epidemic, social, climate, political]
```

**Parameter Research**:
```
For [TOPIC], find:
1. Current baseline values for [VARIABLES]
2. Historical ranges and volatility
3. Expert predictions/scenarios
4. Comparable past events
```

### E2B Execution Flow
```python
async def run_simulation(model_code, parameters):
    sandbox = await CodeInterpreter.create()

    # Install dependencies
    await sandbox.run_python("pip install mesa plotly pandas")

    # Execute model
    result = await sandbox.run_python(model_code)

    # Capture visualizations
    plots = await sandbox.download_file("/tmp/simulation_output.html")

    return result, plots
```

## MVP Features (Hackathon Scope)

### Must Have
- [x] E2B sandbox execution
- [x] At least 1 MCP from Docker Hub
- [ ] 3 working simulation templates
- [ ] Basic news topic extraction
- [ ] Simple parameter selection
- [ ] One visualization type
- [ ] CLI interface

### Nice to Have
- [ ] Web interface
- [ ] Multiple visualization types
- [ ] Confidence intervals
- [ ] Sensitivity analysis
- [ ] Historical validation

### Out of Scope
- Real-time updates
- Multi-agent collaboration
- Custom model building UI
- Production deployment

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM hallucinates parameters | Validate against research data, provide ranges |
| Simulation doesn't converge | Set max iterations, timeout in E2B |
| Topic too complex | Fallback to simpler template |
| MCP rate limits | Cache responses, batch requests |
| E2B timeout | Optimize model, reduce agent count |

## Success Metrics

1. **Technical**: Successfully runs 3+ different simulations via E2B
2. **Innovation**: Novel combination of news + simulation + visualization
3. **Demo-ability**: Clear 90-second demo showing full pipeline
4. **Code Quality**: Clean, documented, reproducible

## Demo Scenario

**"Breaking: Fed Raises Interest Rates by 0.5%"**

1. System fetches news (5 sec)
2. Identifies as economic scenario (3 sec)
3. Researches current economic indicators (10 sec)
4. Generates market simulation with 1000 agents (5 sec)
5. Runs 12-month projection in E2B (20 sec)
6. Shows interactive chart of outcomes (5 sec)
7. Journalist embeds in article (2 sec)

Total: ~50 seconds from news to visualization

## Development Priorities

1. **Core Pipeline** (40%) - Get data flowing end-to-end
2. **Simulation Quality** (30%) - Make results meaningful
3. **Visualization** (20%) - Clear, embeddable output
4. **Polish** (10%) - Error handling, docs

## File Structure
```
news-scenario-simulator/
├── src/
│   ├── mcp_clients/       # MCP integrations
│   ├── analyzers/          # Topic & parameter extraction
│   ├── models/             # Mesa simulation templates
│   ├── sandbox/            # E2B execution layer
│   ├── visualizers/        # Plotly generators
│   └── orchestrator.py     # Main pipeline
├── templates/              # Pre-built scenarios
├── examples/               # Demo news articles
├── tests/                  # Unit tests
└── cli.py                  # Entry point
```

## Next Steps

1. **Immediate**: Setup project, install dependencies
2. **Hour 1-2**: Get E2B Hello World working
3. **Hour 3-4**: Integrate first MCP (Brave Search)
4. **Hour 5-6**: Build first Mesa template
5. **Hour 7-8**: Connect pipeline
6. **Hour 9-12**: Add more templates
7. **Hour 13-14**: Visualization
8. **Hour 15-16**: Demo prep

## Notes for Implementation

- **Keep it simple** - MVP over features
- **Template-first** - Don't try to handle every scenario
- **Fail gracefully** - Always have fallback options
- **Visual impact** - The demo is 50% about the visualization
- **Document assumptions** - Be transparent about limitations

## Libraries & Tools

```python
# Core
mesa==2.1.5           # Agent-based modeling
plotly==5.18.0        # Interactive visualizations
e2b-code-interpreter  # Sandbox execution

# MCP Clients
mcp-client-sdk        # MCP protocol
httpx                 # Async HTTP

# Data Processing
pandas                # Data manipulation
numpy                 # Numerical computing
pydantic              # Data validation

# AI/ML
anthropic             # Claude API
langchain             # LLM orchestration (optional)

# Utilities
rich                  # CLI formatting
python-dotenv         # Environment management
```

## Competitive Advantages

1. **First-mover**: No existing tool combines news + simulation + viz
2. **Journalist-focused**: Designed for storytelling, not academia
3. **Rapid deployment**: Minutes from idea to simulation
4. **Open scenarios**: Extensible template system
5. **Safe execution**: E2B sandbox prevents code injection

## Potential Extensions (Post-Hackathon)

- Multi-scenario comparison
- Collaborative simulations
- Real-time data feeds
- AI-generated narratives
- Blockchain verification
- Mobile app
- SaaS platform