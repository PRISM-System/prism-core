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
        """문서 검색 실행 - nearText를 기본으로 사용 (Weaviate가 자동으로 벡터화)"""
        try:
            # Weaviate의 text2vec-transformers가 자동으로 벡터화 처리
            # nearText가 가장 안정적이고 권장되는 방법
            graphql_query = {
                "query": f'''
                {{
                    Get {{
                        {class_name}(
                            nearText: {{
                                concepts: ["{query}"]
                            }}
                            limit: {top_k}
                        ) {{
                            title
                            content
                            metadata
                            _additional {{
                                id
                                distance
                                certainty
                                vector
                            }}
                        }}
                    }}
                }}
                '''
            }
            
            response = requests.post(
                f"{self._weaviate_url}/v1/graphql",
                json=graphql_query,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"⚠️  GraphQL nearText 오류: {data['errors']}")
                    # Fallback to basic search
                    return self._fallback_search_documents(query, class_name, top_k)
                
                results = data.get("data", {}).get("Get", {}).get(class_name, [])
                
                # Format results to match expected structure
                formatted_results = []
                for result in results:
                    # Get distance and certainty
                    distance = result.get("_additional", {}).get("distance", 1.0)
                    certainty = result.get("_additional", {}).get("certainty", 0.0)
                    
                    formatted_results.append({
                        "class": class_name,
                        "id": result.get("_additional", {}).get("id", ""),
                        "properties": {
                            "title": result.get("title", ""),
                            "content": result.get("content", ""),
                            "metadata": result.get("metadata", "{}")
                        },
                        "vectorWeights": result.get("_additional", {}).get("vector", None),
                        "certainty": certainty,
                        "distance": distance
                    })
                
                print(f"✅ nearText 검색 성공: {len(formatted_results)}개 결과")
                return formatted_results
            else:
                print(f"⚠️  GraphQL nearText 검색 실패: {response.status_code}")
                # Fallback to basic search
                return self._fallback_search_documents(query, class_name, top_k)
                
        except Exception as e:
            print(f"⚠️  nearText 검색 중 오류: {str(e)}")
            # Fallback to basic search
            return self._fallback_search_documents(query, class_name, top_k)


    def _fallback_search_documents(self, query: str, class_name: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback 단순 검색 - GraphQL이 실패할 때 사용"""
        try:
            # REST API로 모든 객체 조회
            response = requests.get(
                f"{self._weaviate_url}/v1/objects",
                params={
                    "class": class_name,
                    "limit": top_k * 3  # 더 많이 가져와서 필터링
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            
            if response.status_code == 200:
                data = response.json()
                objects = data.get("objects", [])
                
                # 간단한 키워드 매칭으로 필터링
                query_lower = query.lower()
                filtered_objects = []
                
                for obj in objects:
                    props = obj.get("properties", {})
                    title = props.get("title", "").lower()
                    content = props.get("content", "").lower()
                    
                    if query_lower in title or query_lower in content:
                        filtered_objects.append(obj)
                
                # 상위 top_k개만 반환
                return filtered_objects[:top_k]
            else:
                print(f"⚠️  Fallback 검색 실패: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️  Fallback 검색 중 오류: {str(e)}")
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
            # 기존 클래스가 있는지 확인
            existing_response = requests.get(f"{self._weaviate_url}/v1/schema/{self._class_research}")
            if existing_response.status_code == 200:
                print(f"✅ {self._class_research} 클래스 이미 존재")
                return
                
            response = requests.post(
                f"{self._weaviate_url}/v1/schema",
                json={
                    "class": self._class_research,
                    "description": "Papers/technical docs knowledge base",
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "vectorizeClassName": False,
                            "poolingStrategy": "masked_mean",
                            "vectorizePropertyName": False
                        }
                    },
                    "properties": [
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Document title",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": False,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Document content",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": False,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "Document metadata",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": True,
                                    "vectorizePropertyName": False
                                }
                            }
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
            # 기존 클래스가 있는지 확인
            existing_response = requests.get(f"{self._weaviate_url}/v1/schema/{self._class_history}")
            if existing_response.status_code == 200:
                print(f"✅ {self._class_history} 클래스 이미 존재")
                return
                
            response = requests.post(
                f"{self._weaviate_url}/v1/schema",
                json={
                    "class": self._class_history,
                    "description": "All users' past execution logs",
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "vectorizeClassName": False,
                            "poolingStrategy": "masked_mean",
                            "vectorizePropertyName": False
                        }
                    },
                    "properties": [
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "History title",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": False,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "History content",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": False,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "History metadata",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": True,
                                    "vectorizePropertyName": False
                                }
                            }
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
            # 기존 클래스가 있는지 확인
            existing_response = requests.get(f"{self._weaviate_url}/v1/schema/{self._class_compliance}")
            if existing_response.status_code == 200:
                print(f"✅ {self._class_compliance} 클래스 이미 존재")
                return
            
            response = requests.post(
                f"{self._weaviate_url}/v1/schema",
                json={
                    "class": self._class_compliance,
                    "description": "Safety regulations and compliance guidelines",
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "vectorizeClassName": False,
                            "poolingStrategy": "masked_mean",
                            "vectorizePropertyName": False
                        }
                    },
                    "properties": [
                        {
                            "name": "title",
                            "dataType": ["text"],
                            "description": "Regulation title",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": False,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Regulation content",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": False,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "metadata",
                            "dataType": ["text"],
                            "description": "Regulation metadata",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": True,
                                    "vectorizePropertyName": False
                                }
                            }
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
        try:
            # 각 클래스에서 샘플 문서의 벡터 확인
            for class_name in [self._class_research, self._class_history, self._class_compliance]:
                try:
                    # GraphQL로 첫 번째 객체의 벡터 확인
                    query = {
                        "query": f'''
                        {{
                            Get {{
                                {class_name}(limit: 1) {{
                                    title
                                    _additional {{
                                        id
                                        vector
                                    }}
                                }}
                            }}
                        }}
                        '''
                    }
                    
                    response = requests.post(
                        f"{self._weaviate_url}/v1/graphql",
                        json=query,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        objects = data.get("data", {}).get("Get", {}).get(class_name, [])
                        
                        if objects:
                            obj = objects[0]
                            vector = obj.get("_additional", {}).get("vector")
                            
                            if vector and len(vector) > 0:
                                print(f"✅ {class_name} 벡터화 확인 완료 (차원: {len(vector)})")
                            else:
                                print(f"⚠️  {class_name} 벡터화 미완료 - 재처리 필요")
                                # 벡터 재생성 시도
                                self._trigger_vectorization(class_name)
                        else:
                            print(f"⚠️  {class_name}에 데이터 없음")
                    else:
                        print(f"⚠️  {class_name} 벡터 확인 실패: {response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️  {class_name} 벡터 검증 중 오류: {str(e)}")
                    
        except Exception as e:
            print(f"⚠️  전체 벡터 검증 실패: {str(e)}")

    def _trigger_vectorization(self, class_name: str) -> None:
        """특정 클래스의 벡터화 다시 트리거"""
        try:
            # 모든 객체를 다시 읽어서 벡터화 트리거
            response = requests.get(
                f"{self._weaviate_url}/v1/objects",
                params={"class": class_name, "limit": 10},
                timeout=10
            )
            
            if response.status_code == 200:
                objects = response.json().get("objects", [])
                for obj in objects:
                    obj_id = obj["id"]
                    properties = obj["properties"]
                    
                    # 객체 업데이트로 벡터화 다시 트리거
                    update_response = requests.put(
                        f"{self._weaviate_url}/v1/objects/{obj_id}",
                        json={
                            "class": class_name,
                            "properties": properties
                        },
                        timeout=10
                    )
                    
                    if update_response.status_code == 200:
                        print(f"📝 {class_name} 객체 {obj_id[:8]}... 벡터화 재트리거")
                    
        except Exception as e:
            print(f"⚠️  {class_name} 벡터화 재트리거 실패: {str(e)}")
    
    def upload_documents(self, documents: List[Dict[str, Any]], domain: str = "compliance") -> Dict[str, Any]:
        """
        문서를 특정 도메인에 업로드
        
        Args:
            documents: 업로드할 문서 리스트 (title, content, metadata 포함)
            domain: 업로드 대상 도메인 (research, history, compliance)
        
        Returns:
            업로드 결과 (성공 개수, 실패 개수 등)
        """
        try:
            # 인덱스 초기화 확인
            self._ensure_index_and_seed()
            
            # 도메인별 클래스 선택
            class_name = self._get_class_name(domain)
            
            success_count = 0
            failed_count = 0
            vectorized_count = 0
            
            for doc in documents:
                try:
                    # 문서 데이터 준비
                    properties = {
                        "title": doc.get("title", ""),
                        "content": doc.get("content", ""),
                        "metadata": str(doc.get("metadata", {}))
                    }
                    
                    # Weaviate에 문서 추가
                    response = requests.post(
                        f"{self._weaviate_url}/v1/objects",
                        json={
                            "class": class_name,
                            "properties": properties
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=15,
                    )
                    
                    if response.status_code in [200, 201]:
                        success_count += 1
                        
                        # 벡터화 확인
                        response_data = response.json()
                        object_id = response_data.get("id")
                        
                        if object_id:
                            # 생성된 객체의 벡터 확인
                            if self._verify_document_vector(class_name, object_id):
                                vectorized_count += 1
                            else:
                                print(f"⚠️  문서 '{doc.get('title', 'Unknown')}' 벡터화 실패 - 재시도")
                                # 벡터화 재시도
                                self._retry_vectorization(class_name, object_id, properties)
                    else:
                        failed_count += 1
                        print(f"⚠️  문서 업로드 실패: {response.status_code} - {doc.get('title', 'Unknown')}")
                        if response.text:
                            print(f"    오류 상세: {response.text[:200]}")
                        
                except Exception as e:
                    failed_count += 1
                    print(f"⚠️  문서 업로드 중 오류: {str(e)} - {doc.get('title', 'Unknown')}")
            
            result = {
                "success": True,
                "domain": domain,
                "class_name": class_name,
                "total": len(documents),
                "uploaded": success_count,
                "vectorized": vectorized_count,
                "failed": failed_count
            }
            
            print(f"✅ 문서 업로드 완료: {success_count}/{len(documents)} 성공, {vectorized_count}개 벡터화 완료 ({domain} 도메인)")
            return result
            
        except Exception as e:
            error_msg = f"문서 업로드 실패: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "domain": domain,
                "total": len(documents),
                "uploaded": 0,
                "vectorized": 0,
                "failed": len(documents)
            }
    
    def batch_upload_documents(self, documents: List[Dict[str, Any]], domain: str = "compliance", batch_size: int = 100) -> Dict[str, Any]:
        """
        배치로 대량 문서 업로드
        
        Args:
            documents: 업로드할 문서 리스트
            domain: 업로드 대상 도메인
            batch_size: 배치 크기
        
        Returns:
            업로드 결과
        """
        try:
            # 인덱스 초기화 확인
            self._ensure_index_and_seed()
            
            # 도메인별 클래스 선택
            class_name = self._get_class_name(domain)
            
            total_success = 0
            total_failed = 0
            total_vectorized = 0
            
            # 배치 처리
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_objects = []
                
                for doc in batch:
                    batch_objects.append({
                        "class": class_name,
                        "properties": {
                            "title": doc.get("title", ""),
                            "content": doc.get("content", ""),
                            "metadata": str(doc.get("metadata", {}))
                        }
                    })
                
                try:
                    # Weaviate 배치 업로드
                    response = requests.post(
                        f"{self._weaviate_url}/v1/batch/objects",
                        json={"objects": batch_objects},
                        headers={"Content-Type": "application/json"},
                        timeout=30,
                    )
                    
                    if response.status_code in [200, 201]:
                        response_data = response.json()
                        
                        # 각 객체의 업로드 결과 확인
                        if isinstance(response_data, list):
                            for obj_result in response_data:
                                if obj_result.get("result", {}).get("status") == "SUCCESS":
                                    total_success += 1
                                    obj_id = obj_result.get("id")
                                    if obj_id and self._verify_document_vector(class_name, obj_id):
                                        total_vectorized += 1
                                else:
                                    total_failed += 1
                        else:
                            total_success += len(batch)
                    else:
                        total_failed += len(batch)
                        print(f"⚠️  배치 업로드 실패: {response.status_code}")
                        if response.text:
                            print(f"    오류 상세: {response.text[:200]}")
                        
                except Exception as e:
                    total_failed += len(batch)
                    print(f"⚠️  배치 업로드 중 오류: {str(e)}")
                
                # 진행상황 출력
                progress = ((i + len(batch)) / len(documents)) * 100
                print(f"📊 업로드 진행: {progress:.1f}% ({i + len(batch)}/{len(documents)})")
                
                # 벡터화 대기
                import time
                time.sleep(0.5)  # 벡터화 처리를 위한 짧은 대기
            
            result = {
                "success": True,
                "domain": domain,
                "class_name": class_name,
                "total": len(documents),
                "uploaded": total_success,
                "vectorized": total_vectorized,
                "failed": total_failed
            }
            
            print(f"✅ 배치 업로드 완료: {total_success}/{len(documents)} 성공, {total_vectorized}개 벡터화 완료 ({domain} 도메인)")
            return result
            
        except Exception as e:
            error_msg = f"배치 업로드 실패: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "domain": domain,
                "total": len(documents),
                "uploaded": 0,
                "vectorized": 0,
                "failed": len(documents)
            }
    
    def _verify_document_vector(self, class_name: str, object_id: str) -> bool:
        """문서가 벡터화되었는지 확인"""
        try:
            response = requests.get(
                f"{self._weaviate_url}/v1/objects/{class_name}/{object_id}",
                params={"include": "vector"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                vector = data.get("vector")
                return vector is not None and len(vector) > 0
            
            return False
            
        except Exception as e:
            print(f"⚠️  벡터 확인 중 오류: {str(e)}")
            return False
    
    def _retry_vectorization(self, class_name: str, object_id: str, properties: Dict[str, Any]) -> bool:
        """문서 벡터화 재시도"""
        try:
            # 문서 내용을 다시 업데이트하여 벡터화 트리거
            response = requests.patch(
                f"{self._weaviate_url}/v1/objects/{class_name}/{object_id}",
                json={"properties": properties},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code == 204:
                # 벡터화 완료 대기
                import time
                time.sleep(1)
                
                # 벡터 재확인
                if self._verify_document_vector(class_name, object_id):
                    print(f"✅ 벡터화 재시도 성공: {object_id[:8]}...")
                    return True
                else:
                    print(f"⚠️  벡터화 재시도 실패: {object_id[:8]}...")
                    return False
            else:
                print(f"⚠️  문서 업데이트 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️  벡터화 재시도 중 오류: {str(e)}")
            return False
    
    def check_document_exists(self, title: str, domain: str = "compliance") -> bool:
        """
        문서 존재 여부 확인
        
        Args:
            title: 확인할 문서 제목
            domain: 검색할 도메인
        
        Returns:
            문서 존재 여부
        """
        try:
            class_name = self._get_class_name(domain)
            
            # Weaviate GraphQL 쿼리
            query = {
                "query": f'''
                {{
                    Get {{
                        {class_name}(
                            where: {{
                                path: ["title"]
                                operator: Equal
                                valueText: "{title}"
                            }}
                            limit: 1
                        ) {{
                            title
                        }}
                    }}
                }}
                '''
            }
            
            response = requests.post(
                f"{self._weaviate_url}/v1/graphql",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("data", {}).get("Get", {}).get(class_name, [])
                return len(results) > 0
            
            return False
            
        except Exception as e:
            print(f"⚠️  문서 존재 확인 실패: {str(e)}")
            return False 