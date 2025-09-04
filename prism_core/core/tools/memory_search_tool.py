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
    from mem0.configs.base import MemoryConfig
    MEM0_AVAILABLE = False
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
                 model_name: Optional[str] = None,
                 encoder_model: Optional[str] = None,
                 vector_dim: Optional[int] = None,
                 client_id: str = "default",
                 class_prefix: str = "Default",
                 tool_type: str = "api"):
        super().__init__(
            name="memory_search",
            description="사용자의 과거 상호작용 기록을 검색하여 개인화된 응답을 제공합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 쿼리"},
                    "user_id": {"type": "string", "description": "사용자 ID"},
                    "session_id": {"type": "string", "description": "세션 ID (선택사항)", "default": None},
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
            },
            tool_type=tool_type
        )
        # 기존 설정 활용
        self._weaviate_url = weaviate_url or f"http://localhost:18080"  # WEAVIATE_PORT from .env.example
        self._openai_base_url = openai_base_url or settings.VLLM_OPENAI_BASE_URL
        self._openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self._client_id = client_id
        self._model_name = model_name or settings.VLLM_MODEL
        self._encoder_model = encoder_model or settings.VECTOR_ENCODER_MODEL
        self._vector_dim = vector_dim or settings.VECTOR_DIM
        
        # 디버그: 파라미터 설정 확인
        print(f"🔧 MemorySearchTool 초기화 파라미터:")
        print(f"   - weaviate_url: {self._weaviate_url}")
        print(f"   - openai_base_url: {self._openai_base_url}")
        print(f"   - openai_api_key: {self._openai_api_key[:10]}..." if self._openai_api_key != "EMPTY" else "   - openai_api_key: EMPTY")
        print(f"   - model_name: {self._model_name}")
        print(f"   - encoder_model: {self._encoder_model}")
        print(f"   - vector_dim: {self._vector_dim}")
        print(f"   - client_id: {self._client_id}")
        print(f"   - class_prefix: {class_prefix}")
        
        # 에이전트별 클래스명 설정
        self._class_history = f"{class_prefix}History"
        
        # Mem0 초기화
        self._mem0_initialized = False
        self._memory: Optional[Memory] = None
        
        if MEM0_AVAILABLE:
            self._initialize_mem0()

    def _initialize_mem0(self) -> None:
        """Mem0 초기화 - .env.example 설정 기준"""
        try:
            # .env.example 설정을 활용한 Mem0 설정 구성
            config = MemoryConfig(
                vector_store={
                    "provider": "weaviate",
                    "config": { "cluster_url": self._weaviate_url }
                },
                llm={
                    "provider": "openai",
                    "config": { "api_key": self._openai_api_key if self._openai_api_key != "EMPTY" else "EMPTY", "base_url": self._openai_base_url, "model": self._model_name  # VLLM_MODEL from .env.example }
                    }
                },
                embedder={
                    "provider": "huggingface",
                    # "config": {"model_name": self._embedder_model_name}  # VECTOR_ENCODER_MODEL from .env.example, "device": "cuda"  # GPU 사용 시 "cuda"로 변경 가능
                }
            )
            
            # 디버그: Mem0 설정 확인
            # print(f"🔧 Mem0 설정 구성:")
            # print(f"   - Vector Store: {config.vector_store.provider} ({config.vector_store.config.cluster_url})")
            # print(f"   - LLM: {config.llm.provider} ({config.llm.config["base_url"]})")
            # print(f"   - LLM Model: {config.llm.config['model']}")
            # print(f"   - Embedder: {config.embedder.provider} ({config.embedder.config['model_name']})")
            # print(f"   - Embedder Device: {config.embedder.config['device']}")
            
            # Mem0 인스턴스 생성
            self._memory = Memory(config=config)
            self._mem0_initialized = True
            
            print("✅ Mem0 메모리 시스템 초기화 완료 (.env.example 설정 기준)")
            print(f"   - Vector Store: Weaviate ({self._weaviate_url})")
            print(f"   - LLM: OpenAI-compatible ({self._openai_base_url})")
            print(f"   - Model: {self._model_name}")
            print(f"   - Embedder: {self._encoder_model}")
            print(f"   - Vector Dim: {self._vector_dim}")
            
        except Exception as e:
            import traceback
            error_info = traceback.extract_tb(e.__traceback__)
            error_line = error_info[-1].lineno
            error_msg = str(e)
            error_type = type(e).__name__
            error_trace = traceback.format_exc()
            
            print(f"⚠️  Error occurred on line {error_line}")
            print(f"⚠️  Error type: {error_type}")
            print(f"⚠️  Error message: {error_msg}")
            print(f"⚠️  Full traceback:\n{error_trace}")
            print(f"⚠️  Mem0 초기화 실패: {str(e)}")
            self._mem0_initialized = False

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Tool 실행"""
        try:
            params = request.parameters
            query = params["query"]
            user_id = params["user_id"]
            session_id = params.get("session_id", None)
            top_k = params.get("top_k", 3)
            memory_type = params.get("memory_type", "user")
            include_context = params.get("include_context", True)
            
            # Mem0가 사용 가능한 경우 우선 사용
            if self._mem0_initialized and self._memory:
                memories = await self._search_with_mem0(query, user_id, top_k)
            else:
                # Mem0가 없는 경우 Vector DB 사용
                memories = await self._search_with_vector_db(query, user_id, top_k)
            
            # 사용자 컨텍스트 정보 추가
            if include_context:
                user_context = await self._get_user_context(user_id)
            else:
                user_context = {}
            
            response_data = {
                "query": query,
                "user_id": user_id,
                "memories": memories,
                "user_context": user_context,
                "memory_type": memory_type,
                "count": len(memories)
            }
            
            if session_id:
                response_data["session_id"] = session_id
            
            return ToolResponse(
                success=True,
                data=response_data
            )
                
        except Exception as e:
            return ToolResponse(
                success=False,
                error=f"메모리 검색 실패: {str(e)}"
            )

    async def _search_with_mem0(self, query: str, user_id: str, top_k: int) -> List[Dict[str, Any]]:
        """Mem0를 사용한 메모리 검색 - 공식 문서에 따른 올바른 방식"""
        try:
            # Mem0 검색 실행
            search_result = self._memory.search(
                query=query,
                user_id=user_id,
                limit=top_k
            )
            
            memories = []
            for result in search_result:
                memory_entry = {
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "timestamp": result.get("timestamp", ""),
                    "memory_type": "user",
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

    async def add_memory(self, user_id: str, messages: List[Dict[str, str]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """새로운 메모리 추가 - 공식 문서에 따른 올바른 방식"""
        try:
            if self._mem0_initialized and self._memory:
                # Mem0에 메모리 추가 (공식 문서 방식)
                result = self._memory.add(
                    messages=messages,
                    user_id=user_id,
                    metadata=metadata or {}
                )
                return True
            else:
                # Weaviate에 메모리 추가 (Fallback)
                content = "\n".join([msg.get("content", "") for msg in messages])
                response = requests.post(
                    f"{self._weaviate_url}/v1/objects",
                    json={
                        "class": self._class_history,
                        "properties": {
                            "title": f"Memory for {user_id}",
                            "content": content,
                            "metadata": f'{{"user_id": "{user_id}", "memory_type": "user", "timestamp": "2024-01-01T00:00:00Z"}}'
                        }
                    },
                    timeout=10,
                )
                return response.status_code in [200, 201]
                
        except Exception as e:
            print(f"⚠️  메모리 추가 실패: {str(e)}")
            return False

    async def get_user_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 메모리 요약 조회 - 공식 문서에 따른 올바른 방식"""
        try:
            if self._mem0_initialized and self._memory:
                # Mem0를 사용한 메모리 요약
                all_memories = self._memory.get_all(user_id=user_id)
                
                summary = {
                    "user_id": user_id,
                    "total_memories": len(all_memories),
                    "recent_memories": all_memories[-5:] if len(all_memories) > 5 else all_memories,
                    "memory_types": {},
                    "last_updated": all_memories[-1].get("timestamp", "") if all_memories else ""
                }
                
                return summary
            else:
                # Vector DB를 사용한 메모리 요약
                return await self._get_vector_db_summary(user_id)
                
        except Exception as e:
            print(f"⚠️  메모리 요약 조회 실패: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _get_vector_db_summary(self, user_id: str) -> Dict[str, Any]:
        """Vector DB를 사용한 메모리 요약"""
        try:
            response = requests.post(
                f"{self._weaviate_url}/v1/objects/{self._class_history}/search",
                json={
                    "query": f"user:{user_id}",
                    "limit": 10
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            
            if response.status_code == 200:
                results = response.json()
                return {
                    "user_id": user_id,
                    "total_memories": len(results),
                    "recent_memories": results[-5:] if len(results) > 5 else results,
                    "memory_types": {"vector_db": len(results)},
                    "last_updated": results[-1].get("timestamp", "") if results else ""
                }
            else:
                return {"user_id": user_id, "error": "Vector DB 조회 실패"}
                
        except Exception as e:
            return {"user_id": user_id, "error": str(e)}

    def is_mem0_available(self) -> bool:
        """Mem0 사용 가능 여부 확인"""
        return self._mem0_initialized and self._memory is not None 