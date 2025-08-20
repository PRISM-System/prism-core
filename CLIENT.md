# PRISM Core Client Guide

PRISM Core Server와 상호작용하는 **Client 애플리케이션 개발 가이드**입니다. 
이 가이드는 Server API를 활용하여 Tool 등록, Agent 관리, RAG 구현 등을 수행하는 Client 개발자를 위한 것입니다.

## 🎯 Client 주요 기능

- **🔧 Tool 등록**: Server에 다양한 타입의 Tool을 동적으로 등록
- **🤖 Agent 관리**: Agent 생성, Tool 할당, 실행 관리
- **🧠 Vector DB 활용**: RAG 구현을 위한 문서 관리 및 검색
- **📊 데이터 분석**: 산업 DB 데이터 분석 및 시각화
- **🔄 워크플로우 자동화**: Multi-Agent 협업 시스템 구축

## 🏗️ Client 아키텍처 권장사항

```
client-app/
├── src/
│   ├── services/           # Server API 통신
│   │   ├── prism_client.py    # PRISM Server API 클라이언트
│   │   ├── tool_service.py    # Tool 관리 서비스
│   │   ├── agent_service.py   # Agent 관리 서비스
│   │   └── vector_service.py  # Vector DB 서비스
│   ├── tools/              # Client 전용 Tool 정의
│   │   ├── custom_tools.py    # 사용자 정의 Tool
│   │   ├── api_tools.py       # 외부 API Tool
│   │   └── analysis_tools.py  # 데이터 분석 Tool
│   ├── workflows/          # 워크플로우 정의
│   │   ├── manufacturing_flow.py
│   │   └── quality_check_flow.py
│   ├── config/             # 설정 관리
│   │   ├── settings.py
│   │   └── tool_configs.py
│   └── utils/              # 유틸리티
│       ├── validators.py
│       └── formatters.py
├── examples/               # 사용 예제
├── tests/                 # 테스트
└── requirements.txt       # Client 의존성
```

## 🚀 Client 개발 시작하기

### 1. PRISM Server 연결 설정

```python
# src/services/prism_client.py
import requests
from typing import Dict, Any, List, Optional

class PRISMClient:
    """PRISM Core Server API 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """서버 상태 확인"""
        response = self.session.get(f"{self.base_url}/")
        return response.json()
    
    # Tool 관련 메서드들
    def list_tools(self) -> List[Dict[str, Any]]:
        """등록된 Tool 목록 조회"""
        response = self.session.get(f"{self.base_url}/api/tools")
        return response.json()
    
    def register_tool(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """새로운 Tool 등록"""
        response = self.session.post(
            f"{self.base_url}/api/tools/register",
            json=tool_config
        )
        return response.json()
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Tool 실행"""
        response = self.session.post(
            f"{self.base_url}/api/tools/execute",
            json={"tool_name": tool_name, "parameters": parameters}
        )
        return response.json()
    
    # Agent 관련 메서드들
    def create_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """새 Agent 생성"""
        response = self.session.post(
            f"{self.base_url}/api/agents",
            json=agent_config
        )
        return response.json()
    
    def invoke_agent(self, agent_name: str, prompt: str, use_tools: bool = True) -> Dict[str, Any]:
        """Agent 실행"""
        response = self.session.post(
            f"{self.base_url}/api/agents/{agent_name}/invoke",
            json={
                "prompt": prompt,
                "use_tools": use_tools,
                "max_tokens": 200,
                "temperature": 0.3
            }
        )
        return response.json()
```

### 2. Tool 관리 서비스

