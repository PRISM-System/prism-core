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

### 1. Tool 등록

```python
def register_tool(tool_config: dict):
    """새로운 Tool 등록"""
    url = "http://localhost:8000/api/tools/register"
    
    response = requests.post(url, json=tool_config)
    return response.json()

# 사용 예시
calculator_tool = {
    "name": "calculator",
    "description": "수학 계산을 수행하는 도구",
    "parameters_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "계산할 수학 표현식"
            }
        },
        "required": ["expression"]
    },
    "tool_type": "calculation",
    "config": {
        "safe_mode": True
    }
}

register_tool(calculator_tool)
```

### 2. Tool 실행

```python
def execute_tool(tool_name: str, parameters: dict):
    """Tool 실행"""
    url = "http://localhost:8000/api/tools/execute"
    data = {
        "tool_name": tool_name,
        "parameters": parameters
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 사용 예시
result = execute_tool("calculator", {"expression": "2 + 3 * 4"})
print(result)
```

### 3. 등록된 Tool 조회

```python
def list_tools():
    """등록된 Tool 목록 조회"""
    url = "http://localhost:8000/api/tools"
    
    response = requests.get(url)
    return response.json()

# 사용 예시
tools = list_tools()
for tool in tools:
    print(f"Tool: {tool['name']}")
    print(f"설명: {tool['description']}")
    print("---")
```

## 📝 실제 예제

### 1. 문서 기반 QA 시스템

```python
class DocumentQA:
    def __init__(self, vector_db_class: str = "Documents"):
        self.vector_db_class = vector_db_class
        self.base_url = "http://localhost:8000"
        self.llm_url = "http://localhost:8001/v1/chat/completions"
    
    def answer_question(self, question: str):
        """문서를 기반으로 질문에 답변"""
        # 1. 관련 문서 검색
        search_results = self._search_documents(question)
        
        # 2. 컨텍스트 구성
        context = self._build_context(search_results)
        
        # 3. LLM으로 답변 생성
        answer = self._generate_answer(question, context)
        
        return {
            "question": question,
            "answer": answer,
            "sources": search_results
        }
    
    def _search_documents(self, query: str):
        """관련 문서 검색"""
        url = f"{self.base_url}/api/vector-db/search/{self.vector_db_class}"
        data = {"query": query, "limit": 3}
        
        response = requests.post(url, json=data)
        return response.json()
    
    def _build_context(self, search_results: list):
        """검색 결과를 컨텍스트로 구성"""
        context_parts = []
        for result in search_results:
            context_parts.append(f"제목: {result.get('title', '')}")
            context_parts.append(f"내용: {result.get('content', '')}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str):
        """LLM으로 답변 생성"""
        prompt = f"""다음 문서를 참고하여 질문에 답변해주세요.

문서 내용:
{context}

질문: {question}

답변:"""
        
        data = {
            "model": "Qwen/Qwen3-0.6B",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.7
        }
        
        response = requests.post(self.llm_url, json=data)
        return response.json()['choices'][0]['message']['content']

# 사용 예시
qa_system = DocumentQA("Documents")
result = qa_system.answer_question("반도체 제조 공정의 주요 단계는 무엇인가요?")
print(f"질문: {result['question']}")
print(f"답변: {result['answer']}")
```

### 2. 지능형 에이전트

