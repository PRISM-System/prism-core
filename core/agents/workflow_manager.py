"""
Workflow Manager

오케스트레이션 워크플로우를 관리하는 클래스입니다.
"""

from typing import Dict, Any, List, Optional
from ..llm.schemas import Agent, AgentInvokeRequest, AgentResponse
from ..tools import ToolRegistry


class WorkflowManager:
    """
    오케스트레이션 워크플로우를 관리하는 매니저
    
    기능:
    - 워크플로우 정의 및 실행
    - 단계별 작업 관리
    - 워크플로우 상태 추적
    - 에러 처리 및 복구
    """
    
    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.tool_registry: Optional[ToolRegistry] = None
    
    def set_tool_registry(self, tool_registry: ToolRegistry) -> None:
        """Tool Registry 설정"""
        self.tool_registry = tool_registry
    
    def define_workflow(self, workflow_name: str, steps: List[Dict[str, Any]]) -> bool:
        """워크플로우 정의"""
        try:
            self.workflows[workflow_name] = {
                "steps": steps,
                "status": "defined",
                "created_at": self._get_timestamp()
            }
            print(f"✅ 워크플로우 '{workflow_name}' 정의 완료")
            return True
        except Exception as e:
            print(f"❌ 워크플로우 정의 실패: {str(e)}")
            return False
    
    def execute_workflow(self, workflow_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 실행"""
        if workflow_name not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_name]
        workflow["status"] = "running"
        
        execution_id = self._generate_execution_id()
        execution_result = {
            "execution_id": execution_id,
            "workflow_name": workflow_name,
            "status": "running",
            "steps": [],
            "start_time": self._get_timestamp(),
            "context": context
        }
        
        try:
            for i, step in enumerate(workflow["steps"]):
                step_result = self._execute_step(step, context, execution_id)
                execution_result["steps"].append(step_result)
                
                if not step_result["success"]:
                    execution_result["status"] = "failed"
                    execution_result["error"] = step_result["error"]
                    break
                
                # 다음 단계에 컨텍스트 전달
                context.update(step_result.get("output", {}))
            
            if execution_result["status"] == "running":
                execution_result["status"] = "completed"
            
            execution_result["end_time"] = self._get_timestamp()
            self.execution_history.append(execution_result)
            
            return execution_result
            
        except Exception as e:
            execution_result["status"] = "failed"
            execution_result["error"] = str(e)
            execution_result["end_time"] = self._get_timestamp()
            self.execution_history.append(execution_result)
            return execution_result
    
    def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
        """단계 실행"""
        step_result = {
            "step_name": step.get("name", "unknown"),
            "step_type": step.get("type", "unknown"),
            "success": False,
            "start_time": self._get_timestamp()
        }
        
        try:
            step_type = step.get("type")
            
            if step_type == "tool_call":
                step_result.update(self._execute_tool_step(step, context))
            elif step_type == "agent_call":
                step_result.update(self._execute_agent_step(step, context))
            elif step_type == "condition":
                step_result.update(self._execute_condition_step(step, context))
            else:
                step_result["error"] = f"Unknown step type: {step_type}"
            
            step_result["end_time"] = self._get_timestamp()
            return step_result
            
        except Exception as e:
            step_result["error"] = str(e)
            step_result["end_time"] = self._get_timestamp()
            return step_result
    
    def _execute_tool_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Tool 호출 단계 실행"""
        if not self.tool_registry:
            return {"success": False, "error": "Tool registry not available"}
        
        tool_name = step.get("tool_name")
        tool = self.tool_registry.get_tool(tool_name)
        
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        # 매개변수 준비 (컨텍스트에서 동적 값 추출)
        parameters = self._prepare_parameters(step.get("parameters", {}), context)
        
        # Tool 실행 (실제로는 async로 실행해야 함)
        # 여기서는 간단한 예시로 동기 실행
        try:
            # 실제 구현에서는 async/await 사용
            result = {"success": True, "output": {"tool_result": "sample"}}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_agent_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 호출 단계 실행"""
        agent_name = step.get("agent_name")
        prompt_template = step.get("prompt_template", "")
        
        # 프롬프트 템플릿에서 컨텍스트 값 치환
        prompt = self._render_template(prompt_template, context)
        
        # 실제 구현에서는 Agent 호출
        try:
            result = {"success": True, "output": {"agent_response": "sample"}}
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_condition_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """조건 단계 실행"""
        condition = step.get("condition", "")
        
        try:
            # 조건 평가 (실제로는 더 안전한 방법 사용)
            condition_result = eval(condition, {"context": context})
            return {
                "success": True,
                "output": {"condition_result": condition_result}
            }
        except Exception as e:
            return {"success": False, "error": f"Condition evaluation failed: {str(e)}"}
    
    def _prepare_parameters(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """매개변수 준비 (컨텍스트 값 치환)"""
        prepared_params = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # 템플릿 변수 치환
                var_name = value[2:-2].strip()
                prepared_params[key] = context.get(var_name, value)
            else:
                prepared_params[key] = value
        
        return prepared_params
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """템플릿 렌더링"""
        rendered = template
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    def _generate_execution_id(self) -> str:
        """실행 ID 생성"""
        import uuid
        return str(uuid.uuid4())
    
    def _get_timestamp(self) -> str:
        """타임스탬프 생성"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        if workflow_name not in self.workflows:
            return {"status": "not_found"}
        
        workflow = self.workflows[workflow_name]
        return {
            "name": workflow_name,
            "status": workflow["status"],
            "steps_count": len(workflow["steps"]),
            "created_at": workflow["created_at"]
        }
    
    def get_execution_history(self, workflow_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """실행 이력 조회"""
        if workflow_name:
            return [execution for execution in self.execution_history 
                   if execution["workflow_name"] == workflow_name]
        else:
            return self.execution_history 