```python
# src/services/tool_service.py
from typing import Dict, Any, List
from .prism_client import PRISMClient

class ToolService:
    """Tool 관리 전용 서비스"""
    
    def __init__(self, client: PRISMClient):
        self.client = client
    
    def register_api_tool(self, name: str, description: str, api_config: Dict[str, Any]) -> bool:
        """API Tool 등록"""
        tool_config = {
            "name": name,
            "description": description,
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "API URL"},
                    "method": {"type": "string", "default": "GET"},
                    "headers": {"type": "object", "description": "Request headers"},
                    "data": {"type": "object", "description": "Request data"}
                },
                "required": ["url"]
            },
            "tool_type": "api",
            "config": api_config
        }
        
        result = self.client.register_tool(tool_config)
        return result.get("success", False)
    
    def register_calculation_tool(self, name: str, description: str) -> bool:
        """계산 Tool 등록"""
        tool_config = {
            "name": name,
            "description": description,
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "수학 표현식"},
                    "variables": {"type": "object", "description": "변수 딕셔너리"}
                },
                "required": ["expression"]
            },
            "tool_type": "calculation"
        }
        
        result = self.client.register_tool(tool_config)
        return result.get("success", False)
    
    def register_custom_tool_with_code(self, name: str, description: str, function_code: str) -> bool:
        """사용자 정의 함수 Tool 등록"""
        tool_config = {
            "name": name,
            "description": description,
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["execute_function"]},
                    "function_params": {"type": "object"}
                },
                "required": ["action"]
            },
            "tool_type": "custom",
            "function_code": function_code
        }
        
        # register-with-code 엔드포인트 사용
        response = self.client.session.post(
            f"{self.client.base_url}/api/tools/register-with-code",
            json=tool_config
        )
        result = response.json()
        return result.get("success", False)
```

### 3. Agent 관리 서비스

```python
# src/services/agent_service.py
from typing import Dict, Any, List
from .prism_client import PRISMClient

class AgentService:
    """Agent 관리 전용 서비스"""
    
    def __init__(self, client: PRISMClient):
        self.client = client
    
    def create_manufacturing_analyst(self, tools: List[str] = None) -> str:
        """제조 분석 전문가 Agent 생성"""
        if tools is None:
            tools = ["database_tool"]
        
        agent_config = {
            "name": "manufacturing_analyst",
            "description": "제조 공정 데이터 분석 전문가",
            "role_prompt": """
            당신은 반도체 제조 공정의 이상 탐지 전문가입니다. 
            사용자의 질문에 대해 데이터베이스를 활용하여 전문적이고 명확한 답변을 제공해주세요.
            데이터 분석 결과를 바탕으로 구체적인 개선 방안을 제시해주세요.
            """,
            "tools": tools
        }
        
        result = self.client.create_agent(agent_config)
        return result.get("message", "")
    
    def create_multi_tool_analyst(self, tools: List[str]) -> str:
        """다중 Tool 분석가 Agent 생성"""
        agent_config = {
            "name": "multi_tool_analyst",
            "description": "다양한 도구를 활용하는 분석 전문가",
            "role_prompt": """
            당신은 다양한 도구를 활용하여 사용자의 요청을 처리하는 분석 전문가입니다.
            사용 가능한 도구들을 적절히 조합하여 최적의 결과를 제공해주세요.
            """,
            "tools": tools
        }
        
        result = self.client.create_agent(agent_config)
        return result.get("message", "")
    
    def query_agent(self, agent_name: str, question: str) -> Dict[str, Any]:
        """Agent에게 질문하고 결과 받기"""
        result = self.client.invoke_agent(agent_name, question, use_tools=True)
        
        return {
            "answer": result.get("response", ""),
            "tools_used": result.get("tools_used", []),
            "tool_results": result.get("tool_results", {}),
            "execution_time": result.get("execution_time_ms", 0)
        }
```

### 4. Vector DB 활용 서비스

