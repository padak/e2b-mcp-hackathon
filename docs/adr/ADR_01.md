# ADR-01: Use OpenAI SDK Instead of Claude Agent SDK

**Status**: Accepted
**Date**: 2024-12-01
**Decision Makers**: @chocho, Claude

## Context

The original plan called for using **Claude Agent SDK** with **claude-code-router** to route requests through OpenRouter to multiple LLM providers (GPT-4, Claude, Gemini).

The architecture was:
```
Claude Agent SDK → claude-code-router (proxy) → OpenRouter → LLM
```

During implementation, we discovered:
1. `claude-code-router` is a Node.js proxy that translates Anthropic API format to OpenAI format
2. Running it inside E2B sandbox added complexity (port binding, startup timing)
3. OpenRouter already provides an OpenAI-compatible API

## Decision

**Use OpenAI SDK directly with OpenRouter instead of Claude Agent SDK + claude-code-router.**

New architecture:
```
OpenAI SDK → OpenRouter API → LLM (GPT-4, Claude, Gemini)
```

## Rationale

### Pros
1. **Simpler**: No translation layer, no proxy to manage
2. **Faster**: One less network hop
3. **More reliable**: Fewer moving parts
4. **Works now**: E2E tested with real OpenRouter API
5. **Native multi-model**: OpenRouter handles all models uniformly

### Cons
1. **No Anthropic-native features**: Can't use `max_budget_usd`, native hooks
2. **Custom agent loop**: We built our own instead of using SDK's
3. **Different from original plan**: Diverges from hackathon proposal

### Why Not Claude Agent SDK?

| Feature | Claude Agent SDK | Our Implementation |
|---------|------------------|-------------------|
| Model support | Claude only | Any model via OpenRouter |
| API format | Anthropic | OpenAI-compatible |
| Budget control | Built-in | Manual tracking |
| Hooks | Native PreToolUse/PostToolUse | Custom ToolHandler |
| Complexity | Requires proxy for multi-model | Direct connection |

## Implementation

- `ArenaRunner` class uses `openai.OpenAI` client
- Points to `https://openrouter.ai/api/v1`
- Tools defined in OpenAI function calling format
- Custom `ToolHandler` for logging and metrics

## Consequences

1. We lose Claude Agent SDK's built-in features
2. We gain simplicity and multi-model support
3. Future: Could add Claude Agent SDK for Claude-only benchmarks if needed

## References

- Commit: `arena-phase-2` tag
- Files: `src/arena/runner/arena_runner.py`
- E2E tests: `tests/arena/test_arena_runner_e2e.py`
