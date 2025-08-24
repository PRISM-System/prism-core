import abc
from typing import Any, Dict

class BaseAgent(abc.ABC):
    """
    The base class for all agents.

    This class defines the essential interface that all agents must implement.
    Agents are responsible for handling a specific task or domain, interacting with
    LLMs, memory, and other tools as needed.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abc.abstractmethod
    def invoke(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        The main method to execute the agent's logic.

        This method should be implemented by all subclasses to define the agent's
        core behavior. It takes a user input and an optional context dictionary,
        and returns the agent's response as a string.

        Args:
            user_input: The input from the user.
            context: An optional dictionary containing additional context for the agent,
                     such as session data or information from other agents.

        Returns:
            The agent's response as a string.
        """
        raise NotImplementedError

    def _call_llm(self, prompt: str, **kwargs) -> str:
        """A helper method to interact with the LLM service."""
        # In a real implementation, this would call the llm_service
        print(f"Calling LLM with prompt: {prompt}")
        return "LLM response to the prompt."

    def _search_memory(self, query: str) -> str:
        """A helper method to search the agent's memory."""
        # This would interact with a memory module (e.g., Weaviate)
        print(f"Searching memory with query: {query}")
        return "Memory search result."

    def _use_tool(self, tool_name: str, **kwargs) -> str:
        """A helper method to use an external tool or API."""
        # This would call another API or service
        print(f"Using tool: {tool_name} with args: {kwargs}")
        return "Tool execution result."

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>" 