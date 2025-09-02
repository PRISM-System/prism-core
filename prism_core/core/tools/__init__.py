from .base import BaseTool
from .registry import ToolRegistry
from .schemas import ToolRequest, ToolResponse, ToolInfo, ToolRegistrationRequest, AgentToolAssignment

# 구체적인 tool 구현체들은 필요할 때만 import하도록 lazy import로 변경
# from .database_tool import DatabaseTool
# from .dynamic_tool import DynamicTool
# from .rag_search_tool import RAGSearchTool
# from .compliance_tool import ComplianceTool
# from .memory_search_tool import MemorySearchTool

def create_rag_search_tool(
    weaviate_url: str = None,
    encoder_model: str = None,
    vector_dim: int = None,
    client_id: str = "default",
    class_prefix: str = "Default"
):
    """RAG Search Tool 생성 (lazy import)"""
    from .rag_search_tool import RAGSearchTool
    return RAGSearchTool(
        weaviate_url=weaviate_url,
        encoder_model=encoder_model,
        vector_dim=vector_dim,
        client_id=client_id,
        class_prefix=class_prefix,
        tool_type="api"
    )

def create_compliance_tool(
    weaviate_url: str = None,
    openai_base_url: str = None,
    openai_api_key: str = None,
    model_name: str = None,
    client_id: str = "default",
    class_prefix: str = "Default"
):
    """Compliance Tool 생성 (lazy import)"""
    from .compliance_tool import ComplianceTool
    return ComplianceTool(
        weaviate_url=weaviate_url,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        model_name=model_name,
        client_id=client_id,
        class_prefix=class_prefix,
        tool_type="api"
    )

def create_memory_search_tool(
    weaviate_url: str = None,
    openai_base_url: str = None,
    openai_api_key: str = None,
    model_name: str = None,
    embedder_model_name: str = None,
    client_id: str = "default",
    class_prefix: str = "Default"
):
    """Memory Search Tool 생성 (lazy import)"""
    from .memory_search_tool import MemorySearchTool
    return MemorySearchTool(
        weaviate_url=weaviate_url,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        model_name=model_name,
        embedder_model_name=embedder_model_name,
        client_id=client_id,
        class_prefix=class_prefix,
        tool_type="api"
    )

def get_database_tool():
    """Database Tool 가져오기 (lazy import)"""
    from .database_tool import DatabaseTool
    return DatabaseTool

def get_dynamic_tool():
    """Dynamic Tool 가져오기 (lazy import)"""
    from .dynamic_tool import DynamicTool
    return DynamicTool

__all__ = [
    "BaseTool",
    "ToolRegistry", 
    "ToolRequest",
    "ToolResponse",
    "ToolInfo",
    "ToolRegistrationRequest",
    "AgentToolAssignment",
    "create_rag_search_tool",
    "create_compliance_tool",
    "create_memory_search_tool",
    "get_database_tool",
    "get_dynamic_tool",
]
