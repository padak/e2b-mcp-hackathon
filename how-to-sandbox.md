# E2B Sandbox Templates

## Templates

| Template | Alias | ID | Purpose |
|----------|-------|-----|---------|
| Master | `chocho-master` | `qsu53e2apwfbl6xlm595` | Flask UI, orchestrates slave sandboxes |
| Slave | `chocho-claude-agent-py313` | `gxstwqtr3rfg5exocc8v` | Runs Claude Agent SDK tasks |

## Master Template

**Packages:** flask, e2b, e2b-code-interpreter, python-dotenv

```python
from e2b import Sandbox

sandbox = Sandbox.create(template="qsu53e2apwfbl6xlm595")
```

## Slave Template

**Packages:** claude-agent-sdk, anthropic

```python
from e2b import Sandbox

sandbox = Sandbox.create(template="gxstwqtr3rfg5exocc8v")
```

## Architecture

```
┌─────────────────────────────────────┐
│  Master Sandbox (chocho-master)     │
│  - Flask UI                         │
│  - E2B SDK                          │
│                                     │
│  Spawns and manages:                │
│    ┌─────────────────────────────┐  │
│    │  Slave Sandbox              │  │
│    │  (chocho-claude-agent-py313)│  │
│    │  - Claude Agent SDK         │  │
│    │  - Runs AI tasks            │  │
│    └─────────────────────────────┘  │
└─────────────────────────────────────┘
```
