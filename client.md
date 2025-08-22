# PRISM-Core 클라이언트 가이드

PRISM-Core를 이용해 AI 에이전트를 만들고 활용하는 단계별 가이드입니다.

## 📋 목차

1. [기본 설정](#기본-설정)
2. [Vector DB 활용](#vector-db-활용)
3. [LLM 서비스 연동](#llm-서비스-연동)
4. [Tool 시스템 활용](#tool-시스템-활용)
5. [실제 예제](#실제-예제)

## 🔧 기본 설정

### 1. PRISM-Core 서버 시작

```bash
# 저장소 클론
git clone https://github.com/PRISM-System/prism-core.git
cd prism-core

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 필요한 설정 수정

# 서비스 시작
docker-compose up -d
```

### 2. 클라이언트 환경 설정

```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 필요한 패키지 설치
pip install requests fastapi uvicorn
```

### 3. 연결 테스트

```python
import requests

# 서버 상태 확인
response = requests.get("http://localhost:8000/")
print(response.json())
# 예상 출력: {"message": "Welcome to PRISM Core", "version": "0.1.0"}
```

## 🧠 Vector DB 활용

### 1. 인덱스 생성

```python
import requests

def create_index(class_name: str, description: str = ""):
    """Vector DB 인덱스 생성"""
    url = "http://localhost:8000/api/vector-db/indices"
    data = {
        "class_name": class_name,
        "description": description,
        "vector_dimension": 384,
        "encoder_model": "sentence-transformers/all-MiniLM-L6-v2"
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시
create_index("Documents", "문서 저장소")
create_index("Knowledge", "지식 베이스")
```

### 2. 문서 추가

```python
def add_documents(class_name: str, documents: list):
    """문서를 Vector DB에 추가"""
    url = f"http://localhost:8000/api/vector-db/documents/{class_name}/batch"
    
    response = requests.post(url, json=documents)
    return response.json()

# 사용 예시
documents = [
    {
        "title": "반도체 제조 공정",
        "content": "반도체 제조는 웨이퍼 준비부터 패키징까지 여러 단계를 거칩니다.",
        "metadata": {"category": "manufacturing", "source": "manual"}
    },
    {
        "title": "품질 관리 가이드",
        "content": "품질 관리는 제품의 일관성과 신뢰성을 보장하는 중요한 과정입니다.",
        "metadata": {"category": "quality", "source": "guide"}
    }
]

add_documents("Documents", documents)
```

### 3. 문서 검색

```python
def search_documents(query: str, class_name: str = "Documents", limit: int = 5):
    """문서 검색"""
    url = f"http://localhost:8000/api/vector-db/search/{class_name}"
    data = {
        "query": query,
        "limit": limit
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시
results = search_documents("반도체 제조 공정", "Documents", 3)
for result in results:
    print(f"점수: {result['score']:.3f}")
    print(f"내용: {result['content']}")
    print("---")
```

## 🤖 LLM 서비스 연동

### 1. 텍스트 생성

```python
def generate_text(prompt: str, model: str = "Qwen/Qwen3-0.6B"):
    """LLM을 이용한 텍스트 생성"""
    url = "http://localhost:8001/v1/chat/completions"
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시
response = generate_text("반도체 제조 공정에 대해 설명해주세요.")
print(response['choices'][0]['message']['content'])
```

### 2. 대화형 챗봇

```python
class ChatBot:
    def __init__(self, model: str = "Qwen/Qwen3-0.6B"):
        self.model = model
        self.conversation_history = []
        self.base_url = "http://localhost:8001/v1/chat/completions"
    
    def chat(self, message: str):
        """대화형 응답 생성"""
        self.conversation_history.append({"role": "user", "content": message})
        
        data = {
            "model": self.model,
            "messages": self.conversation_history,
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(self.base_url, json=data)
        assistant_message = response.json()['choices'][0]['message']['content']
        
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        return assistant_message
    
    def reset(self):
        """대화 기록 초기화"""
        self.conversation_history = []

# 사용 예시
bot = ChatBot()
response = bot.chat("안녕하세요!")
print(response)
```

## 🔧 Tool 시스템 활용

PRISM-Core의 Tool 시스템은 AI 에이전트가 외부 기능을 수행할 수 있도록 해주는 핵심 구성 요소입니다. Tool은 데이터베이스 조회, API 호출, 계산, 파일 처리 등 다양한 작업을 수행할 수 있습니다.

### 1. Tool의 개념과 동작원리

#### Tool이란?
- **정의**: AI 에이전트가 호출할 수 있는 함수나 서비스
- **목적**: LLM의 텍스트 생성 능력을 외부 시스템과 연결
- **특징**: JSON 스키마로 정의된 매개변수를 받아 결과를 반환

#### 동작원리
```
1. 사용자 질의 → 2. LLM 분석 → 3. Tool 선택 → 4. Tool 실행 → 5. 결과 반환
```

1. **사용자 질의**: "A-1 라인 압력 데이터를 조회해줘"
2. **LLM 분석**: 데이터베이스 조회가 필요하다고 판단
3. **Tool 선택**: `database_query` Tool 선택
4. **Tool 실행**: SQL 쿼리 실행하여 데이터 조회
5. **결과 반환**: 조회된 데이터를 포함한 응답 생성

### 2. Tool 정의 및 스키마

#### 기본 Tool 구조
```python
class CustomTool:
    def __init__(self):
        self.name = "tool_name"
        self.description = "도구 설명"
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "parameter1": {
                    "type": "string",
                    "description": "매개변수 설명"
                }
            },
            "required": ["parameter1"]
        }
    
    async def execute(self, parameters: dict):
        # 실제 작업 수행
        return {"result": "작업 결과"}
```

#### 매개변수 스키마 상세 설명
```python
parameters_schema = {
    "type": "object",                    # 객체 타입
    "properties": {                      # 속성 정의
        "query": {
            "type": "string",            # 문자열 타입
            "description": "SQL 쿼리",   # 설명
            "enum": ["SELECT", "INSERT"] # 열거형 (선택사항)
        },
        "limit": {
            "type": "integer",           # 정수 타입
            "description": "반환할 행 수",
            "minimum": 1,                # 최소값
            "maximum": 1000              # 최대값
        },
        "filters": {
            "type": "object",            # 객체 타입
            "description": "필터 조건",
            "properties": {
                "line": {"type": "string"},
                "date_from": {"type": "string", "format": "date"}
            }
        }
    },
    "required": ["query"]               # 필수 매개변수
}
```

### 3. Tool 등록 및 관리

#### 3.1 Tool 등록
```python
def register_tool(tool_config: dict):
    """새로운 Tool 등록"""
    url = "http://localhost:8000/api/tools/register"
    
    response = requests.post(url, json=tool_config)
    return response.json()

# 데이터베이스 조회 Tool 등록
database_tool = {
    "name": "database_query",
    "description": "PostgreSQL 데이터베이스에서 데이터를 조회합니다",
    "parameters_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "실행할 SQL 쿼리"
            },
            "timeout": {
                "type": "integer",
                "description": "쿼리 타임아웃 (초)",
                "default": 30
            }
        },
        "required": ["query"]
    },
    "tool_type": "database"
}

result = register_tool(database_tool)
print(f"Tool 등록 결과: {result}")
```

#### 3.2 Tool 목록 조회
```python
def list_tools():
    """등록된 Tool 목록 조회"""
    url = "http://localhost:8000/api/tools"
    
    response = requests.get(url)
    tools = response.json()
    
    print("등록된 Tools:")
    for tool in tools:
        print(f"- {tool['name']}: {tool['description']}")
        print(f"  매개변수: {tool['parameters_schema']}")
    
    return tools

tools = list_tools()
```

#### 3.3 Tool 정보 조회
```python
def get_tool_info(tool_name: str):
    """특정 Tool의 상세 정보 조회"""
    url = f"http://localhost:8000/api/tools/{tool_name}"
    
    response = requests.get(url)
    return response.json()

# 사용 예시
tool_info = get_tool_info("database_query")
print(f"Tool 정보: {tool_info}")
```

#### 3.4 Tool 삭제
```python
def delete_tool(tool_name: str):
    """Tool 삭제"""
    url = f"http://localhost:8000/api/tools/{tool_name}"
    
    response = requests.delete(url)
    return response.json()

# 사용 예시
result = delete_tool("unused_tool")
print(f"삭제 결과: {result}")
```

### 4. Tool 실행 및 활용

#### 4.1 직접 Tool 실행
```python
def execute_tool(tool_name: str, parameters: dict):
    """Tool 직접 실행"""
    url = "http://localhost:8000/api/tools/execute"
    data = {
        "tool_name": tool_name,
        "parameters": parameters
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 데이터베이스 조회 예시
result = execute_tool("database_query", {
    "query": "SELECT * FROM pressure_sensors WHERE line='A-1' LIMIT 10"
})

if result["success"]:
    print("조회된 데이터:")
    for row in result["result"]["rows"]:
        print(f"- {row}")
else:
    print(f"오류: {result['error_message']}")
```

#### 4.2 에이전트와 함께 Tool 사용

##### Agent에 Tool 등록의 의미

에이전트에 Tool을 등록하는 것은 **AI 에이전트가 자동으로 Tool을 선택하고 사용할 수 있도록 권한을 부여**하는 것입니다.

```python
def assign_tools_to_agent(agent_name: str, tool_names: list):
    """에이전트에 Tool 할당"""
    url = f"http://localhost:8000/api/agents/{agent_name}/tools"
    
    data = {
        "agent_name": agent_name,
        "tool_names": tool_names
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시: 분석 에이전트에 도구 할당
result = assign_tools_to_agent("analysis_agent", [
    "database_query",      # 데이터베이스 조회
    "vector_search",       # 벡터 검색
    "statistical_analysis" # 통계 분석
])
print(f"Tool 할당 결과: {result}")
```

**Agent 등록의 의미:**
- **권한 부여**: 에이전트가 특정 Tool을 사용할 수 있는 권한
- **컨텍스트 제공**: LLM에게 "이 에이전트는 어떤 도구들을 사용할 수 있는지" 알려줌
- **자동 선택**: 사용자 질의에 따라 LLM이 적절한 Tool을 자동으로 선택
- **보안**: 에이전트별로 사용 가능한 Tool을 제한하여 보안 강화

##### Tool 트리거 시 실제 동작 과정

Tool이 트리거될 때의 전체 동작 과정을 단계별로 설명합니다:

```python
def invoke_agent_with_tools(agent_name: str, prompt: str):
    """에이전트를 호출하여 Tool 자동 사용"""
    url = f"http://localhost:8000/api/agents/{agent_name}/invoke"
    
    data = {
        "prompt": prompt,
        "use_tools": True,           # Tool 사용 활성화
        "max_tool_calls": 5,         # 최대 Tool 호출 횟수
        "max_tokens": 1000,
        "temperature": 0.3
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시
result = invoke_agent_with_tools("analysis_agent", 
    "A-1 라인 압력 데이터를 조회하고 이상치를 분석해줘")

print(f"에이전트 응답: {result['text']}")
print(f"사용된 Tools: {result['tools_used']}")
print(f"Tool 결과: {result['tool_results']}")
```

**실제 동작 과정:**

```
1. 클라이언트 요청
   ↓
2. 서버에서 에이전트 로드
   ↓
3. LLM이 사용자 질의 분석
   ↓
4. Tool 선택 및 호출
   ↓
5. Tool 실행
   ↓
6. 결과를 LLM에 전달
   ↓
7. 최종 응답 생성
   ↓
8. 클라이언트에 응답
```

**상세 동작 과정:**

1. **클라이언트 요청 단계**
   ```python
   # 클라이언트에서 에이전트 호출
   response = requests.post(
       "http://localhost:8000/api/agents/analysis_agent/invoke",
       json={
           "prompt": "A-1 라인 압력 데이터를 조회하고 이상치를 분석해줘",
           "use_tools": True,
           "max_tool_calls": 5
       }
   )
   ```

2. **서버에서 에이전트 로드**
   ```python
   # 서버 내부 동작 (PrismLLMService)
   agent = agent_registry.get_agent("analysis_agent")
   # agent.tools = ["database_query", "vector_search", "statistical_analysis"]
   ```

3. **LLM이 사용자 질의 분석**
   ```python
   # LLM이 질의를 분석하여 필요한 Tool 결정
   # "A-1 라인 압력 데이터를 조회하고 이상치를 분석해줘"
   # → database_query (데이터 조회) + statistical_analysis (이상치 분석) 필요
   ```

4. **Tool 선택 및 호출**
   ```python
   # LLM이 자동으로 Tool 호출 결정
   tool_calls = [
       {
           "tool": "database_query",
           "parameters": {
               "query": "SELECT * FROM pressure_sensors WHERE line='A-1'"
           }
       }
   ]
   ```

5. **Tool 실행**
   ```python
   # 서버에서 Tool 실행
   tool_result = tool_registry.execute_tool("database_query", {
       "query": "SELECT * FROM pressure_sensors WHERE line='A-1'"
   })
   # 결과: {"rows": [{"id": 1, "pressure": 2.5, ...}]}
   ```

6. **결과를 LLM에 전달**
   ```python
   # Tool 실행 결과를 LLM에 컨텍스트로 제공
   context = f"""
   Tool 실행 결과:
   database_query: {tool_result}
   
   이제 이상치 분석을 수행하세요.
   """
   ```

7. **최종 응답 생성**
   ```python
   # LLM이 Tool 결과를 바탕으로 최종 응답 생성
   final_response = llm.generate(context + "사용자 질의: " + prompt)
   ```

8. **클라이언트에 응답**
   ```python
   # 클라이언트에 최종 결과 반환
   return {
       "text": "A-1 라인 압력 데이터 분석 결과...",
       "tools_used": ["database_query", "statistical_analysis"],
       "tool_results": [
           {
               "tool": "database_query",
               "result": {"rows": [...]}
           },
           {
               "tool": "statistical_analysis", 
               "result": {"anomalies": [...]}
           }
       ]
   }
   ```

##### Tool 트리거 시 서버-클라이언트 통신 흐름

```python
# 전체 통신 흐름 예시
def demonstrate_tool_workflow():
    """Tool 워크플로우 시연"""
    
    # 1. 에이전트 등록 (한 번만 수행)
    agent_config = {
        "name": "data_analyst",
        "description": "데이터 분석 전문가",
        "role_prompt": "당신은 제조 공정 데이터를 분석하는 전문가입니다.",
        "tools": []  # 초기에는 빈 리스트
    }
    
    # 에이전트 등록
    requests.post("http://localhost:8000/api/agents", json=agent_config)
    
    # 2. Tool 할당
    assign_tools_to_agent("data_analyst", [
        "database_query",
        "vector_search", 
        "statistical_analysis"
    ])
    
    # 3. 에이전트 호출 (Tool 자동 사용)
    result = invoke_agent_with_tools("data_analyst",
        "A-1 라인에서 압력 이상이 발생한 것 같아. 최근 데이터를 조회하고 분석해줘.")
    
    print("=== Tool 워크플로우 결과 ===")
    print(f"최종 응답: {result['text']}")
    print(f"사용된 Tools: {result['tools_used']}")
    print(f"Tool 실행 횟수: {len(result['tool_results'])}")
    
    # 4. Tool 실행 결과 상세 확인
    for i, tool_result in enumerate(result['tool_results'], 1):
        print(f"\nTool {i}: {tool_result['tool']}")
        print(f"결과: {tool_result['result']}")

# 워크플로우 실행
demonstrate_tool_workflow()
```

##### Tool 사용 권한 관리

```python
def manage_tool_permissions():
    """Tool 사용 권한 관리"""
    
    # 1. 에이전트별 Tool 권한 설정
    agent_tools = {
        "data_analyst": ["database_query", "statistical_analysis", "vector_search"],
        "system_monitor": ["database_query", "alert_system"],
        "report_generator": ["database_query", "file_writer", "email_sender"]
    }
    
    # 2. 권한 할당
    for agent_name, tools in agent_tools.items():
        assign_tools_to_agent(agent_name, tools)
        print(f"{agent_name}에 {len(tools)}개 Tool 할당 완료")
    
    # 3. 권한 확인
    for agent_name in agent_tools.keys():
        agent_info = requests.get(f"http://localhost:8000/api/agents/{agent_name}").json()
        print(f"{agent_name} 사용 가능 Tool: {agent_info['tools']}")

# 권한 관리 실행
manage_tool_permissions()
```

### 5. 고급 Tool 개발

#### 5.1 복잡한 Tool 예시
```python
class AdvancedAnalysisTool:
    def __init__(self):
        self.name = "advanced_analysis"
        self.description = "복합적인 데이터 분석을 수행합니다"
        self.parameters_schema = {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": ["trend", "anomaly", "correlation"],
                    "description": "분석 유형"
                },
                "data_source": {
                    "type": "string",
                    "description": "데이터 소스 (테이블명)"
                },
                "time_range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "format": "date-time"},
                        "end": {"type": "string", "format": "date-time"}
                    },
                    "required": ["start", "end"]
                },
                "parameters": {
                    "type": "object",
                    "description": "분석별 추가 매개변수"
                }
            },
            "required": ["analysis_type", "data_source"]
        }
    
    async def execute(self, parameters: dict):
        analysis_type = parameters["analysis_type"]
        data_source = parameters["data_source"]
        time_range = parameters.get("time_range")
        
        if analysis_type == "trend":
            return await self._analyze_trend(data_source, time_range)
        elif analysis_type == "anomaly":
            return await self._detect_anomaly(data_source, time_range)
        elif analysis_type == "correlation":
            return await self._analyze_correlation(data_source, time_range)
    
    async def _analyze_trend(self, data_source, time_range):
        # 트렌드 분석 로직
        return {
            "trend": "increasing",
            "slope": 0.15,
            "confidence": 0.85
        }
    
    async def _detect_anomaly(self, data_source, time_range):
        # 이상치 탐지 로직
        return {
            "anomalies": [
                {"timestamp": "2025-08-22T10:30:00Z", "value": 3.2, "severity": "high"}
            ],
            "total_anomalies": 1
        }
    
    async def _analyze_correlation(self, data_source, time_range):
        # 상관관계 분석 로직
        return {
            "correlation_matrix": {
                "pressure_temperature": 0.75,
                "pressure_flow": 0.45
            }
        }
```

#### 5.2 Tool 체이닝 (Tool Chaining)
```python
def create_tool_chain():
    """여러 Tool을 순차적으로 실행하는 체인 생성"""
    
    # 1단계: 데이터 조회
    data_result = execute_tool("database_query", {
        "query": "SELECT * FROM sensors WHERE timestamp > '2025-08-22'"
    })
    
    if not data_result["success"]:
        return {"error": "데이터 조회 실패"}
    
    # 2단계: 데이터 전처리
    preprocess_result = execute_tool("data_preprocessor", {
        "data": data_result["result"]["rows"],
        "operations": ["normalize", "remove_outliers"]
    })
    
    if not preprocess_result["success"]:
        return {"error": "전처리 실패"}
    
    # 3단계: 분석 수행
    analysis_result = execute_tool("statistical_analysis", {
        "data": preprocess_result["result"]["processed_data"],
        "methods": ["mean", "std", "correlation"]
    })
    
    return {
        "data_count": len(data_result["result"]["rows"]),
        "preprocessing_status": preprocess_result["result"]["status"],
        "analysis_results": analysis_result["result"]
    }

# 사용 예시
chain_result = create_tool_chain()
print(f"Tool 체인 결과: {chain_result}")
```

### 6. Tool 모니터링 및 디버깅

#### 6.1 Tool 실행 로그
```python
def monitor_tool_execution(tool_name: str, parameters: dict):
    """Tool 실행을 모니터링하고 성능 측정"""
    import time
    
    start_time = time.time()
    
    # Tool 실행
    result = execute_tool(tool_name, parameters)
    
    execution_time = time.time() - start_time
    
    # 실행 정보 로깅
    log_info = {
        "tool_name": tool_name,
        "parameters": parameters,
        "execution_time": execution_time,
        "success": result["success"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    print(f"Tool 실행 로그: {log_info}")
    return result

# 사용 예시
result = monitor_tool_execution("database_query", {
    "query": "SELECT COUNT(*) FROM sensors"
})
```

#### 6.2 Tool 오류 처리
```python
def safe_tool_execution(tool_name: str, parameters: dict, max_retries: int = 3):
    """안전한 Tool 실행 (재시도 로직 포함)"""
    
    for attempt in range(max_retries):
        try:
            result = execute_tool(tool_name, parameters)
            
            if result["success"]:
                return result
            
            print(f"시도 {attempt + 1} 실패: {result.get('error_message', 'Unknown error')}")
            
        except Exception as e:
            print(f"시도 {attempt + 1} 예외: {str(e)}")
        
        if attempt < max_retries - 1:
            import time
            time.sleep(2 ** attempt)  # 지수 백오프
    
    return {
        "success": False,
        "error_message": f"Tool 실행 실패 (최대 {max_retries}회 시도)"
    }

# 사용 예시
result = safe_tool_execution("database_query", {
    "query": "SELECT * FROM sensors"
})
```

### 7. Tool 테스트 및 검증

#### 7.1 Tool 단위 테스트
```python
def test_tool_functionality():
    """Tool 기능 테스트"""
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "기본 데이터 조회",
            "tool": "database_query",
            "parameters": {"query": "SELECT 1 as test"},
            "expected": {"success": True}
        },
        {
            "name": "잘못된 쿼리",
            "tool": "database_query", 
            "parameters": {"query": "INVALID SQL"},
            "expected": {"success": False}
        }
    ]
    
    results = []
    for test_case in test_cases:
        result = execute_tool(test_case["tool"], test_case["parameters"])
        
        test_result = {
            "test_name": test_case["name"],
            "expected": test_case["expected"]["success"],
            "actual": result["success"],
            "passed": result["success"] == test_case["expected"]["success"]
        }
        
        results.append(test_result)
        print(f"테스트 '{test_case['name']}': {'통과' if test_result['passed'] else '실패'}")
    
    return results

# 테스트 실행
test_results = test_tool_functionality()
```

이제 Tool 시스템의 전체 동작 과정을 완전히 이해할 수 있습니다! 🚀 