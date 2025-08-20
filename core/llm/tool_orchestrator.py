import json
import re
from typing import List

from .base import BaseLLMService
from .schemas import LLMGenerationRequest
from .tools import Tool, ToolRegistry


class ToolOrchestrator:
    def __init__(self, llm_service: BaseLLMService, tool_registry: ToolRegistry) -> None:
        self.llm_service = llm_service
        self.tool_registry = tool_registry

    def _build_tools_prompt(self, tools: List[Tool]) -> str:
        if not tools:
            return ""
        lines = [
            "You have access to the following tools. To call a tool, output exactly a JSON object wrapped in <tool_call> tags.",
            "Use this format: <tool_call>{\"tool_name\": \"name\", \"arguments\": { ... }} </tool_call>",
            "If you are ready to provide the final answer, wrap it in <final> ... </final>.",
            "Tools:",
        ]
        for tool in tools:
            lines.append(f"- name: {tool.name}")
            lines.append(f"  description: {tool.description}")
            lines.append("  json_input_schema:")
            lines.append(json.dumps(tool.input_schema))
        return "\n".join(lines)

    def generate_with_tools(self, *, base_prompt: str, client_id: str, tools: List[Tool], max_tool_calls: int, max_tokens: int, temperature: float, stop: list | None) -> str:
        conversation = []
        system_instructions = (
            "You are a helpful assistant that can use tools. "
            "Decide whether a tool is needed. If so, emit a tool call. "
            "Otherwise, output the final answer."
        )
        tool_prompt = self._build_tools_prompt(tools)

        prompt = f"System:\n{system_instructions}\n\n{tool_prompt}\n\nUser:\n{base_prompt}\n"
        for _ in range(max_tool_calls + 1):
            request = LLMGenerationRequest(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop,
            )
            model_output = self.llm_service.generate(request)

            final_match = re.search(r"<final>(.*?)</final>", model_output, flags=re.S)
            if final_match:
                return final_match.group(1).strip()

            tool_match = re.search(r"<tool_call>(\{.*?\})</tool_call>", model_output, flags=re.S)
            if not tool_match:
                # Fallback: no structured output, return raw
                return model_output.strip()

            call_json_text = tool_match.group(1)
            try:
                call_obj = json.loads(call_json_text)
                tool_name = call_obj.get("tool_name")
                arguments = call_obj.get("arguments", {})
            except json.JSONDecodeError:
                return model_output.strip()

            # Execute tool
            tool_result = self.tool_registry.execute_tool(client_id, tool_name, arguments)

            # Append tool result and continue
            prompt += f"\nTool '{tool_name}' result:\n{tool_result}\nNow, based on the tool result, either call another tool or provide the final answer.\n"

        # If exceeded tool call budget, ask model to finalize
        request = LLMGenerationRequest(
            prompt=prompt + "\nPlease provide the final answer wrapped in <final> ... </final>.",
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )
        model_output = self.llm_service.generate(request)
        final_match = re.search(r"<final>(.*?)</final>", model_output, flags=re.S)
        if final_match:
            return final_match.group(1).strip()
        return model_output.strip() 