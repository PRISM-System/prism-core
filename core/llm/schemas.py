from pydantic import BaseModel, Field
from typing import Optional, List

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7
    stop: Optional[List[str]] = None

class GenerationResponse(BaseModel):
    text: str

class LLMGenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7
    stop: Optional[List[str]] = None

class Agent(BaseModel):
    name: str = Field(..., description="The name of the agent")
    description: str = Field(..., description="The description of the agent")
    role_prompt: str = Field(..., description="The role prompt for the agent")

    def get_full_prompt(self, prompt: str) -> str:
        return f"{self.role_prompt}\n\n{prompt}"

class AgentResponse(GenerationResponse):
    pass

class AgentResponseCollection(BaseModel):
    responses: List[AgentResponse] 