```python
# src/services/vector_service.py
from typing import Dict, Any, List
from .prism_client import PRISMClient

class VectorService:
    """Vector DB 관리 서비스"""
    
    def __init__(self, client: PRISMClient):
        self.client = client
    
    def create_document_index(self, class_name: str, encoder_model: str = "intfloat/multilingual-e5-base") -> bool:
        """문서 인덱스 생성"""
        index_config = {
            "class_name": class_name,
            "description": f"Document index for {class_name}",
            "vector_dimension": 768,
            "encoder_model": encoder_model,
            "distance_metric": "cosine"
        }
        
        response = self.client.session.post(
            f"{self.client.base_url}/vector-db/indices",
            json=index_config
        )
        result = response.json()
        return result.get("success", False)
    
    def add_documents(self, class_name: str, documents: List[Dict[str, Any]], encoder_model: str = None) -> Dict[str, Any]:
        """문서 배치 추가"""
        params = {"encoder_model": encoder_model} if encoder_model else {}
        
        response = self.client.session.post(
            f"{self.client.base_url}/vector-db/documents/{class_name}/batch",
            json=documents,
            params=params
        )
        return response.json()
    
    def search_documents(self, class_name: str, query: str, limit: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """문서 검색"""
        search_query = {
            "query": query,
            "limit": limit,
            "threshold": threshold,
            "include_metadata": True
        }
        
        response = self.client.session.post(
            f"{self.client.base_url}/vector-db/search/{class_name}",
            json=search_query
        )
        return response.json()
    
    def implement_rag(self, class_name: str, question: str, agent_name: str = "manufacturing_analyst") -> Dict[str, Any]:
        """RAG 구현 - 검색 + 생성"""
        # 1. 관련 문서 검색
        search_results = self.search_documents(class_name, question)
        
        if not search_results:
            return {"answer": "관련 문서를 찾을 수 없습니다.", "sources": []}
        
        # 2. 컨텍스트 구성
        context = "\n\n".join([result["content"] for result in search_results[:3]])
        
        # 3. Agent에게 컨텍스트와 함께 질문
        enhanced_prompt = f"""
        다음 문서들을 참고하여 질문에 답변해주세요:
        
        {context}
        
        질문: {question}
        """
        
        # 4. Agent 실행
        agent_result = self.client.invoke_agent(agent_name, enhanced_prompt, use_tools=False)
        
        return {
            "answer": agent_result.get("response", ""),
            "sources": [result.get("source", "") for result in search_results[:3]],
            "relevance_scores": [result.get("score", 0) for result in search_results[:3]],
            "context_used": len(search_results)
        }
```

## 🔧 Client Tool 개발 예제

### 1. 외부 API Tool

```python
# src/tools/api_tools.py
from src.services.tool_service import ToolService

class WeatherAPITool:
    """날씨 API Tool"""
    
    @staticmethod
    def register(tool_service: ToolService, api_key: str) -> bool:
        """날씨 API Tool 등록"""
        api_config = {
            "base_url": "https://api.openweathermap.org/data/2.5",
            "api_key": api_key,
            "timeout": 10
        }
        
        return tool_service.register_api_tool(
            name="weather_api_tool",
            description="Get current weather information from OpenWeatherMap API",
            api_config=api_config
        )

class DatabaseAPITool:
    """외부 데이터베이스 API Tool"""
    
    @staticmethod
    def register(tool_service: ToolService, db_config: dict) -> bool:
        """외부 DB API Tool 등록"""
        return tool_service.register_api_tool(
            name="external_db_tool",
            description="Access external database via REST API",
            api_config=db_config
        )
```

### 2. 사용자 정의 분석 Tool

