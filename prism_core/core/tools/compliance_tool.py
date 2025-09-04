"""
Compliance Tool

안전 규정 및 법규 준수 여부를 검증하는 Tool입니다.
LLM을 통한 지능형 규정 준수 분석을 제공합니다.
RAG Search Tool의 compliance 도메인을 활용합니다.
"""

import requests
import json
import sys
from typing import Dict, Any, List, Optional
from .base import BaseTool
from .schemas import ToolRequest, ToolResponse
from ..config import settings

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI 라이브러리가 설치되지 않았습니다. 기본 키워드 분석만 사용 가능합니다.")


class ComplianceTool(BaseTool):
    """
    안전 규정 및 법규 준수 여부를 검증하는 Tool
    
    기능:
    - 제안된 조치의 안전 규정 준수 여부 검증
    - 관련 법규 및 사내 규정 매칭 (RAG Search Tool의 compliance 도메인 활용)
    - LLM을 통한 지능형 준수 여부 판단
    - 준수 여부에 따른 권장사항 제공
    """
    
    def __init__(self, 
                 weaviate_url: Optional[str] = None,
                 openai_base_url: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 model_name: Optional[str] = None,
                 encoder_model: Optional[str] = None,
                 vector_dim: Optional[int] = None,
                 client_id: str = "default",
                 class_prefix: str = "Default",
                 tool_type: str = "api"):
        super().__init__(
            name="compliance_check",
            description="제안된 조치가 안전 규정 및 사내 규정을 준수하는지 검증합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "검증할 조치 내용"},
                    "context": {"type": "string", "description": "조치의 맥락 정보"},
                    "user_id": {"type": "string", "description": "사용자 ID (선택사항)"},
                    "session_id": {"type": "string", "description": "세션 ID (선택사항)", "default": None}
                },
                "required": ["action"]
            },
            tool_type=tool_type
        )
        # 에이전트별 설정 또는 기본값 사용
        self._weaviate_url = weaviate_url or settings.WEAVIATE_URL
        self._openai_base_url = openai_base_url or settings.VLLM_OPENAI_BASE_URL
        self._openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self._model_name = model_name or settings.DEFAULT_MODEL
        self._encoder_model = encoder_model or settings.VECTOR_ENCODER_MODEL
        self._vector_dim = vector_dim or settings.VECTOR_DIM
        self._client_id = client_id
        
        # RAG Search Tool 초기화 (compliance 도메인 전용)
        from .rag_search_tool import RAGSearchTool
        self._rag_tool = RAGSearchTool(
            weaviate_url=self._weaviate_url,
            encoder_model=self._encoder_model,
            vector_dim=self._vector_dim,
            client_id=self._client_id,
            class_prefix=class_prefix
        )
        
        # OpenAI 클라이언트 초기화
        self._openai_client = None
        if OPENAI_AVAILABLE:
            self._initialize_openai()

    def _initialize_openai(self) -> None:
        """OpenAI 클라이언트 초기화"""
        try:
            self._openai_client = OpenAI(
                base_url=self._openai_base_url,
                api_key=self._openai_api_key
            )
            print("✅ OpenAI 클라이언트 초기화 완료")
        except Exception as e:
            print(f"⚠️  OpenAI 클라이언트 초기화 실패: {str(e)}")
            self._openai_client = None

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Tool 실행"""
        try:
            params = request.parameters
            action = params["action"]
            context = params.get("context", "")
            user_id = params.get("user_id", "")
            session_id = params.get("session_id", "")
            
            # 1. RAG Search Tool을 사용하여 compliance 도메인에서 관련 규정 검색
            compliance_docs = await self._search_compliance_rules(action, context)
            
            print(f"🔍 Compliance docs: {compliance_docs}", file=sys.stderr, flush=True)
            
            # 2. LLM을 통한 준수 여부 분석
            compliance_analysis = await self._analyze_compliance_with_llm(action, context, compliance_docs)
            print(f"🔍 Compliance analysis: {compliance_analysis}", file=sys.stderr, flush=True)
            
            return ToolResponse(
                success=True,
                result=compliance_analysis
            )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error_message=f"규정 준수 검증 실패: {str(e)}"
            )

    async def _search_compliance_rules(self, action: str, context: str) -> List[Dict[str, Any]]:
        """RAG Search Tool을 사용하여 compliance 도메인에서 관련 규정 검색"""
        try:
            # RAG Search Tool 요청 생성
            from .schemas import ToolRequest as RAGToolRequest
            
            search_query = f"안전 규정 준수 검증: {action} {context}"
            
            rag_request = RAGToolRequest(
                tool_name="rag_search",
                parameters={
                    "query": search_query,
                    "top_k": 5,
                    "domain": "compliance"  # compliance 도메인만 검색
                }
            )
            
            print(f"🔍 RAG Search Tool로 compliance 도메인 검색: {search_query}", file=sys.stderr, flush=True)
            
            # RAG Search Tool 실행
            rag_response = await self._rag_tool.execute(rag_request)
            print(f"🔍 RAG Search Tool 응답: {rag_response}", file=sys.stderr, flush=True)
            
            if rag_response.success:
                results = rag_response.result
                print(f"✅ RAG Search Tool에서 {len(results)}개 결과 반환", file=sys.stderr, flush=True)
                
                # 결과 포맷 변환 (LLM 분석에 적합하도록)
                formatted_results = []
                for result in results:
                    props = result.get("properties", {})
                    formatted_results.append({
                        "title": props.get("title", ""),
                        "content": props.get("content", ""),
                        "metadata": props.get("metadata", "{}"),
                        "certainty": result.get("certainty", 0.0),
                        "class": result.get("class", "")
                    })
                
                return formatted_results
            else:
                print(f"⚠️  RAG Search Tool 검색 실패: {rag_response.error}", file=sys.stderr, flush=True)
                return []
                
        except Exception as e:
            print(f"⚠️  RAG Search Tool 사용 중 오류: {str(e)}", file=sys.stderr, flush=True)
            return []

    async def _analyze_compliance_with_llm(self, action: str, context: str, compliance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """LLM을 통한 준수 여부 분석"""
        if not self._openai_client:
            # OpenAI가 없는 경우 기본 키워드 분석
            return self._basic_compliance_analysis(action, context, compliance_docs)
        
        try:
            # 관련 규정 정보 구성
            rules_text = ""
            for doc in compliance_docs:
                title = doc.get("title", "")
                content = doc.get("content", "")
                class_name = doc.get("class", "")
                
                # KOSHA 데이터인지 확인하여 출처 표시
                source_info = "KOSHA 안전규정" if "KOSHA" in class_name else "사내 안전규정"
                rules_text += f"**[{source_info}] {title}**\n{content}\n\n"
            
            # LLM 프롬프트 구성
            prompt = f"""
