# PRISM Core

PRISM Core는 산업용 데이터베이스와 LLM 기반 Multi-Agent 시스템을 활용한 지능형 제조 공정 분석 플랫폼의 핵심 구성요소입니다.

## 🎯 주요 기능

- **Multi-Agent 시스템**: 다양한 역할을 수행하는 AI 에이전트들의 협업
- **산업 DB 연동**: 반도체 제조 공정 데이터 분석 및 이상 탐지
- **LLM 서비스**: vLLM 기반 대규모 언어모델 추론 서비스
- **RESTful API**: FastAPI 기반 웹 API 제공
- **PostgreSQL 연동**: 산업 데이터 저장 및 관리

## 🏗️ 아키텍처

```
prism-core/
├── core/                    # 핵심 모듈
│   ├── agents/             # 에이전트 정의 및 관리
│   ├── llm/               # LLM 서비스 레이어
│   ├── data/              # 데이터 접근 레이어
│   ├── api.py             # API 라우터
│   ├── config.py          # 설정 관리
│   └── schemas.py         # 데이터 스키마
├── Industrial_DB_sample/   # 산업 DB 샘플 데이터
├── scripts/               # 유틸리티 스크립트
├── docker/               # Docker 설정
└── main.py              # 애플리케이션 진입점
```

## 🚀 빠른 시작

### 필요 조건

- Python 3.10+
- Docker & Docker Compose
- NVIDIA GPU (선택사항, LLM 추론 가속화용)
- PostgreSQL 15+

### 설치 및 실행

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

3. **Docker Compose로 실행**
```bash
docker-compose up -d
```

4. **로컬 개발 환경 설정** (선택사항)
```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는 .venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
# 또는 uv를 사용하는 경우
uv sync

# 개발 서버 실행
./run.sh
```

## ⚡ 빠른 시작

### 1. Docker Compose로 전체 시스템 실행
```bash
# 환경 변수 설정 (선택사항)
export HUGGING_FACE_TOKEN=your_token_here

# 서비스 시작
docker-compose up -d

# 상태 확인
docker-compose ps
```

### 2. API 테스트
```bash
# 서버 상태 확인
curl http://localhost:8000/

# 데이터베이스 테이블 목록 조회
curl http://localhost:8000/api/db/tables

# Agent 목록 조회
curl http://localhost:8000/api/agents

# Swagger UI에서 전체 API 확인
open http://localhost:8000/docs
```

## 📊 산업 DB 스키마

이 프로젝트는 반도체 제조 공정의 이상 탐지를 위한 다음과 같은 핵심 테이블들을 포함합니다:

- **SEMI_LOT_MANAGE**: 생산 LOT 관리
- **SEMI_PROCESS_HISTORY**: 공정별 이력 추적
- **SEMI_PARAM_MEASURE**: 공정 파라미터 측정 결과
- **SEMI_*_SENSORS**: 각종 센서 데이터 (CVD, Etch, CMP 등)

자세한 스키마 정보는 [`Industrial_DB_sample/제조공정db.md`](Industrial_DB_sample/제조공정db.md)를 참조하세요.

### 데이터베이스 테스트

**DB 연결 및 데이터 확인**:
```bash
# 가상환경 활성화 후 DB 테스트 실행
source .venv/bin/activate
python test_db.py

# 또는 Docker 환경에서 직접 DB 접근
docker-compose exec db psql -U myuser -d mydatabase -c "SELECT COUNT(*) FROM semi_lot_manage;"
```

## 🚀 서버 실행

### Docker Compose 실행
```bash
# 환경 변수 설정 (필요한 경우)
export HUGGING_FACE_TOKEN=your_token_here

# 서비스 시작
docker-compose up -d

# 실행 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f llm_agent
docker-compose logs -f db
```

### 서비스 구성
- **llm_agent**: LLM 및 Agent API 서버 (포트: 8000)
- **db**: PostgreSQL 데이터베이스 (포트: 5432)

## 🔧 API 사용법

서버가 실행되면 완전히 분리된 두 개의 API 모듈을 사용할 수 있습니다:

### 📋 API 엔드포인트 목록

