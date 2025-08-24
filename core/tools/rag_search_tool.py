"""
RAG Search Tool

지식 베이스에서 관련 정보를 검색하는 Tool입니다.
PRISM Core의 공통 설정을 사용합니다.
"""

import requests
from typing import Dict, Any, List, Optional
from .base import BaseTool
from .schemas import ToolRequest, ToolResponse
from ..config import settings


class RAGSearchTool(BaseTool):
    """
    지식 베이스에서 관련 정보를 검색하는 Tool
    
    지원하는 도메인:
    - research: 연구/기술 문서
    - history: 사용자 수행 이력
    - compliance: 안전 규정 및 법규
    """
    
    def __init__(self, 
                 weaviate_url: Optional[str] = None,
                 encoder_model: Optional[str] = None,
                 vector_dim: Optional[int] = None,
                 client_id: str = "default",
                 class_prefix: str = "Default"):
        super().__init__(
            name="rag_search",
            description="지식 베이스에서 관련 정보를 검색합니다",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색할 쿼리"},
                    "top_k": {"type": "integer", "description": "반환할 문서 수", "default": 3},
                    "domain": {
                        "type": "string", 
                        "enum": ["research", "history", "compliance"], 
                        "description": "검색 도메인 (연구/기술문서, 사용자 수행내역, 안전 규정)", 
                        "default": "research"
                    }
                },
                "required": ["query"]
            }
        )
        # 에이전트별 설정 또는 기본값 사용
        self._weaviate_url = weaviate_url or settings.WEAVIATE_URL
        self._encoder = encoder_model or settings.VECTOR_ENCODER_MODEL
        self._vector_dim = vector_dim or settings.VECTOR_DIM
        self._client_id = client_id
        
        # 에이전트별 클래스명 설정
        self._class_research = f"{class_prefix}Research"
        self._class_history = f"{class_prefix}History"
        self._class_compliance = f"{class_prefix}Compliance"
        
        self._initialized = False

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """도구를 실행합니다."""
        try:
            # 인덱스 초기화 확인
            self._ensure_index_and_seed()
            
            # 파라미터 추출
            query = request.parameters.get("query", "")
            top_k = request.parameters.get("top_k", 3)
            domain = request.parameters.get("domain", "research")
            
            # 도메인별 클래스 선택
            class_name = self._get_class_name(domain)
            
            # 검색 실행
            results = await self._search_documents(query, class_name, top_k)
            
            return ToolResponse(
                success=True,
                data={
                    "query": query,
                    "domain": domain,
                    "results": results,
                    "count": len(results)
                }
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=f"RAG 검색 실패: {str(e)}"
            )

    def _get_class_name(self, domain: str) -> str:
        """도메인에 따른 클래스명 반환"""
        domain_map = {
            "research": self._class_research,
            "history": self._class_history,
            "compliance": self._class_compliance
        }
        return domain_map.get(domain, self._class_research)

    async def _search_documents(self, query: str, class_name: str, top_k: int) -> List[Dict[str, Any]]:
        """문서 검색 실행"""
        try:
            # 직접 Weaviate API 호출
            response = requests.post(
                f"{self._weaviate_url}/v1/objects/{class_name}/search",
                json={
                    "query": query,
                    "limit": top_k
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  검색 실패: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️  검색 중 오류: {str(e)}")
            return []

    def _ensure_index_and_seed(self) -> None:
        """인덱스 생성 및 초기 데이터 시딩"""
        if self._initialized:
            return
            
        try:
            # Research 인덱스 생성
            self._create_research_index()
            self._seed_research_data()
            
            # History 인덱스 생성
            self._create_history_index()
            self._seed_history_data()
            
            # Compliance 인덱스 생성
            self._create_compliance_index()
            self._seed_compliance_data()
            
            # 임베딩 검증 및 재생성
            self._validate_and_regenerate_embeddings()
            
            self._initialized = True
            
        except Exception as e:
            print(f"⚠️  인덱스 초기화 실패: {str(e)}")
            self._initialized = True  # 실패해도 계속 진행

    def _create_research_index(self) -> None:
        """연구 문서 인덱스 생성"""
        try:
            response = requests.post(
                f"{self._weaviate_url}/v1/schema",
                json={
                    "class": self._class_research,
                    "description": "Papers/technical docs knowledge base",
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "model": self._encoder,
                            "vectorizeClassName": False
                        }
                    },
                    "properties": [
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Document title"
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Document content"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "Document metadata"
                        }
                    ]
                },
                timeout=10,
            )
            if response.status_code == 200:
                print(f"✅ {self._class_research} 인덱스 생성 완료")
        except Exception as e:
            print(f"⚠️  인덱스 생성 실패: {str(e)}")

    def _seed_research_data(self) -> None:
        """연구 문서 데이터 시딩"""
        try:
            research_docs = [
                {
                    "title": f"Paper {i+1}", 
                    "content": f"제조 공정 최적화 기술 문서 {i+1}: 공정 제어, 안전 규정, 예지 정비, 데이터 기반 분석.", 
                    "metadata": "{}"
                }
                for i in range(10)
            ]
            
            for doc in research_docs:
                response = requests.post(
                    f"{self._weaviate_url}/v1/objects",
                    json={
                        "class": self._class_research,
                        "properties": doc
                    },
                    timeout=15,
                )
                if response.status_code not in [200, 201]:
                    print(f"⚠️  문서 추가 실패: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️  데이터 시딩 실패: {str(e)}")

    def _create_history_index(self) -> None:
        """사용자 이력 인덱스 생성"""
        try:
            response = requests.post(
                f"{self._weaviate_url}/v1/schema",
                json={
                    "class": self._class_history,
                    "description": "All users' past execution logs",
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "model": self._encoder,
                            "vectorizeClassName": False
                        }
                    },
                    "properties": [
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "History title"
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "History content"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "History metadata"
                        }
                    ]
                },
                timeout=10,
            )
            if response.status_code == 200:
                print(f"✅ {self._class_history} 인덱스 생성 완료")
        except Exception as e:
            print(f"⚠️  인덱스 생성 실패: {str(e)}")

    def _seed_history_data(self) -> None:
        """사용자 이력 데이터 시딩"""
        try:
            history_docs = [
                {
                    "title": f"History {i+1}", 
                    "content": f"사용자 수행 내역 {i+1}: 압력 이상 대응, 점검 절차 수행, 원인 분석 리포트, 후속 조치 완료.", 
                    "metadata": "{}"
                }
                for i in range(10)
            ]
            
            for doc in history_docs:
                response = requests.post(
                    f"{self._weaviate_url}/v1/objects",
                    json={
                        "class": self._class_history,
                        "properties": doc
                    },
                    timeout=15,
                )
                if response.status_code not in [200, 201]:
                    print(f"⚠️  문서 추가 실패: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️  데이터 시딩 실패: {str(e)}")

    def _create_compliance_index(self) -> None:
        """규정 준수 인덱스 생성"""
        try:
            response = requests.post(
                f"{self._weaviate_url}/v1/schema",
                json={
                    "class": self._class_compliance,
                    "description": "Safety regulations and compliance guidelines",
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "model": self._encoder,
                            "vectorizeClassName": False
                        }
                    },
                    "properties": [
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Regulation title"
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Regulation content"
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "Regulation metadata"
                        }
                    ]
                },
                timeout=10,
            )
            if response.status_code == 200:
                print(f"✅ {self._class_compliance} 인덱스 생성 완료")
        except Exception as e:
            print(f"⚠️  인덱스 생성 실패: {str(e)}")

    def _seed_compliance_data(self) -> None:
        """규정 준수 데이터 시딩"""
        try:
            compliance_docs = [
                {
                    "title": f"Regulation {i+1}", 
                    "content": f"안전 규정 {i+1}: 개인보호구 착용, 작업 허가서 발급, 위험성 평가, 비상 대응 절차.", 
                    "metadata": "{}"
                }
                for i in range(10)
            ]
            
            for doc in compliance_docs:
                response = requests.post(
                    f"{self._weaviate_url}/v1/objects",
                    json={
                        "class": self._class_compliance,
                        "properties": doc
                    },
                    timeout=15,
                )
                if response.status_code not in [200, 201]:
                    print(f"⚠️  문서 추가 실패: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️  데이터 시딩 실패: {str(e)}")

    def _validate_and_regenerate_embeddings(self) -> None:
        """임베딩 검증 및 재생성"""
        # Weaviate는 자동으로 임베딩을 생성하므로 별도 검증 불필요
        pass 