다음 조치가 안전 규정을 준수하는지 분석해주세요:

**검토할 조치:**
{action}

**조치 맥락:**
{context}

**관련 안전 규정:**
{rules_text}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{{
    "status": "compliant|non_compliant|requires_review",
    "risk_level": "low|medium|high",
    "related_rules": ["관련된 규정들의 제목"],
    "recommendations": ["구체적인 권장사항들"],
    "reasoning": "상세한 분석 근거"
}}
"""
            
            # LLM 호출
            response = self._openai_client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": "당신은 안전 규정 준수 전문가입니다. 정확하고 신중한 분석을 제공해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            # 응답 파싱
            result_text = response.choices[0].message.content
            
            # JSON 파싱 시도
            try:
                import json
                import re
                
                # JSON 블록 추출
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    parsed_result = json.loads(json_str)
                    
                    # 필수 필드 확인 및 기본값 설정
                    return {
                        "status": parsed_result.get("status", "requires_review"),
                        "risk_level": parsed_result.get("risk_level", "medium"),
                        "related_rules": parsed_result.get("related_rules", [doc.get("title", "") for doc in compliance_docs[:3]]),
                        "recommendations": parsed_result.get("recommendations", [
                            "안전 규정을 다시 한번 확인하세요",
                            "필요시 안전 담당자와 상의하세요",
                            "작업 허가서를 발급받으세요"
                        ]),
                        "reasoning": parsed_result.get("reasoning", result_text)
                    }
                else:
                    # JSON 파싱 실패 시 텍스트 분석
                    return self._parse_text_analysis(result_text, compliance_docs)
                    
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 분석
                return self._parse_text_analysis(result_text, compliance_docs)
                
        except Exception as e:
            print(f"⚠️  LLM 분석 실패: {str(e)}", file=sys.stderr, flush=True)
            return self._basic_compliance_analysis(action, context, compliance_docs)

    def _parse_text_analysis(self, result_text: str, compliance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """텍스트 기반 분석 결과 파싱"""
        lines = result_text.split('\n')
        status = "requires_review"
        risk_level = "medium"
        related_rules = []
        recommendations = []
        reasoning = result_text
        
        for line in lines:
            line = line.strip().lower()
            if "status" in line or "준수" in line:
                if "compliant" in line and "non_compliant" not in line:
                    status = "compliant"
                elif "non_compliant" in line:
                    status = "non_compliant"
            elif "risk" in line or "위험" in line:
                if "low" in line or "낮음" in line:
                    risk_level = "low"
                elif "high" in line or "높음" in line:
                    risk_level = "high"
            elif "recommendation" in line or "권장" in line:
                recommendations.append(line)
        
        # 관련 규정 추출
        related_rules = [doc.get("title", "") for doc in compliance_docs[:3]]
        
        if not recommendations:
            recommendations = [
                "안전 규정을 다시 한번 확인하세요",
                "필요시 안전 담당자와 상의하세요",
                "작업 허가서를 발급받으세요"
            ]
        
        return {
            "status": status,
            "risk_level": risk_level,
            "related_rules": related_rules,
            "recommendations": recommendations,
            "reasoning": reasoning
        }

    def _basic_compliance_analysis(self, action: str, context: str, compliance_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """기본 키워드 기반 준수 여부 분석"""
        # 위험 키워드 체크
        danger_keywords = ["위험", "폭발", "화재", "독성", "고압", "고온", "전기", "화학물질", "밀폐공간", "고소작업"]
        safety_keywords = ["안전", "보호", "점검", "허가", "절차", "규정", "교육", "장비", "검사"]
        
        action_lower = action.lower()
        context_lower = context.lower()
        
        # 위험도 평가
        danger_count = sum(1 for keyword in danger_keywords if keyword in action_lower or keyword in context_lower)
        safety_count = sum(1 for keyword in safety_keywords if keyword in action_lower or keyword in context_lower)
        
        # 상태 결정
        if danger_count > safety_count and danger_count > 2:
            status = "non_compliant"
            risk_level = "high"
        elif safety_count > danger_count:
            status = "compliant"
            risk_level = "low"
        else:
            status = "requires_review"
            risk_level = "medium"
        
        # 관련 규정 추출
        related_rules = []
        for doc in compliance_docs[:3]:
            title = doc.get("title", "규정")
            if title:
                related_rules.append(title)
        
        return {
            "status": status,
            "risk_level": risk_level,
            "related_rules": related_rules,
            "recommendations": [
                "안전 규정을 다시 한번 확인하세요",
                "필요시 안전 담당자와 상의하세요",
                "작업 허가서를 발급받아야 합니다",
                "개인보호구 착용을 확인하세요",
                "작업 전 위험성 평가를 실시하세요"
            ],
            "reasoning": f"기본 키워드 분석 결과: 위험 키워드 {danger_count}개, 안전 키워드 {safety_count}개 검출. compliance 도메인에서 관련 규정 {len(compliance_docs)}개 확인됨."
        } 