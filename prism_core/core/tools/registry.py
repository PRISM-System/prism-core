from typing import Dict, List, Optional
from .base import BaseTool
from .schemas import ToolInfo, ToolRegistrationRequest


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        Register a new tool.
        
        Args:
            tool: Tool instance to register
            
        Raises:
            ValueError: If tool with same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered")
        
        self._tools[tool.name] = tool
    
    def register_dynamic_tool(self, request: ToolRegistrationRequest, config: Dict = None) -> BaseTool:
        """
        Register a new dynamic tool from a client request.
        
        Args:
            request: Tool registration request
            config: Additional configuration for the tool
            
        Returns:
            The created tool instance
            
        Raises:
            ValueError: If tool with same name already exists or invalid tool type
        """
        if request.name in self._tools:
            raise ValueError(f"Tool with name '{request.name}' is already registered")
        
        # Validate tool type
        valid_types = ["api", "calculation", "function", "database"]
        if request.tool_type not in valid_types:
            raise ValueError(f"Invalid tool type '{request.tool_type}'. Must be one of: {valid_types}")
        
        # Create dynamic tool (lazy import)
        from .dynamic_tool import DynamicTool
        tool = DynamicTool(
            name=request.name,
            description=request.description,
            parameters_schema=request.parameters_schema,
            tool_type=request.tool_type,
            config=config or {}
        )
        
        # Register the tool
        self._tools[request.name] = tool
        return tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolInfo]:
        """
        Get list of all registered tools.
        
        Returns:
            List of tool information
        """
        return [
            ToolInfo(
                name=tool.name,
                description=tool.description,
                parameters_schema=tool.parameters_schema,
                tool_type=tool.tool_type,
            )
            for tool in self._tools.values()
        ]
    
    def delete_tool(self, name: str) -> bool:
        """
        Delete a tool by name.
        
        Args:
            name: Tool name to delete
            
        Returns:
            True if tool was deleted, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def get_tool_info(self, name: str) -> Optional[Dict]:
        """
        Get detailed information about a tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool information dictionary if found, None otherwise
        """
        tool = self._tools.get(name)
        if not tool:
            return None
        
        info = {
            "name": tool.name,
            "description": tool.description,
            "parameters_schema": tool.parameters_schema,
            "type": "static"  # Default type
        }
        
        # Add additional info for dynamic tools
        if isinstance(tool, DynamicTool):
            info.update({
                "type": "dynamic",
                "tool_type": tool.tool_type,
                "config": tool.config
            })
        
        return info
    
    def get_tools_for_query(self, query: str) -> List[BaseTool]:
        """
        Get tools that might be relevant for a given query.
        This is a simple implementation - could be enhanced with ML/NLP.
        
        Args:
            query: User query
            
        Returns:
            List of potentially relevant tools
        """
        query_lower = query.lower()
        relevant_tools = []
        
        # Simple keyword matching
        for tool in self._tools.values():
            tool_keywords = (tool.description.lower() + " " + tool.name.lower())
            if any(word in tool_keywords for word in query_lower.split()):
                relevant_tools.append(tool)
        
        return relevant_tools
    
    def update_tool_config(self, name: str, config: Dict) -> bool:
        """
        Update configuration for a dynamic tool.
        
        Args:
            name: Tool name
            config: New configuration
            
        Returns:
            True if updated successfully, False if tool not found or not dynamic
        """
        tool = self._tools.get(name)
        if not tool or not isinstance(tool, DynamicTool):
            return False
        
        tool.config.update(config)
        return True 