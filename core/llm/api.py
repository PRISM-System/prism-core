from fastapi import APIRouter, Depends, HTTPException
from typing import List

from .base import BaseLLMService
from .agent_registry import AgentRegistry
from .schemas import (
    GenerationRequest, 
    GenerationResponse, 
    Agent, 
    AgentResponse, 
    LLMGenerationRequest
)

def create_llm_router(agent_registry: AgentRegistry, llm_service: BaseLLMService) -> APIRouter:
    router = APIRouter()

    def get_agent_registry():
        return agent_registry

    def get_llm_service():
        return llm_service

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

    @router.post("/agents/{agent_name}/invoke", response_model=AgentResponse)
    async def invoke_agent(
        agent_name: str, 
        request: GenerationRequest,
        registry: AgentRegistry = Depends(get_agent_registry),
        llm: BaseLLMService = Depends(get_llm_service)
    ):
        agent = registry.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        combined_prompt = agent.get_full_prompt(request.prompt)

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
        llm: BaseLLMService = Depends(get_llm_service)
    ):
        """
        Generate text based on a prompt.
        """
        llm_request = LLMGenerationRequest(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=request.stop,
        )
        generated_text = llm_service.generate(llm_request)
        return GenerationResponse(text=generated_text)
    
    return router 