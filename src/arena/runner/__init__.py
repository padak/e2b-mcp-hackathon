"""Arena runner module.

This module contains the core components for running LLM evaluations:
- ArenaRunner: Main runner class
- Tools: execute_code, install_package, submit_prediction
- Hooks: Logging and metrics collection
- Prompts: Direct and simulation mode prompts
"""

from .arena_runner import ArenaRunner
from .tools import (
    TOOL_DEFINITIONS,
    ToolMetrics,
    ExecutionResult,
    PredictionResult,
    execute_code,
    install_package,
    validate_prediction,
)
from .hooks import (
    ToolHandler,
    ToolCall,
    RunLog,
    create_tool_handler,
)
from .prompts import (
    get_system_prompt,
    get_user_prompt,
    DIRECT_MODE_PROMPT,
    SIMULATION_MODE_PROMPT,
)

__all__ = [
    "ArenaRunner",
    "TOOL_DEFINITIONS",
    "ToolMetrics",
    "ExecutionResult",
    "PredictionResult",
    "execute_code",
    "install_package",
    "validate_prediction",
    "ToolHandler",
    "ToolCall",
    "RunLog",
    "create_tool_handler",
    "get_system_prompt",
    "get_user_prompt",
    "DIRECT_MODE_PROMPT",
    "SIMULATION_MODE_PROMPT",
]
