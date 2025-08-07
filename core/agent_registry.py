from typing import Dict, List, Optional
from .schemas import Agent

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def register_agent(self, agent: Agent):
        if agent.name in self._agents:
            raise ValueError(f"Agent with name '{agent.name}' is already registered.")
        self._agents[agent.name] = agent

    def get_agent(self, agent_name: str) -> Optional[Agent]:
        return self._agents.get(agent_name)

    def list_agents(self) -> List[Agent]:
        return list(self._agents.values())

agent_registry = AgentRegistry() 