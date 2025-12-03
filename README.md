# PRISM Core

산업 제조 도메인을 위한 멀티 에이전트/툴 오케스트레이션 서버입니다. FastAPI 기반 단일 서비스에서 다음을 제공합니다.
- LLM/에이전트 호출 및 툴 레지스트리 (`/core/api/agents`, `/core/api/tools`)
- Postgres 산업 데이터베이스 조회 API (`/core/api/db`)
- vLLM(OpenAI 호환)와 연동되는 LLM 서비스 (`PrismLLMService`)
- (선택) Weaviate 기반 Vector DB 유틸

## 빠른 시작: Docker Compose
`docker-compose.yml`이 기본 실행 방법입니다.

### 사전 준비
- Docker 20.10+, Docker Compose 2.x
- 외부 네트워크가 필요합니다: `docker network create prism-shared-network` (없으면 compose가 실패)
- `.env` 파일 생성 (루트). 최소 예시는 아래와 같이 맞춰주세요.
  ```env
  HUGGING_FACE_TOKEN=your_token_here   # vLLM 이미지가 HF 토큰을 요구
  VLLM_MODEL=Qwen/Qwen3-14B
  VLLM_ARGS=--enable-auto-tool-choice --tool-call-parser hermes --dtype bf16
  # 필요 시 덮어쓸 항목
  # OPENAI_API_KEY=EMPTY
  # VLLM_HOST=0.0.0.0
  # VLLM_PORT=8001
  # SELF_URL=http://prism-core-llm_agent-1:8000  # 내부 호출용, 기본값은 main.py에서 지정
  ```

### 실행
```bash
docker compose up -d --build
# 포트: core API 8000, vLLM(OpenAI 호환) 8001, Postgres 5432
```

### 확인
- 헬스: `curl http://localhost:8000/` → `{"message":"Welcome to PRISM Core","version":"0.1.0"}`
- OpenAPI 문서: `http://localhost:8000/docs`
- DB 상태: `curl http://localhost:8000/core/api/db`

### 정지/정리
```bash
docker compose down        # 컨테이너 종료
docker compose down -v     # Postgres 데이터 볼륨까지 삭제
```

## 서비스 구성 (docker-compose)
| 서비스 | 역할 | 포트 | 비고 |
| --- | --- | --- | --- |
| llm_agent | FastAPI 앱 + 에이전트/툴/DB API, vLLM 클라이언트 | 8000 | 코드 볼륨 마운트, reload 지원 |
| vllm | OpenAI 호환 vLLM 서버 | 8001 | GPU 지원 이미지 사용 |
| db | Postgres 15 | 5432 | 볼륨 `postgres_data` 영구화 |

## 주요 API
- 에이전트/툴: `/core/api/agents`, `/core/api/tools`
- LLM 호출: `/core/api/generate`
- 에이전트 호출: `/core/api/agents/{agent_name}/invoke`
- DB: `/core/api/db`, `/core/api/db/tables`, `/core/api/db/tables/{table}/schema`, `/core/api/db/query`
- Vector DB(Weaviate 프록시): `/core/api/vector-db` (현재 기본 라우터는 주석 처리되어 있으며 필요 시 main.py에서 포함)

### 예제 요청
- 테이블 목록
  ```bash
  curl http://localhost:8000/core/api/db/tables
  ```
- 에이전트 등록
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
- 에이전트 호출
  ```bash
  curl -X POST http://localhost:8000/core/api/agents/demo_agent/invoke \
    -H "Content-Type: application/json" \
    -d '{"prompt": "공정 상태를 요약해줘"}'
  ```
- 툴 실행(등록된 툴 이름 필요)
  ```bash
  curl -X POST http://localhost:8000/core/api/tools/execute \
    -H "Content-Type: application/json" \
    -d '{"tool_name": "database_tool", "parameters": {"action": "list_tables"}}'
  ```

## 설정
`prism_core/core/config.py`의 기본값을 환경 변수로 덮어쓸 수 있습니다.
- 데이터베이스: `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- LLM/vLLM: `VLLM_MODEL`, `VLLM_ARGS`, `VLLM_OPENAI_BASE_URL`, `OPENAI_API_KEY`
- Hugging Face: `HUGGING_FACE_TOKEN`
- 내부 호출 베이스 URL: `SELF_URL` (main.py에서 PrismLLMService 초기화 시 사용)

## 데이터 및 스크립트
- 샘플 산업 데이터: `Industrial_DB_sample/*.csv`
- 초기화/검증 스크립트: `scripts/init_db.py`, `scripts/verify_db.py`
- 데모: `tool_demo.py`, `vector_db_demo.py`

## 개발 모드 (로컬 실행)
```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- 로컬 Postgres를 사용하려면 `DATABASE_URL`을 환경 변수로 지정하세요.
- Vector DB 라우터를 쓰려면 `main.py`의 `create_vector_db_router` 부분을 주석 해제합니다.

## 테스트
```bash
pytest -q
```
- 단위 예제: `tests/test_api.py`, `test_db.py`, `test_client.py`

## 참고 문서
- `client.md`: 클라이언트 연동 가이드
- `server.md`: 서버 설정 및 배포 가이드
- `PROJECT_STRUCTURE.md`: 디렉터리 구조 설명

