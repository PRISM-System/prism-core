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
    prompt: Optional[str] = Field(default=None, description="Optional plain prompt; prefer chat messages")
    messages: Optional[List[Dict[str, Any]]] = Field(default=None, description="OpenAI-style chat messages")
    extra_body: Optional[Dict[str, Any]] = Field(default=None, description="Pass-through fields (e.g., messages, tool_choice)")
    max_tokens: int = 1024
    temperature: float = 0.7
    stop: Optional[List[str]] = None

class Agent(BaseModel):
    name: str = Field(..., description="The name of the agent")
    description: str = Field(..., description="The description of the agent")
    role_prompt: str = Field(..., description="The role prompt for the agent")
    tools: List[str] = Field(default_factory=list, description="List of tool names available to this agent")

    def get_full_prompt(self, prompt: str, tool_results: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate full prompt including role, tools info, and tool results if any."""
        full_prompt = f"{self.role_prompt}\n\n"
        
        if self.tools:
            tools_info = f"Available tools: {', '.join(self.tools)}\n"
            full_prompt += tools_info
        
        if tool_results:
            full_prompt += "Tool execution results:\n"
            for i, result in enumerate(tool_results, 1):
                full_prompt += f"Tool {i}: {result}\n"
            full_prompt += "\n"
        
        full_prompt += f"User query: {prompt}"
        return full_prompt

class AgentResponse(GenerationResponse):
    tools_used: List[str] = Field(default_factory=list, description="List of tools used in this response")
    tool_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from tool executions")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata about the response")

class AgentResponseCollection(BaseModel):
    responses: List[AgentResponse]

class AgentInvokeRequest(BaseModel):
    prompt: str = Field(..., description="User prompt/query")
    max_tokens: int = Field(default=1024, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    use_tools: bool = Field(default=True, description="Whether to automatically use tools if relevant") 
    max_tool_calls: int = Field(default=3, description="Max number of tool call rounds for chat with tools")
    extra_body: Optional[Dict[str, Any]] = Field(default=None, description="OpenAI-compatible extra options (e.g., repetition_penalty, chat_template_kwargs)")
    user_id: Optional[str] = Field(default=None, description="User ID for memory search and personalization") 
    tool_for_use: Optional[List[str]] = Field(default=None, description="List of tools to use at this request, all tools should be registered in the tool registry of the agent")