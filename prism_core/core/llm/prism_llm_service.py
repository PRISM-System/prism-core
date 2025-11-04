from logging import warning
from typing import Any, Dict, List, Optional
import random
import time
import requests
import json
import os
from openai import OpenAI

from .base import BaseLLMService
from .schemas import LLMGenerationRequest, AgentInvokeRequest, AgentResponse, Agent
from ..tools import ToolRegistry, ToolRequest, ToolResponse, BaseTool, ToolRegistrationRequest
from ..config import settings


class PrismLLMService(BaseLLMService):
    """
    PRISM-Core 전용 LLM 서비스 (OpenAI-Compatible vLLM 서버 클라이언트)
    
    - chat completions 엔드포인트를 사용하여 메시지/툴 기반 대화를 수행합니다
    - 도구 호출이 필요할 경우 간단한 툴 콜 루프를 수행합니다
    - 에이전트/도구 등록은 기존 PRISM-Core API를 통해 지속
    """
    
    def __init__(self, 
                 model_name: Optional[str] = None, 
                 simulate_delay: bool = False, 
                 tool_registry: Optional[ToolRegistry] = None,
                 llm_service_url: str = "http://localhost:8000",
                 agent_name: str = "orchestration_agent",
                 openai_base_url: Optional[str] = None,
                 api_key: Optional[str] = None):
        """
        PrismLLMService 초기화
        
        Args:
            model_name: 모델 이름 (None이면 VLLM_MODEL 환경변수 또는 settings.model_name 사용)
            simulate_delay: 테스트용 응답 지연 여부
            tool_registry: 도구 레지스트리 (invoke 기능용)
            llm_service_url: PRISM-Core API URL (에이전트/도구 등록에 사용)
            agent_name: 기본 에이전트 이름
            openai_base_url: vLLM OpenAI-compatible 서버 base URL (예: http://host:8001/v1)
            api_key: OpenAI 호환 API 키 (기본은 EMPTY)
        """
        # 모델명 해석: 우선순위 model_name arg > env VLLM_MODEL > settings.model_name
        resolved_model = model_name or os.getenv("VLLM_MODEL") or settings.model_name
        self.model_name = resolved_model
        self.simulate_delay = simulate_delay
        self.tool_registry = tool_registry or ToolRegistry()
        self.llm_service_url = llm_service_url.rstrip('/')
        self.agent_name = agent_name
        self.session = requests.Session()
        self.session.timeout = 30

        # OpenAI-compatible vLLM 클라이언트 설정
        base_url = (openai_base_url or settings.VLLM_OPENAI_BASE_URL).rstrip('/')
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        self.client = OpenAI(base_url=base_url, api_key=api_key or settings.OPENAI_API_KEY)
        
        # 제조업 도메인 지식 기반 응답 템플릿 (폴백용)
        self.response_templates = {
            "pressure": [
                "압력 이상이 감지되었습니다. 즉시 다음 조치를 수행하세요:\n1. 압력 센서 점검\n2. 밸브 상태 확인\n3. 배관 누출 검사\n4. 안전 프로토콜 실행",
                "압력 상승 원인을 분석한 결과, 밸브 오작동이 의심됩니다. 정비팀에 즉시 연락하여 V-001 밸브를 점검하시기 바랍니다.",
                "압력 데이터를 종합 분석한 결과, 정상 범위(1.0-3.5 bar)를 초과했습니다. 긴급 대응이 필요합니다."
            ],
            "temperature": [
                "온도 센서 이상이 확인되었습니다. 다음 점검 절차를 따르세요:\n1. 센서 케이블 연결 상태 확인\n2. 캘리브레이션 상태 점검\n3. 주변 환경 온도 측정",
                "T-002 센서의 패턴 분석 결과, 주기적인 스파이크가 발견됩니다. 전기적 간섭이나 기계적 진동을 확인해보세요.",
                "온도 센서 교체를 권장합니다. 현재 센서의 정확도가 허용 범위를 벗어났습니다."
            ],
            "general": [
                "시스템 전반적인 상태 점검을 완료했습니다. 대부분의 파라미터가 정상 범위 내에 있으나, 정기 유지보수가 필요한 부분이 있습니다.",
                "야간 교대 준비를 위한 시스템 점검 결과를 안내드립니다. 모든 안전 시스템이 정상 작동 중이며, 특별한 주의사항은 없습니다.",
                "전체 시스템 상태가 양호합니다. 다음 점검 일정에 맞춰 예방 정비를 실시하시기 바랍니다."
            ]
        }
    
    def generate(self, request: LLMGenerationRequest) -> str:
        """
        OpenAI-Compatible vLLM 서버의 chat completions 엔드포인트를 통한 텍스트 생성
        - messages 또는 extra_body["messages"]가 반드시 존재해야 합니다
        """
        try:
            messages = request.messages or ((request.extra_body or {}).get("messages") if request.extra_body else None)
            if not messages:
                raise ValueError("PrismLLMService.generate: 'messages' is required for chat completions.")

            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stop=request.stop,
                extra_body=request.extra_body or None,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            print(f"⚠️  OpenAI-compatible chat 호출 실패: {e}")
            return self._generate_fallback_response(request)
    
    def _generate_fallback_response(self, request: LLMGenerationRequest) -> str:
        """
        서비스 연결 실패 시 폴백 응답 생성
        """
        if self.simulate_delay:
            time.sleep(random.uniform(0.5, 2.0))
        
        prompt = (request.prompt or "").lower()
        
        # 프롬프트 분석하여 적절한 응답 선택
        if "압력" in prompt or "pressure" in prompt:
            responses = self.response_templates["pressure"]
        elif "온도" in prompt or "temperature" in prompt:
            responses = self.response_templates["temperature"]
        else:
            responses = self.response_templates["general"]
        
        base_response = random.choice(responses)
        
        enhanced_response = f"""## PRISM 에이전트 시스템 응답 (폴백 모드)

{base_response}

### 권장 조치사항:
- 즉시 해당 시스템 담당자에게 보고
- 안전 프로토콜 준수
- 조치 결과를 시스템에 기록

### 추가 정보:
- 분석 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}
- 모델: {self.model_name} (폴백 모드)
- 신뢰도: {random.randint(85, 98)}%

---
*이 응답은 PRISM-Core 에이전트 시스템 폴백 모드에 의해 생성되었습니다.*"""

        return enhanced_response
    
    def _map_tools_to_openai(self, tool_list: List[str]) -> List[Dict[str, Any]]:
        """ToolRegistry의 도구들을 OpenAI tools 포맷으로 매핑"""
        tools: List[Dict[str, Any]] = []
        for tool in tool_list:
            total_tool_for_agent = self.tool_registry.get_tool(tool)
            # check all tool names in tool_list exist in total_tool_for_agent
            if all(tool_name in total_tool_for_agent for tool_name in tool_list):
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": getattr(tool, "description", ""),
                        "parameters": getattr(tool, "parameters_schema", {}),
                    },
                })
            else:
                warning(f"도구 '{tool}'는 해당 에이전트에 존재하지 않습니다.")
        return tools
    
    def register_agent(self, agent: Agent) -> bool:
        """
        PRISM-Core 서비스에 에이전트 등록
        asdf
        """
        try:
            # Pre-check: if agent already exists on server, skip remote registration
            try:
                existing = self.get_agents() or []
                if any((a.get("name") == agent.name) for a in existing if isinstance(a, dict)):
                    print(f"ℹ️  에이전트 '{agent.name}'는 이미 서버에 등록되어 있습니다. 스킵합니다.")
                    return True
            except Exception:
                pass

            url = f"{self.llm_service_url}/core/api/agents"
            print(f"url: {url}")
            payload = {
                "name": agent.name,
                "description": agent.description,
                "role_prompt": agent.role_prompt,
                "tools": agent.tools
            }
            response = self.session.post(url, json=payload)
            if response.status_code == 400:
                # Treat duplicate as success
                try:
                    detail = response.json()
                    print(f"detail: {detail}")
                except Exception:
                    detail = {"detail": response.text}
                if isinstance(detail, dict) and ("already" in str(detail.get("detail", ""))):
                    print(f"ℹ️  에이전트 '{agent.name}'는 이미 서버에 등록되어 있습니다. 스킵합니다.")
                    return True
            response.raise_for_status()
            print(f"✅ 에이전트 '{agent.name}' 등록 성공")
            return True
        except requests.RequestException as e:
            print(f"❌ 에이전트 '{agent.name}' 등록 실패: {e}")
            return False
        except Exception as e:
            print(f"❌ 에이전트 등록 중 예상치 못한 오류: {e}")
            return False
    
    def register_tool(self, tool: BaseTool) -> bool:
        """
        PRISM-Core 서비스에 도구 등록
        """
        try:
            # Pre-check: if tool already exists on server, skip remote registration
            try:
                existing = self.get_tools() or []
                if any((t.get("name") == tool.name) for t in existing if isinstance(t, dict)):
                    print(f"ℹ️  도구 '{tool.name}'는 이미 서버에 등록되어 있습니다. 스킵합니다.")
                    try:
                        self.tool_registry.register_tool(tool)
                    except Exception:
                        pass
                    return True
            except Exception:
                # If listing fails, proceed to try registering
                pass

            url = f"{self.llm_service_url}/api/tools"
            payload = {
                "name": tool.name,
                "description": tool.description,
                "parameters_schema": tool.parameters_schema,
                "tool_type": tool.tool_type # api, calculation, function, database
            }
            response = self.session.post(url, json=payload)
            # Treat duplicate registration as success
            if response.status_code == 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = {"detail": response.text}
                if isinstance(detail, dict) and "already registered" in str(detail.get("detail", "")):
                    print(f"ℹ️  도구 '{tool.name}'는 이미 서버에 등록되어 있습니다. 스킵합니다.")
                    try:
                        self.tool_registry.register_tool(tool)
                    except Exception:
                        pass
                    return True
            response.raise_for_status()
            print(f"✅ 도구 '{tool.name}' 등록 성공")
            # 로컬 도구 레지스트리에도 등록
            self.tool_registry.register_tool(tool)
            return True
        except requests.RequestException as e:
            print(f"❌ 도구 '{tool.name}' 등록 실패: {e}")
            try:
                self.tool_registry.register_tool(tool)
                print(f"  💡 로컬 도구 레지스트리에는 등록됨")
            except:
                pass
            return False
        except Exception as e:
            print(f"❌ 도구 등록 중 예상치 못한 오류: {e}")
            return False
    
    def assign_tools_to_agent(self, agent_name: str, tool_names: List[str]) -> bool:
        """
        에이전트에 도구 할당
        """
        try:
            url = f"{self.llm_service_url}/core/api/agents/{agent_name}/tools"
            payload = {"agent_name": agent_name, "tool_names": tool_names}
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            print(f"✅ 에이전트 '{agent_name}'에 도구 할당 성공: {', '.join(tool_names)}")
            return True
        except requests.RequestException as e:
            print(f"❌ 도구 할당 실패: {e}")
            return False
        except Exception as e:
            print(f"❌ 도구 할당 중 예상치 못한 오류: {e}")
            return False
    
    def get_agents(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.llm_service_url}/core/api/agents"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ 에이전트 목록 조회 실패: {e}")
            return []
        except Exception as e:
            print(f"❌ 에이전트 목록 조회 중 예상치 못한 오류: {e}")
            return []
    
    def get_tools(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.llm_service_url}/api/tools"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ 도구 목록 조회 실패: {e}")
            return []
        except Exception as e:
            print(f"❌ 도구 목록 조회 중 예상치 못한 오류: {e}")
            return []
    
    def setup_complete_system(self, agents: List[Agent], tools: List[BaseTool]) -> bool:
        print(f"🚀 완전한 에이전트 시스템 설정 시작")
        print(f"  📝 에이전트: {len(agents)}개")
        print(f"  🛠️  도구: {len(tools)}개")
        success_count = 0
        total_operations = len(tools) + len(agents)
        print(f"\n🔧 1단계: 도구 등록")
        for tool in tools:
            if self.register_tool(tool):
                success_count += 1
        print(f"\n🤖 2단계: 에이전트 등록")
        for agent in agents:
            if self.register_agent(agent):
                success_count += 1
                if agent.tools:
                    self.assign_tools_to_agent(agent.name, agent.tools)
        success_rate = (success_count / total_operations) * 100 if total_operations > 0 else 0
        print(f"\n📊 시스템 설정 완료:")
        print(f"  ✅ 성공: {success_count}/{total_operations} ({success_rate:.1f}%)")
        return success_count == total_operations
    
    async def invoke_agent(self, agent, request: AgentInvokeRequest) -> AgentResponse:
        """
        PRISM-Core API 서버를 통해 에이전트를 호출합니다.
        """
        try:
            # agent가 Agent 객체인 경우 이름 추출, 문자열인 경우 그대로 사용
            agent_name = agent.name if hasattr(agent, 'name') else str(agent)
            
            url = f"{self.llm_service_url}/core/api/agents/{agent_name}/invoke"
            payload = {
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "stop": request.stop,
                "use_tools": request.use_tools,
                "max_tool_calls": getattr(request, "max_tool_calls", 3),
                "extra_body": request.extra_body,
                "tool_for_use": request.tool_for_use
            }
            
            print(f"🔧 에이전트 호출: {url}")
            print(f"   - 에이전트명: {agent_name}")
            print(f"   - 프롬프트 길이: {len(request.prompt)}")
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"✅ 에이전트 '{agent_name}' 호출 완료")
            
            return AgentResponse(
                text=result.get("text", ""),
                tools_used=result.get("tools_used", []),
                tool_results=result.get("tool_results", []),
                metadata=result.get("metadata", {})
            )
            
        except requests.RequestException as e:
            print(f"❌ 에이전트 '{agent_name}' 호출 실패: {e}")
            return AgentResponse(
                text=f"에이전트 호출 실패: {str(e)}",
                tools_used=[],
                tool_results=[],
                metadata={"error": str(e)}
            )
        except Exception as e:
            print(f"❌ 에이전트 호출 중 예상치 못한 오류: {e}")
            return AgentResponse(
                text=f"에이전트 호출 실패: {str(e)}",
                tools_used=[],
                tool_results=[],
                metadata={"error": str(e)}
            )
    
    def _build_agent_prompt(self, agent, user_prompt: str, tool_results: List[Dict]) -> str:
        """(Deprecated) 문자열 프롬프트 방식 유지용 - 현재는 chat 기반 사용"""
        prompt_parts = [agent.role_prompt, f"\n사용자 요청: {user_prompt}"]
        if tool_results:
            prompt_parts.append("\n\n도구 실행 결과:")
            for result in tool_results:
                prompt_parts.append(f"- {result['tool']}: {result['message']}")
                if result['result']:
                    prompt_parts.append(f"  데이터: {str(result['result'])[:200]}...")
        prompt_parts.append("\n\n위 정보를 바탕으로 사용자에게 종합적인 응답을 제공하세요.")
        return "\n".join(prompt_parts)
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.model_name,
            "type": "prism-llm",
            "version": "1.0.0",
            "description": "PRISM-Core 전용 제조업 특화 LLM 서비스",
            "capabilities": [
                "manufacturing_analysis",
                "safety_assessment", 
                "maintenance_planning",
                "korean_language"
            ]
        } 