"""
Configuration for E2B + Claude Agent SDK Demo
"""

# =============================================================================
# E2B TEMPLATES
# =============================================================================

# Master sandbox - runs Flask UI server
# Should have pre-installed: flask, e2b-code-interpreter, python-dotenv
MASTER_TEMPLATE = "chocho-master"

# Slave sandbox - runs Claude Agent SDK tasks
# Should have pre-installed: claude-agent-sdk
SLAVE_TEMPLATE = "chocho-claude-agent-py313"

# =============================================================================
# TIMEOUTS (in seconds)
# =============================================================================

# How long master sandbox stays alive
MASTER_TIMEOUT = 1800  # 30 minutes

# How long slave sandbox stays alive for each task
SLAVE_TIMEOUT = 300  # 5 minutes

# Timeout for agent task execution
AGENT_TASK_TIMEOUT = 120  # 2 minutes

# Timeout for pip install commands
PIP_INSTALL_TIMEOUT = 180  # 3 minutes

# =============================================================================
# FLASK SERVER
# =============================================================================

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

# =============================================================================
# PATHS (inside sandbox)
# =============================================================================

SANDBOX_WORK_DIR = "/home/user"
AGENT_SCRIPT_PATH = f"{SANDBOX_WORK_DIR}/agent_task.py"
TEST_FILE_PATH = f"{SANDBOX_WORK_DIR}/test_file.txt"
RESULTS_PATH = f"{SANDBOX_WORK_DIR}/results.txt"
FLASK_LOG_PATH = f"{SANDBOX_WORK_DIR}/flask.log"

# =============================================================================
# FALLBACK BEHAVIOR
# =============================================================================

# If True, falls back to default sandbox if template not found
# If False, raises error if template not found
FALLBACK_TO_DEFAULT = False

# Install packages even if using template (useful for testing)
FORCE_PIP_INSTALL = False

# =============================================================================
# CLAUDE AGENT SDK OPTIONS
# =============================================================================

# Model to use for analysis (supported by SDK)
AGENT_MODEL = "claude-sonnet-4-20250514"

# System prompt for the agent (supported by SDK)
AGENT_SYSTEM_PROMPT = """You are a helpful document analyst. Analyze documents concisely and extract key information.
Keep responses focused and under 30 words unless more detail is explicitly requested."""

# Maximum tokens for response (set via CLAUDE_CODE_MAX_OUTPUT_TOKENS env var)
AGENT_MAX_TOKENS = 200000

# Default analysis prompt template (use {content} placeholder for file content)
AGENT_ANALYSIS_PROMPT = """Analyze this document and provide:
1. A brief summary (2-3 sentences)
2. Key points or findings (bullet list)
3. Any notable patterns or insights

Document content:
{content}"""
