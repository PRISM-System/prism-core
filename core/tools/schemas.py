from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List


class ToolRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")


class ToolResponse(BaseModel):
    """Response from tool execution."""
    success: bool = Field(..., description="Whether the tool execution was successful")
    result: Any = Field(None, description="Tool execution result")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time_ms: Optional[float] = Field(None, description="Tool execution time in milliseconds")


class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters_schema: Dict[str, Any] = Field(..., description="JSON schema for tool parameters")


class ToolRegistrationRequest(BaseModel):
    """Request to register a new tool."""
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Tool description")
    parameters_schema: Dict[str, Any] = Field(..., description="JSON schema for tool parameters")
    tool_type: str = Field(..., description="Type of tool (e.g., 'database', 'api', 'calculation')")


class AgentToolAssignment(BaseModel):
    """Request to assign tools to an agent."""
    agent_name: str = Field(..., description="Name of the agent")
    tool_names: List[str] = Field(..., description="List of tool names to assign to the agent") 