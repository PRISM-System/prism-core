"""
Weaviate Client

Weaviate Vector Database와의 연결 및 기본 CRUD 작업을 담당
"""

import uuid
import time
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

try:
    import weaviate
    from weaviate.client import Client
except ImportError:
    raise ImportError("Weaviate client not installed. Run: pip install weaviate-client")

from .schemas import DocumentSchema, SearchQuery, SearchResult, IndexConfig, VectorDBStatus, BulkOperation
from .encoder import EncoderManager

logger = logging.getLogger(__name__)


class WeaviateClient:
    """
    Weaviate Vector Database 클라이언트
    
    문서 인덱싱, 검색, 삭제 등의 기본 기능을 제공
    """
    
    def __init__(
        self,
        url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        timeout: int = 60,
        encoder: Optional[EncoderManager] = None
    ):
        """
        Weaviate 클라이언트 초기화
        
        Args:
            url: Weaviate 서버 URL
            api_key: API 키 (필요한 경우)
            timeout: 연결 타임아웃
            encoder: 텍스트 인코더 (선택사항)
        """
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.encoder = encoder
        
        self.client: Optional[Client] = None
        self._connected = False
        
    def connect(self) -> bool:
        """Weaviate 서버에 연결"""
        try:
            # 인증 설정
            auth_config = None
            if self.api_key:
                auth_config = weaviate.AuthApiKey(api_key=self.api_key)
            
            # 클라이언트 생성
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config,
                timeout_config=(5, self.timeout)
            )
            
            # 연결 테스트
            if self.client.is_ready():
                self._connected = True
                logger.info(f"Connected to Weaviate at {self.url}")
                return True
            else:
                logger.error("Weaviate server is not ready")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """연결 해제"""
        if self.client:
            self.client = None
        self._connected = False
        logger.info("Disconnected from Weaviate")
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        if not self._connected or not self.client:
            return False
        
        try:
            return self.client.is_ready()
        except:
            self._connected = False
            return False
    
    def create_index(self, config: IndexConfig) -> bool:
        """
        새 인덱스(클래스) 생성
        
        Args:
            config: 인덱스 설정
            
        Returns:
            성공 여부
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Weaviate")
        
        try:
            schema = config.get_weaviate_schema()
            
            # 기존 클래스가 있는지 확인
            if self.client.schema.exists(config.class_name):
                logger.warning(f"Class {config.class_name} already exists")
                return False
            
            # 클래스 생성
            self.client.schema.create_class(schema)
            logger.info(f"Created class: {config.class_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create class {config.class_name}: {e}")
            return False
    
    def delete_index(self, class_name: str) -> bool:
        """
        인덱스(클래스) 삭제
        
        Args:
            class_name: 클래스명
            
        Returns:
            성공 여부
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Weaviate")
        
        try:
            if not self.client.schema.exists(class_name):
                logger.warning(f"Class {class_name} does not exist")
                return False
            
            self.client.schema.delete_class(class_name)
            logger.info(f"Deleted class: {class_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete class {class_name}: {e}")
            return False
    
    def add_document(self, class_name: str, document: DocumentSchema) -> Optional[str]:
        """
        단일 문서 추가
        
        Args:
            class_name: 클래스명
            document: 문서 데이터
            
        Returns:
            생성된 문서 ID
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Weaviate")
        
        try:
            # 벡터 생성 (인코더가 있는 경우)
            vector = None
            if self.encoder and document.content:
                embeddings = self.encoder.encode_texts(document.content)
                vector = embeddings[0].tolist()
            elif document.vector:
                vector = document.vector
            
            # 문서 데이터 준비
            properties = {
                "content": document.content,
                "title": document.title,
                "source": document.source,
                "created_at": document.created_at.isoformat() if document.created_at else datetime.now().isoformat()
            }
            
            # 메타데이터 추가
            if document.metadata:
                for key, value in document.metadata.items():
                    if key not in properties:
                        properties[key] = value
            
            # 문서 ID 생성 또는 사용
            doc_id = document.id or str(uuid.uuid4())
            
            # 문서 추가
            self.client.data_object.create(
                data_object=properties,
                class_name=class_name,
                uuid=doc_id,
                vector=vector
            )
            
            logger.debug(f"Added document {doc_id} to {class_name}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document to {class_name}: {e}")
            return None
    
    def add_documents(self, class_name: str, documents: List[DocumentSchema]) -> List[Optional[str]]:
        """
        배치로 문서 추가
        
        Args:
            class_name: 클래스명
            documents: 문서 리스트
            
        Returns:
            생성된 문서 ID 리스트
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Weaviate")
        
        results = []
        
        try:
            # 벡터 배치 생성 (인코더가 있는 경우)
            vectors = None
            if self.encoder:
                contents = [doc.content for doc in documents if doc.content]
                if contents:
                    embeddings = self.encoder.encode_texts(contents)
                    vectors = embeddings.tolist()
            
            # 배치 작업 시작
            with self.client.batch as batch:
                for i, document in enumerate(documents):
                    try:
                        # 벡터 설정
                        vector = None
                        if vectors and i < len(vectors):
                            vector = vectors[i]
                        elif document.vector:
                            vector = document.vector
                        
                        # 문서 데이터 준비
                        properties = {
                            "content": document.content,
                            "title": document.title,
                            "source": document.source,
                            "created_at": document.created_at.isoformat() if document.created_at else datetime.now().isoformat()
                        }
                        
                        # 메타데이터 추가
                        if document.metadata:
                            for key, value in document.metadata.items():
                                if key not in properties:
                                    properties[key] = value
                        
                        # 문서 ID 생성 또는 사용
                        doc_id = document.id or str(uuid.uuid4())
                        
                        # 배치에 추가
                        batch.add_data_object(
                            data_object=properties,
                            class_name=class_name,
                            uuid=doc_id,
                            vector=vector
                        )
                        
                        results.append(doc_id)
                        
                    except Exception as e:
                        logger.error(f"Failed to prepare document {i}: {e}")
                        results.append(None)
            
            logger.info(f"Added {len([r for r in results if r])} documents to {class_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to add documents to {class_name}: {e}")
            return [None] * len(documents)
    
    def search(self, class_name: str, query: SearchQuery) -> List[SearchResult]:
        """
        유사도 검색 수행
        
        Args:
            class_name: 클래스명
            query: 검색 쿼리
            
        Returns:
            검색 결과 리스트
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Weaviate")
        
        try:
            # 쿼리 벡터 생성
            query_vector = None
            if self.encoder:
                embeddings = self.encoder.encode_texts(query.query)
                query_vector = embeddings[0].tolist()
            
            # 검색 쿼리 구성
            search_query = self.client.query.get(class_name, [
                "content", "title", "source", "created_at"
            ])
            
            # 벡터 검색 (쿼리 벡터가 있는 경우)
            if query_vector:
                search_query = search_query.with_near_vector({
                    "vector": query_vector,
                    "distance": 1 - query.threshold  # Weaviate는 distance 사용
                })
            else:
                # 텍스트 검색 (벡터가 없는 경우)
                search_query = search_query.with_bm25(
                    query=query.query
                )
            
            # 필터 적용
            if query.filters:
                where_filter = self._build_where_filter(query.filters)
                search_query = search_query.with_where(where_filter)
            
            # 결과 개수 제한
            search_query = search_query.with_limit(query.limit)
            
            # 추가 필드 포함
            additional_fields = ["id", "certainty"]
            if query.include_vector:
                additional_fields.append("vector")
            
            search_query = search_query.with_additional(additional_fields)
            
            # 검색 실행
            result = search_query.do()
            
            # 결과 변환
            search_results = []
            if "data" in result and "Get" in result["data"]:
                objects = result["data"]["Get"].get(class_name, [])
                
                for obj in objects:
                    # 점수 계산 (certainty -> score)
                    score = obj.get("_additional", {}).get("certainty", 0.0)
                    
                    search_result = SearchResult(
                        id=obj.get("_additional", {}).get("id", ""),
                        content=obj.get("content", ""),
                        title=obj.get("title"),
                        score=score,
                        metadata={k: v for k, v in obj.items() if k not in ["content", "title", "source", "_additional"]},
                        source=obj.get("source"),
                        vector=obj.get("_additional", {}).get("vector") if query.include_vector else None
                    )
                    
                    search_results.append(search_result)
            
            logger.debug(f"Found {len(search_results)} results for query in {class_name}")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed in {class_name}: {e}")
            return []
    
    def delete_document(self, class_name: str, doc_id: str) -> bool:
        """
        문서 삭제
        
        Args:
            class_name: 클래스명
            doc_id: 문서 ID
            
        Returns:
            성공 여부
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to Weaviate")
        
        try:
            self.client.data_object.delete(
                uuid=doc_id,
                class_name=class_name
            )
            logger.debug(f"Deleted document {doc_id} from {class_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id} from {class_name}: {e}")
            return False
    
    def delete_documents(self, class_name: str, doc_ids: List[str]) -> List[bool]:
        """
        배치로 문서 삭제
        
        Args:
            class_name: 클래스명
            doc_ids: 문서 ID 리스트
            
        Returns:
            삭제 성공 여부 리스트
        """
        results = []
        for doc_id in doc_ids:
            success = self.delete_document(class_name, doc_id)
            results.append(success)
        
        logger.info(f"Deleted {sum(results)} out of {len(doc_ids)} documents from {class_name}")
        return results
    
    def get_status(self) -> VectorDBStatus:
        """Vector DB 상태 정보 조회"""
        if not self.is_connected():
            return VectorDBStatus(connected=False)
        
        try:
            # 메타 정보 조회
            meta = self.client.get_meta()
            
            # 스키마 정보 조회
            schema = self.client.schema.get()
            classes = [cls["class"] for cls in schema.get("classes", [])]
            
            # 총 객체 수 계산
            total_objects = 0
            for class_name in classes:
                try:
                    result = self.client.query.aggregate(class_name).with_meta_count().do()
                    if "data" in result and "Aggregate" in result["data"]:
                        count_info = result["data"]["Aggregate"].get(class_name, [])
                        if count_info:
                            total_objects += count_info[0].get("meta", {}).get("count", 0)
                except:
                    pass
            
            return VectorDBStatus(
                connected=True,
                total_objects=total_objects,
                classes=classes,
                health="healthy",
                version=meta.get("version", "unknown")
            )
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return VectorDBStatus(
                connected=self._connected,
                health="error"
            )
    
    def _build_where_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """필터 조건을 Weaviate Where 형식으로 변환"""
        if not filters:
            return {}
        
        conditions = []
        
        for field, value in filters.items():
            if isinstance(value, dict):
                # 연산자 기반 필터
                for op, val in value.items():
                    condition = {
                        "path": [field],
                        "operator": self._map_operator(op),
                        "valueText" if isinstance(val, str) else "valueNumber": val
                    }
                    conditions.append(condition)
            else:
                # 단순 동등 필터
                condition = {
                    "path": [field],
                    "operator": "Equal",
                    "valueText" if isinstance(value, str) else "valueNumber": value
                }
                conditions.append(condition)
        
        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return {
                "operator": "And",
                "operands": conditions
            }
        
        return {}
    
    def _map_operator(self, op: str) -> str:
        """연산자 매핑"""
        mapping = {
            "eq": "Equal",
            "ne": "NotEqual",
            "gt": "GreaterThan",
            "gte": "GreaterThanEqual",
            "lt": "LessThan",
            "lte": "LessThanEqual",
            "like": "Like",
            "contains": "ContainsAny"
        }
        return mapping.get(op.lower(), "Equal")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        if not self.is_connected():
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.disconnect() 