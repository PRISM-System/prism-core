"""
Memory Search Tool

사용자의 과거 상호작용 기록을 검색하는 Tool입니다.
Mem0를 활용하여 장기 기억과 개인화된 상호작용을 제공합니다.
PRISM Core의 공통 설정을 사용합니다.
"""

import requests
from typing import Dict, Any, List, Optional
from .base import BaseTool
from .schemas import ToolRequest, ToolResponse
from ..config import settings

try:
    from mem0 import Memory
    from openai import OpenAI
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    print("⚠️  Mem0 라이브러리가 설치되지 않았습니다. 기본 메모리 검색만 사용 가능합니다.")


class MemorySearchTool(BaseTool):
    """
    사용자의 과거 상호작용 기록을 검색하는 Tool
    
    Mem0를 활용한 기능:
    - 사용자별 장기 기억 관리
    - 세션별 컨텍스트 유지
    - 개인화된 응답 생성
    - 적응형 학습 및 기억 강화
    """
    
    def __init__(self, 
                 weaviate_url: Optional[str] = None,
                 openai_base_url: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 client_id: str = "default",
                 class_prefix: str = "Default"):
        super().__init__(
            name="memory_search",
            description="사용자의 과거 상호작용 기록을 검색하여 개인화된 응답을 제공합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 쿼리"},
                    "user_id": {"type": "string", "description": "사용자 ID"},
                    "top_k": {"type": "integer", "description": "반환할 기록 수", "default": 3},
                    "memory_type": {
                        "type": "string", 
                        "enum": ["user", "session", "agent"], 
                        "description": "메모리 타입 (사용자별, 세션별, 에이전트별)", 
                        "default": "user"
                    },
                    "include_context": {
                        "type": "boolean", 
                        "description": "컨텍스트 정보 포함 여부", 
                        "default": True
                    }
                },
                "required": ["query", "user_id"]
            }
        )
        # 에이전트별 설정 또는 기본값 사용
        self._weaviate_url = weaviate_url or settings.WEAVIATE_URL
        self._openai_base_url = openai_base_url or settings.VLLM_OPENAI_BASE_URL
        self._openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self._client_id = client_id
        
        # 에이전트별 클래스명 설정
        self._class_history = f"{class_prefix}History"
        
        # Mem0 초기화
        self._mem0_initialized = False
        self._memory: Optional[Memory] = None
        self._openai_client: Optional[OpenAI] = None
        
        if MEM0_AVAILABLE:
            self._initialize_mem0()

    def _initialize_mem0(self) -> None:
        """Mem0 초기화"""
        try:
            # OpenAI 클라이언트 초기화 (Mem0에서 사용)
            # self._openai_client = OpenAI(
            #     base_url=settings.OPENAI_BASE_URL or "http://localhost:8001/v1",
            #     api_key=settings.OPENAI_API_KEY
            # )
            
            # Mem0 메모리 인스턴스 생성
            self._memory = Memory()
            self._mem0_initialized = True
            
            print("✅ Mem0 메모리 시스템 초기화 완료")
            
        except Exception as e:
            print(f"⚠️  Mem0 초기화 실패: {str(e)}")
            self._mem0_initialized = False

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Tool 실행"""
        try:
            params = request.parameters
            query = params["query"]
            user_id = params["user_id"]
            top_k = params.get("top_k", 3)
            memory_type = params.get("memory_type", "user")
            include_context = params.get("include_context", True)
            
            # Mem0가 사용 가능한 경우 우선 사용
            if self._mem0_initialized and self._memory:
                memories = await self._search_with_mem0(query, user_id, top_k, memory_type)
            else:
                # Mem0가 없는 경우 Vector DB 사용
                memories = await self._search_with_vector_db(query, user_id, top_k)
            
            # 사용자 컨텍스트 정보 추가
            if include_context:
                user_context = await self._get_user_context(user_id)
            else:
                user_context = {}
            
            return ToolResponse(
                success=True,
                data={
                    "query": query,
                    "user_id": user_id,
                    "memories": memories,
                    "user_context": user_context,
                    "memory_type": memory_type,
                    "count": len(memories)
                }
            )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error=f"메모리 검색 실패: {str(e)}"
            )

    async def _search_with_mem0(self, query: str, user_id: str, top_k: int, memory_type: str) -> List[Dict[str, Any]]:
        """Mem0를 사용한 메모리 검색"""
        try:
            # Mem0 검색 실행
            search_result = self._memory.search(
                query=query,
                user_id=user_id,
                limit=top_k,
                memory_type=memory_type
            )
            
            memories = []
            for result in search_result:
                memory_entry = {
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "timestamp": result.get("timestamp", ""),
                    "memory_type": memory_type,
                    "source": "mem0"
                }
                memories.append(memory_entry)
            
            return memories
            
        except Exception as e:
            print(f"⚠️  Mem0 검색 실패: {str(e)}")
            return []

    async def _search_with_vector_db(self, query: str, user_id: str, top_k: int) -> List[Dict[str, Any]]:
        """Vector DB를 사용한 메모리 검색 (Fallback)"""
        try:
            # 직접 Weaviate API 호출
            search_query = f"{query} user:{user_id}"
            
            response = requests.post(
                f"{self._weaviate_url}/v1/objects/{self._class_history}/search",
                json={
                    "query": search_query,
                    "limit": top_k
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            
            memories = []
            if response.status_code == 200:
                results = response.json()
                
                for result in results:
                    memory_entry = {
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0),
                        "timestamp": result.get("timestamp", ""),
                        "memory_type": "vector_db",
                        "source": "weaviate"
                    }
                    memories.append(memory_entry)
            
            return memories
                
        except Exception as e:
            print(f"⚠️  Vector DB 검색 실패: {str(e)}")
            return []

    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """사용자 컨텍스트 정보 조회"""
        try:
            # 사용자별 컨텍스트 정보 구성
            context = {
                "user_id": user_id,
                "preferences": {},
                "recent_interactions": [],
                "expertise_areas": [],
                "last_active": ""
            }
            
            # 최근 상호작용 기록 조회
            recent_query = f"user:{user_id}"
            response = requests.post(
                f"{self._weaviate_url}/v1/objects/{self._class_history}/search",
                json={
                    "query": recent_query,
                    "limit": 5
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            
            if response.status_code == 200:
                recent_results = response.json()
                context["recent_interactions"] = [
                    {
                        "content": result.get("content", ""),
                        "timestamp": result.get("timestamp", "")
                    }
                    for result in recent_results
                ]
            
            return context
            
        except Exception as e:
            print(f"⚠️  사용자 컨텍스트 조회 실패: {str(e)}")
            return {"user_id": user_id}

    async def add_memory(self, user_id: str, content: str, memory_type: str = "user") -> bool:
        """새로운 메모리 추가"""
        try:
            if self._mem0_initialized and self._memory:
                # Mem0에 메모리 추가
                self._memory.add(
                    content=content,
                    user_id=user_id,
                    memory_type=memory_type
                )
                return True
            else:
                # Weaviate에 메모리 추가
                response = requests.post(
                    f"{self._weaviate_url}/v1/objects",
                    json={
                        "class": self._class_history,
                        "properties": {
                            "title": f"Memory for {user_id}",
                            "content": content,
                            "metadata": f'{{"user_id": "{user_id}", "memory_type": "{memory_type}", "timestamp": "2024-01-01T00:00:00Z"}}'
                        }
                    },
                    timeout=10,
                )
                return response.status_code in [200, 201]
                
        except Exception as e:
            print(f"⚠️  메모리 추가 실패: {str(e)}")
            return False 