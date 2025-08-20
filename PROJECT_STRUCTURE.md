# PRISM Core Project Structure Guide

이 문서는 PRISM Core 프로젝트의 현재 구조와 향후 분리 계획을 설명합니다.

## 🏗️ 현재 구조 (Monorepo)

```
prism-core/
├── README.md              # 서버 중심 README
├── CLIENT.md              # 클라이언트 개발 가이드
├── PROJECT_STRUCTURE.md   # 이 문서
├── 
├── core/                  # 🔧 Server Core Components
│   ├── llm/              # LLM & Agent 서비스
│   ├── tools/            # Tool 시스템
│   ├── vector_db/        # Vector DB Utils
│   ├── data/             # Database 접근 레이어
│   ├── agents/           # Agent 구현체
│   ├── api.py            # API 라우터
│   ├── config.py         # 서버 설정
│   └── schemas.py        # 데이터 스키마
│
├── Industrial_DB_sample/  # 샘플 데이터
├── scripts/              # 유틸리티 스크립트
├── docker/               # Docker 설정
├── tool_demo.py          # Tool 시스템 데모
├── vector_db_demo.py     # Vector DB 데모
├── main.py               # 서버 진입점
├── requirements.txt      # 서버 의존성
└── docker-compose.yml    # 서버 배포 설정
```

## 🎯 향후 분리 계획

### Option 1: 별도 레포지토리 분리

```
# Server Repository
prism-core-server/
├── README.md             # 서버 전용 README
├── core/                 # 서버 핵심 모듈
├── Industrial_DB_sample/
├── scripts/
├── docker/
├── main.py
├── requirements.txt
└── docker-compose.yml

# Client Repository  
prism-core-client/
├── README.md             # 클라이언트 전용 README
├── src/
│   ├── services/         # Server API 통신
│   ├── tools/           # Client Tool 정의
│   ├── workflows/       # 워크플로우
│   ├── config/          # 설정 관리
│   └── utils/           # 유틸리티
├── examples/            # 사용 예제
├── tests/              # 테스트
├── requirements.txt    # Client 의존성
└── docker-compose.yml  # Client 배포 설정
```

### Option 2: 하위 디렉토리 분리 (권장)

```
prism-core/
├── README.md                    # 전체 프로젝트 개요
├── PROJECT_STRUCTURE.md         # 이 문서
├── 
├── server/                      # 🔧 Server Components
│   ├── README.md               # 서버 README
│   ├── core/
│   │   ├── llm/
│   │   ├── tools/
│   │   ├── vector_db/
│   │   ├── data/
│   │   └── ...
│   ├── Industrial_DB_sample/
│   ├── scripts/
│   ├── docker/
│   ├── main.py
│   ├── requirements.txt
│   └── docker-compose.yml
│
├── client/                      # 🎯 Client Components
│   ├── README.md               # 클라이언트 README  
│   ├── src/
│   │   ├── services/
│   │   ├── tools/
│   │   ├── workflows/
│   │   ├── config/
│   │   └── utils/
│   ├── examples/
│   ├── tests/
│   ├── requirements.txt
│   └── docker-compose.yml
│
├── shared/                      # 🔗 Shared Components
│   ├── schemas/                # 공통 스키마
│   ├── types/                  # 타입 정의
│   └── utils/                  # 공통 유틸리티
│
└── docs/                       # 📚 Documentation
    ├── api/                    # API 문서
    ├── guides/                 # 가이드
    └── examples/               # 예제 모음
```

## 🚀 마이그레이션 계획

### Phase 1: 디렉토리 구조 분리
```bash
# 현재 구조에서 하위 디렉토리 분리로 이동

# 1. 서버 디렉토리 생성 및 이동
mkdir server
mv core/ server/
mv Industrial_DB_sample/ server/
mv scripts/ server/
mv docker/ server/
mv main.py server/
mv requirements.txt server/
mv docker-compose.yml server/
cp README.md server/README.md

# 2. 클라이언트 디렉토리 생성
mkdir client
# CLIENT.md 내용을 기반으로 클라이언트 구조 생성

# 3. 공통 디렉토리 생성
mkdir shared
mkdir docs
```

