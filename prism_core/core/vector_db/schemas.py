"""
Vector DB Schemas

Vector Database에서 사용할 데이터 모델과 스키마 정의
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentSchema(BaseModel):
    """문서 스키마 - Vector DB에 저장될 문서의 기본 구조"""
    
    id: Optional[str] = Field(None, description="문서 고유 ID")
    content: str = Field(..., description="문서 내용")
    title: Optional[str] = Field(None, description="문서 제목")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    source: Optional[str] = Field(None, description="문서 출처")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    updated_at: Optional[datetime] = Field(None, description="수정 시간")
    vector: Optional[List[float]] = Field(None, description="벡터 임베딩")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SearchQuery(BaseModel):
    """검색 쿼리 스키마"""
    
    query: str = Field(..., description="검색 쿼리 텍스트")
    limit: int = Field(10, ge=1, le=100, description="반환할 결과 수")
    threshold: float = Field(0.7, ge=0.0, le=1.0, description="유사도 임계값")
    filters: Dict[str, Any] = Field(default_factory=dict, description="필터 조건")
    include_metadata: bool = Field(True, description="메타데이터 포함 여부")
    include_vector: bool = Field(False, description="벡터 포함 여부")


class SearchResult(BaseModel):
    """검색 결과 스키마"""
    
    id: str = Field(..., description="문서 ID")
    content: str = Field(..., description="문서 내용")
    title: Optional[str] = Field(None, description="문서 제목")
    score: float = Field(..., description="유사도 점수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    source: Optional[str] = Field(None, description="문서 출처")
    vector: Optional[List[float]] = Field(None, description="벡터 임베딩")


class IndexConfig(BaseModel):
    """인덱스 설정 스키마"""
    
    class_name: str = Field(..., description="Weaviate 클래스명")
    description: str = Field(..., description="인덱스 설명")
    vector_dimension: int = Field(..., description="벡터 차원")
    encoder_model: str = Field(..., description="인코더 모델 (path or HF model ID)")
    properties: List[Dict[str, Any]] = Field(default_factory=list, description="속성 정의")
    vectorizer: str = Field("none", description="벡터라이저 설정")
    distance_metric: str = Field("cosine", description="거리 메트릭")
    
    def get_weaviate_schema(self) -> Dict[str, Any]:
        """Weaviate 스키마 형식으로 변환"""
        schema = {
            "class": self.class_name,
            "description": self.description,
            "vectorizer": self.vectorizer,
            "moduleConfig": {
                "text2vec-transformers": {
                    "model": self.encoder_model
                }
            },
            "properties": self.properties or [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "title", 
                    "dataType": ["string"],
                    "description": "Document title"
                },
                {
                    "name": "source",
                    "dataType": ["string"],
                    "description": "Document source"
                },
                {
                    "name": "created_at",
                    "dataType": ["date"],
                    "description": "Creation timestamp"
                }
            ],
            "vectorIndexConfig": {
                "distance": self.distance_metric
            }
        }
        return schema


class BulkOperation(BaseModel):
    """배치 작업 스키마"""
    
    operation: str = Field(..., description="작업 유형 (insert, update, delete)")
    documents: List[DocumentSchema] = Field(default_factory=list, description="문서 목록")
    ids: List[str] = Field(default_factory=list, description="ID 목록 (delete용)")


class VectorDBStatus(BaseModel):
    """Vector DB 상태 정보"""
    
    connected: bool = Field(..., description="연결 상태")
    total_objects: int = Field(0, description="총 객체 수")
    classes: List[str] = Field(default_factory=list, description="클래스 목록")
    health: str = Field("unknown", description="상태")
    version: Optional[str] = Field(None, description="Weaviate 버전")


class APIResponse(BaseModel):
    """API 응답 스키마"""
    
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
    error: Optional[str] = Field(None, description="오류 메시지")
    execution_time_ms: Optional[float] = Field(None, description="실행 시간(ms)") 