# PRISM-Core 클라이언트 가이드

PRISM-Core의 REST API(`/core/api/*`)를 사용하는 최소 예제입니다. (서버는 `docker compose up -d --build` 후 `http://localhost:8000` 기준)

## 시작 전 체크
- 헬스: `curl http://localhost:8000/`
- Docs: `http://localhost:8000/docs`
- DB 상태: `curl http://localhost:8000/core/api/db`

## 에이전트/툴 기본 흐름

### 1) 에이전트 등록
```bash
curl -X POST http://localhost:8000/core/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo_agent",
    "description": "Demo agent",
    "role_prompt": "You are a helpful manufacturing analyst.",
    "tools": []
  }'
```

### 2) 툴 확인 또는 등록
- 기본 툴(예: `database_tool`)이 레지스트리에 존재해야 에이전트에 할당 가능.
```bash
curl http://localhost:8000/core/api/tools
# 동적 툴 등록
curl -X POST http://localhost:8000/core/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "echo_tool",
    "description": "Echo text back",
    "parameters_schema": {
      "type": "object",
      "properties": { "text": {"type": "string"} },
      "required": ["text"]
    },
    "tool_type": "calculation"
  }'
```

### 3) 에이전트에 툴 할당
```bash
curl -X POST http://localhost:8000/core/api/agents/demo_agent/tools \
  -H "Content-Type: application/json" \
  -d '{ "tool_names": ["database_tool"] }'
```

### 4) 에이전트 호출
```bash
curl -X POST http://localhost:8000/core/api/agents/demo_agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "공정 상태를 요약해줘",
    "max_tokens": 512,
    "temperature": 0.3,
    "use_tools": false
  }'
```

### 5) 툴 직접 실행
```bash
curl -X POST http://localhost:8000/core/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "database_tool",
    "parameters": { "action": "list_tables" }
  }'
```

## 데이터베이스 API 예시
```bash
curl http://localhost:8000/core/api/db/tables
curl http://localhost:8000/core/api/db/tables/SEMI_CVD_SENSORS/schema
curl -X POST http://localhost:8000/core/api/db/query \
  -H "Content-Type: application/json" \
  -d '{ "query": "SELECT * FROM SEMI_CVD_SENSORS LIMIT 5" }'
```

## Python 예제
```python
import requests

BASE = "http://localhost:8000/core/api"

def invoke_agent(agent: str, prompt: str):
    resp = requests.post(
        f"{BASE}/agents/{agent}/invoke",
        json={"prompt": prompt, "max_tokens": 512, "temperature": 0.3, "use_tools": False},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["text"]

def list_tables():
    return requests.get(f"{BASE}/db/tables", timeout=10).json()["tables"]

print("agent:", invoke_agent("demo_agent", "공정 상태를 한 줄로 요약"))
print("tables:", list_tables()[:5])
```

## Vector DB 사용 (옵션)
- 기본 라우터는 `main.py`에서 주석 처리되어 있습니다. 활성화 후 `/core/api/vector-db/*` 경로를 사용합니다.
- 활성화 예: `create_vector_db_router` 부분 주석 해제 후 재실행.

## 문제 해결
- 404/Not Found: 경로에 `/core/api` 접두사가 빠지지 않았는지 확인.
- 500/LLM 실패: vLLM 서비스 상태(`docker compose logs vllm`)와 `HUGGING_FACE_TOKEN`을 확인.
- DB 연결 오류: `docker compose logs db`, `DATABASE_URL` 값 확인.

