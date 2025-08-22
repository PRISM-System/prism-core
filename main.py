from fastapi import FastAPI
from core.llm import AgentRegistry, create_llm_router
from core.llm import ToolRegistry
from core.data.service import DatabaseService
from core.data.api import create_db_router
from core.tools import ToolRegistry, DatabaseTool
import os
from core.vector_db.api import create_vector_db_router

# FastAPI 앱 생성
app = FastAPI(
    title="PRISM Core",
    description="산업용 데이터베이스와 LLM 기반 Multi-Agent 시스템을 활용한 지능형 제조 공정 분석 플랫폼",
    version="0.1.0"
)

# 데이터베이스 연결
db_url = os.getenv("DATABASE_URL", "postgresql://myuser:mysecretpassword@localhost:5432/mydatabase")
db_service = DatabaseService(db_url)

# Tool 시스템 초기화
tool_registry = ToolRegistry()

# Database Tool 등록
database_tool = DatabaseTool(db_service)
tool_registry.register_tool(database_tool)

# Agent 시스템 초기화 (Tool Registry와 연결)
agent_registry = AgentRegistry(tool_registry)
from core.llm import PrismLLMService
llm_service = PrismLLMService()

# API 라우터들 생성 및 포함
# LLM/Agent API (Tool Registry 포함)
llm_router = create_llm_router(agent_registry, llm_service, tool_registry)
app.include_router(llm_router, prefix="/api")

# Database API (완전히 분리됨)
db_router = create_db_router(db_service)
app.include_router(db_router, prefix="/api")

# Vector-DB API (Weaviate 프록시)
weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
vector_router = create_vector_db_router(weaviate_url, weaviate_api_key)
app.include_router(vector_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to PRISM Core", "version": "0.1.0"}
