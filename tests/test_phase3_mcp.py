"""Tests for Phase 3: Perplexity MCP Client."""

import pytest
import asyncio
from src.sandbox.runner import create_sandbox
from src.mcp_clients.perplexity_client import create_mcp_client, search


@pytest.mark.asyncio
async def test_mcp_client_connection(check_api_keys):
    """Test MCP client connection to gateway."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        async with create_mcp_client(sbx) as session:
            assert session is not None
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
async def test_list_tools(check_api_keys):
    """Test listing available MCP tools."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        async with create_mcp_client(sbx) as session:
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]

            assert len(tool_names) > 0
            # Check for Perplexity tools
            assert any("perplexity" in name.lower() for name in tool_names)
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
async def test_perplexity_search(check_api_keys):
    """Test Perplexity search via MCP."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        result = await search(sbx, "What is 2+2?")

        assert result is not None
        assert len(result) > 0
        # Should contain some response
        assert isinstance(result, str)
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
async def test_perplexity_search_news(check_api_keys):
    """Test Perplexity search for news/current events."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        result = await search(sbx, "Fed interest rate decision December 2024")

        assert result is not None
        assert len(result) > 0
        # Should contain relevant keywords
        assert any(word in result.lower() for word in ["fed", "rate", "percent", "interest"])
    finally:
        await loop.run_in_executor(None, sbx.kill)


@pytest.mark.asyncio
async def test_search_returns_string(check_api_keys):
    """Test that search returns a string."""
    sbx = await create_sandbox()
    loop = asyncio.get_event_loop()

    try:
        result = await search(sbx, "Python programming language")

        assert isinstance(result, str)
        assert len(result) > 10  # Should have some content
    finally:
        await loop.run_in_executor(None, sbx.kill)
