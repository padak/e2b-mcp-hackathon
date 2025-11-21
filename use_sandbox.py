"""
Example: Using the custom E2B template with Claude Agent SDK.

Make sure to:
1. Run build_template.py first to create the template
2. Set your E2B_API_KEY environment variable
3. Set your ANTHROPIC_API_KEY environment variable
"""

import os

from e2b import Sandbox


# Template with Python 3.13 + Claude Agent SDK
TEMPLATE_ID = "gxstwqtr3rfg5exocc8v"


def run_agent_in_sandbox():
    """Start a sandbox and run Claude Agent SDK code inside it."""

    # Create sandbox from your custom template
    sandbox = Sandbox.create(
        template=TEMPLATE_ID,
        timeout=300,  # 5 minutes
        envs={
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
        },
    )

    print(f"Sandbox started: {sandbox.sandbox_id}")

    try:
        # Example: Verify Claude Agent SDK is installed
        result = sandbox.commands.run("python -c \"import claude_agent_sdk; print(f'Claude Agent SDK version: {claude_agent_sdk.__version__}')\"")
        print(f"Output: {result.stdout}")

        # Example: Check Python version
        result = sandbox.commands.run("python --version")
        print(f"Python: {result.stdout}")

        # Example: Verify Claude Agent SDK module is available
        result = sandbox.commands.run("python -c \"import claude_agent_sdk; print('Claude Agent SDK is ready to use!')\"")
        print(f"Output: {result.stdout}")

    finally:
        # Clean up
        sandbox.kill()
        print("Sandbox terminated")


if __name__ == "__main__":
    run_agent_in_sandbox()
