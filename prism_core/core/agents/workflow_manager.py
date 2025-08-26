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
    
    async def execute_workflow(self, workflow_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
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
                step_result = await self._execute_step(step, context, execution_id)
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
    
    async def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any], execution_id: str) -> Dict[str, Any]:
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
                step_result.update(await self._execute_tool_step(step, context))
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
    
    async def _execute_tool_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Tool 호출 단계 실행"""
        if not self.tool_registry:
            return {"success": False, "error": "Tool registry not available"}
        
        tool_name = step.get("tool_name")
        tool = self.tool_registry.get_tool(tool_name)
        
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        # 매개변수 준비 (컨텍스트에서 동적 값 추출)
        parameters = self._prepare_parameters(step.get("parameters", {}), context)
        
        # Tool 타입에 따른 실행 방식 결정
        try:
            if hasattr(tool, 'tool_type'):
                # DynamicTool인 경우
                result = await self._execute_dynamic_tool(tool, parameters)
            elif tool_name == "database_tool":
                # Database Tool인 경우
                result = await self._execute_database_tool(tool, parameters)
            else:
                # 일반 Tool인 경우
                result = await self._execute_generic_tool(tool, parameters)
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_dynamic_tool(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """DynamicTool 실행 (tool_type에 따라 다른 방식)"""
        tool_type = tool.tool_type
        
        if tool_type == "function":
            # Custom 파이프라인: Python 명령어 실행
            return await self._execute_function_pipeline(tool, parameters)
        elif tool_type == "database":
            # Database: PostgreSQL 명령어를 URL로 실행
            return await self._execute_database_command(tool, parameters)
        elif tool_type == "api":
            # API: 해당 API 호출
            return await self._execute_api_call(tool, parameters)
        elif tool_type == "calculation":
            # Calculation: 수학 계산
            return await self._execute_calculation(tool, parameters)
        else:
            return {"success": False, "error": f"Unknown tool type: {tool_type}"}
    
    async def _execute_function_pipeline(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fuction 파이프라인: 전달된 함수만 실행 (실제 파이프라인은 함수 내 구현 버전)
        parameters: { function: callable, args?: list, kwargs?: dict }
        """
        try:
            func = tool
            args = parameters.get("args", [])
            kwargs = parameters.get("kwargs", {})

            if not callable(func):
                return {"success": False, "error": "parameters.function must be a callable"}

            import inspect
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            return {"success": True, "output": {"result": result}}

        except Exception as e:
            return {"success": False, "error": f"Custom pipeline execution failed: {str(e)}"}
            
    async def _execute_database_command(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Database 명령어 실행 (PostgreSQL URL)"""
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            # Database URL에서 연결 정보 추출
            db_url = parameters.get("database_url")
            if not db_url:
                return {"success": False, "error": "Database URL not provided"}
            
            parsed_url = urlparse(db_url)
            
            # PostgreSQL 연결
            conn = psycopg2.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 5432,
                database=parsed_url.path[1:],  # Remove leading slash
                user=parsed_url.username,
                password=parsed_url.password
            )
            
            cursor = conn.cursor()
            
            # SQL 쿼리 실행
            query = parameters.get("query")
            if not query:
                return {"success": False, "error": "SQL query not provided"}
            
            cursor.execute(query)
            
            # 결과 가져오기
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                data = [dict(zip(columns, row)) for row in results]
            else:
                conn.commit()
                data = {"affected_rows": cursor.rowcount}
            
            cursor.close()
            conn.close()
            
            return {"success": True, "output": {"data": data}}
            
        except Exception as e:
            return {"success": False, "error": f"Database execution failed: {str(e)}"}
    
    async def _execute_api_call(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """API 호출 실행"""
        try:
            import requests
            
            url = parameters.get("url")
            method = parameters.get("method", "GET").upper()
            headers = parameters.get("headers", {})
            data = parameters.get("data", {})
            timeout = parameters.get("timeout", 30)
            
            if not url:
                return {"success": False, "error": "API URL not provided"}
            
            # API 호출
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if method in ["POST", "PUT", "PATCH"] else None,
                params=data if method == "GET" else None,
                timeout=timeout
            )
            
            response.raise_for_status()
            
            # 응답 처리
            try:
                result_data = response.json()
            except:
                result_data = response.text
            
            return {
                "success": True,
                "output": {
                    "status_code": response.status_code,
                    "data": result_data,
                    "headers": dict(response.headers)
                }
            }
            
        except requests.RequestException as e:
            return {"success": False, "error": f"API call failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"API execution failed: {str(e)}"}
    
    async def _execute_calculation(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """수학 계산 실행"""
        try:
            import math
            
            expression = parameters.get("expression")
            variables = parameters.get("variables", {})
            
            if not expression:
                return {"success": False, "error": "Expression not provided"}
            
            # 안전한 계산 환경
            safe_namespace = {
                "__builtins__": {},
                "math": math,
                "abs": abs, "min": min, "max": max, "sum": sum, "round": round,
                **variables
            }
            
            # 안전성 검사
            allowed_chars = set("0123456789+-*/.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
            forbidden_keywords = ["import", "exec", "eval", "open", "file", "__"]
            
            if not set(expression).issubset(allowed_chars):
                return {"success": False, "error": "Expression contains forbidden characters"}
            
            for keyword in forbidden_keywords:
                if keyword in expression:
                    return {"success": False, "error": f"Expression contains forbidden keyword: {keyword}"}
            
            result = eval(expression, safe_namespace)
            
            return {
                "success": True,
                "output": {
                    "expression": expression,
                    "result": result,
                    "variables_used": variables
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Calculation failed: {str(e)}"}
    
    async def _execute_database_tool(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Database Tool 실행"""
        try:
            # DatabaseTool의 execute 메서드 호출
            from ..tools.schemas import ToolRequest, ToolResponse
            
            request = ToolRequest(parameters=parameters)
            response = await tool.execute(request)
            
            if response.success:
                return {"success": True, "output": response.result}
            else:
                return {"success": False, "error": response.error_message}
                
        except Exception as e:
            return {"success": False, "error": f"Database tool execution failed: {str(e)}"}
    
    async def _execute_generic_tool(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """일반 Tool 실행"""
        try:
            # Tool의 execute 메서드 호출
            from ..tools.schemas import ToolRequest, ToolResponse
            
            request = ToolRequest(parameters=parameters)
            response = await tool.execute(request)
            
            if response.success:
                return {"success": True, "output": response.result}
            else:
                return {"success": False, "error": response.error_message}
                
        except Exception as e:
            return {"success": False, "error": f"Generic tool execution failed: {str(e)}"}
    
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