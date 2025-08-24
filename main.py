from fastapi import FastAPI
from prism_core.core.llm import AgentRegistry, create_llm_router
from prism_core.core.llm import ToolRegistry
from prism_core.core.data.service import DatabaseService
from prism_core.core.data.api import create_db_router
from prism_core.core.tools import ToolRegistry
from prism_core.core.config import settings
from prism_core.core.vector_db.api import create_vector_db_router

# FastAPI 앱 생성
app = FastAPI(
    title="PRISM Core",
    description="산업용 데이터베이스와 LLM 기반 Multi-Agent 시스템을 활용한 지능형 제조 공정 분석 플랫폼",
    version="0.1.0"
)

# 데이터베이스 연결
db_service = DatabaseService(settings.DATABASE_URL)

# Tool 시스템 초기화
tool_registry = ToolRegistry()

# Database Tool 등록 (lazy import)
from prism_core.core.tools import get_database_tool
DatabaseTool = get_database_tool()
database_tool = DatabaseTool(db_service)
tool_registry.register_tool(database_tool)

# RAG Search Tool 등록 (lazy import)
from prism_core.core.tools import create_rag_search_tool
rag_search_tool = create_rag_search_tool(class_prefix="Core")
tool_registry.register_tool(rag_search_tool)

# Compliance Tool 등록 (lazy import)
from prism_core.core.tools import create_compliance_tool
compliance_tool = create_compliance_tool(class_prefix="Core")
tool_registry.register_tool(compliance_tool)

# Memory Search Tool 등록 (lazy import)
from prism_core.core.tools import create_memory_search_tool
memory_search_tool = create_memory_search_tool(class_prefix="Core")
tool_registry.register_tool(memory_search_tool)

# Agent 시스템 초기화 (Tool Registry와 연결)
agent_registry = AgentRegistry(tool_registry)
from prism_core.core.llm import PrismLLMService
llm_service = PrismLLMService()

# API 라우터들 생성 및 포함
# LLM/Agent API (Tool Registry 포함)
llm_router = create_llm_router(agent_registry, llm_service, tool_registry)
app.include_router(llm_router, prefix="/api")

# Database API (완전히 분리됨)
db_router = create_db_router(db_service)
app.include_router(db_router, prefix="/api")

# Vector-DB API (Weaviate 프록시)
vector_router = create_vector_db_router(settings.WEAVIATE_URL, settings.WEAVIATE_API_KEY)
app.include_router(vector_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to PRISM Core", "version": "0.1.0"}
