from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import httpx

# DEPRECATED: Legacy HTTP tool registry (client-scoped).
# Current orchestration uses OpenAI-compatible chat tools via PrismLLMService.
# This module remains for backward compatibility and standalone HTTP tools.


class HttpEndpoint(BaseModel):
    url: str = Field(..., description="HTTP endpoint URL to invoke the tool")
    method: str = Field("POST", description="HTTP method to invoke the tool: GET or POST")
    headers: Optional[Dict[str, str]] = Field(None, description="Optional HTTP headers to include")
    timeout_s: float = Field(10.0, description="Request timeout in seconds")


class Tool(BaseModel):
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="What the tool does and when to use it")
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for the tool's input arguments")
    endpoint: HttpEndpoint = Field(..., description="How to invoke the tool")

    def to_openai_tool(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._client_to_tools: Dict[str, Dict[str, Tool]] = {}

    def register_tool(self, client_id: str, tool: Tool) -> None:
        if client_id not in self._client_to_tools:
            self._client_to_tools[client_id] = {}
        if tool.name in self._client_to_tools[client_id]:
            raise ValueError(f"Tool with name '{tool.name}' already exists for client '{client_id}'.")
        self._client_to_tools[client_id][tool.name] = tool

    def list_tools(self, client_id: str) -> List[Tool]:
        return list(self._client_to_tools.get(client_id, {}).values())

    def get_tool(self, client_id: str, tool_name: str) -> Optional[Tool]:
        return self._client_to_tools.get(client_id, {}).get(tool_name)

    def delete_tool(self, client_id: str, tool_name: str) -> bool:
        tools_for_client = self._client_to_tools.get(client_id)
        if not tools_for_client or tool_name not in tools_for_client:
            return False
        del tools_for_client[tool_name]
        return True

    def execute_tool(self, client_id: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        tool = self.get_tool(client_id, tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found for client '{client_id}'.")

        endpoint = tool.endpoint
        timeout = httpx.Timeout(endpoint.timeout_s)
        headers = endpoint.headers or {}

        try:
            if endpoint.method.upper() == "GET":
                with httpx.Client(timeout=timeout) as client:
                    resp = client.get(endpoint.url, params=arguments, headers=headers)
            else:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(endpoint.url, json=arguments, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            return f"[tool_error] HTTP error invoking tool '{tool_name}': {e}"

        # Try to return JSON if available, else text
        try:
            data = resp.json()
            return str(data)
        except ValueError:
            return resp.text 