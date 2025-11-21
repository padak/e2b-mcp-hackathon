# CLAUDE.md - AI Assistant Guide

## Project Overview

**n8n to Python Agentic Transpiler** - A hackathon project that converts n8n workflow definitions (JSON) into standalone, executable Python scripts using Claude AI and E2B sandboxes.

### Core Functionality
- Parse n8n workflow JSON files
- Analyze workflow intent using Claude LLM
- Generate Python implementation
- Execute in E2B sandbox for validation
- Iteratively fix errors (up to 5 retries)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set required environment variables
export ANTHROPIC_API_KEY="sk-..."
export E2B_API_KEY="e2b_..."

# Run transpiler
python n8n_agent/agent.py test_workflow.json --output my_script.py
```

## Project Structure

```
e2b-mcp-hackathon/
├── n8n_agent/              # Main Python package
│   ├── agent.py            # CLI entry point and orchestration
│   ├── generator.py        # LLM code generation and fixing
│   ├── evaluator.py        # E2B sandbox execution
│   ├── utils.py            # Workflow parsing utilities
│   ├── config.py           # Configuration loader
│   └── config.json         # Model configuration
├── docs/                   # Project documentation (Czech)
│   ├── GOAL.md             # High-level project goal
│   ├── claude-idea.md      # Technical design
│   └── gemini3-idea.md     # Alternative MCP approach
├── test_workflow.json      # Example n8n workflow
└── requirements.txt        # Python dependencies
```

## Key Modules

### agent.py (Entry Point)
- CLI argument parsing
- Orchestrates the transpilation pipeline
- Implements retry loop with error fixing

### generator.py
- `analyze_workflow()` - Extract intent from workflow summary
- `generate_code()` - Generate initial Python implementation
- `fix_code()` - Fix code based on execution errors

### evaluator.py
- `run_in_sandbox()` - Execute code in E2B sandbox
- Captures stdout/stderr with 30-second timeout

### utils.py
- `load_workflow()` - Load JSON file
- `parse_workflow()` - Parse into Pydantic models
- `get_workflow_summary()` - Generate text summary for LLM

## Dependencies

- **anthropic** - Claude API client
- **e2b-code-interpreter** - Sandbox execution
- **pydantic** - Data validation
- **python-dotenv** - Environment management

## Code Conventions

### Type Hints
All functions use Python type hints:
```python
def load_workflow(file_path: str) -> Dict[str, Any]:
```

### Pydantic Models
n8n structures are validated with Pydantic:
- `N8nNode` - Individual workflow node
- `N8nConnection` - Edge between nodes
- `N8nWorkflow` - Complete workflow

### Generated Code Patterns
- Self-contained Python scripts
- `MOCK_MODE` flag for sandbox testing
- Clear stdout output for verification

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| ANTHROPIC_API_KEY | Yes | Claude API access |
| E2B_API_KEY | Yes | E2B sandbox execution |

## CLI Usage

```bash
python n8n_agent/agent.py <workflow_file> [options]

Options:
  --output, -o      Output file path (default: generated_agent.py)
  --max-retries     Maximum fix iterations (default: 5)
  --api-key         Anthropic API key (overrides env var)
```

## Architecture Flow

```
n8n JSON → Parse → Analyze Intent → Generate Code → Execute in E2B
                                                         ↓
                                    Success → Save    Failure → Fix → Retry
```

## Development Notes

### Adding New Node Types
Extend `utils.py` to handle additional n8n node types in `parse_workflow()` and `get_workflow_summary()`.

### Changing Models
Edit `n8n_agent/config.json` to switch between:
- `claude-haiku-4-5-20251001` (default, fast)
- `claude-sonnet-4-5-20250929` (balanced)
- `claude-opus-4-1-20250805` (most capable)

### Testing
Use `test_workflow.json` as a reference for workflow format. The generated code runs in mock mode by default.

## Important Files for Modifications

- **Entry point**: `n8n_agent/agent.py:41` (main function)
- **Code generation prompts**: `n8n_agent/generator.py:20-45`
- **Sandbox execution**: `n8n_agent/evaluator.py:15-35`
- **Workflow parsing**: `n8n_agent/utils.py:35-66`

## Hackathon Context

This project was built for the E2B MCP Hackathon with requirements:
- E2B sandbox integration (mandatory)
- At least one MCP from Docker Hub
- Fully functional, submittable code
- Demo video under 2 minutes

## Notes for AI Assistants

1. Documentation in `docs/` is in Czech language
2. The project uses a simple retry mechanism for error fixing
3. Generated code includes mock mode for testing without real API credentials
4. All execution happens in E2B sandbox (isolated environment)
5. The codebase is minimal (~318 lines of Python total)
