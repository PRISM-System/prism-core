from fastapi import APIRouter, HTTPException
from .llm_service import llm_service
from .agent_registry import agent_registry
from .schemas import (
    GenerationRequest, 
    GenerationResponse, 
    Agent, 
    AgentResponse, 
    LLMGenerationRequest
)
from typing import List

router = APIRouter()

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

@router.post("/agents/{agent_name}/invoke", response_model=AgentResponse)
async def invoke_agent(agent_name: str, request: GenerationRequest):
    agent = agent_registry.get_agent(agent_name)
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
async def generate(request: GenerationRequest):
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