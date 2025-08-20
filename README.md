# PRISM Core Server

PRISM Core Server는 산업용 데이터베이스와 LLM 기반 Multi-Agent 시스템을 활용한 지능형 제조 공정 분석 플랫폼의 **서버 구성요소**입니다.

## 🎯 주요 기능

- **Multi-Agent 시스템**: 다양한 역할을 수행하는 AI 에이전트들의 협업
- **🔧 Tool 시스템**: Agent가 자동으로 사용할 수 있는 도구 등록 및 관리
- **🧠 Vector DB Utils**: RAG 구현을 위한 Weaviate 기반 벡터 데이터베이스 유틸리티
- **산업 DB 연동**: 반도체 제조 공정 데이터 분석 및 이상 탐지
- **LLM 서비스**: vLLM 기반 대규모 언어모델 추론 서비스
- **RESTful API**: FastAPI 기반 웹 API 제공
- **PostgreSQL 연동**: 산업 데이터 저장 및 관리

## 🏗️ 서버 아키텍처

```
prism-core/
├── core/                    # 핵심 모듈
│   ├── agents/             # 에이전트 정의 및 관리
│   ├── tools/              # 🔧 Tool 시스템
│   │   ├── base.py        # Tool 베이스 클래스
│   │   ├── registry.py    # Tool 등록 관리
│   │   ├── database_tool.py  # Database 접근 Tool
│   │   ├── dynamic_tool.py   # 동적 Tool 구현
│   │   └── schemas.py     # Tool 관련 스키마
│   ├── vector_db/         # 🧠 Vector DB Utils
│   │   ├── client.py      # Weaviate 클라이언트
│   │   ├── encoder.py     # 텍스트 인코더 관리
│   │   ├── api.py         # Vector DB API
│   │   └── schemas.py     # Vector DB 스키마
│   ├── llm/               # LLM 서비스 레이어
│   ├── data/              # 데이터 접근 레이어
│   ├── api.py             # API 라우터
│   ├── config.py          # 설정 관리
│   └── schemas.py         # 데이터 스키마
├── Industrial_DB_sample/   # 산업 DB 샘플 데이터
├── scripts/               # 유틸리티 스크립트
├── docker/               # Docker 설정
├── tool_demo.py          # Tool 시스템 데모 스크립트
├── vector_db_demo.py     # Vector DB Utils 데모 스크립트
└── main.py              # 서버 애플리케이션 진입점
```

## 🚀 서버 설치 및 실행

### 필요 조건

- Python 3.10+
- Docker & Docker Compose
- NVIDIA GPU (선택사항, LLM 추론 가속화용)
- PostgreSQL 15+

### Docker Compose로 서버 실행

1. **저장소 클론**
```bash
git clone <repository-url>
cd prism-core
```

2. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 설정값들을 입력
```

3. **서비스 시작**
```bash
docker-compose up -d
```

4. **서버 상태 확인**
```bash
# 컨테이너 상태 확인
docker-compose ps

# API 서버 응답 확인
curl http://localhost:8000/

# Swagger UI 문서 확인
open http://localhost:8000/docs
```

### 로컬 개발 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는 .venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
./run.sh
```

## 📋 Server API 엔드포인트

### 🤖 LLM & Agent API
- `GET /`: 서비스 상태 확인
- `GET /docs`: Swagger UI 문서
- `POST /api/agents`: 새 에이전트 등록
- `GET /api/agents`: 등록된 에이전트 목록 조회
- `DELETE /api/agents/{agent_name}`: 특정 에이전트 삭제
- `POST /api/agents/{agent_name}/tools`: 에이전트에 Tool 할당
- `POST /api/agents/{agent_name}/invoke`: 특정 에이전트 실행
- `POST /api/generate`: 직접 텍스트 생성

### 🔧 Tool Management API
- `GET /api/tools`: 등록된 Tool 목록 조회
- `POST /api/tools/register`: 새로운 Tool 등록 (Client 요청)
- `POST /api/tools/register-with-code`: 사용자 정의 함수 Tool 등록
- `GET /api/tools/{tool_name}`: 특정 Tool 정보 상세 조회
- `DELETE /api/tools/{tool_name}`: Tool 삭제
- `PUT /api/tools/{tool_name}/config`: Tool 설정 업데이트
- `POST /api/tools/execute`: Tool 직접 실행

### 🧠 Vector DB API
- `GET /vector-db/status`: Vector DB 상태 조회
- `POST /vector-db/indices`: 인덱스 생성
- `DELETE /vector-db/indices/{class_name}`: 인덱스 삭제
- `POST /vector-db/documents/{class_name}`: 문서 추가
- `POST /vector-db/documents/{class_name}/batch`: 배치 문서 추가
- `POST /vector-db/search/{class_name}`: 문서 검색
- `DELETE /vector-db/documents/{class_name}/{doc_id}`: 문서 삭제
- `GET /vector-db/encoders/recommended`: 추천 인코더 목록

### 🗄️ Database API
- `GET /api/db/`: 데이터베이스 정보 및 통계
- `GET /api/db/tables`: 모든 테이블 목록 조회
- `GET /api/db/tables/{table_name}/schema`: 특정 테이블 스키마 조회
- `GET /api/db/tables/{table_name}/data`: 특정 테이블 데이터 조회
- `POST /api/db/query`: 커스텀 SQL 쿼리 실행
- `POST /api/db/tables/{table_name}/query`: 고급 테이블 쿼리

