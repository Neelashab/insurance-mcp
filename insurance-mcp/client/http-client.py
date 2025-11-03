import asyncio
from typing import Any, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import logging
import os
from base_client import BaseMCPOpenAIClient


class MCPOpenAIHTTPClient(BaseMCPOpenAIClient):
    """HTTP Client"""

    def __init__(self, model: str = "gpt-4o", server_address: str = None):
        super().__init__(model)
        self.server_address = server_address or os.getenv("SERVER_ADDRESS", "http://localhost:8000")
        self.read_stream: Optional[Any] = None
        self.write_stream: Optional[Any] = None

    async def connect_to_server(self):

        http_transport = await self.exit_stack.enter_async_context(
            streamablehttp_client(self.server_address)
        )

        self.read_stream, self.write_stream, get_session_id = http_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.read_stream, self.write_stream)
        )

        await self.session.initialize()

        tools_result = await self.session.list_tools()
        logging.info("\nConnected to server with tools:")
        for tool in tools_result.tools:
            logging.info(f"  - {tool.name}: {tool.description}")

async def main():
    client = MCPOpenAIHTTPClient()
    await client.connect_to_server()
    await client.run_interactive_session("MCP HTTP")
    await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())