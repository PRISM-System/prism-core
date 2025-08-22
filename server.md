# PRISM-Core 서버 가이드

PRISM-Core 서버를 설정하고 운영하기 위한 간단한 가이드입니다.

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [설치 및 설정](#설치-및-설정)
3. [서비스 실행](#서비스-실행)
4. [환경 변수 설정](#환경-변수-설정)
5. [모니터링 및 로그](#모니터링-및-로그)
6. [문제 해결](#문제-해결)

## 🖥️ 시스템 요구사항

### 최소 요구사항
- **CPU**: 8코어 이상
- **RAM**: 16GB 이상
- **Storage**: 50GB 이상의 SSD
- **OS**: Ubuntu 20.04+, macOS 10.15+, Windows 10+

### 권장 요구사항
- **CPU**: 16코어 이상
- **RAM**: 32GB 이상
- **Storage**: 100GB 이상의 SSD
- **GPU**: NVIDIA GPU (LLM 추론 가속화용, 선택사항)

### 소프트웨어 요구사항
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **Git**: 2.30 이상

## 🔧 설치 및 설정

### 1. 저장소 클론

```bash
git clone https://github.com/PRISM-System/prism-core.git
cd prism-core
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
nano .env
```

### 3. Docker 이미지 빌드

```bash
# 전체 서비스 빌드
docker-compose build

# 특정 서비스만 빌드
docker-compose build llm_agent
docker-compose build db
```

## 🚀 서비스 실행

### 전체 서비스 시작

```bash
# 백그라운드 실행
docker-compose up -d

# 로그와 함께 실행
docker-compose up
```

### 개별 서비스 시작

```bash
# 데이터베이스만 시작
docker-compose up -d db

# Weaviate만 시작
docker-compose up -d weaviate

# vLLM만 시작
docker-compose up -d vllm

# LLM Agent만 시작
docker-compose up -d llm_agent
```

### 서비스 상태 확인

```bash
# 모든 서비스 상태
docker-compose ps

# 특정 서비스 로그
docker-compose logs llm_agent
docker-compose logs weaviate
docker-compose logs vllm
```

## ⚙️ 환경 변수 설정

### 필수 환경 변수

```env
# 데이터베이스 설정
DATABASE_URL=postgresql://myuser:mysecretpassword@localhost:5432/mydatabase

# Weaviate 설정
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=

# vLLM 설정
VLLM_MODEL=Qwen/Qwen3-0.6B
VLLM_HOST=0.0.0.0
VLLM_PORT=8001

# Hugging Face 토큰
HUGGING_FACE_TOKEN=your_token_here
```

### 선택적 환경 변수

```env
# 성능 설정
GPU_MEMORY_UTILIZATION=0.90
MAX_MODEL_LEN=4096
TENSOR_PARALLEL_SIZE=1

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/prism_core.log
```

## 📊 모니터링 및 로그

### 서비스 상태 확인

```bash
# 컨테이너 상태
docker-compose ps

# 리소스 사용량
docker stats

# 포트 사용 확인
netstat -tlnp | grep :800
```

### 로그 확인

```bash
# 실시간 로그
docker-compose logs -f llm_agent

# 특정 시간대 로그
docker-compose logs --since="2025-08-22T10:00:00" llm_agent

# 오류 로그만
docker-compose logs llm_agent | grep -i error
```

### 성능 모니터링

```bash
# GPU 사용량 (GPU 사용 시)
nvidia-smi

# 메모리 사용량
free -h

# 디스크 사용량
df -h
```

### API 헬스체크

```bash
# 메인 API 상태
curl http://localhost:8000/

# Vector DB 상태
curl http://localhost:8000/api/vector-db/status

# vLLM 상태
curl http://localhost:8001/v1/models

# Weaviate 상태
curl http://localhost:8080/v1/meta
```

## 🔍 문제 해결

### 일반적인 문제들

#### 1. 서비스 시작 실패

```bash
# 모든 컨테이너 중지 및 삭제
docker-compose down -v

# 이미지 재빌드
docker-compose build --no-cache

# 서비스 재시작
docker-compose up -d
```

#### 2. 메모리 부족 오류

```bash
# Docker 메모리 제한 확인
docker stats

# 시스템 메모리 확인
free -h

# 불필요한 컨테이너 정리
docker system prune -a
```

#### 3. 포트 충돌

```bash
# 포트 사용 확인
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8001
sudo netstat -tulpn | grep :8080

# 충돌하는 프로세스 종료
sudo kill -9 <PID>
```

#### 4. 데이터베이스 연결 실패

```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose logs db

# 데이터베이스 재시작
docker-compose restart db

# 연결 테스트
docker-compose exec db psql -U myuser -d mydatabase -c "SELECT 1;"
```

### 로그 분석

```bash
# 오류 로그 필터링
docker-compose logs llm_agent | grep -i error

# 특정 시간대 로그
docker-compose logs --since="1h" llm_agent

# API 호출 로그
docker-compose logs llm_agent | grep "POST\|GET"
```

## 🔧 개발 환경

### 로컬 개발 설정

```bash
# 개발용 환경 변수
cp .env.example .env.dev

# 개발 서비스 시작
docker-compose -f docker-compose.dev.yml up -d

# 로그 모니터링
docker-compose -f docker-compose.dev.yml logs -f
```

### 테스트 실행

```bash
# 전체 테스트
python -m pytest tests/ -v

# 특정 테스트
python -m pytest tests/test_vector_db.py -v

# 커버리지 테스트
python -m pytest tests/ --cov=core --cov-report=html
```

## 📚 데모 스크립트

### 기본 데모 실행

```bash
# Vector DB 데모
python vector_db_demo.py

# Tool 시스템 데모
python tool_demo.py

# 데이터베이스 연결 테스트
python test_db.py
```

### API 테스트

```bash
# API 문서 확인
open http://localhost:8000/docs

# Weaviate 콘솔 확인
open http://localhost:8080
```

---

**참고**: 더 자세한 정보는 [GitHub Issues](https://github.com/PRISM-System/prism-core/issues)를 참조하세요. 