# News Scenario Simulator - Implementation Plan

## Executive Summary

AI-powered tool that helps journalists explore "what-if" scenarios by automatically generating and running simulations based on current news topics. The system uses LLMs to **dynamically generate complete Mesa simulation models** based on news context and research data, then executes them in secure E2B sandboxes.

**Key Innovation**: LLM generates the entire simulation code on-the-fly, not just parameters. This showcases the true power of AI + sandboxed execution.

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
   - Single MCP: Perplexity (handles both news search and research)
   - Unified interface for topic discovery and parameter research
   - Response caching for demo reliability

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
   - Identify actors, variables, dynamics
   - Determine simulation approach

5. Dynamic Model Generator
   - LLM generates complete Mesa model code
   - System prompt with Mesa examples and best practices
   - Includes agents, behaviors, metrics, visualization

6. Validation & Retry Loop
   - Execute in E2B sandbox
   - Capture errors and output
   - LLM fixes code if execution fails
   - Max 5 retries before fallback
```

### Phase 3: Reference Model & Testing (Hours 9-12)
```
7. Reference Model (Fallback)
   - One hand-crafted Economic Shock model
   - Well-tested, reliable for demo
   - Used when LLM-generated code fails after retries

8. System Prompt Engineering
   - Mesa code generation examples
   - Output format specification
   - Error handling patterns
   - Visualization requirements

9. End-to-End Testing
   - Test with various news topics
   - Verify retry loop works
   - Cache successful MCP responses for demo
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
- [ ] E2B sandbox execution with retry loop
- [ ] Perplexity MCP for news + research
- [ ] LLM-generated Mesa models (dynamic)
- [ ] One reference model as fallback
- [ ] Basic Plotly visualization
- [ ] CLI interface

### Nice to Have
- [ ] Monte Carlo variants (multiple runs)
- [ ] Confidence intervals
- [ ] Response caching for offline demo

### Out of Scope
- Web interface
- Multiple visualization types
- Real-time updates
- Production deployment

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM generates buggy code | Retry loop with error feedback (max 5 attempts) |
| Model doesn't converge | Set max iterations, E2B timeout (30s) |
| Generated code too complex | Prompt engineering for simple models |
| All retries fail | Fallback to reference Economic Shock model |
| Perplexity rate limits | Cache responses for demo |
| E2B timeout | Limit agent count in prompt (max 500) |

## Success Metrics

1. **Technical**: LLM successfully generates working Mesa models for different topics
2. **Innovation**: Dynamic code generation + sandboxed execution (not just templates)
3. **Demo-ability**: Clear 90-second demo showing news → generated simulation → viz
4. **Reliability**: Retry loop and fallback ensure demo never fails

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

1. **Hour 1-2**: Setup project, E2B Hello World, Perplexity MCP
2. **Hour 3-4**: Build reference Economic Shock model (fallback)
3. **Hour 5-6**: LLM model generator with system prompt
4. **Hour 7-8**: Retry loop and error handling
5. **Hour 9-10**: End-to-end pipeline integration
6. **Hour 11-12**: Testing with various topics
7. **Hour 13-14**: Visualization and CLI polish
8. **Hour 15-16**: Demo prep and caching

## Notes for Implementation

- **Trust the LLM** - Let it generate complete models, not just fill parameters
- **Robust retry loop** - Key differentiator, must work flawlessly
- **One solid fallback** - Reference model saves the demo if all else fails
- **Visual impact** - The demo is 50% about the visualization
- **Cache for demo** - Pre-cache Perplexity responses for reliable demo

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

1. **Dynamic generation**: LLM creates custom simulations, not just templates
2. **True AI + execution**: Showcases LLM code generation + E2B sandboxing
3. **Self-healing**: Retry loop with error feedback - AI fixes its own bugs
4. **Journalist-focused**: Designed for storytelling, not academia
5. **Safe execution**: E2B sandbox prevents code injection

## Potential Extensions (Post-Hackathon)

- Multi-scenario comparison
- Collaborative simulations
- Real-time data feeds
- AI-generated narratives
- Blockchain verification
- Mobile app
- SaaS platform