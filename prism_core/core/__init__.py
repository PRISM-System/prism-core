"""
PRISM Core - Multi-Agent System with LLM and Vector DB

This package provides core components for building multi-agent systems
with large language models and vector databases.
"""

__version__ = "0.2.3"

# LLM 모듈 import
try:
    from .llm.base import BaseLLMService
    from .llm.schemas import (
        LLMGenerationRequest,
        GenerationResponse,
        Agent,
        AgentResponse,
        AgentInvokeRequest
    )
    from .llm.agent_registry import AgentRegistry
except ImportError:
    # LLM 의존성이 없는 경우 무시
    pass

# Vector DB 모듈 import  
try:
    from .vector_db.client import WeaviateClient
    from .vector_db.api import VectorDBAPI
    from .vector_db.schemas import (
        DocumentSchema,
        SearchQuery,
        SearchResult,
        IndexConfig
    )
except ImportError:
    # Vector DB 의존성이 없는 경우 무시
    pass

# Tools 모듈 import
try:
    from .tools.base import BaseTool
    from .tools.registry import ToolRegistry
    from .tools.schemas import ToolRequest, ToolResponse
except ImportError:
    # Tools 의존성이 없는 경우 무시
    pass

# Agents 모듈 import
try:
    from .agents.base import BaseAgent
    from .agents.agent_manager import AgentManager
    from .agents.workflow_manager import WorkflowManager
except ImportError:
    # Agents 의존성이 없는 경우 무시
    pass

__all__ = [
    "__version__",
    # LLM
    "BaseLLMService",
    "LLMGenerationRequest", 
    "GenerationResponse",
    "Agent",
    "AgentResponse",
    "AgentInvokeRequest",
    "AgentRegistry",
    # Vector DB
    "WeaviateClient",
    "VectorDBAPI",
    "DocumentSchema",
    "SearchQuery", 
    "SearchResult",
    "IndexConfig",
    # Tools
    "BaseTool",
    "ToolRegistry",
    "ToolRequest",
    "ToolResponse",
    # Agents
    "BaseAgent",
    "AgentManager",
    "WorkflowManager",
]