#### 🤖 LLM & Agent API
- `GET /`: 서비스 상태 확인
- `GET /docs`: Swagger UI 문서
- `POST /api/agents`: 새 에이전트 등록
- `GET /api/agents`: 등록된 에이전트 목록 조회
- `DELETE /api/agents/{agent_name}`: 특정 에이전트 삭제
- `POST /api/agents/{agent_name}/invoke`: 특정 에이전트 실행
- `POST /api/generate`: 직접 텍스트 생성

#### 🗄️ Database API
- `GET /api/db/`: 데이터베이스 정보 및 통계
- `GET /api/db/tables`: 모든 테이블 목록 조회
- `GET /api/db/tables/{table_name}/schema`: 특정 테이블 스키마 조회
- `GET /api/db/tables/{table_name}/data`: 특정 테이블 데이터 조회 (페이징 지원)
- `POST /api/db/query`: 커스텀 SQL 쿼리 실행 (SELECT만 허용)
- `POST /api/db/tables/{table_name}/query`: 고급 테이블 쿼리 (필터링 지원)

### 예시 요청

**기본 API 테스트**:
```bash
# 서비스 상태 확인
curl -X GET "http://localhost:8000/"

# Swagger UI 문서 확인
curl -X GET "http://localhost:8000/docs"
```

**에이전트 관리**:
```bash
# 등록된 에이전트 목록 조회
curl -X GET "http://localhost:8000/api/agents"

# 새 에이전트 등록
curl -X POST "http://localhost:8000/api/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "manufacturing_analyst",
    "description": "제조 공정 데이터 분석 전문가",
    "role_prompt": "당신은 반도체 제조 공정의 이상 탐지 전문가입니다. 사용자의 질문에 대해 전문적이고 명확한 답변을 제공해주세요."
  }'

# 특정 에이전트 삭제
curl -X DELETE "http://localhost:8000/api/agents/manufacturing_analyst"
```

**LLM 텍스트 생성**:
```bash
# 직접 텍스트 생성
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "안녕하세요! 간단한 자기소개를 해주세요.",
    "max_tokens": 100,
    "temperature": 0.7
  }'

# 에이전트를 통한 전문가 답변 생성
curl -X POST "http://localhost:8000/api/agents/manufacturing_analyst/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "반도체 웨이퍼 수율이 갑자기 떨어졌습니다. 어떤 원인들을 확인해야 할까요?",
    "max_tokens": 200,
    "temperature": 0.3
  }'
```

**데이터베이스 API**:
```bash
# 데이터베이스 정보 확인
curl -X GET "http://localhost:8000/api/db/"

# 모든 테이블 목록 조회
curl -X GET "http://localhost:8000/api/db/tables"

# 특정 테이블 스키마 조회
curl -X GET "http://localhost:8000/api/db/tables/semi_lot_manage/schema"

# 테이블 데이터 조회 (기본 10개 행)
curl -X GET "http://localhost:8000/api/db/tables/semi_lot_manage/data"

# 페이징을 통한 테이블 데이터 조회
curl -X GET "http://localhost:8000/api/db/tables/semi_lot_manage/data?limit=5&offset=10"

# WHERE 조건을 포함한 테이블 데이터 조회
curl -X GET "http://localhost:8000/api/db/tables/semi_lot_manage/data?where_clause=lot_id='LOT001'&limit=20"

# 커스텀 SQL 쿼리 실행
curl -X POST "http://localhost:8000/api/db/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT COUNT(*) as total_lots FROM semi_lot_manage WHERE create_date >= NOW() - INTERVAL '\''1 day'\''"
  }'

# 고급 테이블 쿼리 (JSON 바디 사용)
curl -X POST "http://localhost:8000/api/db/tables/semi_lot_manage/query" \
  -H "Content-Type: application/json" \
  -d '{
    "table_name": "semi_lot_manage",
    "limit": 5,
    "where_clause": "lot_status = '\''ACTIVE'\''",
    "order_by": "create_date DESC"
  }'
```

## 🔍 시스템 상태 확인

**Docker 컨테이너 상태**:
```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 서비스 로그 확인
docker-compose logs llm_agent
docker-compose logs db

# 실시간 로그 모니터링
docker-compose logs -f llm_agent
```

