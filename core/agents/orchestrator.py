from typing import Any, Dict

from .base import BaseAgent


class OrchestrationAgent(BaseAgent):
    """
    An agent responsible for orchestrating tasks among other agents and tools.

    This agent receives a user request, determines the best agent or tool to
    handle the request, and delegates the task accordingly.
    """

    def __init__(self, available_agents: Dict[str, BaseAgent]):
        super().__init__(
            name="orchestration_agent",
            description="A master agent that routes tasks to the appropriate sub-agent."
        )
        self.available_agents = available_agents

    def invoke(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        Orchestrates a task based on user input.

        1.  Uses an LLM to decide which sub-agent is best suited for the task.
        2.  Delegates the task to the selected agent.
        """
        print(f"Orchestrator received input: '{user_input}'")

        # 1. Decide which agent to use
        agent_names = list(self.available_agents.keys())
        prompt = (
            f"Given the user request: '{user_input}', "
            f"which of the following agents is the most appropriate to handle this task? "
            f"Please respond with only the name of the agent. "
            f"Available agents: {agent_names}"
        )
        
        # Use the internal _call_llm method to make the decision
        # In a real scenario, the LLM would return one of the agent names.
        # For this example, we'll simulate the LLM's response.
        chosen_agent_name = self._call_llm(prompt) 
        
        # --- Simulation for this example ---
        # Let's pretend the LLM chose 'safety_protocol_assistant' for safety-related queries
        if "황산" in user_input or "안전" in user_input:
            chosen_agent_name = "safety_protocol_assistant"
        else:
            # A mock default agent
            chosen_agent_name = agent_names[0] if agent_names else None
        # --- End of Simulation ---
        
        print(f"Orchestrator decided to use: '{chosen_agent_name}'")

        # 2. Delegate the task to the chosen agent
        if chosen_agent_name and chosen_agent_name in self.available_agents:
            chosen_agent = self.available_agents[chosen_agent_name]
            # The orchestrator calls the 'invoke' method of the sub-agent
            return chosen_agent.invoke(user_input, context)
        
        return "Sorry, I could not find an appropriate agent to handle your request." 