import json
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from mcp import ClientSession
from openai import AsyncOpenAI
import logging


load_dotenv("../.env")


class BaseMCPOpenAIClient(ABC):
    """Base client for interacting with OpenAI models using MCP tools."""

    def __init__(self, model: str = "gpt-4o"):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai_client = AsyncOpenAI()
        self.model = model

    @abstractmethod
    async def connect_to_server(self, *args, **kwargs):
        """Connection logic, implemented by subclasses."""
        pass

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get available tools."""
        tools_result = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in tools_result.tools
        ]

    async def process_query(self, query: str) -> str:
        """Process a query w/ MCP tools"""

        tools = await self.get_mcp_tools()

        response = self.openai_client.responses.create(
                    model="gpt-4.1",
                    input=query,
                    tools=tools,
                    tool_choice= "auto")

        response = await self.responses.create(
            model=self.model,
            input=[{"role": "user", "content": query}],
            tools=tools,
            tool_choice="auto",
        )

        assistant_message = response.output_text
        messages = [
            {"role": "user", "content": query},
            assistant_message,
        ]
        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                result = await self.session.call_tool(
                    tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments),
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result.content[0].text,
                    }
                )

            # Get final response from OpenAI with tool results
            final_response = await self.openai_client.responses.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="none",  # Don't allow more tool calls
            )

            return final_response.choices[0].message.content

        return assistant_message.content

    async def cleanup(self):
        """Clean up resources."""
        await self.exit_stack.aclose()

    async def run_interactive_session(self, client_type: str = "MCP"):
        """Run an interactive chat session."""
        query = ""

        print(f"Hi! I am an {client_type} client which provides tools for giving business owners quotes for group health insurance plans.")
        print("Ask me to retrieve eligible plans for a business or estimate individual claims. Type 'exit' to stop.")
        
        while query != "exit":
            query = input("\nYou: ").strip()
            if query == "exit":
                break
            
            try:
                response = await self.process_query(query)
                print(f"\nResponse: {response}")
            except Exception as e:
                print(f"\nError: {e}")
                logging.error(f"Error processing query: {e}")