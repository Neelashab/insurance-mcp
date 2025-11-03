import asyncio
from typing import Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging
from base_client import BaseMCPOpenAIClient


class MCPOpenAIClient(BaseMCPOpenAIClient):
    """STDIO client"""

    def __init__(self, model: str = "gpt-4o"):
        super().__init__(model)
        self.stdio: Optional[Any] = None
        self.write: Optional[Any] = None

    async def connect_to_server(self, server_script_path: str = "../server.py"):
        """Connect to an MCP server via stdio."""
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        tools_result = await self.session.list_tools()
        logging.info("\nConnected to server with tools:")
        for tool in tools_result.tools:
            logging.info(f"  - {tool.name}: {tool.description}")


async def main():
    """Main entry point for the stdio client."""
    client = MCPOpenAIClient()
    await client.connect_to_server("../server.py")
    await client.run_interactive_session("MCP stdio")
    await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())