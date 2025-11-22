"""MCP Client for connecting to E2B Perplexity gateway."""

from contextlib import asynccontextmanager
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from e2b import AsyncSandbox


@asynccontextmanager
async def create_mcp_client(sandbox: AsyncSandbox):
    """Create and connect an MCP client to the sandbox.

    Args:
        sandbox: E2B AsyncSandbox with MCP enabled

    Yields:
        Connected ClientSession
    """
    mcp_url = sandbox.get_mcp_url()
    mcp_token = await sandbox.get_mcp_token()

    async with streamablehttp_client(
        url=mcp_url,
        headers={"Authorization": f"Bearer {mcp_token}"},
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def search(sandbox: AsyncSandbox, query: str) -> str:
    """Search Perplexity via MCP.

    Args:
        sandbox: E2B AsyncSandbox with MCP enabled
        query: Search query string

    Returns:
        Search results as string
    """
    async with create_mcp_client(sandbox) as session:
        # Find the perplexity_ask tool dynamically
        tools = await session.list_tools()
        tool_name = None
        for tool in tools.tools:
            if "perplexity" in tool.name.lower() and "ask" in tool.name.lower():
                tool_name = tool.name
                break

        if not tool_name:
            raise RuntimeError(f"Perplexity ask tool not found. Available: {[t.name for t in tools.tools]}")

        result = await session.call_tool(
            tool_name,
            {"messages": [{"role": "user", "content": query}]}
        )

        # Extract text content from result
        if result.content:
            return "\n".join(
                block.text for block in result.content
                if hasattr(block, 'text')
            )
        return ""
