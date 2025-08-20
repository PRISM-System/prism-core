from typing import Any, Dict, List, Optional
from openai import OpenAI

from ..config import settings


class OpenAICompatService:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        self.base_url = base_url or settings.vllm_openai_base_url
        self.api_key = api_key or settings.openai_api_key
        self.model_name = model_name or settings.model_name
        # Note: vLLM's OpenAI-compatible server ignores api_key by default unless configured
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    @staticmethod
    def _map_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Expecting tools as [{name, description, parameters}], already OpenAI-like
        mapped: List[Dict[str, Any]] = []
        for t in tools:
            mapped.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                }
            })
        return mapped

    def chat_complete_with_tools(
        self,
        *,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tool_choice: Optional[str] = "auto",
    ) -> str:
        openai_tools = self._map_tools(tools)

        while True:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice=tool_choice if openai_tools else None,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choice = resp.choices[0]
            message = choice.message

            # Tool calls
            if message.tool_calls and len(message.tool_calls) > 0:
                # Append assistant message with tool_calls to transcript
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [tc.model_dump() for tc in message.tool_calls],
                })

                # Execute each tool and append tool results
                for tool_call in message.tool_calls:
                    arguments = tool_call.function.arguments
                    # Defer execution to caller by returning tool calls?
                    # In this service we expect the caller to handle tool execution.
                    # For simplicity, return a special marker; the router will handle execution loop.
                    # But to keep service self-contained, we will break here.
                    pass

                # The execution of tools is managed by higher-level orchestration in API.
                # Break to allow caller to execute tools and continue the loop with appended tool results.
                return "__TOOL_CALLS__"

            # Final content
            return message.content or "" 