"""Tests for Phase 2: E2B Sandbox with MCP Gateway."""

import pytest
import asyncio
from src.sandbox.runner import create_sandbox


@pytest.mark.asyncio
async def test_create_sandbox(check_api_keys):
    """Test sandbox creation with MCP enabled."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        assert sbx is not None
        assert sbx.sandbox_id is not None
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
async def test_mcp_gateway_url(check_api_keys):
    """Test MCP gateway URL and token generation."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        mcp_url = sbx.get_mcp_url()
        mcp_token = sbx.get_mcp_token()

        assert mcp_url is not None
        assert "mcp" in mcp_url.lower() or "e2b" in mcp_url.lower()
        assert mcp_token is not None
        assert len(mcp_token) > 0
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
async def test_code_execution(check_api_keys):
    """Test code execution in sandbox."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        result = await loop.run_in_executor(
            None, lambda: sbx.commands.run('python3 -c "print(\'Hello from E2B\')"')
        )
        assert "Hello from E2B" in result.stdout
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
@pytest.mark.slow
async def test_mesa_installation(check_api_keys):
    """Test Mesa installation and import in sandbox."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        # Install Mesa (can take a while)
        await loop.run_in_executor(
            None, lambda: sbx.commands.run('pip install mesa', timeout=300)
        )

        # Test import
        result = await loop.run_in_executor(
            None, lambda: sbx.commands.run('''python3 -c "
from mesa import Agent, Model
print('Mesa imported successfully')
"''')
        )
        assert "Mesa imported successfully" in result.stdout
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
async def test_python_execution(check_api_keys):
    """Test basic Python computation in sandbox."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        result = await loop.run_in_executor(
            None, lambda: sbx.commands.run('python3 -c "print(2 + 2)"')
        )
        assert "4" in result.stdout
    finally:
        await loop.run_in_executor(None, sbx.kill)