```python
class IntelligentAgent:
    def __init__(self, name: str):
        self.name = name
        self.tools = []
        self.knowledge_base = "Knowledge"
        self.base_url = "http://localhost:8000"
        self.llm_url = "http://localhost:8001/v1/chat/completions"
    
    def add_tool(self, tool_name: str):
        """에이전트에 Tool 추가"""
        self.tools.append(tool_name)
    
    def process_request(self, request: str):
        """사용자 요청 처리"""
        # 1. 요청 분석
        analysis = self._analyze_request(request)
        
        # 2. 필요한 Tool 결정
        required_tools = self._determine_tools(analysis)
        
        # 3. 지식 베이스 검색
        knowledge = self._search_knowledge(request)
        
        # 4. 응답 생성
        response = self._generate_response(request, analysis, required_tools, knowledge)
        
        return response
    
    def _analyze_request(self, request: str):
        """요청 분석"""
        prompt = f"""다음 요청을 분석해주세요:
요청: {request}

분석 결과를 JSON 형태로 반환해주세요:
- intent: 의도
- required_tools: 필요한 도구들
- complexity: 복잡도 (simple/medium/complex)
"""
        
        data = {
            "model": "Qwen/Qwen3-0.6B",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        response = requests.post(self.llm_url, json=data)
        return response.json()['choices'][0]['message']['content']
    
    def _determine_tools(self, analysis: str):
        """필요한 Tool 결정"""
        # 간단한 키워드 기반 Tool 매칭
        tools_needed = []
        analysis_lower = analysis.lower()
        
        if "계산" in analysis_lower or "수학" in analysis_lower:
            tools_needed.append("calculator")
        
        return tools_needed
    
    def _search_knowledge(self, query: str):
        """지식 베이스 검색"""
        url = f"{self.base_url}/api/vector-db/search/{self.knowledge_base}"
        data = {"query": query, "limit": 2}
        
        response = requests.post(url, json=data)
        return response.json()
    
    def _generate_response(self, request: str, analysis: str, tools: list, knowledge: list):
        """응답 생성"""
        context_parts = [f"요청: {request}"]
        
        if knowledge:
            context_parts.append("관련 지식:")
            for item in knowledge:
                context_parts.append(f"- {item.get('content', '')}")
        
        if tools:
            context_parts.append(f"사용할 도구: {', '.join(tools)}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""다음 정보를 바탕으로 사용자 요청에 답변해주세요:

{context}

답변:"""
        
        data = {
            "model": "Qwen/Qwen3-0.6B",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(self.llm_url, json=data)
        return response.json()['choices'][0]['message']['content']

# 사용 예시
agent = IntelligentAgent("제조 전문가")
agent.add_tool("calculator")

response = agent.process_request("반도체 제조 공정의 품질 관리 방법을 알려주세요.")
print(response)
```

## 🧪 테스트 및 디버깅

### 1. 서비스 연결 테스트

```python
def test_connections():
    """모든 서비스 연결 테스트"""
    services = {
        "PRISM-Core API": "http://localhost:8000/",
        "vLLM Service": "http://localhost:8001/v1/models",
        "Weaviate": "http://localhost:8080/v1/meta"
    }
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {service_name}: 연결 성공")
        except Exception as e:
            print(f"❌ {service_name}: 연결 실패 - {str(e)}")

test_connections()
```

### 2. 기능 테스트

```python
def test_basic_functionality():
    """기본 기능 테스트"""
    # Vector DB 테스트
    print("=== Vector DB 테스트 ===")
    create_index("TestDocs", "테스트용 문서")
    
    test_docs = [{
        "title": "테스트 문서",
        "content": "이것은 테스트용 문서입니다.",
        "metadata": {"test": True}
    }]
    
    add_documents("TestDocs", test_docs)
    results = search_documents("테스트", "TestDocs")
    print(f"검색 결과: {len(results)}개 문서")
    
    # LLM 테스트
    print("\n=== LLM 테스트 ===")
    response = generate_text("안녕하세요!")
    print(f"LLM 응답: {response['choices'][0]['message']['content']}")

test_basic_functionality()
```

## 📚 추가 리소스

- **API 문서**: http://localhost:8000/docs
- **Weaviate 콘솔**: http://localhost:8080
- **GitHub 저장소**: https://github.com/PRISM-System/prism-core

---

**팁**: 데모를 위해 간단한 예제부터 시작하여 점진적으로 복잡한 기능을 추가해보세요! 