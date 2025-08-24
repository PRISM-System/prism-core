import abc
from typing import Any, Dict, Optional, List
from .schemas import ToolRequest, ToolResponse


class BaseTool(abc.ABC):
    """
    Base class for all tools.
    
    Tools are reusable components that agents can use to perform specific actions
    like database queries, API calls, calculations, etc.
    """
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        """
        Initialize a tool.
        
        Args:
            name: Unique name for the tool
            description: Description of what the tool does
            parameters_schema: JSON schema defining the parameters this tool accepts
        """
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
    
    @abc.abstractmethod
    async def execute(self, request: ToolRequest) -> ToolResponse:
        """
        Execute the tool with given parameters.
        
        Args:
            request: Tool request containing parameters
            
        Returns:
            Tool response with results
        """
        raise NotImplementedError
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate parameters against the schema.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Simple validation - in real implementation would use jsonschema
        required_params = self.parameters_schema.get("required", [])
        for param in required_params:
            if param not in parameters:
                return False
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information including schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters_schema": self.parameters_schema
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>" 