```python
# src/tools/analysis_tools.py
from src.services.tool_service import ToolService

class StatisticalAnalysisTool:
    """통계 분석 Tool"""
    
    @staticmethod
    def register(tool_service: ToolService) -> bool:
        """통계 분석 Tool 등록"""
        function_code = '''
def main():
    import math
    import statistics
    
    def analyze_data(data):
        """데이터 통계 분석"""
        if not data or not isinstance(data, list):
            return {"error": "Invalid data format"}
        
        try:
            result = {
                "count": len(data),
                "mean": statistics.mean(data),
                "median": statistics.median(data),
                "std_dev": statistics.stdev(data) if len(data) > 1 else 0,
                "min": min(data),
                "max": max(data),
                "range": max(data) - min(data)
            }
            
            # 이상치 탐지 (IQR 방법)
            q1 = statistics.quantiles(data, n=4)[0]
            q3 = statistics.quantiles(data, n=4)[2]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [x for x in data if x < lower_bound or x > upper_bound]
            result["outliers"] = outliers
            result["outlier_count"] = len(outliers)
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    # 기본 테스트 데이터로 분석 수행
    test_data = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 100]  # 100은 이상치
    analysis_result = analyze_data(test_data)
    
    return {
        "analysis_completed": True,
        "result": analysis_result,
        "message": "Statistical analysis completed successfully"
    }
'''
        
        return tool_service.register_custom_tool_with_code(
            name="statistical_analyzer",
            description="Perform statistical analysis on numerical data including outlier detection",
            function_code=function_code
        )

class QualityControlTool:
    """품질 관리 Tool"""
    
    @staticmethod
    def register(tool_service: ToolService) -> bool:
        """품질 관리 Tool 등록"""
        function_code = '''
def main():
    def quality_check(measurements, spec_limits):
        """품질 관리 체크"""
        if not measurements or not spec_limits:
            return {"error": "Missing data"}
        
        lower_limit = spec_limits.get("lower", float("-inf"))
        upper_limit = spec_limits.get("upper", float("inf"))
        
        passed = []
        failed = []
        
        for measurement in measurements:
            if lower_limit <= measurement <= upper_limit:
                passed.append(measurement)
            else:
                failed.append(measurement)
        
        pass_rate = len(passed) / len(measurements) * 100
        
        return {
            "total_measurements": len(measurements),
            "passed": len(passed),
            "failed": len(failed),
            "pass_rate": round(pass_rate, 2),
            "failed_measurements": failed,
            "status": "PASS" if pass_rate >= 95 else "FAIL"
        }
    
    # 예제 데이터로 품질 체크
    sample_measurements = [9.8, 10.1, 9.9, 10.2, 9.7, 10.3, 9.6]
    sample_spec = {"lower": 9.5, "upper": 10.5}
    
    result = quality_check(sample_measurements, sample_spec)
    
    return {
        "quality_check_completed": True,
        "result": result,
        "message": "Quality control analysis completed"
    }
'''
        
        return tool_service.register_custom_tool_with_code(
            name="quality_control_tool",
            description="Perform quality control analysis on manufacturing measurements",
            function_code=function_code
        )
```

## 🔄 Client 워크플로우 예제

### 1. 제조 공정 모니터링 워크플로우

```python
# src/workflows/manufacturing_flow.py
from src.services.prism_client import PRISMClient
from src.services.tool_service import ToolService
from src.services.agent_service import AgentService
from src.tools.analysis_tools import StatisticalAnalysisTool, QualityControlTool

class ManufacturingWorkflow:
    """제조 공정 모니터링 워크플로우"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.client = PRISMClient(server_url)
        self.tool_service = ToolService(self.client)
        self.agent_service = AgentService(self.client)
    
    def setup_workflow(self) -> bool:
        """워크플로우 초기 설정"""
        # 1. 필요한 Tool들 등록
        tools_registered = []
        
        # 통계 분석 Tool 등록
        if StatisticalAnalysisTool.register(self.tool_service):
            tools_registered.append("statistical_analyzer")
            print("✅ Statistical Analysis Tool registered")
        
        # 품질 관리 Tool 등록
        if QualityControlTool.register(self.tool_service):
            tools_registered.append("quality_control_tool")
            print("✅ Quality Control Tool registered")
        
        # 기본 DB Tool 추가
        tools_registered.append("database_tool")
        
        # 2. 전문 Agent 생성
        agent_result = self.agent_service.create_multi_tool_analyst(tools_registered)
        print(f"✅ Multi-tool analyst created: {agent_result}")
        
        return len(tools_registered) > 0
    
    def monitor_process(self, process_id: str) -> Dict[str, Any]:
        """특정 공정 모니터링"""
        query = f"""
        공정 ID {process_id}의 최근 상태를 분석해주세요.
        데이터베이스에서 관련 정보를 조회하고, 통계 분석과 품질 관리 체크를 수행해주세요.
        """
        
        result = self.agent_service.query_agent("multi_tool_analyst", query)
        
        return {
            "process_id": process_id,
            "analysis_result": result["answer"],
            "tools_used": result["tools_used"],
            "execution_time": result["execution_time"]
        }
    
    def daily_quality_report(self) -> Dict[str, Any]:
        """일일 품질 보고서 생성"""
        query = """
        오늘의 전체 제조 공정 품질 상태를 분석해주세요.
        1. 데이터베이스에서 오늘의 LOT 데이터 조회
        2. 각 공정별 통계 분석 수행
        3. 품질 관리 기준 대비 평가
        4. 이상 상황이 있다면 원인 분석 및 개선 방안 제시
        """
        
        result = self.agent_service.query_agent("multi_tool_analyst", query)
        
        return {
            "date": "today",
            "quality_report": result["answer"],
            "tools_used": result["tools_used"],
            "recommendations": "품질 개선 권장사항이 포함됨"
        }
```

