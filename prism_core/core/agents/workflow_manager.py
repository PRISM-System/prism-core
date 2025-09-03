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
        self.llm_service: Optional[Any] = None
        self.agent_manager: Optional[Any] = None
    
    def set_tool_registry(self, tool_registry: ToolRegistry) -> None:
        """Tool Registry 설정"""
        self.tool_registry = tool_registry
    
    def set_llm_service(self, llm_service: Any) -> None:
        """LLM 서비스 설정"""
        self.llm_service = llm_service
    
    def set_agent_manager(self, agent_manager: Any) -> None:
        """에이전트 매니저 설정"""
        self.agent_manager = agent_manager
    
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
            return {"status": "failed", "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_name]
        workflow["status"] = "running"
        
        # steps가 None인 경우 처리
        steps = workflow.get("steps")
        if steps is None:
            return {"status": "failed", "error": "Workflow steps not defined"}
        
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
            import sys
            print(f"🔧 워크플로우 실행: {workflow_name}, 단계 수: {len(steps)}")
            for i, step in enumerate(steps):
                print(f"🔧 단계 {i+1}/{len(steps)} 실행 중: {step.get('name', 'unknown') if step else 'None step'}")
                print(f"🔧 [WF-DEBUG-1] About to execute step: {step}", file=sys.stderr, flush=True)
                step_result = await self._execute_step(step, context, execution_id)
                print(f"🔧 [WF-DEBUG-2] Step completed: {step.get('name', 'unknown')}", file=sys.stderr, flush=True)
                execution_result["steps"].append(step_result)
                
                if not step_result["success"]:
                    execution_result["status"] = "failed"
                    execution_result["error"] = step_result["error"]
                    break
                
                # 다음 단계에 컨텍스트 전달
                output = step_result.get("output", {})
                if output is not None and isinstance(output, dict):
                    context.update(output)
            
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
        import sys
        print(f"🔧 [STEP-EXEC-1] Starting step execution: {step.get('name', 'unknown') if step else 'None'}", file=sys.stderr, flush=True)
        
        if step is None:
            print("🔧 [STEP-EXEC-2] Step is None, returning error", file=sys.stderr, flush=True)
            return {
                "step_name": "unknown",
                "step_type": "unknown", 
                "success": False,
                "error": "Step is None",
                "start_time": self._get_timestamp(),
                "end_time": self._get_timestamp()
            }
            
        step_result = {
            "step_name": step.get("name", "unknown"),
            "step_type": step.get("type", "unknown"),
            "success": False,
            "start_time": self._get_timestamp()
        }
        
        try:
            step_type = step.get("type")
            print(f"🔧 [STEP-EXEC-3] Step type: {step_type}", file=sys.stderr, flush=True)
            
            if step_type == "tool_call":
                step_result.update(await self._execute_tool_step(step, context))
            elif step_type == "agent_call":
                step_result.update(await self._execute_agent_step(step, context))
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
        parameters = step.get("parameters")
        if parameters is None:
            parameters = {}
        parameters = self._prepare_parameters(parameters, context)
        
        # Tool 타입에 따른 실행 방식 결정
        try:
            if hasattr(tool, 'tool_type') and hasattr(tool, 'url'):
                # DynamicTool인 경우 (url 속성을 가진 경우)
                result = await self._execute_dynamic_tool(tool, parameters)
            elif tool_name == "database_tool":
                # Database Tool인 경우
                result = await self._execute_database_tool(tool, parameters)
            else:
                # 일반 Tool인 경우 (BaseTool 파생 클래스들)
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
        """Calculation Tool 실행"""
        try:
            # CalculationTool의 execute 메서드 호출
            from ..tools.schemas import ToolRequest, ToolResponse
            
            request = ToolRequest(tool_name=tool.name, parameters=parameters)
            response = await tool.execute(request)
            
            if response.success:
                return {"success": True, "output": response.result}
            else:
                return {"success": False, "error": response.error_message}
                
        except Exception as e:
            return {"success": False, "error": f"Calculation failed: {str(e)}"}
    
    async def _execute_database_tool(self, tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Database Tool 실행"""
        try:
            # DatabaseTool의 execute 메서드 호출
            from ..tools.schemas import ToolRequest, ToolResponse
            
            request = ToolRequest(tool_name=tool.name, parameters=parameters)
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
            
            request = ToolRequest(tool_name=tool.name, parameters=parameters)
            response = await tool.execute(request)
            
            if response.success:
                return {"success": True, "output": response.result}
            else:
                return {"success": False, "error": response.error_message}
                
        except Exception as e:
            return {"success": False, "error": f"Generic tool execution failed: {str(e)}"}
    
    async def _execute_agent_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 호출 단계 실행"""
        agent_name = step.get("agent_name")
        prompt_template = step.get("prompt_template", "")
        
        # 디버그: 에이전트명 확인
        print(f"🔧 워크플로우 에이전트 호출:")
        print(f"   - 단계명: {step.get('name', 'unknown')}")
        print(f"   - 에이전트명: {agent_name}")
        print(f"   - 프롬프트 템플릿 길이: {len(prompt_template) if prompt_template else 0}")
        
        # 프롬프트 템플릿에서 컨텍스트 값 치환
        prompt = self._render_template(prompt_template, context)
        
        # LLM 서비스가 설정되어 있는지 확인
        if not self.llm_service:
            return {"success": False, "error": "LLM service not available"}
        
        try:
            # 에이전트 호출 요청 생성
            from ..llm.schemas import AgentInvokeRequest
            request = AgentInvokeRequest(
                prompt=prompt,
                max_tokens=context.get("max_tokens", 1024),
                temperature=context.get("temperature", 0.7),
                stop=context.get("stop", None),
                use_tools=context.get("use_tools", False),
                max_tool_calls=context.get("max_tool_calls", 3),
                extra_body=context.get("extra_body", {"enable_thinking": False}),
                user_id=context.get("user_id", None),
                tool_for_use=context.get("tool_for_use", None),
            )
            
            # 원격 API를 통한 에이전트 호출
            import sys
            print(f"🔄 API를 통한 에이전트 호출...", file=sys.stderr, flush=True)
            print(f"🔧 [AGENT-CALL-1] About to invoke agent: {agent_name}", file=sys.stderr, flush=True)
            print(f"🔧 [AGENT-CALL-2] Prompt length: {len(prompt)}", file=sys.stderr, flush=True)
            response = await self.llm_service.invoke_agent(agent_name, request)
            print(f"🔧 [AGENT-CALL-3] Agent response received, length: {len(response.text) if hasattr(response, 'text') else 'unknown'}", file=sys.stderr, flush=True)
            
            print(f"✅ 에이전트 '{agent_name}' 호출 완료 (응답 길이: {len(response.text)})")
            
            return {
                "success": True,
                "output": {"agent_response": response.text}
            }
            
        except Exception as e:
            print(f"❌ 에이전트 '{agent_name}' 호출 실패: {str(e)}")
            return {"success": False, "error": f"Agent execution failed: {str(e)}"}
    
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
        if parameters is None:
            return {}
            
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
        """템플릿 렌더링 (중첩된 객체 접근 지원)"""
        if template is None:
            return ""
            
        rendered = template
        
        # 중첩된 객체 접근을 위한 헬퍼 함수
        def get_nested_value(obj, path):
            """점 표기법을 사용하여 중첩된 객체에서 값을 가져옵니다."""
            keys = path.split('.')
            current = obj
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    current = current[int(key)]
                else:
                    return None
            return current
        
        # 템플릿 변수 치환
        import re
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_match(match):
            var_path = match.group(1).strip()
            value = get_nested_value(context, var_path)
            return str(value) if value is not None else match.group(0)
        
        rendered = re.sub(pattern, replace_match, rendered)
        
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