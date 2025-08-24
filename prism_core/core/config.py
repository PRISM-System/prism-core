import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

# 프로젝트 루트 디렉토리
project_root = Path(__file__).parent.parent

class Settings(BaseSettings):
    """
    PRISM Core 설정 클래스
    환경 변수나 .env 파일에서 설정을 로드합니다.
    """
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database Settings
    DATABASE_URL: str = "postgresql://myuser:mysecretpassword@localhost:5432/mydatabase"
    POSTGRES_USER: str = "myuser"
    POSTGRES_PASSWORD: str = "mysecretpassword"
    POSTGRES_DB: str = "mydatabase"
    
    # LLM Settings
    VLLM_HOST: str = "0.0.0.0"
    VLLM_PORT: int = 8001
    VLLM_MODEL: str = "Qwen/Qwen3-14B"
    VLLM_ARGS: str = "--enable-auto-tool-choice --tool-call-parser hermes"
    VLLM_OPENAI_BASE_URL: str = "http://vllm:8001/v1"
    DEFAULT_MODEL: str = "Qwen/Qwen3-14B"
    
    # OpenAI Settings
    OPENAI_API_KEY: str = "EMPTY"
    
    # Hugging Face Settings
    HUGGING_FACE_TOKEN: str = "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"
    
    # Vector encoder configuration (에이전트별로 관리되므로 기본값만 제공)
    # 각 에이전트가 자신만의 벡터 인코더 설정을 관리합니다
    
    # PRISM-Core base URL (for internal tool communication)
    PRISM_CORE_BASE_URL: str = "http://localhost:8000"
    
    # Pydantic-settings 설정
    model_config = SettingsConfigDict(
        env_file=project_root / ".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

# 전역 설정 객체
settings = Settings() 