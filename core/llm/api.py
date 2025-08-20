from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from .base import BaseLLMService
from .agent_registry import AgentRegistry
from .schemas import (
    GenerationRequest,
    GenerationResponse,
    Agent,
    AgentResponse,
    LLMGenerationRequest,
    RegisterToolRequest,
    ToolDefinition,
    ToolListResponse,
)
from .tools import Tool, ToolRegistry
from .tool_orchestrator import ToolOrchestrator
from .openai_compat_service import OpenAICompatService


def create_llm_router(agent_registry: AgentRegistry, llm_service: BaseLLMService, tool_registry: ToolRegistry, openai_service: OpenAICompatService | None = None) -> APIRouter:
    router = APIRouter()

    def get_agent_registry():
        return agent_registry

    def get_llm_service():
        return llm_service

    def get_tool_registry():
        return tool_registry

    def get_openai_service():
        return openai_service

    @router.post("/agents", response_model=Agent)
    async def register_agent(agent: Agent):
        try:
            agent_registry.register_agent(agent)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return agent

    @router.get("/agents", response_model=List[Agent])
    async def get_agents():
        return agent_registry.list_agents()

    @router.delete("/agents/{agent_name}")
    async def delete_agent(
        agent_name: str,
        registry: AgentRegistry = Depends(get_agent_registry)
    ):
        """
        Delete an agent by name.
        """
        if not registry.delete_agent(agent_name):
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": f"Agent '{agent_name}' has been deleted successfully"}

    # Tool management endpoints (per client)
    @router.post("/clients/{client_id}/tools", response_model=ToolDefinition)
    async def register_tool(
        client_id: str,
        request: RegisterToolRequest,
        registry: ToolRegistry = Depends(get_tool_registry),
    ):
        tool = Tool(
            name=request.name,
            description=request.description,
            input_schema=request.input_schema,
            endpoint=request.endpoint,  # type: ignore[arg-type]
        )
        try:
            registry.register_tool(client_id, tool)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return request

    @router.get("/clients/{client_id}/tools", response_model=ToolListResponse)
    async def list_tools(client_id: str, registry: ToolRegistry = Depends(get_tool_registry)):
        tools = registry.list_tools(client_id)
        # Convert internal Tool to API ToolDefinition
        tool_defs = [
            ToolDefinition(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema,
                endpoint=t.endpoint,  # type: ignore[arg-type]
            )
            for t in tools
        ]
        return ToolListResponse(tools=tool_defs)

    @router.delete("/clients/{client_id}/tools/{tool_name}")
    async def delete_tool(client_id: str, tool_name: str, registry: ToolRegistry = Depends(get_tool_registry)):
        if not registry.delete_tool(client_id, tool_name):
            raise HTTPException(status_code=404, detail="Tool not found")
        return {"message": f"Tool '{tool_name}' deleted for client '{client_id}'"}

    def _to_openai_tools(client_id: str, tools_reg: ToolRegistry) -> List[Dict[str, Any]]:
        tools = tools_reg.list_tools(client_id)
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            }
            for t in tools
        ]

    def _run_tool_loop(
        *,
        base_prompt: str,
        client_id: str,
        max_tokens: int,
        temperature: float,
        stop: list | None,
        tools_reg: ToolRegistry,
        oa_service: OpenAICompatService,
    ) -> str:
        # Build initial messages
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": base_prompt},
        ]
        tools_def = _to_openai_tools(client_id, tools_reg)

        # Loop
        for _ in range(16):
            text = oa_service.chat_complete_with_tools(
                messages=messages,
                tools=tools_def,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if text != "__TOOL_CALLS__":
                return text

            # Last assistant message includes tool_calls
            last_msg = messages[-1]
            tool_calls = last_msg.get("tool_calls", [])
            for tc in tool_calls:
                name = tc.get("function", {}).get("name")
                arguments = tc.get("function", {}).get("arguments")
                # Execute
                result = tools_reg.execute_tool(client_id, name, arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "name": name,
                    "content": result,
                })

        # Fallback: return last assistant content if any
        return ""

    @router.post("/agents/{agent_name}/invoke", response_model=AgentResponse)
    async def invoke_agent(
        agent_name: str,
        request: GenerationRequest,
        registry: AgentRegistry = Depends(get_agent_registry),
        llm: BaseLLMService = Depends(get_llm_service),
        tools_reg: ToolRegistry = Depends(get_tool_registry),
        oa_service: OpenAICompatService | None = Depends(get_openai_service),
    ):
        agent = registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        combined_prompt = agent.get_full_prompt(request.prompt)

        if request.use_tools:
            if not request.client_id:
                raise HTTPException(status_code=400, detail="client_id is required when use_tools=True")
            if oa_service is None:
                # Fallback to naive orchestrator if OpenAI-compatible service not provided
                tools = tools_reg.list_tools(request.client_id)
                orchestrator = ToolOrchestrator(llm_service, tools_reg)
                text = orchestrator.generate_with_tools(
                    base_prompt=combined_prompt,
                    client_id=request.client_id,
                    tools=tools,
                    max_tool_calls=request.max_tool_calls,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    stop=request.stop,
                )
                return AgentResponse(text=text)
            # Use vLLM OpenAI-compatible tool calling
            text = _run_tool_loop(
                base_prompt=combined_prompt,
                client_id=request.client_id,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stop=request.stop,
                tools_reg=tools_reg,
                oa_service=oa_service,
            )
            return AgentResponse(text=text)

        llm_request = LLMGenerationRequest(
            prompt=combined_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )
        generated_text = llm_service.generate(llm_request)
        return AgentResponse(text=generated_text)

    @router.post("/generate", response_model=GenerationResponse)
    async def generate(
        request: GenerationRequest,
        llm: BaseLLMService = Depends(get_llm_service),
        tools_reg: ToolRegistry = Depends(get_tool_registry),
        oa_service: OpenAICompatService | None = Depends(get_openai_service),
    ):
        """
        Generate text based on a prompt.
        """
        if request.use_tools:
            if not request.client_id:
                raise HTTPException(status_code=400, detail="client_id is required when use_tools=True")
            if oa_service is None:
                tools = tools_reg.list_tools(request.client_id)
                orchestrator = ToolOrchestrator(llm_service, tools_reg)
                text = orchestrator.generate_with_tools(
                    base_prompt=request.prompt,
                    client_id=request.client_id,
                    tools=tools,
                    max_tool_calls=request.max_tool_calls,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    stop=request.stop,
                )
                return GenerationResponse(text=text)
            text = _run_tool_loop(
                base_prompt=request.prompt,
                client_id=request.client_id,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stop=request.stop,
                tools_reg=tools_reg,
                oa_service=oa_service,
            )
            return GenerationResponse(text=text)

        llm_request = LLMGenerationRequest(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )
        generated_text = llm_service.generate(llm_request)
        return GenerationResponse(text=generated_text)

    return router 