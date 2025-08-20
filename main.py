from fastapi import FastAPI
from core.llm import AgentRegistry, VLLMService, create_llm_router
from core.llm import ToolRegistry, OpenAICompatService
from core.data.service import DatabaseService
from core.data.api import create_db_router
import os

# FastAPI 앱 생성
app = FastAPI(
    title="PRISM Core",
    description="산업용 데이터베이스와 LLM 기반 Multi-Agent 시스템을 활용한 지능형 제조 공정 분석 플랫폼",
    version="0.1.0"
)

# 서비스 인스턴스 생성
agent_registry = AgentRegistry()
llm_service = VLLMService()
tool_registry = ToolRegistry()
openai_service = OpenAICompatService()

# 데이터베이스 연결 (분리된 서비스)
db_url = os.getenv("DATABASE_URL", "postgresql://myuser:mysecretpassword@localhost:5432/mydatabase")
db_service = DatabaseService(db_url)

# API 라우터들 생성 및 포함
# LLM/Agent API
llm_router = create_llm_router(agent_registry, llm_service, tool_registry, openai_service)
app.include_router(llm_router, prefix="/api")

# Database API (완전히 분리됨)
db_router = create_db_router(db_service)
app.include_router(db_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to PRISM Core", "version": "0.1.0"}
