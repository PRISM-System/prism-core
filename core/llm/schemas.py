from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7
    stop: Optional[List[str]] = None
    client_id: Optional[str] = Field(None, description="Client identifier; required when use_tools=True")
    use_tools: bool = Field(False, description="Whether to enable tool calling for this generation")
    max_tool_calls: int = Field(3, description="Max number of tool calls allowed in a single generation")

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

# Tool-related schemas used by API contracts
class HttpEndpoint(BaseModel):
    url: str
    method: str = "POST"
    headers: Optional[Dict[str, str]] = None
    timeout_s: float = 10.0

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    endpoint: HttpEndpoint

class RegisterToolRequest(ToolDefinition):
    pass

class ToolListResponse(BaseModel):
    tools: List[ToolDefinition]

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] 