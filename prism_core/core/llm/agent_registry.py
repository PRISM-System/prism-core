from typing import Dict, List, Optional, Any
from .schemas import Agent
from ..tools import ToolRegistry, BaseTool
import re
import json


class AgentRegistry:
    def __init__(self, tool_registry: ToolRegistry = None):
        self._agents: Dict[str, Agent] = {}
        self.tool_registry = tool_registry or ToolRegistry()

    def register_agent(self, agent: Agent):
        if agent.name in self._agents:
            raise ValueError(f"Agent with name '{agent.name}' is already registered.")
        
        # Validate that all assigned tools exist
        for tool_name in agent.tools:
            if not self.tool_registry.get_tool(tool_name):
                raise ValueError(f"Tool '{tool_name}' not found in tool registry")
        
        self._agents[agent.name] = agent

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        return self._agents.get(agent_name)

    def list_agents(self) -> List[Agent]:
        return list(self._agents.values())

    def delete_agent(self, agent_name: str) -> bool:
        """
        Delete an agent by name.
        
        Args:
            agent_name: Name of the agent to delete
            
        Returns:
            True if agent was deleted, False if agent was not found
        """
        if agent_name in self._agents:
            del self._agents[agent_name]
            return True
        return False
    
    def assign_tools_to_agent(self, agent_name: str, tool_names: List[str]) -> bool:
        """
        Assign tools to an existing agent.
        
        Args:
            agent_name: Name of the agent
            tool_names: List of tool names to assign
            
        Returns:
            True if successful, False if agent not found
            
        Raises:
            ValueError: If any tool doesn't exist
        """
        agent = self._agents.get(agent_name)
        if not agent:
            return False
        
        # Validate all tools exist
        for tool_name in tool_names:
            if not self.tool_registry.get_tool(tool_name):
                raise ValueError(f"Tool '{tool_name}' not found in tool registry")
        
        # Update agent tools
        agent.tools = tool_names
        return True
    
    def get_relevant_tools_for_query(self, agent_name: str, query: str) -> List[BaseTool]:
        """
        Get tools assigned to an agent that are relevant for a query.
        
        Args:
            agent_name: Name of the agent
            query: User query
            
        Returns:
            List of relevant tools
        """
        agent = self._agents.get(agent_name)
        if not agent:
            return []
        
        relevant_tools = []
        for tool_name in agent.tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool and self._is_tool_relevant(tool, query):
                relevant_tools.append(tool)
        
        return relevant_tools
    
    def _is_tool_relevant(self, tool: BaseTool, query: str) -> bool:
        """
        Determine if a tool is relevant for a given query.
        This is a simple implementation that can be enhanced.
        
        Args:
            tool: Tool to check
            query: User query
            
        Returns:
            True if tool seems relevant
        """
        query_lower = query.lower()
        tool_keywords = (tool.description.lower() + " " + tool.name.lower())
        
        # Database tool keywords
        db_keywords = [
            "data", "database", "table", "query", "select", "count", "find", 
            "search", "lot", "process", "manufacturing", "sensor", "parameter",
            "history", "measure", "cvd", "etch", "cmp"
        ]
        
        # Check if query contains database-related terms and tool is database tool
        if tool.name == "database_tool":
            return any(keyword in query_lower for keyword in db_keywords)
        
        # General keyword matching
        return any(word in tool_keywords for word in query_lower.split())
    
    def should_use_tools(self, query: str) -> bool:
        """
        Determine if tools should be used for a given query.
        
        Args:
            query: User query
            
        Returns:
            True if tools should be used
        """
        query_lower = query.lower()
        
        # Keywords that suggest tool usage
        tool_indicators = [
            "data", "table", "query", "find", "search", "count", "show", "list",
            "get", "retrieve", "check", "analyze", "how many", "what is"
        ]
        
        return any(indicator in query_lower for indicator in tool_indicators) 