# PRISM-Core 서버 가이드

Docker Compose로 PRISM-Core를 구동하는 방법과 필수 설정을 정리했습니다. (현재 Compose 서비스: `llm_agent` FastAPI 앱, `vllm` OpenAI 호환 LLM 서버, `db` Postgres)

## 사전 준비
- Docker 20.10+, Docker Compose 2.x
- 네트워크: `docker network create prism-shared-network` (없으면 compose 실패)
- `.env`(루트) 작성: 최소 값
  ```env
  HUGGING_FACE_TOKEN=your_token_here
  VLLM_MODEL=Qwen/Qwen3-14B
  VLLM_ARGS=--enable-auto-tool-choice --tool-call-parser hermes --dtype bf16
  # 선택: OPENAI_API_KEY, VLLM_HOST, VLLM_PORT, SELF_URL 등
  ```

## 실행
```bash
docker compose up -d --build
# 포트: core API 8000, vLLM 8001, Postgres 5432
```

### 헬스 체크
- 루트: `curl http://localhost:8000/`
- Docs: `http://localhost:8000/docs`
- DB: `curl http://localhost:8000/core/api/db`

### 종료/정리
```bash
docker compose down        # 컨테이너만
docker compose down -v     # Postgres 볼륨까지
```

## 환경 변수(주요)
- DB: `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- LLM/vLLM: `VLLM_MODEL`, `VLLM_ARGS`, `VLLM_OPENAI_BASE_URL`, `OPENAI_API_KEY`
- HF 토큰: `HUGGING_FACE_TOKEN`
- 내부 호출 URL: `SELF_URL` (PrismLLMService가 자기 자신을 부를 때 사용)

## 로그/모니터링
```bash
docker compose ps
docker compose logs -f llm_agent
docker compose logs -f vllm
docker compose logs -f db
```
GPU 사용 시 `nvidia-smi`로 확인.

## 문제 해결 팁
- 포트 충돌: `lsof -i :8000` 등으로 확인 후 프로세스 종료
- DB 연결 불가: `docker compose logs db` → 필요 시 `docker compose restart db`
- 모델 다운로드 실패: `HUGGING_FACE_TOKEN` 재확인

## 개발 모드 (로컬)
```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- 로컬 Postgres 사용 시 `DATABASE_URL` 지정.
- Vector DB 라우터 사용하려면 `main.py`의 `create_vector_db_router` 부분을 주석 해제 후 환경 변수(WEAVIATE_*)를 맞춥니다.

## 관련 자료
- `README.md`: 전체 개요 및 API 예제
- `client.md`: 클라이언트 연동 가이드
- `PROJECT_STRUCTURE.md`: 디렉터리 구조

