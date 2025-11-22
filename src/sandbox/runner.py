"""E2B Sandbox runner with MCP Gateway support."""

import os
import asyncio
from e2b import AsyncSandbox
from dotenv import load_dotenv

load_dotenv()


async def create_sandbox() -> AsyncSandbox:
    """Create E2B sandbox with Perplexity MCP enabled."""
    sbx = await AsyncSandbox.create(
        template="code-interpreter-v1",
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


async def test_perplexity_mcp():
    """Test Perplexity search via MCP gateway."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from src.mcp.client import create_mcp_client, search

    sbx = await create_sandbox()

    try:
        print("Connecting to MCP gateway...")
        async with create_mcp_client(sbx) as session:
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

        # Test search
        print("\nSearching for Fed interest rate decision...")
        result = await search(sbx, "Fed interest rate decision December 2024")
        print(f"Search result:\n{result[:500]}..." if len(result) > 500 else f"Search result:\n{result}")

        return True

    finally:
        await sbx.kill()


async def test_economic_model():
    """Test economic shock model in E2B sandbox."""
    # Use code-interpreter-v1 for Python 3.12 (no MCP needed for model)
    sbx = await AsyncSandbox.create(
        template="code-interpreter-v1",
        timeout=300,
    )

    try:
        # Install dependencies from requirements.txt
        print("Installing dependencies...")
        req_path = os.path.join(os.path.dirname(__file__), '..', '..', 'requirements.txt')
        with open(req_path, 'r') as f:
            req_content = f.read()
        await sbx.files.write('/tmp/requirements.txt', req_content)
        await sbx.commands.run('pip install -r /tmp/requirements.txt', timeout=120)

        # Check installed version
        ver = await sbx.commands.run('pip show mesa | grep Version')
        print(f"Mesa version: {ver.stdout}")

        # Read and upload the model code
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'economic_shock.py')
        with open(model_path, 'r') as f:
            model_code = f.read()

        # Write model to sandbox
        await sbx.files.write('/tmp/economic_shock.py', model_code)

        # Run the model test
        print("Running economic shock model in E2B...")
        result = await sbx.commands.run('python3 /tmp/economic_shock.py', timeout=60)

        print(f"Output:\n{result.stdout}")
        if result.stderr:
            print(f"Errors:\n{result.stderr}")

        return True

    finally:
        await sbx.kill()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        asyncio.run(test_perplexity_mcp())
    elif len(sys.argv) > 1 and sys.argv[1] == "model":
        asyncio.run(test_economic_model())
    else:
        asyncio.run(test_sandbox())