**서비스 헬스 체크**:
```bash
# 서버 응답 확인
curl -X GET "http://localhost:8000/" | jq

# DB 연결 상태 확인
docker-compose exec db pg_isready -U myuser -d mydatabase
```

## 🛠️ 개발

### 📁 프로젝트 구조

```
core/
├── llm/                    # 🤖 LLM & Agent 모듈
│   ├── api.py             # LLM/Agent API 라우터
│   ├── agent_registry.py  # Agent 레지스트리 관리
│   ├── schemas.py         # LLM/Agent 관련 스키마
│   ├── base.py            # LLM 서비스 베이스 클래스
│   ├── vllm_service.py    # vLLM 구현체
│   └── __init__.py        # 모듈 export
├── data/                   # 🗄️ Database 모듈
│   ├── api.py             # Database API 라우터
│   ├── service.py         # DB 서비스 클래스
│   ├── schemas.py         # DB 관련 스키마
│   ├── base.py            # DB 서비스 베이스 클래스
│   ├── postgresql.py      # PostgreSQL 구현체
│   └── __init__.py        # 모듈 export
├── agents/                 # 🎯 Agent 구현체들
└── config.py              # ⚙️ 전역 설정
```

### ✨ 모듈 분리 특징
- **완전 분리**: LLM과 DB가 독립적인 API와 서비스를 가짐
- **명확한 책임**: 각 모듈이 고유한 역할과 엔드포인트를 담당
- **확장성**: 새로운 LLM 서비스나 DB 타입을 쉽게 추가 가능

### 🔧 개발 가이드

#### 새 에이전트 추가
1. `core/agents/` 디렉토리에 새 에이전트 클래스 생성
2. `BaseAgent`를 상속하여 구현
3. API를 통해 `AgentRegistry`에 등록

#### 새 DB 타입 추가
1. `core/data/` 디렉토리에 새 DB 구현체 생성
2. `BaseDataStore`를 상속하여 구현
3. `DatabaseService`에서 사용

#### API 확장
- **LLM API**: `core/llm/api.py`에서 라우터 확장
- **DB API**: `core/data/api.py`에서 라우터 확장

### 환경 변수

주요 환경 변수들:

- `HUGGING_FACE_TOKEN`: Hugging Face 모델 다운로드용 토큰
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `MODEL_NAME`: 사용할 LLM 모델명 (기본: meta-llama/Llama-3.2-1B)
- `GPU_MEMORY_UTILIZATION`: GPU 메모리 사용률 (기본: 0.90)

### 개발 도구 사용법

**개발 의존성 설치**:
```bash
# pip 사용
pip install -r requirements-dev.txt

# 또는 uv 사용
uv sync --dev

# 또는 pyproject.toml의 dev 의존성 사용
pip install -e ".[dev]"
```

**코드 포매팅**:
```bash
# 코드 포매팅
black .
isort .

# 린팅
flake8 .
mypy core/
```

**테스트 실행**:
```bash
# 전체 테스트 실행
pytest

# 커버리지와 함께 실행
pytest --cov=core --cov-report=html

# 특정 테스트 파일만 실행
pytest tests/test_api.py
```

## 🔧 문제 해결

**일반적인 문제들**:

1. **서버가 시작되지 않는 경우**:
```bash
# 컨테이너 재시작
docker-compose down
docker-compose build llm_agent
docker-compose up -d

# 로그 확인
docker-compose logs llm_agent
```

2. **DB 연결 실패**:
```bash
# DB 컨테이너 상태 확인
docker-compose ps db
docker-compose logs db

# DB 재시작
docker-compose restart db
```

3. **GPU 관련 문제**:
```bash
# NVIDIA 런타임 확인
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# Docker Compose에서 GPU 사용 확인
docker-compose logs llm_agent | grep -i cuda
```

4. **포트 충돌**:
```bash
# 포트 사용 현황 확인
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :5432

# 다른 포트로 변경하려면 docker-compose.yml 수정
```

---

**PRISM Core** - 지능형 제조 혁신을 위한 AI 플랫폼