### 2. RAG 기반 지식 관리 워크플로우

```python
# src/workflows/knowledge_management.py
from src.services.prism_client import PRISMClient
from src.services.vector_service import VectorService

class KnowledgeManagementWorkflow:
    """RAG 기반 지식 관리 워크플로우"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.client = PRISMClient(server_url)
        self.vector_service = VectorService(self.client)
    
    def setup_knowledge_base(self, documents: List[Dict[str, Any]]) -> bool:
        """지식 베이스 구축"""
        # 1. 문서 인덱스 생성
        if not self.vector_service.create_document_index("ManufacturingDocs"):
            return False
        
        # 2. 문서들 배치 추가
        result = self.vector_service.add_documents(
            "ManufacturingDocs", 
            documents, 
            encoder_model="intfloat/multilingual-e5-base"
        )
        
        return result.get("success", False)
    
    def query_knowledge_base(self, question: str) -> Dict[str, Any]:
        """지식 베이스 질의"""
        return self.vector_service.implement_rag(
            class_name="ManufacturingDocs",
            question=question,
            agent_name="manufacturing_analyst"
        )
    
    def add_new_knowledge(self, document: Dict[str, Any]) -> bool:
        """새로운 지식 추가"""
        result = self.vector_service.add_documents("ManufacturingDocs", [document])
        return result.get("success", False)
```

## 📊 Client 사용 예제

### 완전한 Client 애플리케이션 예제

```python
# examples/manufacturing_client.py
from src.services.prism_client import PRISMClient
from src.workflows.manufacturing_flow import ManufacturingWorkflow
from src.workflows.knowledge_management import KnowledgeManagementWorkflow

def main():
    """제조업 Client 애플리케이션 메인"""
    
    # 1. 서버 연결 확인
    client = PRISMClient("http://localhost:8000")
    health = client.health_check()
    print(f"🚀 Server Status: {health}")
    
    # 2. 제조 워크플로우 설정
    manufacturing_flow = ManufacturingWorkflow()
    if manufacturing_flow.setup_workflow():
        print("✅ Manufacturing workflow setup completed")
    
    # 3. 지식 관리 시스템 설정
    knowledge_flow = KnowledgeManagementWorkflow()
    
    # 샘플 문서 데이터
    sample_docs = [
        {
            "content": "반도체 제조에서 CVD 공정은 화학 기상 증착을 통해 박막을 형성하는 중요한 공정입니다.",
            "title": "CVD 공정 개요",
            "source": "manufacturing_handbook.pdf",
            "metadata": {"category": "process", "department": "fab"}
        },
        {
            "content": "품질 관리에서 SPC(Statistical Process Control)는 공정 변동을 모니터링하는 핵심 방법입니다.",
            "title": "SPC 품질 관리",
            "source": "quality_manual.pdf", 
            "metadata": {"category": "quality", "department": "qc"}
        }
    ]
    
    if knowledge_flow.setup_knowledge_base(sample_docs):
        print("✅ Knowledge base setup completed")
    
    # 4. 실제 업무 시나리오 테스트
    print("\n" + "="*50)
    print("📊 Manufacturing Process Analysis")
    print("="*50)
    
    # 공정 모니터링
    process_result = manufacturing_flow.monitor_process("PROC_001")
    print(f"Process Analysis Result:\n{process_result['analysis_result']}")
    
    # 일일 품질 보고서
    quality_report = manufacturing_flow.daily_quality_report()
    print(f"\nDaily Quality Report:\n{quality_report['quality_report']}")
    
    # 5. 지식 베이스 활용
    print("\n" + "="*50)
    print("🧠 Knowledge Base Query")
    print("="*50)
    
    knowledge_query = "CVD 공정에서 품질 관리는 어떻게 해야 하나요?"
    knowledge_result = knowledge_flow.query_knowledge_base(knowledge_query)
    
    print(f"Question: {knowledge_query}")
    print(f"Answer: {knowledge_result['answer']}")
    print(f"Sources: {knowledge_result['sources']}")

if __name__ == "__main__":
    main()
```

