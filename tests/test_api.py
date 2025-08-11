import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock

from main import app


@pytest.fixture
def client():
    """테스트 클라이언트 픽스처"""
    return TestClient(app)


def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to PRISM Core"
    assert data["version"] == "0.1.0"


def test_agents_list_endpoint(client):
    """에이전트 목록 조회 엔드포인트 테스트"""
    response = client.get("/api/agents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_agent_registration(client):
    """에이전트 등록 테스트"""
    agent_data = {
        "name": "test_agent",
        "description": "테스트용 에이전트",
        "role_prompt": "당신은 테스트용 에이전트입니다."
    }
    
    response = client.post("/api/agents", json=agent_data)
    assert response.status_code == 200
    
    # 등록된 에이전트 확인
    response_data = response.json()
    assert response_data["name"] == agent_data["name"]
    assert response_data["description"] == agent_data["description"]
    assert response_data["role_prompt"] == agent_data["role_prompt"] 