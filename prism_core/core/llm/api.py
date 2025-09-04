from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from .base import BaseLLMService
from .agent_registry import AgentRegistry
from .prism_llm_service import PrismLLMService
from .schemas import (
    GenerationRequest, 
    GenerationResponse, 
    Agent, 
    AgentResponse, 
    LLMGenerationRequest,
    AgentInvokeRequest
)
from ..tools import (
    ToolRegistry, 
    ToolRequest, 
    ToolResponse, 
    ToolInfo,
    BaseTool
)
from ..tools.schemas import AgentToolAssignment, ToolRegistrationRequest


def create_llm_router(agent_registry: AgentRegistry, llm_service: BaseLLMService, tool_registry: ToolRegistry = None) -> APIRouter:
    router = APIRouter()
    
    if tool_registry is None:
        tool_registry = ToolRegistry()

    # PrismLLMService는 내장된 완전한 기능을 제공

    def get_agent_registry():
        return agent_registry

    def get_llm_service():
        return llm_service
        
    def get_tool_registry():
        return tool_registry

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
        """Delete an agent by name."""
        if not registry.delete_agent(agent_name):
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": f"Agent '{agent_name}' has been deleted successfully"}

    @router.post("/agents/{agent_name}/tools", response_model=dict)
    async def assign_tools_to_agent(
        agent_name: str,
        assignment: AgentToolAssignment,
        registry: AgentRegistry = Depends(get_agent_registry)
    ):
        """Assign tools to an agent."""
        try:
            success = registry.assign_tools_to_agent(agent_name, assignment.tool_names)
            if not success:
                raise HTTPException(status_code=404, detail="Agent not found")
            return {"message": f"Tools {assignment.tool_names} assigned to agent '{agent_name}'"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/agents/{agent_name}/invoke", response_model=AgentResponse)
    async def invoke_agent(
        agent_name: str, 
        request: AgentInvokeRequest,
        registry: AgentRegistry = Depends(get_agent_registry),
        llm: BaseLLMService = Depends(get_llm_service),
        tools_reg: ToolRegistry = Depends(get_tool_registry),
    ):
        """Invoke an agent with automatic tool usage."""
        agent = registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # PrismLLMService인 경우 내장된 invoke_agent 메서드 사용 (권장)
        if isinstance(llm, PrismLLMService):
            # 도구 레지스트리 설정
            llm.tool_registry = tools_reg
            return await llm.invoke_agent(agent, request)
        
        # 다른 LLM 서비스를 위한 기본 구현 (폴백)
        llm_request = LLMGenerationRequest(
            prompt=agent.get_full_prompt(request.prompt, []),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )
        generated_text = llm.generate(llm_request)
        
        metadata = {}
        if request.session_id:
            metadata["session_id"] = request.session_id
        
        return AgentResponse(
            text=generated_text, 
            tools_used=[],
            tool_results=[],
            metadata=metadata
        )

    # Tool Management APIs
    @router.get("/tools", response_model=List[ToolInfo])
    async def list_tools(
        tool_registry: ToolRegistry = Depends(get_tool_registry)
    ):
        """List all registered tools."""
        return tool_registry.list_tools()

    @router.post("/tools", response_model=dict)
    async def register_tool(
        request: ToolRegistrationRequest,
        tool_registry: ToolRegistry = Depends(get_tool_registry)
    ):
        """Register a new dynamic tool."""
        try:
            # Extract config from request if it's a custom tool with function code
            config = {}
            
            # If it's a custom tool, check for function_code in the request
            if request.tool_type == "custom":
                # For custom tools, we can accept function_code as part of the request
                # This will be passed to the tool's config
                pass  # Config will be handled separately
            
            tool = tool_registry.register_dynamic_tool(request, config)
            return {
                "message": f"Tool '{tool.name}' registered successfully",
                "tool_info": {
                    "name": tool.name,
                    "description": tool.description,
                    "tool_type": request.tool_type
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/tools/register-with-code", response_model=dict)
    async def register_tool_with_code(
        request: dict,
        tool_registry: ToolRegistry = Depends(get_tool_registry)
    ):
        """Register a new custom tool with function code."""
        try:
            # Validate required fields
            required_fields = ["name", "description", "parameters_schema", "tool_type"]
            for field in required_fields:
                if field not in request:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create tool registration request
            tool_request = ToolRegistrationRequest(
                name=request["name"],
                description=request["description"],
                parameters_schema=request["parameters_schema"],
                tool_type=request["tool_type"]
            )
            
            # Extract config (including function_code for custom tools)
            config = {}
            if "function_code" in request:
                config["function_code"] = request["function_code"]
            if "config" in request:
                config.update(request["config"])
            
            tool = tool_registry.register_dynamic_tool(tool_request, config)
            return {
                "message": f"Tool '{tool.name}' registered successfully with custom code",
                "tool_info": {
                    "name": tool.name,
                    "description": tool.description,
                    "tool_type": request["tool_type"],
                    "has_custom_code": "function_code" in config
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/tools/{tool_name}", response_model=dict)
    async def get_tool_info(
        tool_name: str,
        tool_registry: ToolRegistry = Depends(get_tool_registry)
    ):
        """Get detailed information about a specific tool."""
        tool_info = tool_registry.get_tool_info(tool_name)
        if not tool_info:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool_info

    @router.delete("/tools/{tool_name}")
    async def delete_tool(
        tool_name: str,
        tool_registry: ToolRegistry = Depends(get_tool_registry)
    ):
        """Delete a tool by name."""
        if not tool_registry.delete_tool(tool_name):
            raise HTTPException(status_code=404, detail="Tool not found")
        return {"message": f"Tool '{tool_name}' has been deleted successfully"}

    @router.put("/tools/{tool_name}/config", response_model=dict)
    async def update_tool_config(
        tool_name: str,
        config: Dict[str, Any],
        tool_registry: ToolRegistry = Depends(get_tool_registry)
    ):
        """Update configuration for a dynamic tool."""
        success = tool_registry.update_tool_config(tool_name, config)
        if not success:
            raise HTTPException(status_code=404, detail="Tool not found or not a dynamic tool")
        return {"message": f"Configuration for tool '{tool_name}' updated successfully"}

    @router.post("/tools/execute", response_model=ToolResponse)
    async def execute_tool(
        request: ToolRequest,
        tool_registry: ToolRegistry = Depends(get_tool_registry)
    ):
        """Execute a tool directly."""
        tool = tool_registry.get_tool(request.tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")
        
        try:
            return await tool.execute(request)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

    @router.post("/generate", response_model=GenerationResponse)
    async def generate(
        request: GenerationRequest,
        llm: BaseLLMService = Depends(get_llm_service),
    ):
        """Generate text based on a prompt."""
        llm_request = LLMGenerationRequest(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )
        generated_text = llm.generate(llm_request)
        return GenerationResponse(text=generated_text)
    
    return router


def _extract_database_params(query: str) -> dict:
    """
    Extract database parameters from user query.
    This is a simple implementation that can be enhanced with NLP.
    """
    query_lower = query.lower()
    params = {"action": "list_tables"}  # Default action
    
    # Detect query type
    if any(word in query_lower for word in ["select", "query", "sql"]):
        params["action"] = "query"
        # Try to extract SQL query - this is basic pattern matching
        if "select" in query_lower:
            # For now, just return list_tables as we need more sophisticated parsing
            params["action"] = "list_tables"
    elif any(word in query_lower for word in ["schema", "structure", "columns"]):
        params["action"] = "get_table_schema"
        # Try to extract table name
        for word in query_lower.split():
            if word.endswith("_table") or word.endswith("table"):
                params["table_name"] = word.replace("_table", "").replace("table", "")
                break
    elif any(word in query_lower for word in ["data", "rows", "records", "show"]):
        params["action"] = "get_table_data"
        # Try to extract table name
        for word in query_lower.split():
            if word.endswith("_table") or word.endswith("table"):
                params["table_name"] = word.replace("_table", "").replace("table", "")
                break
        params["limit"] = 10  # Default limit
    
    return params 