## 🔧 Client 설정 관리

```python
# src/config/settings.py
from typing import Dict, Any
import os

class ClientSettings:
    """Client 설정 관리"""
    
    # Server 연결 설정
    PRISM_SERVER_URL = os.getenv("PRISM_SERVER_URL", "http://localhost:8000")
    WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    # Tool 설정
    DEFAULT_ENCODER_MODEL = "intfloat/multilingual-e5-base"
    DEFAULT_VECTOR_DIMENSION = 768
    
    # API 키 설정 (필요한 경우)
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # 품질 관리 기준
    QUALITY_THRESHOLDS = {
        "pass_rate_minimum": 95.0,
        "outlier_threshold": 1.5,
        "control_limit_sigma": 3.0
    }
    
    @classmethod
    def get_tool_config(cls, tool_type: str) -> Dict[str, Any]:
        """Tool 타입별 기본 설정 반환"""
        configs = {
            "weather_api": {
                "api_key": cls.OPENWEATHER_API_KEY,
                "base_url": "https://api.openweathermap.org/data/2.5",
                "timeout": 10
            },
            "quality_control": {
                "thresholds": cls.QUALITY_THRESHOLDS
            },
            "vector_db": {
                "encoder_model": cls.DEFAULT_ENCODER_MODEL,
                "vector_dimension": cls.DEFAULT_VECTOR_DIMENSION
            }
        }
        
        return configs.get(tool_type, {})
```

## 📋 Client 개발 체크리스트

### ✅ 개발 단계별 체크리스트

**1. 기본 설정**
- [ ] PRISM Server 연결 확인
- [ ] API 클라이언트 구현
- [ ] 환경 변수 설정
- [ ] 오류 처리 구현

**2. Tool 개발**
- [ ] 필요한 Tool 타입 식별
- [ ] Tool 등록 함수 구현
- [ ] Tool 테스트 스크립트 작성
- [ ] Tool 설정 관리

**3. Agent 활용**
- [ ] 업무별 Agent 설계
- [ ] Agent-Tool 연결 구현
- [ ] 프롬프트 엔지니어링
- [ ] 결과 검증 로직

**4. 워크플로우 구축**
- [ ] 업무 프로세스 분석
- [ ] 워크플로우 클래스 설계
- [ ] 예외 처리 구현
- [ ] 성능 최적화

**5. RAG 구현**
- [ ] 문서 수집 및 전처리
- [ ] Vector DB 인덱스 생성
- [ ] 검색 품질 평가
- [ ] 답변 품질 검증

**6. 테스트 및 배포**
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 수행
- [ ] 성능 테스트
- [ ] 배포 스크립트 작성

## 🚀 Client 배포 가이드

### Docker를 활용한 Client 배포

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY examples/ ./examples/

CMD ["python", "examples/manufacturing_client.py"]
```

```yaml
# docker-compose.yml (Client용)
version: '3.8'

services:
  manufacturing-client:
    build: .
    environment:
      - PRISM_SERVER_URL=http://prism-server:8000
      - WEAVIATE_URL=http://weaviate:8080
    depends_on:
      - prism-server
    networks:
      - prism-network

networks:
  prism-network:
    external: true
```

---

**PRISM Core Client** - 강력한 AI 서버와 함께하는 지능형 제조 혁신 클라이언트 🎯 