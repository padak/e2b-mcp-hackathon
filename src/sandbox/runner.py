"""E2B Sandbox runner with MCP Gateway support."""

import os
import asyncio
from e2b import AsyncSandbox
from dotenv import load_dotenv

load_dotenv()


async def create_sandbox() -> AsyncSandbox:
    """Create E2B sandbox with Perplexity MCP enabled."""
    sbx = await AsyncSandbox.create(
        timeout=300,  # 5 minutes
        mcp={
            "perplexityAsk": {
                "perplexityApiKey": os.getenv("PERPLEXITY_API_KEY"),
            },
        }
    )
    return sbx


async def test_sandbox():
    """Test E2B sandbox with MCP gateway."""
    sbx = await create_sandbox()

    try:
        # 2.2 Test MCP connection
        mcp_url = sbx.get_mcp_url()
        mcp_token = await sbx.get_mcp_token()
        print(f"MCP Gateway URL: {mcp_url}")
        print(f"MCP Token: {mcp_token[:20]}...")

        # 2.3 Test code execution via commands
        result = await sbx.commands.run('python3 -c "print(\'Hello from E2B\')"')
        print(f"Code execution: {result.stdout}")

        # 2.4 Test Mesa installation and import
        print("Installing Mesa, plotly, pandas, numpy...")
        await sbx.commands.run('pip install mesa plotly pandas numpy', timeout=120)

        result = await sbx.commands.run('''python3 -c "
from mesa import Agent, Model
import pandas as pd
import numpy as np
print('Mesa, pandas, numpy imported successfully!')
"''')
        print(f"Mesa test: {result.stdout}")

        return True

    finally:
        await sbx.kill()


if __name__ == "__main__":
    asyncio.run(test_sandbox())
