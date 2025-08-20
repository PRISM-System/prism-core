"""
Vector DB API

Vector Database 기능을 REST API로 제공
"""

import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from .schemas import (
    DocumentSchema, SearchQuery, SearchResult, IndexConfig, 
    VectorDBStatus, APIResponse, BulkOperation
)
from .client import WeaviateClient
from .encoder import EncoderManager

logger = logging.getLogger(__name__)


class VectorDBAPI:
    """Vector DB API 관리자"""
    
    def __init__(self, weaviate_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        """
        Vector DB API 초기화
        
        Args:
            weaviate_url: Weaviate 서버 URL
            api_key: API 키 (선택사항)
        """
        self.weaviate_url = weaviate_url
        self.api_key = api_key
        self.clients: Dict[str, WeaviateClient] = {}
        self.encoders: Dict[str, EncoderManager] = {}
        
    def get_client(self, client_id: str = "default") -> WeaviateClient:
        """클라이언트 인스턴스 가져오기"""
        if client_id not in self.clients:
            self.clients[client_id] = WeaviateClient(
                url=self.weaviate_url,
                api_key=self.api_key
            )
        return self.clients[client_id]
    
    def get_encoder(self, model_path_or_id: str) -> EncoderManager:
        """인코더 인스턴스 가져오기 (캐시됨)"""
        if model_path_or_id not in self.encoders:
            self.encoders[model_path_or_id] = EncoderManager(model_path_or_id)
        return self.encoders[model_path_or_id]
    
    def create_router(self) -> APIRouter:
        """FastAPI 라우터 생성"""
        router = APIRouter(prefix="/vector-db", tags=["Vector Database"])
        
        @router.get("/status", response_model=VectorDBStatus)
        async def get_status(client_id: str = "default"):
            """Vector DB 상태 조회"""
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                status = client.get_status()
                return status
                
            except Exception as e:
                logger.error(f"Failed to get status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.post("/indices", response_model=APIResponse)
        async def create_index(
            config: IndexConfig,
            client_id: str = "default"
        ):
            """새 인덱스 생성"""
            start_time = time.time()
            
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                # 인코더 설정
                if config.encoder_model:
                    encoder = self.get_encoder(config.encoder_model)
                    client.encoder = encoder
                
                success = client.create_index(config)
                
                execution_time = (time.time() - start_time) * 1000
                
                if success:
                    return APIResponse(
                        success=True,
                        message=f"Index '{config.class_name}' created successfully",
                        execution_time_ms=execution_time
                    )
                else:
                    return APIResponse(
                        success=False,
                        message=f"Failed to create index '{config.class_name}'",
                        execution_time_ms=execution_time
                    )
                    
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Failed to create index: {e}")
                return APIResponse(
                    success=False,
                    message="Failed to create index",
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        @router.delete("/indices/{class_name}", response_model=APIResponse)
        async def delete_index(
            class_name: str,
            client_id: str = "default"
        ):
            """인덱스 삭제"""
            start_time = time.time()
            
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                success = client.delete_index(class_name)
                
                execution_time = (time.time() - start_time) * 1000
                
                if success:
                    return APIResponse(
                        success=True,
                        message=f"Index '{class_name}' deleted successfully",
                        execution_time_ms=execution_time
                    )
                else:
                    return APIResponse(
                        success=False,
                        message=f"Failed to delete index '{class_name}'",
                        execution_time_ms=execution_time
                    )
                    
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Failed to delete index: {e}")
                return APIResponse(
                    success=False,
                    message="Failed to delete index",
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        @router.post("/documents/{class_name}", response_model=APIResponse)
        async def add_document(
            class_name: str,
            document: DocumentSchema,
            client_id: str = "default",
            encoder_model: Optional[str] = None
        ):
            """단일 문서 추가"""
            start_time = time.time()
            
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                # 인코더 설정
                if encoder_model:
                    encoder = self.get_encoder(encoder_model)
                    client.encoder = encoder
                
                doc_id = client.add_document(class_name, document)
                
                execution_time = (time.time() - start_time) * 1000
                
                if doc_id:
                    return APIResponse(
                        success=True,
                        message="Document added successfully",
                        data={"document_id": doc_id},
                        execution_time_ms=execution_time
                    )
                else:
                    return APIResponse(
                        success=False,
                        message="Failed to add document",
                        execution_time_ms=execution_time
                    )
                    
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Failed to add document: {e}")
                return APIResponse(
                    success=False,
                    message="Failed to add document",
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        @router.post("/documents/{class_name}/batch", response_model=APIResponse)
        async def add_documents_batch(
            class_name: str,
            documents: List[DocumentSchema],
            background_tasks: BackgroundTasks,
            client_id: str = "default",
            encoder_model: Optional[str] = None
        ):
            """배치로 문서 추가"""
            start_time = time.time()
            
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                # 인코더 설정
                if encoder_model:
                    encoder = self.get_encoder(encoder_model)
                    client.encoder = encoder
                
                # 백그라운드에서 처리 (문서가 많은 경우)
                if len(documents) > 100:
                    background_tasks.add_task(
                        self._process_batch_documents,
                        client, class_name, documents
                    )
                    
                    return APIResponse(
                        success=True,
                        message=f"Batch processing started for {len(documents)} documents",
                        data={"status": "processing"},
                        execution_time_ms=(time.time() - start_time) * 1000
                    )
                else:
                    doc_ids = client.add_documents(class_name, documents)
                    success_count = len([id for id in doc_ids if id is not None])
                    
                    execution_time = (time.time() - start_time) * 1000
                    
                    return APIResponse(
                        success=True,
                        message=f"Added {success_count} out of {len(documents)} documents",
                        data={
                            "document_ids": doc_ids,
                            "success_count": success_count,
                            "total_count": len(documents)
                        },
                        execution_time_ms=execution_time
                    )
                    
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Failed to add documents: {e}")
                return APIResponse(
                    success=False,
                    message="Failed to add documents",
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        @router.post("/search/{class_name}", response_model=List[SearchResult])
        async def search_documents(
            class_name: str,
            query: SearchQuery,
            client_id: str = "default",
            encoder_model: Optional[str] = None
        ):
            """문서 검색"""
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                # 인코더 설정
                if encoder_model:
                    encoder = self.get_encoder(encoder_model)
                    client.encoder = encoder
                
                results = client.search(class_name, query)
                return results
                
            except Exception as e:
                logger.error(f"Search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @router.delete("/documents/{class_name}/{doc_id}", response_model=APIResponse)
        async def delete_document(
            class_name: str,
            doc_id: str,
            client_id: str = "default"
        ):
            """단일 문서 삭제"""
            start_time = time.time()
            
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                success = client.delete_document(class_name, doc_id)
                
                execution_time = (time.time() - start_time) * 1000
                
                if success:
                    return APIResponse(
                        success=True,
                        message="Document deleted successfully",
                        execution_time_ms=execution_time
                    )
                else:
                    return APIResponse(
                        success=False,
                        message="Failed to delete document",
                        execution_time_ms=execution_time
                    )
                    
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Failed to delete document: {e}")
                return APIResponse(
                    success=False,
                    message="Failed to delete document",
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        @router.post("/documents/{class_name}/delete-batch", response_model=APIResponse)
        async def delete_documents_batch(
            class_name: str,
            doc_ids: List[str],
            client_id: str = "default"
        ):
            """배치로 문서 삭제"""
            start_time = time.time()
            
            try:
                client = self.get_client(client_id)
                if not client.is_connected():
                    client.connect()
                
                results = client.delete_documents(class_name, doc_ids)
                success_count = sum(results)
                
                execution_time = (time.time() - start_time) * 1000
                
                return APIResponse(
                    success=True,
                    message=f"Deleted {success_count} out of {len(doc_ids)} documents",
                    data={
                        "success_count": success_count,
                        "total_count": len(doc_ids),
                        "results": results
                    },
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Failed to delete documents: {e}")
                return APIResponse(
                    success=False,
                    message="Failed to delete documents",
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        @router.get("/encoders/recommended")
        async def get_recommended_encoders():
            """추천 인코더 모델 목록"""
            return EncoderManager.get_recommended_models()
        
        @router.post("/encoders/test", response_model=APIResponse)
        async def test_encoder(
            model_path_or_id: str,
            test_texts: List[str] = ["Hello world", "안녕하세요"]
        ):
            """인코더 모델 테스트"""
            start_time = time.time()
            
            try:
                encoder = self.get_encoder(model_path_or_id)
                embeddings = encoder.encode_texts(test_texts)
                
                execution_time = (time.time() - start_time) * 1000
                
                return APIResponse(
                    success=True,
                    message="Encoder test completed",
                    data={
                        "model_info": encoder.get_model_info(),
                        "embeddings_shape": embeddings.shape,
                        "sample_embedding": embeddings[0][:5].tolist()  # 처음 5개 차원만
                    },
                    execution_time_ms=execution_time
                )
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                logger.error(f"Encoder test failed: {e}")
                return APIResponse(
                    success=False,
                    message="Encoder test failed",
                    error=str(e),
                    execution_time_ms=execution_time
                )
        
        return router
    
    async def _process_batch_documents(
        self, 
        client: WeaviateClient, 
        class_name: str, 
        documents: List[DocumentSchema]
    ):
        """백그라운드에서 배치 문서 처리"""
        try:
            logger.info(f"Starting batch processing of {len(documents)} documents")
            doc_ids = client.add_documents(class_name, documents)
            success_count = len([id for id in doc_ids if id is not None])
            logger.info(f"Batch processing completed: {success_count}/{len(documents)} documents added")
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")


def create_vector_db_router(
    weaviate_url: str = "http://localhost:8080",
    api_key: Optional[str] = None
) -> APIRouter:
    """
    Vector DB API 라우터 생성 함수
    
    Args:
        weaviate_url: Weaviate 서버 URL
        api_key: API 키 (선택사항)
        
    Returns:
        FastAPI 라우터
    """
    api = VectorDBAPI(weaviate_url, api_key)
    return api.create_router() 