## 🔧 Tool 시스템

서버는 다양한 타입의 Tool을 지원하며, Client의 요청에 따라 동적으로 Tool을 등록하고 관리합니다.

### 지원하는 Tool 타입

1. **Database Tool**: 산업 데이터베이스 접근 (기본 제공)
2. **API Tool**: 외부 API 호출 (Client 등록)
3. **Calculation Tool**: 안전한 수학 계산 (Client 등록)
4. **Custom Tool**: 사용자 정의 로직 (Client 등록)

### Tool 등록 예시 (Server 관점)

```python
# 서버에서 Tool Registry 초기화
from core.tools import ToolRegistry, DatabaseTool

tool_registry = ToolRegistry()
tool_registry.register_tool(DatabaseTool(database_service))

# Client 요청으로 동적 Tool 등록 처리
@app.post("/api/tools/register")
async def register_tool(request: ToolRegistrationRequest):
    tool = DynamicTool(
        name=request.name,
        description=request.description,
        parameters_schema=request.parameters_schema,
        tool_type=request.tool_type,
        config=request.config
    )
    tool_registry.register_tool(tool)
```

## 🧠 Vector DB Utils

서버는 RAG 구현을 위한 완전한 Vector Database 솔루션을 제공합니다.

### 주요 구성 요소

- **WeaviateClient**: Weaviate Vector DB 관리
- **EncoderManager**: 다양한 임베딩 모델 지원
- **VectorDBAPI**: REST API 인터페이스
- **스키마 관리**: 문서, 검색, 인덱스 스키마

### 지원하는 인코더 모델

- **multilingual-e5-base**: 다국어 지원 (768차원)
- **bge-m3**: 고성능 다국어 (1024차원)
- **korean-sentence-transformers**: 한국어 특화 (768차원)
- **OpenAI ada-002**: OpenAI API (1536차원)

## 📊 산업 DB 스키마

반도체 제조 공정의 이상 탐지를 위한 핵심 테이블들:

- **SEMI_LOT_MANAGE**: 생산 LOT 관리
- **SEMI_PROCESS_HISTORY**: 공정별 이력 추적
- **SEMI_PARAM_MEASURE**: 공정 파라미터 측정 결과
- **SEMI_*_SENSORS**: 각종 센서 데이터 (CVD, Etch, CMP 등)

자세한 스키마 정보는 [`Industrial_DB_sample/제조공정db.md`](Industrial_DB_sample/제조공정db.md)를 참조하세요.

## 🛠️ 서버 개발

### 환경 변수

- `HUGGING_FACE_TOKEN`: Hugging Face 모델 다운로드용 토큰
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `MODEL_NAME`: 사용할 LLM 모델명 (기본: meta-llama/Llama-3.2-1B)
- `GPU_MEMORY_UTILIZATION`: GPU 메모리 사용률 (기본: 0.90)

### 새 Tool 추가 (서버 개발자용)

1. `core/tools/` 디렉토리에 새 Tool 클래스 생성
2. `BaseTool`을 상속하여 구현
3. `main.py`에서 `ToolRegistry`에 등록

```python
from core.tools import BaseTool, ToolRequest, ToolResponse

class WeatherTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="weather_tool",
            description="Get current weather information",
            parameters_schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        )
    
    async def execute(self, request: ToolRequest) -> ToolResponse:
        # Tool 구현 로직
        pass
```

## 🔍 서버 모니터링

### 상태 확인

```bash
# 서비스 상태
docker-compose ps

# 로그 확인
docker-compose logs llm_agent
docker-compose logs db

# API 헬스 체크
curl http://localhost:8000/ | jq
curl http://localhost:8000/api/db/ | jq
```

### 성능 모니터링

```bash
# GPU 사용률 확인
docker-compose exec llm_agent nvidia-smi

# 메모리 사용량 확인
docker stats

# API 응답 시간 테스트
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/agents
```

## 🔧 문제 해결

### 일반적인 문제들

1. **서버 시작 실패**:
```bash
docker-compose down
docker-compose build --no-cache llm_agent
docker-compose up -d
```

2. **DB 연결 실패**:
```bash
docker-compose restart db
docker-compose logs db
```

3. **GPU 인식 실패**:
```bash
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

4. **포트 충돌**:
```bash
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :5432
```

## 📚 데모 스크립트

서버 기능을 테스트하기 위한 데모 스크립트들:

```bash
# Tool 시스템 데모
python tool_demo.py

# Vector DB Utils 데모
python vector_db_demo.py

# 데이터베이스 연결 테스트
python test_db.py
```

---

## 📖 Client 개발 가이드

Client 애플리케이션 개발에 대한 자세한 내용은 [`CLIENT.md`](CLIENT.md)를 참조하세요.

**주요 Client 기능:**
- Tool 등록 및 관리
- Agent와의 상호작용
- Vector DB 활용
- RAG 구현

---

**PRISM Core Server** - 지능형 제조 혁신을 위한 AI 플랫폼의 강력한 서버 엔진 🚀
