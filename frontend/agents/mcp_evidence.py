"""Official ClickHouse MCP boundary used by Studio Mesh agents at runtime."""

async def run_mcp_query(query: str) -> str:
    """Execute a read through the official ClickHouse/mcp-clickhouse server."""
    # Lazy imports keep pure compliance/unit tests independent of integration
    # packages while production installs both from requirements.txt.
    from fastmcp import Client
    from mcp_clickhouse.mcp_server import mcp as clickhouse_mcp_server

    async with Client(clickhouse_mcp_server) as client:
        result = await client.call_tool("run_query", {"query": query})
    return str(result.data if result.data is not None else result.content[0].text)
