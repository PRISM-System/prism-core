# PRISM-Core API 스키마 문서

PRISM-Core의 모든 API 엔드포인트와 데이터 스키마를 상세히 설명하는 문서입니다.

## 📋 목차

1. [기본 정보](#기본-정보)
2. [Vector Database API](#vector-database-api)
3. [LLM & Agent API](#llm--agent-api)
4. [Tools API](#tools-api)
5. [Database API](#database-api)
6. [공통 스키마](#공통-스키마)

## 🔧 기본 정보

### 서버 정보
- **Base URL**: `http://localhost:8000`
- **API 버전**: v0.1.0
- **문서**: `http://localhost:8000/docs`

### 인증
현재 버전에서는 인증이 필요하지 않습니다.

---

## 🧠 Vector Database API

Vector Database 관련 API 엔드포인트들입니다.

### Base Path
```
/api/vector-db
```

### 1. 상태 조회

#### `GET /api/vector-db/status`

Vector Database의 상태를 조회합니다.

**응답 스키마:**
```json
{
  "connected": true,
  "total_objects": 150,
  "classes": ["OrchResearch", "OrchHistory", "OrchCompliance"],
  "health": "healthy",
  "version": "1.25.8"
}
```

### 2. 인덱스 관리

#### `POST /api/vector-db/indices`

새로운 인덱스를 생성합니다.

**요청 스키마:**
```json
{
  "class_name": "Documents",
  "description": "문서 저장소",
  "vector_dimension": 384,
  "encoder_model": "sentence-transformers/all-MiniLM-L6-v2",
  "properties": [
    {
      "name": "content",
      "dataType": ["text"],
      "description": "Document content"
    },
    {
      "name": "title",
      "dataType": ["string"],
      "description": "Document title"
    }
  ],
  "vectorizer": "none",
  "distance_metric": "cosine"
}
```

**응답 스키마:**
```json
{
  "success": true,
  "message": "Index 'Documents' created successfully",
  "execution_time_ms": 1250.5
}
```

#### `DELETE /api/vector-db/indices/{class_name}`

인덱스를 삭제합니다.

**경로 매개변수:**
- `class_name` (string): 삭제할 클래스명

**응답 스키마:**
```json
{
  "success": true,
  "message": "Index 'Documents' deleted successfully",
  "execution_time_ms": 450.2
}
```

### 3. 문서 관리

#### `POST /api/vector-db/documents/{class_name}`

단일 문서를 추가합니다.

**경로 매개변수:**
- `class_name` (string): 문서를 추가할 클래스명

**쿼리 매개변수:**
- `client_id` (string, optional): 클라이언트 ID (기본값: "default")
- `encoder_model` (string, optional): 인코더 모델

**요청 스키마:**
```json
{
  "id": "doc_123",
  "content": "문서 내용입니다.",
  "title": "문서 제목",
  "metadata": {
    "source": "manual",
    "category": "guide"
  },
  "source": "internal",
  "created_at": "2025-08-22T10:00:00Z",
  "updated_at": "2025-08-22T10:00:00Z"
}
```

**응답 스키마:**
```json
{
  "success": true,
  "message": "Document added successfully",
  "data": {
    "document_id": "doc_123"
  },
  "execution_time_ms": 850.3
}
```

#### `POST /api/vector-db/documents/{class_name}/batch`

배치로 문서를 추가합니다.

**경로 매개변수:**
- `class_name` (string): 문서를 추가할 클래스명

**쿼리 매개변수:**
- `client_id` (string, optional): 클라이언트 ID (기본값: "default")
- `encoder_model` (string, optional): 인코더 모델

**요청 스키마:**
```json
[
  {
    "content": "첫 번째 문서 내용",
    "title": "첫 번째 문서",
    "metadata": {"source": "manual"}
  },
  {
    "content": "두 번째 문서 내용",
    "title": "두 번째 문서",
    "metadata": {"source": "manual"}
  }
]
```

**응답 스키마:**
```json
{
  "success": true,
  "message": "Added 2 out of 2 documents",
  "data": {
    "document_ids": ["doc_1", "doc_2"],
    "success_count": 2,
    "total_count": 2
  },
  "execution_time_ms": 1250.8
}
```

#### `GET /api/vector-db/documents/{class_name}`

클래스의 모든 문서를 조회합니다.

**경로 매개변수:**
- `class_name` (string): 조회할 클래스명

**쿼리 매개변수:**
- `client_id` (string, optional): 클라이언트 ID (기본값: "default")
- `limit` (integer, optional): 반환할 문서 수 (기본값: 100)
- `offset` (integer, optional): 오프셋 (기본값: 0)

**응답 스키마:**
```json
[
  {
    "id": "doc_1",
    "content": "문서 내용",
    "title": "문서 제목",
    "metadata": {"source": "manual"},
    "source": "internal",
    "created_at": "2025-08-22T10:00:00Z",
    "vectorWeights": [0.1, 0.2, 0.3, ...]
  }
]
```

#### `DELETE /api/vector-db/documents/{class_name}/{doc_id}`

단일 문서를 삭제합니다.

**경로 매개변수:**
- `class_name` (string): 클래스명
- `doc_id` (string): 삭제할 문서 ID

**쿼리 매개변수:**
- `client_id` (string, optional): 클라이언트 ID (기본값: "default")

**응답 스키마:**
```json
{
  "success": true,
  "message": "Document deleted successfully",
  "execution_time_ms": 320.1
}
```

#### `POST /api/vector-db/documents/{class_name}/delete-batch`

배치로 문서를 삭제합니다.

**경로 매개변수:**
- `class_name` (string): 클래스명

**쿼리 매개변수:**
- `client_id` (string, optional): 클라이언트 ID (기본값: "default")

**요청 스키마:**
```json
["doc_1", "doc_2", "doc_3"]
```

**응답 스키마:**
```json
{
  "success": true,
  "message": "Deleted 3 out of 3 documents",
  "data": {
    "success_count": 3,
    "total_count": 3,
    "results": [true, true, true]
  },
  "execution_time_ms": 650.4
}
```

### 4. 문서 검색

#### `POST /api/vector-db/search/{class_name}`

벡터 검색을 수행합니다.

**경로 매개변수:**
- `class_name` (string): 검색할 클래스명

**쿼리 매개변수:**
- `client_id` (string, optional): 클라이언트 ID (기본값: "default")
- `encoder_model` (string, optional): 인코더 모델

**요청 스키마:**
```json
{
  "query": "검색할 쿼리",
  "limit": 10,
  "threshold": 0.7,
  "filters": {
    "source": "manual"
  },
  "include_metadata": true,
  "include_vector": false
}
```

**응답 스키마:**
```json
[
  {
    "id": "doc_1",
    "content": "검색된 문서 내용",
    "title": "검색된 문서 제목",
    "score": 0.95,
    "metadata": {"source": "manual"},
    "source": "internal"
  }
]
```

### 5. 인코더 관리

#### `GET /api/vector-db/encoders/recommended`

추천 인코더 모델 목록을 조회합니다.

**응답 스키마:**
```json
[
  {
    "name": "sentence-transformers/all-MiniLM-L6-v2",
    "description": "Fast and accurate sentence embeddings",
    "dimension": 384,
    "languages": ["en", "ko"]
  },
  {
    "name": "BAAI/bge-m3",
    "description": "Multilingual embedding model",
    "dimension": 1024,
    "languages": ["en", "ko", "zh", "ja"]
  }
]
```

#### `POST /api/vector-db/encoders/test`

인코더 모델을 테스트합니다.

**요청 스키마:**
```json
{
  "model_path_or_id": "sentence-transformers/all-MiniLM-L6-v2",
  "test_texts": ["Hello world", "안녕하세요"]
}
```

**응답 스키마:**
```json
{
  "success": true,
  "message": "Encoder test completed",
  "data": {
    "model_info": {
      "name": "sentence-transformers/all-MiniLM-L6-v2",
      "dimension": 384
    },
    "embeddings_shape": [2, 384],
    "sample_embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
  },
  "execution_time_ms": 1250.3
}
```

---

## 🤖 LLM & Agent API

LLM 서비스와 AI 에이전트 관련 API 엔드포인트들입니다.

### Base Path
```
/api
```

### 1. 에이전트 관리

#### `POST /api/agents`

새로운 에이전트를 등록합니다.

**요청 스키마:**
```json
{
  "name": "analysis_agent",
  "description": "데이터 분석 전문 에이전트",
  "role_prompt": "당신은 제조 공정 데이터를 분석하는 전문가입니다. 주어진 데이터를 분석하여 인사이트를 제공하세요.",
  "tools": ["database_query", "vector_search"]
}
```

**응답 스키마:**
```json
{
  "name": "analysis_agent",
  "description": "데이터 분석 전문 에이전트",
  "role_prompt": "당신은 제조 공정 데이터를 분석하는 전문가입니다...",
  "tools": ["database_query", "vector_search"]
}
```

#### `GET /api/agents`

등록된 모든 에이전트 목록을 조회합니다.

**응답 스키마:**
```json
[
  {
    "name": "analysis_agent",
    "description": "데이터 분석 전문 에이전트",
    "role_prompt": "당신은 제조 공정 데이터를 분석하는 전문가입니다...",
    "tools": ["database_query", "vector_search"]
  },
  {
    "name": "monitoring_agent",
    "description": "시스템 모니터링 에이전트",
    "role_prompt": "당신은 시스템 상태를 모니터링하는 전문가입니다...",
    "tools": ["system_status", "alert_system"]
  }
]
```

#### `DELETE /api/agents/{agent_name}`

특정 에이전트를 삭제합니다.

**경로 매개변수:**
- `agent_name` (string): 삭제할 에이전트명

**응답 스키마:**
```json
{
  "message": "Agent 'analysis_agent' has been deleted successfully"
}
```

#### `POST /api/agents/{agent_name}/tools`

에이전트에 도구를 할당합니다.

**경로 매개변수:**
- `agent_name` (string): 에이전트명

**요청 스키마:**
```json
{
  "agent_name": "analysis_agent",
  "tool_names": ["database_query", "vector_search", "calculator"]
}
```

**응답 스키마:**
```json
{
  "message": "Tools ['database_query', 'vector_search', 'calculator'] assigned to agent 'analysis_agent'"
}
```

#### `POST /api/agents/{agent_name}/invoke`

특정 에이전트를 실행합니다.

**경로 매개변수:**
- `agent_name` (string): 실행할 에이전트명

**요청 스키마:**
```json
{
  "prompt": "A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야?",
  "max_tokens": 1000,
  "temperature": 0.3,
  "use_tools": true,
  "max_tool_calls": 3,
  "user_id": "engineer_kim"
}
```

**응답 스키마:**
```json
{
  "text": "A-1 라인 압력 이상 분석 결과...",
  "tools_used": ["database_query", "vector_search"],
  "tool_results": [
    {
      "tool": "database_query",
      "result": {
        "query": "SELECT * FROM pressure_sensors WHERE line='A-1'",
        "data": [...]
      }
    },
    {
      "tool": "vector_search",
      "result": {
        "documents": [...]
      }
    }
  ],
  "metadata": {
    "compliance_checked": true,
    "execution_time": 2.5
  }
}
```

### 2. 텍스트 생성

#### `POST /api/generate`

LLM을 사용하여 텍스트를 생성합니다.

**요청 스키마:**
```json
{
  "prompt": "반도체 제조 공정에 대해 설명해주세요.",
  "max_tokens": 500,
  "temperature": 0.7,
  "stop": ["\n\n", "###"],
  "client_id": "user_123",
  "use_tools": false,
  "max_tool_calls": 3
}
```

**응답 스키마:**
```json
{
  "text": "반도체 제조 공정은 웨이퍼 준비부터 패키징까지..."
}
```

---

## 🔧 Tools API

도구(Tool) 시스템 관련 API 엔드포인트들입니다.

### Base Path
```
/api/tools
```

### 1. 도구 관리

#### `GET /api/tools`

등록된 모든 도구 목록을 조회합니다.

**응답 스키마:**
```json
[
  {
    "name": "database_query",
    "description": "데이터베이스 쿼리 실행",
    "parameters_schema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "SQL 쿼리"
        }
      },
      "required": ["query"]
    }
  },
  {
    "name": "vector_search",
    "description": "벡터 검색 수행",
    "parameters_schema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "검색 쿼리"
        },
        "limit": {
          "type": "integer",
          "description": "반환할 결과 수"
        }
      },
      "required": ["query"]
    }
  }
]
```

#### `POST /api/tools/register`

새로운 도구를 등록합니다.

**요청 스키마:**
```json
{
  "name": "custom_calculator",
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
  "tool_type": "calculation"
}
```

**응답 스키마:**
```json
{
  "success": true,
  "message": "Tool 'custom_calculator' registered successfully"
}
```

#### `GET /api/tools/{tool_name}`

특정 도구의 정보를 조회합니다.

**경로 매개변수:**
- `tool_name` (string): 도구명

**응답 스키마:**
```json
{
  "name": "database_query",
  "description": "데이터베이스 쿼리 실행",
  "parameters_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "SQL 쿼리"
      }
    },
    "required": ["query"]
  }
}
```

#### `DELETE /api/tools/{tool_name}`

특정 도구를 삭제합니다.

**경로 매개변수:**
- `tool_name` (string): 삭제할 도구명

**응답 스키마:**
```json
{
  "success": true,
  "message": "Tool 'custom_calculator' deleted successfully"
}
```

#### `PUT /api/tools/{tool_name}/config`

도구 설정을 업데이트합니다.

**경로 매개변수:**
- `tool_name` (string): 도구명

**요청 스키마:**
```json
{
  "description": "업데이트된 도구 설명",
  "parameters_schema": {
    "type": "object",
    "properties": {
      "expression": {
        "type": "string",
        "description": "계산할 수학 표현식"
      },
      "precision": {
        "type": "integer",
        "description": "소수점 자릿수"
      }
    },
    "required": ["expression"]
  }
}
```

**응답 스키마:**
```json
{
  "success": true,
  "message": "Tool configuration updated successfully"
}
```

#### `POST /api/tools/execute`

도구를 직접 실행합니다.

**요청 스키마:**
```json
{
  "tool_name": "database_query",
  "parameters": {
    "query": "SELECT * FROM pressure_sensors LIMIT 10"
  }
}
```

**응답 스키마:**
```json
{
  "success": true,
  "result": {
    "rows": [
      {"id": 1, "line": "A-1", "pressure": 2.5},
      {"id": 2, "line": "A-1", "pressure": 2.3}
    ],
    "count": 2
  },
  "message": "Query executed successfully",
  "execution_time_ms": 150.2
}
```

---

## 🗄️ Database API

데이터베이스 관련 API 엔드포인트들입니다.

### Base Path
```
/api/db
```

### 1. 데이터베이스 정보

#### `GET /api/db/`

데이터베이스 정보 및 통계를 조회합니다.

**응답 스키마:**
```json
{
  "database_name": "mydatabase",
  "total_tables": 15,
  "total_records": 125000,
  "connection_status": "connected",
  "version": "PostgreSQL 15.0"
}
```

#### `GET /api/db/tables`

모든 테이블 목록을 조회합니다.

**응답 스키마:**
```json
[
  {
    "table_name": "pressure_sensors",
    "record_count": 5000,
    "columns": ["id", "line", "pressure", "timestamp"]
  },
  {
    "table_name": "temperature_sensors",
    "record_count": 5000,
    "columns": ["id", "line", "temperature", "timestamp"]
  }
]
```

#### `GET /api/db/tables/{table_name}/schema`

특정 테이블의 스키마를 조회합니다.

**경로 매개변수:**
- `table_name` (string): 테이블명

**응답 스키마:**
```json
{
  "table_name": "pressure_sensors",
  "columns": [
    {
      "name": "id",
      "type": "integer",
      "nullable": false,
      "primary_key": true
    },
    {
      "name": "line",
      "type": "varchar(50)",
      "nullable": false
    },
    {
      "name": "pressure",
      "type": "numeric(5,2)",
      "nullable": true
    },
    {
      "name": "timestamp",
      "type": "timestamp",
      "nullable": false
    }
  ]
}
```

#### `GET /api/db/tables/{table_name}/data`

특정 테이블의 데이터를 조회합니다.

**경로 매개변수:**
- `table_name` (string): 테이블명

**쿼리 매개변수:**
- `limit` (integer, optional): 반환할 행 수 (기본값: 100)
- `offset` (integer, optional): 오프셋 (기본값: 0)
- `order_by` (string, optional): 정렬 기준 컬럼
- `order_direction` (string, optional): 정렬 방향 (ASC/DESC)

**응답 스키마:**
```json
{
  "table_name": "pressure_sensors",
  "data": [
    {
      "id": 1,
      "line": "A-1",
      "pressure": 2.5,
      "timestamp": "2025-08-22T10:00:00Z"
    },
    {
      "id": 2,
      "line": "A-1",
      "pressure": 2.3,
      "timestamp": "2025-08-22T10:01:00Z"
    }
  ],
  "total_count": 5000,
  "limit": 100,
  "offset": 0
}
```

### 2. 쿼리 실행

#### `POST /api/db/query`

커스텀 SQL 쿼리를 실행합니다.

**요청 스키마:**
```json
{
  "query": "SELECT line, AVG(pressure) as avg_pressure FROM pressure_sensors GROUP BY line",
  "parameters": {},
  "timeout": 30
}
```

**응답 스키마:**
```json
{
  "success": true,
  "data": [
    {
      "line": "A-1",
      "avg_pressure": 2.45
    },
    {
      "line": "A-2",
      "avg_pressure": 2.52
    }
  ],
  "execution_time_ms": 125.3,
  "row_count": 2
}
```

#### `POST /api/db/tables/{table_name}/query`

고급 테이블 쿼리를 실행합니다.

**경로 매개변수:**
- `table_name` (string): 테이블명

**요청 스키마:**
```json
{
  "select": ["line", "pressure"],
  "where": {
    "line": "A-1",
    "pressure": {
      "operator": ">",
      "value": 2.0
    }
  },
  "order_by": "timestamp",
  "order_direction": "DESC",
  "limit": 50,
  "offset": 0
}
```

**응답 스키마:**
```json
{
  "success": true,
  "data": [
    {
      "line": "A-1",
      "pressure": 2.5
    },
    {
      "line": "A-1",
      "pressure": 2.3
    }
  ],
  "total_count": 1250,
  "execution_time_ms": 85.2
}
```

---

## 📊 공통 스키마

모든 API에서 공통으로 사용되는 스키마들입니다.

### APIResponse

모든 API 응답의 기본 구조입니다.

```json
{
  "success": true,
  "message": "작업이 성공적으로 완료되었습니다.",
  "data": {},
  "error": null,
  "execution_time_ms": 1250.5
}
```

**필드 설명:**
- `success` (boolean): 작업 성공 여부
- `message` (string): 응답 메시지
- `data` (any): 응답 데이터 (선택사항)
- `error` (string): 오류 메시지 (실패 시)
- `execution_time_ms` (float): 실행 시간 (밀리초)

### DocumentSchema

Vector Database에 저장되는 문서의 기본 구조입니다.

```json
{
  "id": "doc_123",
  "content": "문서 내용",
  "title": "문서 제목",
  "metadata": {
    "source": "manual",
    "category": "guide"
  },
  "source": "internal",
  "created_at": "2025-08-22T10:00:00Z",
  "updated_at": "2025-08-22T10:00:00Z",
  "vector": [0.1, 0.2, 0.3, ...]
}
```

### SearchQuery

검색 쿼리의 기본 구조입니다.

```json
{
  "query": "검색할 쿼리",
  "limit": 10,
  "threshold": 0.7,
  "filters": {
    "source": "manual"
  },
  "include_metadata": true,
  "include_vector": false
}
```

### SearchResult

검색 결과의 기본 구조입니다.

```json
{
  "id": "doc_123",
  "content": "검색된 문서 내용",
  "title": "검색된 문서 제목",
  "score": 0.95,
  "metadata": {
    "source": "manual"
  },
  "source": "internal",
  "vector": [0.1, 0.2, 0.3, ...]
}
```

### ToolRequest

도구 실행 요청의 기본 구조입니다.

```json
{
  "tool_name": "database_query",
  "parameters": {
    "query": "SELECT * FROM sensors LIMIT 10"
  }
}
```

### ToolResponse

도구 실행 응답의 기본 구조입니다.

```json
{
  "success": true,
  "result": {
    "rows": [...],
    "count": 10
  },
  "message": "Query executed successfully",
  "error_message": null,
  "execution_time_ms": 150.2
}
```

### AgentInvokeRequest

에이전트 실행 요청의 기본 구조입니다.

```json
{
  "prompt": "사용자 질의",
  "max_tokens": 1000,
  "temperature": 0.7,
  "stop": ["\n\n"],
  "use_tools": true,
  "max_tool_calls": 3,
  "extra_body": {},
  "user_id": "user_123"
}
```

### AgentResponse

에이전트 실행 응답의 기본 구조입니다.

```json
{
  "text": "에이전트 응답",
  "tools_used": ["database_query", "vector_search"],
  "tool_results": [
    {
      "tool": "database_query",
      "result": {...}
    }
  ],
  "metadata": {
    "compliance_checked": true,
    "execution_time": 2.5
  }
}
```

---

## 🔍 오류 코드

### HTTP 상태 코드

- `200 OK`: 요청 성공
- `400 Bad Request`: 잘못된 요청
- `404 Not Found`: 리소스를 찾을 수 없음
- `422 Unprocessable Entity`: 요청 데이터 검증 실패
- `500 Internal Server Error`: 서버 내부 오류

### 오류 응답 예시

```json
{
  "success": false,
  "message": "Failed to create index",
  "error": "Class 'Documents' already exists",
  "execution_time_ms": 1250.5
}
```

---

## 📚 사용 예시

### Python 클라이언트 예시

```python
import requests

# Vector DB 검색
response = requests.post(
    "http://localhost:8000/api/vector-db/search/Documents",
    json={
        "query": "압력 이상",
        "limit": 5
    }
)
results = response.json()

# 에이전트 실행
response = requests.post(
    "http://localhost:8000/api/agents/analysis_agent/invoke",
    json={
        "prompt": "A-1 라인 압력에 이상이 생긴 것 같은데, 원인이 뭐야?",
        "max_tokens": 1000,
        "temperature": 0.3
    }
)
result = response.json()

# 도구 실행
response = requests.post(
    "http://localhost:8000/api/tools/execute",
    json={
        "tool_name": "database_query",
        "parameters": {
            "query": "SELECT * FROM pressure_sensors WHERE line='A-1'"
        }
    }
)
tool_result = response.json()
```

### cURL 예시

```bash
# Vector DB 상태 조회
curl -X GET "http://localhost:8000/api/vector-db/status"

# 문서 검색
curl -X POST "http://localhost:8000/api/vector-db/search/Documents" \
  -H "Content-Type: application/json" \
  -d '{"query": "압력 이상", "limit": 5}'

# 에이전트 등록
curl -X POST "http://localhost:8000/api/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_agent",
    "description": "테스트 에이전트",
    "role_prompt": "당신은 테스트 에이전트입니다.",
    "tools": []
  }'
```

---

**참고**: 더 자세한 정보는 [PRISM-Core GitHub](https://github.com/PRISM-System/prism-core)를 참조하세요. 