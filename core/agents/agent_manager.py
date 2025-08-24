"""
Agent Manager

에이전트 생명주기와 관리를 담당하는 클래스입니다.
"""

from typing import Dict, Any, Optional, List
from ..llm.schemas import Agent
from ..tools import ToolRegistry


class AgentManager:
    """
    에이전트 생명주기와 관리를 담당하는 매니저
    
    기능:
    - 에이전트 등록 및 관리
    - 에이전트별 Tool 할당
    - 에이전트 상태 모니터링
    - 에이전트 설정 관리
    """
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.tool_registry: Optional[ToolRegistry] = None
    
    def set_tool_registry(self, tool_registry: ToolRegistry) -> None:
        """Tool Registry 설정"""
        self.tool_registry = tool_registry
    
    def register_agent(self, agent: Agent) -> bool:
        """에이전트 등록"""
        try:
            self.agents[agent.name] = agent
            print(f"✅ 에이전트 '{agent.name}' 등록 완료")
            return True
        except Exception as e:
            print(f"❌ 에이전트 등록 실패: {str(e)}")
            return False
    
    def get_agent(self, agent_name: str) -> Optional[Agent]:
        """에이전트 조회"""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Agent]:
        """등록된 에이전트 목록 반환"""
        return list(self.agents.values())
    
    def delete_agent(self, agent_name: str) -> bool:
        """에이전트 삭제"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            print(f"✅ 에이전트 '{agent_name}' 삭제 완료")
            return True
        else:
            print(f"❌ 에이전트 '{agent_name}'를 찾을 수 없습니다")
            return False
    
    def assign_tools_to_agent(self, agent_name: str, tool_names: List[str]) -> bool:
        """에이전트에 Tool 할당"""
        if agent_name not in self.agents:
            print(f"❌ 에이전트 '{agent_name}'를 찾을 수 없습니다")
            return False
        
        agent = self.agents[agent_name]
        agent.tools = tool_names
        print(f"✅ 에이전트 '{agent_name}'에 {len(tool_names)}개 Tool 할당 완료")
        return True
    
    def get_agent_tools(self, agent_name: str) -> List[str]:
        """에이전트의 Tool 목록 조회"""
        agent = self.get_agent(agent_name)
        return agent.tools if agent else []
    
    def update_agent_config(self, agent_name: str, config: Dict[str, Any]) -> bool:
        """에이전트 설정 업데이트"""
        if agent_name not in self.agents:
            return False
        
        self.agent_configs[agent_name] = config
        print(f"✅ 에이전트 '{agent_name}' 설정 업데이트 완료")
        return True
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """에이전트 설정 조회"""
        return self.agent_configs.get(agent_name, {})
    
    def validate_agent_tools(self, agent_name: str) -> Dict[str, Any]:
        """에이전트의 Tool 유효성 검증"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {"valid": False, "error": "Agent not found"}
        
        if not self.tool_registry:
            return {"valid": False, "error": "Tool registry not set"}
        
        invalid_tools = []
        valid_tools = []
        
        for tool_name in agent.tools:
            if self.tool_registry.get_tool(tool_name):
                valid_tools.append(tool_name)
            else:
                invalid_tools.append(tool_name)
        
        return {
            "valid": len(invalid_tools) == 0,
            "valid_tools": valid_tools,
            "invalid_tools": invalid_tools,
            "total_tools": len(agent.tools)
        }
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """에이전트 상태 정보 조회"""
        agent = self.get_agent(agent_name)
        if not agent:
            return {"status": "not_found"}
        
        tool_validation = self.validate_agent_tools(agent_name)
        
        return {
            "name": agent.name,
            "description": agent.description,
            "tools_count": len(agent.tools),
            "tool_validation": tool_validation,
            "config": self.get_agent_config(agent_name)
        } 