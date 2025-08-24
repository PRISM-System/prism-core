"""
Encoder Manager

다양한 인코더 모델을 관리하고 텍스트를 벡터로 변환하는 기능 제공
"""

import os
import torch
import logging
from typing import List, Optional, Dict, Any, Union
from transformers import AutoTokenizer, AutoModel
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class EncoderManager:
    """
    인코더 모델 관리자
    
    HuggingFace 모델 또는 로컬 모델을 로드하고 텍스트를 벡터로 변환
    """
    
    def __init__(self, model_path_or_id: str, device: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        인코더 초기화
        
        Args:
            model_path_or_id: 모델 경로 또는 HuggingFace 모델 ID
            device: 사용할 디바이스 ('cpu', 'cuda', 'auto')
            cache_dir: 모델 캐시 디렉토리
        """
        self.model_path_or_id = model_path_or_id
        self.cache_dir = cache_dir
        self.device = self._setup_device(device)
        
        self.tokenizer = None
        self.model = None
        self.vector_dimension = None
        self._is_loaded = False
        
        # 기본 설정
        self.max_length = 512
        self.batch_size = 32
        
    def _setup_device(self, device: Optional[str]) -> str:
        """디바이스 설정"""
        if device == "auto" or device is None:
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def load_model(self) -> None:
        """모델 로드"""
        try:
            logger.info(f"Loading encoder model: {self.model_path_or_id}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path_or_id,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # 모델 로드
            self.model = AutoModel.from_pretrained(
                self.model_path_or_id,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # 디바이스로 이동
            self.model.to(self.device)
            self.model.eval()
            
            # 벡터 차원 확인
            with torch.no_grad():
                dummy_input = self.tokenizer("test", return_tensors="pt", padding=True, truncation=True)
                dummy_input = {k: v.to(self.device) for k, v in dummy_input.items()}
                dummy_output = self.model(**dummy_input)
                self.vector_dimension = dummy_output.last_hidden_state.shape[-1]
            
            self._is_loaded = True
            logger.info(f"Model loaded successfully. Vector dimension: {self.vector_dimension}")
            
        except Exception as e:
            logger.error(f"Failed to load model {self.model_path_or_id}: {e}")
            raise
    
    def encode_texts(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        텍스트를 벡터로 변환
        
        Args:
            texts: 단일 텍스트 또는 텍스트 리스트
            normalize: 벡터 정규화 여부
            
        Returns:
            벡터 배열 (shape: [n_texts, vector_dim])
        """
        if not self._is_loaded:
            self.load_model()
        
        if isinstance(texts, str):
            texts = [texts]
        
        all_embeddings = []
        
        # 배치 처리
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self._encode_batch(batch_texts)
            all_embeddings.append(batch_embeddings)
        
        # 결합
        embeddings = np.vstack(all_embeddings)
        
        # 정규화
        if normalize:
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings
    
    def _encode_batch(self, texts: List[str]) -> np.ndarray:
        """배치 단위로 텍스트 인코딩"""
        try:
            # 토크나이징
            inputs = self.tokenizer(
                texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_length
            )
            
            # 디바이스로 이동
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 모델 실행
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # 평균 풀링 (CLS 토큰 대신)
                embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
            
            return embeddings.cpu().numpy()
            
        except Exception as e:
            logger.error(f"Error encoding batch: {e}")
            raise
    
    def _mean_pooling(self, model_output, attention_mask):
        """평균 풀링 적용"""
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_path_or_id": self.model_path_or_id,
            "device": self.device,
            "vector_dimension": self.vector_dimension,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "is_loaded": self._is_loaded
        }
    
    def set_batch_size(self, batch_size: int) -> None:
        """배치 크기 설정"""
        self.batch_size = max(1, batch_size)
    
    def set_max_length(self, max_length: int) -> None:
        """최대 길이 설정"""
        self.max_length = max(1, min(max_length, 512))
    
    @staticmethod
    def get_recommended_models() -> Dict[str, Dict[str, Any]]:
        """추천 모델 목록"""
        return {
            "multilingual-e5-base": {
                "model_id": "intfloat/multilingual-e5-base",
                "description": "다국어 지원 임베딩 모델",
                "vector_dimension": 768,
                "languages": ["ko", "en", "zh", "ja"],
                "use_case": "일반적인 텍스트 임베딩"
            },
            "bge-m3": {
                "model_id": "BAAI/bge-m3",
                "description": "다국어 지원 고성능 임베딩 모델",
                "vector_dimension": 1024,
                "languages": ["ko", "en", "zh", "ja"],
                "use_case": "고품질 검색 및 RAG"
            },
            "korean-sentence-transformers": {
                "model_id": "jhgan/ko-sroberta-multitask",
                "description": "한국어 특화 문장 임베딩 모델",
                "vector_dimension": 768,
                "languages": ["ko"],
                "use_case": "한국어 텍스트 처리"
            },
            "openai-ada": {
                "model_id": "text-embedding-ada-002",
                "description": "OpenAI 임베딩 모델 (API 필요)",
                "vector_dimension": 1536,
                "languages": ["en", "ko"],
                "use_case": "고품질 임베딩 (API 기반)"
            }
        }
    
    def __del__(self):
        """리소스 정리"""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
        if hasattr(self, 'tokenizer') and self.tokenizer is not None:
            del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class OpenAIEncoder:
    """
    OpenAI API 기반 인코더
    
    OpenAI의 text-embedding-ada-002 등을 사용
    """
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        """
        OpenAI 인코더 초기화
        
        Args:
            api_key: OpenAI API 키
            model: 사용할 모델명
        """
        self.api_key = api_key
        self.model = model
        self.vector_dimension = 1536 if model == "text-embedding-ada-002" else None
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    def encode_texts(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """OpenAI API를 사용하여 텍스트 인코딩"""
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            embeddings = np.array([data.embedding for data in response.data])
            
            if normalize:
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"OpenAI encoding error: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model": self.model,
            "vector_dimension": self.vector_dimension,
            "provider": "OpenAI"
        } 