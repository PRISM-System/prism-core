# Prism Core: 산업 현장용 AI 에이전트 백엔드

Prism Core는 다양한 산업 현장의 요구에 맞는 특화된 AI 에이전트를 개발, 등록, 관리하기 위한 핵심 백엔드 시스템입니다. 이 프레임워크를 통해 우리 팀은 각 산업 도메인(반도체, 제조, 물류 등)의 문제를 해결하는 에이전트를 일관된 방식으로 구현하고 실험할 수 있습니다.

## 주요 목표

- **도메인 특화 에이전트 관리**: 각 산업 현장에 필요한 에이전트를 API를 통해 동적으로 등록하고 관리합니다.
- **일관된 개발 환경**: 모든 에이전트가 동일한 백엔드 인프라를 공유하여 개발 및 배포 효율을 높입니다.
- **LLM 기반 확장성**: vLLM을 기반으로 하므로, 에이전트의 목적에 맞는 다양한 LLM을 유연하게 적용할 수 있습니다.

## 시작하기

### 필수 조건

- Python 3.8 이상
- Docker 및 Docker Compose

### 설치 및 실행

1.  **저장소 복제 및 의존성 설치**:
    ```bash
    git clone https://github.com/your-repo/prism.git
    cd prism/prism-core
    pip install -r requirements.txt
    ```

