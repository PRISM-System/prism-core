from .base import BaseTool
from .registry import ToolRegistry
from .database_tool import DatabaseTool
from .dynamic_tool import DynamicTool
from .rag_search_tool import RAGSearchTool
from .compliance_tool import ComplianceTool
from .memory_search_tool import MemorySearchTool
from .schemas import ToolRequest, ToolResponse, ToolInfo, ToolRegistrationRequest, AgentToolAssignment

def create_rag_search_tool(
    weaviate_url: str = None,
    encoder_model: str = None,
    vector_dim: int = None,
    client_id: str = "default",
    class_prefix: str = "Default"
) -> RAGSearchTool:
    """RAG Search Tool 생성"""
    return RAGSearchTool(
        weaviate_url=weaviate_url,
        encoder_model=encoder_model,
        vector_dim=vector_dim,
        client_id=client_id,
        class_prefix=class_prefix
    )

def create_compliance_tool(
    weaviate_url: str = None,
    openai_base_url: str = None,
    openai_api_key: str = None,
    model_name: str = None,
    client_id: str = "default",
    class_prefix: str = "Default"
) -> ComplianceTool:
    """Compliance Tool 생성"""
    return ComplianceTool(
        weaviate_url=weaviate_url,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        model_name=model_name,
        client_id=client_id,
        class_prefix=class_prefix
    )

def create_memory_search_tool(
    weaviate_url: str = None,
    openai_base_url: str = None,
    openai_api_key: str = None,
    client_id: str = "default",
    class_prefix: str = "Default"
) -> MemorySearchTool:
    """Memory Search Tool 생성"""
    return MemorySearchTool(
        weaviate_url=weaviate_url,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        client_id=client_id,
        class_prefix=class_prefix
    )

__all__ = [
    "BaseTool",
    "ToolRegistry", 
    "DatabaseTool",
    "DynamicTool",
    "RAGSearchTool",
    "ComplianceTool",
    "MemorySearchTool",
    "create_rag_search_tool",
    "create_compliance_tool",
    "create_memory_search_tool",
    "ToolRequest",
    "ToolResponse",
    "ToolInfo",
    "ToolRegistrationRequest",
    "AgentToolAssignment"
]
