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
        result = await session.call_tool(
            "perplexity-ask-perplexity_ask",
            {"messages": [{"role": "user", "content": query}]}
        )

        # Extract text content from result
        if result.content:
            return "\n".join(
                block.text for block in result.content
                if hasattr(block, 'text')
            )
        return ""