2.  **환경 변수 설정**:
    `.env.example` 파일을 복사하여 `.env` 파일을 생성한 후, 여러분의 환경에 맞게 수정합니다.
    ```bash
    cp .env.example .env
    ```
    이후 `.env` 파일을 열어 사용할 모델 이름과 Hugging Face 토큰을 설정합니다.

    ```dotenv
    # .env
    MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
    HUGGING_FACE_HUB_TOKEN=your_token_here
    ```

    > **중요**: `meta-llama/Llama-2-7b-chat-hf`와 같이 접근 권한이 필요한 모델을 다운로드하려면 Hugging Face Hub 토큰이 반드시 필요합니다.
    > 토큰은 [Hugging Face 설정](https://huggingface.co/settings/tokens) 페이지에서 발급받을 수 있습니다. 이 토큰은 `docker-compose up` 실행 시 모델을 다운로드하는 데 사용됩니다.

3.  **Prism Core 실행**:
    Docker Compose를 사용하여 백엔드 서버를 실행합니다.
    ```bash
    docker-compose up --build
    ```
    서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.

## 산업 현장용 에이전트 만들기

Prism Core에서는 API를 통해 각 산업 현장에 필요한 에이전트를 만들고 관리합니다.

### 1. 에이전트 등록하기

`POST /agents` 엔드포인트를 사용하여 새로운 에이전트를 시스템에 등록합니다. 각 에이전트는 `이름(name)`, `설명(description)`, 그리고 가장 중요한 `역할 프롬프트(role_prompt)`로 구성됩니다. 각 필드의 역할은 다음과 같습니다.

-   **`name` (이름)**
    -   **역할**: 에이전트를 시스템에서 유일하게 식별하는 ID입니다. API 호출 시 이 이름을 사용합니다.
    -   **규칙**: 영어 소문자와 언더스코어(`_`)를 조합한 `snake_case`로 작성해주세요. (예: `safety_protocol_assistant`, `quality_check_bot`)

-   **`description` (설명)**
    -   **역할**: 이 에이전트가 어떤 역할을 하는지 사람이 쉽게 이해할 수 있도록 간략히 설명하는 문장입니다.
    -   **목적**: 여러 에이전트 목록 속에서 각 에이전트의 기능을 빠르게 파악하는 데 도움을 줍니다.

-   **`role_prompt` (역할 프롬프트)**
    -   **역할**: 에이전트의 정체성, 행동 방식, 응답 스타일을 정의하는 **가장 핵심적인 부분**입니다. LLM에게 지시하는 '시스템 프롬프트'와 같습니다.
    -   **작성 팁**: 좋은 프롬프트는 정체성(Persona), 과업(Task), 어조(Tone)를 명확하게 포함합니다.
        -   **정체성**: "당신은 20년 경력의 반도체 공정 안전 전문가입니다."
        -   **과업**: "사용자의 질문에 대해 안전 수칙을 명확하고 간결하게 설명해야 합니다."
        -   **어조/스타일**: "가장 중요한 안전 조치부터 순서대로, 번호를 붙여 안내하세요."

**예시: '공정 안전수칙 안내' 에이전트 등록**

```bash
curl -X POST "http://localhost:8000/agents" \
-H "Content-Type: application/json" \
-d '{
    "name": "safety_protocol_assistant",
    "description": "반도체 공정 중 발생할 수 있는 안전 문제에 대한 수칙을 안내하는 에이전트",
    "role_prompt": "당신은 반도체 공정 안전 전문가입니다. 공정 중 발생할 수 있는 위험 상황에 대해 안전 수칙을 명확하고 간결하게 설명해야 합니다. 사용자가 질문한 상황의 핵심을 파악하고, 가장 중요한 안전 조치부터 순서대로 안내하세요."
}'
```

### 2. vLLM 서버에서 LLM response 호출하기

`POST /agents/{agent_name}/invoke` 엔드포인트를 사용하여 등록된 에이전트를 호출하고 작업을 수행합니다.

**예시: '안전수칙 안내' 에이전트에게 질문하기**

```bash
curl -X POST "http://localhost:8000/agents/safety_protocol_assistant/invoke" \
-H "Content-Type: application/json" \
-d '{
    "prompt": "세정 공정에서 황산 누출 시 가장 먼저 해야 할 일은 무엇인가요?",
    "max_tokens": 200,
    "temperature": 0.2
}'
```

**예상 응답:**

```json
{
  "text": "즉시 해당 구역의 비상벨을 누르고 모든 인원을 대피시키십시오. 그 다음, 지정된 비상 대응팀에 연락하고 안전 장비를 착용한 담당자 외에는 절대 접근을 금지해야 합니다."
}
```

### 3. 등록된 에이전트 목록 확인하기

`GET /agents` 엔드포인트를 사용하여 현재 시스템에 등록된 모든 에이전트의 목록을 확인할 수 있습니다.

**요청 예시 (`curl` 사용):**

```bash
curl -X GET "http://localhost:8000/agents"
```

### Python으로 에이전트 테스트하기

`curl` 뿐만 아니라 Python 코드로도 에이전트를 쉽게 테스트할 수 있습니다. 다음은 `requests` 라이브러리를 사용하여 에이전트를 등록하고 호출하는 전체 예시입니다.

먼저, `requests` 라이브러리를 설치해야 합니다.
```bash
pip install requests
```

**`test_agent.py` 예시:**
```python
import requests
import json

# Prism Core 서버 주소
BASE_URL = "http://localhost:8000"

def register_safety_agent():
    """'공정 안전수칙 안내' 에이전트를 등록합니다."""
    print("Registering 'safety_protocol_assistant'...")
    agent_data = {
        "name": "safety_protocol_assistant",
        "description": "반도체 공정 중 발생할 수 있는 안전 문제에 대한 수칙을 안내하는 에이전트",
        "role_prompt": "당신은 반도체 공정 안전 전문가입니다. 공정 중 발생할 수 있는 위험 상황에 대해 안전 수칙을 명확하고 간결하게 설명해야 합니다. 사용자가 질문한 상황의 핵심을 파악하고, 가장 중요한 안전 조치부터 순서대로 안내하세요."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/agents", json=agent_data)
        response.raise_for_status()
        print("✅ Agent registered successfully:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return True
    except requests.exceptions.HTTPError as http_err:
        # 400 에러 중, 이미 등록되었다는 메시지가 포함된 경우는 성공으로 간주합니다.
        if response.status_code == 400 and "already registered" in response.text:
            print("ℹ️ Agent was already registered.")
            return True
        print(f"❌ HTTP error occurred: {http_err} - {response.text}")
        return False
    except Exception as err:
        print(f"❌ An error occurred: {err}")
        return False


def invoke_safety_agent(prompt: str):
    """등록된 에이전트를 호출하여 질문에 대한 답변을 받습니다."""
    print(f"\\nInvoking agent with prompt: '{prompt}'")
    invoke_data = {
        "prompt": prompt,
        "max_tokens": 200,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/agents/safety_protocol_assistant/invoke", json=invoke_data)
        response.raise_for_status()
        print("✅ Agent response received:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as err:
        print(f"❌ An error occurred during invocation: {err}")


if __name__ == "__main__":
    if register_safety_agent():
        question = "세정 공정에서 황산 누출 시 가장 먼저 해야 할 일은 무엇인가요?"
        invoke_safety_agent(question)
```

## 각 모듈 별 에이전트 클래스 선언

각각의 에이전트는 다른 함수들로 구성이 될 것으로 예상됩니다. 
코드 관리 및 안정성을 위해 기본적인 에이전트 클래스를 선언하였습니다. 
해당 클래스를 아래와 같이 상속받아 각 에이전트를 구현해주세요. 

혹시 추가적으로 더 필요하다고 생각하시는 기본 함수(abstract method)가 있다면 간단하게라도 말씀해주세요.

### `BaseAgent` 구조

`BaseAgent`는 모든 에이전트가 가져야 할 기본 구조를 정의합니다.
- **`__init__(self, name, description)`**: 에이전트의 이름과 설명을 초기화합니다.
- **`invoke(self, user_input, context)`**: 에이전트의 핵심 로직을 구현해야 하는 추상 메서드입니다.

### 예시: 오케스트레이션 에이전트

다음은 사용자의 요청을 분석하여 가장 적절한 하위 에이전트에게 작업을 위임하는 `OrchestrationAgent`의 예시입니다. 이 코드는 `prism-core/core/agents/orchestrator.py`에서 확인할 수 있습니다.

```python
from typing import Any, Dict
from .base import BaseAgent

class OrchestrationAgent(BaseAgent):
    """
    다른 에이전트와 도구 사이의 작업을 조율하는 에이전트입니다.
    사용자 요청을 받아 가장 적절한 에이전트나 도구를 결정하고 작업을 위임합니다.
    """
    def __init__(self, available_agents: Dict[str, BaseAgent]):
        super().__init__(
            name="orchestration_agent",
            description="마스터 에이전트로, 작업을 적절한 하위 에이전트에게 라우팅합니다."
        )
        self.available_agents = available_agents

    def invoke(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """사용자 입력을 기반으로 작업을 조율합니다."""
        print(f"오케스트레이터가 입력을 받음: '{user_input}'")

        # 1. 어떤 에이전트를 사용할지 결정
        agent_names = list(self.available_agents.keys())
        prompt = (
            f"사용자 요청: '{user_input}'\n"
            f"이 작업을 처리하기에 가장 적합한 에이전트는 다음 중 무엇입니까? "
            f"에이전트의 이름만으로 응답해주세요. "
            f"사용 가능한 에이전트: {agent_names}"
        )
        
        # 내부 _call_llm 메서드를 사용하여 결정을 내림
        chosen_agent_name = self._call_llm(prompt)
        # ... (실제 구현에서는 LLM이 에이전트 이름을 반환) ...
        
        print(f"오케스트레이터가 선택한 에이전트: '{chosen_agent_name}'")

        # 2. 선택된 에이전트에게 작업 위임
        if chosen_agent_name and chosen_agent_name in self.available_agents:
            chosen_agent = self.available_agents[chosen_agent_name]
            return chosen_agent.invoke(user_input, context)
        
        return "죄송합니다, 요청을 처리할 적절한 에이전트를 찾지 못했습니다."

```

## 라이브러리로 사용하기

`prism-core`는 각 에이전트 구현 시 라이브러리로 설치하여 사용할 수 있습니다.

### 1. 설치

```bash
pip install git+https://github.com/your-repo/prism.git#subdirectory=prism-core
```
### 2. FastAPI 프로젝트에 통합하기

다음은 `prism-core`를 사용하여 자신만의 FastAPI 애플리케이션을 만드는 예시입니다.

**`my_app.py` 예시:**
```python
from fastapi import FastAPI
from prism_core.core.llm_service import LLMService
from prism_core.core.agent_registry import AgentRegistry
from prism_core.core.api import create_api_router
from prism_core.core.schemas import Agent

# 1. FastAPI 앱 생성
app = FastAPI(title="My Custom Agent Service")

# 2. 핵심 서비스 인스턴스화
# 필요에 따라 설정을 커스터마이징할 수 있습니다.
llm_service = LLMService()
agent_registry = AgentRegistry()

# 3. prism-core API 라우터 생성 및 포함
# 생성한 서비스 인스턴스를 라우터 팩토리 함수에 전달합니다.
api_router = create_api_router(agent_registry, llm_service)
app.include_router(api_router, prefix="/api")

# 4. (선택) 시작 시 기본 에이전트 등록
@app.on_event("startup")
async def startup_event():
    safety_agent_data = {
        "name": "safety_protocol_assistant",
        "description": "반도체 공정 중 발생할 수 있는 안전 문제에 대한 수칙을 안내하는 에이전트",
        "role_prompt": "당신은 반도체 공정 안전 전문가입니다. 사용자의 질문에 대해 안전 수칙을 명확하고 간결하게 설명해야 합니다."
    }
    safety_agent = Agent(**safety_agent_data)
    agent_registry.register_agent(safety_agent)
    print("Default agent 'safety_protocol_assistant' registered.")

# 5. 서버 실행
# uvicorn my_app:app --reload
```

## API 엔드포인트 요약

- `POST /agents`: 새로운 에이전트를 등록합니다.
- `GET /agents`: 등록된 모든 에이전트 목록을 조회합니다.
- `POST /agents/{agent_name}/invoke`: 특정 에이전트와 상호작용(대화)합니다.
- `POST /generate`: 특정 에이전트를 거치지 않고 LLM의 응답을 직접 생성합니다.