### Phase 2: 독립적인 배포 설정

**Server 배포 (server/docker-compose.yml)**
```yaml
version: '3.8'

services:
  prism-server:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://myuser:mypass@db:5432/mydatabase
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=myuser
      - POSTGRES_PASSWORD=mypass
      - POSTGRES_DB=mydatabase
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./Industrial_DB_sample:/docker-entrypoint-initdb.d

volumes:
  postgres_data:
```

**Client 배포 (client/docker-compose.yml)**
```yaml
version: '3.8'

services:
  manufacturing-client:
    build: .
    environment:
      - PRISM_SERVER_URL=http://prism-server:8000
      - WEAVIATE_URL=http://weaviate:8080
    depends_on:
      - prism-server
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs

  prism-server:
    image: prism-core-server:latest
    ports:
      - "8000:8000"

  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      - QUERY_DEFAULTS_LIMIT=25
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
```

### Phase 3: CI/CD 분리

**Server CI/CD (.github/workflows/server.yml)**
```yaml
name: Server CI/CD

on:
  push:
    paths:
      - 'server/**'
  pull_request:
    paths:
      - 'server/**'

jobs:
  test-server:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./server
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: pytest tests/
    
    - name: Build Docker image
      run: docker build -t prism-core-server .
```

**Client CI/CD (.github/workflows/client.yml)**
```yaml
name: Client CI/CD

on:
  push:
    paths:
      - 'client/**'
  pull_request:
    paths:
      - 'client/**'

jobs:
  test-client:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./client
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: pytest tests/
    
    - name: Build Docker image
      run: docker build -t prism-core-client .
```

## 📋 마이그레이션 체크리스트

### ✅ 준비 단계
- [ ] 현재 코드 백업
- [ ] 의존성 분석 완료
- [ ] 공통 컴포넌트 식별
- [ ] 마이그레이션 스크립트 준비

### ✅ 구조 분리
- [ ] server/ 디렉토리 생성 및 이동
- [ ] client/ 디렉토리 생성
- [ ] shared/ 디렉토리 생성
- [ ] docs/ 디렉토리 생성

### ✅ 설정 분리
- [ ] 서버 전용 requirements.txt
- [ ] 클라이언트 전용 requirements.txt  
- [ ] 독립적인 Docker 설정
- [ ] 환경 변수 분리

### ✅ 문서 업데이트
- [ ] 서버 README 작성
- [ ] 클라이언트 README 작성
- [ ] API 문서 분리
- [ ] 설치/배포 가이드 업데이트

### ✅ 테스트 및 검증
- [ ] 서버 독립 실행 테스트
- [ ] 클라이언트 독립 실행 테스트
- [ ] 통합 테스트 수행
- [ ] 성능 테스트

## 🔄 개발 워크플로우

### 분리 후 개발 흐름

1. **Server 개발자**
   ```bash
   cd server/
   # 서버 개발 작업
   python main.py
   ```

2. **Client 개발자**
   ```bash
   cd client/
   # 클라이언트 개발 작업
   python examples/manufacturing_client.py
   ```

3. **통합 테스트**
   ```bash
   # 루트에서 전체 시스템 테스트
   docker-compose -f server/docker-compose.yml up -d
   docker-compose -f client/docker-compose.yml up
   ```

## 📚 분리 후 장점

### 🎯 개발 효율성
- **명확한 책임 분리**: Server/Client 개발자 역할 구분
- **독립적인 배포**: 각각 독립적으로 배포 가능
- **선택적 사용**: Client만 필요한 경우 Server 없이도 개발 가능

### 🔧 유지보수성
- **의존성 분리**: Server/Client 각각의 의존성 관리
- **버전 관리**: 독립적인 버전 관리 가능
- **테스트 분리**: 각각 독립적인 테스트 수행

### 🚀 확장성
- **다양한 Client**: 여러 종류의 Client 개발 가능
- **Server 재사용**: 동일한 Server를 여러 Client가 활용
- **기술 스택 유연성**: Client는 다른 언어/프레임워크 사용 가능

---

이 구조 분리를 통해 PRISM Core는 더욱 모듈화되고 확장 가능한 플랫폼이 될 것입니다! 🚀 