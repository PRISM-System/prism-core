from fastapi import FastAPI
from core.api import create_api_router
from core.agent_registry import AgentRegistry
from core.llm.vllm_service import VLLMService

# FastAPI 앱 생성
app = FastAPI(
    title="PRISM Core",
    description="산업용 데이터베이스와 LLM 기반 Multi-Agent 시스템을 활용한 지능형 제조 공정 분석 플랫폼",
    version="0.1.0"
)

# 서비스 인스턴스 생성
agent_registry = AgentRegistry()
llm_service = VLLMService()

# API 라우터 생성 및 포함
api_router = create_api_router(agent_registry, llm_service)
app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to PRISM Core", "version": "0.1.0"}
