#!/usr/bin/env python3
"""
Tool System Demo Script

이 스크립트는 PRISM Core의 tool 시스템 사용법을 보여줍니다.
Client에서 tool을 등록하고, agent에 할당하여 자동으로 사용하는 예제입니다.
"""

import requests
import json
import sys

# API 서버 설정
BASE_URL = "http://localhost:8000/api"

def main():
    print("🚀 PRISM Core Tool System Demo")
    print("=" * 50)
    
    try:
        # 1. 서버 상태 확인
        print("1. 서버 상태 확인...")
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print(f"✅ 서버 연결 성공: {response.json()}")
        else:
            print(f"❌ 서버 연결 실패: {response.status_code}")
            return
        
        # 2. 등록된 Tool 목록 조회
        print("\n2. 등록된 Tool 목록 조회...")
        response = requests.get(f"{BASE_URL}/tools")
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ 등록된 Tool 수: {len(tools)}")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        else:
            print(f"❌ Tool 목록 조회 실패: {response.status_code}")
            return
        
        # 3. Client에서 새로운 Tool 등록
        print("\n3. Client에서 새로운 Tool 등록...")
        
        # 3.1. API Tool 등록
        api_tool_data = {
            "name": "weather_api_tool",
            "description": "Get weather information from external API",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "API URL to call"
                    },
                    "method": {
                        "type": "string",
                        "default": "GET",
                        "description": "HTTP method"
                    },
                    "data": {
                        "type": "object",
                        "description": "Request data"
                    }
                },
                "required": []
            },
            "tool_type": "api"
        }
        
        response = requests.post(f"{BASE_URL}/tools/register", json=api_tool_data)
        if response.status_code == 200:
            print(f"✅ API Tool 등록 성공: {response.json()['message']}")
        else:
            print(f"❌ API Tool 등록 실패: {response.status_code}, {response.text}")
        
        # 3.2. Calculation Tool 등록
        calc_tool_data = {
            "name": "math_calculator",
            "description": "Perform mathematical calculations safely",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Variables to use in the expression"
                    }
                },
                "required": ["expression"]
            },
            "tool_type": "calculation"
        }
        
        response = requests.post(f"{BASE_URL}/tools/register", json=calc_tool_data)
        if response.status_code == 200:
            print(f"✅ Calculation Tool 등록 성공: {response.json()['message']}")
        else:
            print(f"❌ Calculation Tool 등록 실패: {response.status_code}, {response.text}")
        
        # 3.3. Custom Tool 등록
        custom_tool_data = {
            "name": "text_processor",
            "description": "Process and transform text data",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["echo", "transform"],
                        "description": "Action to perform"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message for echo action"
                    },
                    "data": {
                        "type": "object",
                        "description": "Data for transform action"
                    }
                },
                "required": ["action"]
            },
            "tool_type": "custom"
        }
        
        response = requests.post(f"{BASE_URL}/tools/register", json=custom_tool_data)
        if response.status_code == 200:
            print(f"✅ Custom Tool 등록 성공: {response.json()['message']}")
        else:
            print(f"❌ Custom Tool 등록 실패: {response.status_code}, {response.text}")
        
        # 3.4. 사용자 정의 함수를 포함한 Custom Tool 등록
        custom_function_tool_data = {
            "name": "data_analyzer",
            "description": "Analyze data using custom user-defined functions",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["execute_function"],
                        "description": "Action to perform"
                    },
                    "function_params": {
                        "type": "object",
                        "description": "Parameters to pass to the custom function"
                    }
                },
                "required": ["action"]
            },
            "tool_type": "custom",
            "function_code": """
def main():
    # 사용자 정의 함수 예제
    import math
    
    # 간단한 데이터 분석 함수
    def analyze_numbers(numbers):
        if not numbers:
            return {"error": "No numbers provided"}
        
        avg = sum(numbers) / len(numbers)
        variance = sum((x - avg)**2 for x in numbers) / len(numbers)
        
        return {
            "count": len(numbers),
            "sum": sum(numbers),
            "average": avg,
            "min": min(numbers),
            "max": max(numbers),
            "std_dev": math.sqrt(variance)
        }
    
    # 기본 테스트 데이터
    test_data = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
    result = analyze_numbers(test_data)
    
    return {
        "analysis_result": result,
        "message": "Data analysis completed successfully"
    }
"""
        }
        
        response = requests.post(f"{BASE_URL}/tools/register-with-code", json=custom_function_tool_data)
        if response.status_code == 200:
            print(f"✅ Custom Function Tool 등록 성공: {response.json()['message']}")
        else:
            print(f"❌ Custom Function Tool 등록 실패: {response.status_code}, {response.text}")
        
        # 4. 업데이트된 Tool 목록 확인
        print("\n4. 업데이트된 Tool 목록 확인...")
        response = requests.get(f"{BASE_URL}/tools")
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ 총 등록된 Tool 수: {len(tools)}")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description']}")
        
        # 5. 새로운 Tool들 직접 테스트
        print("\n5. 새로운 Tool들 직접 테스트...")
        
        # 5.1. Math Calculator 테스트
        print("\n5.1. Math Calculator 테스트...")
        calc_request = {
            "tool_name": "math_calculator",
            "parameters": {
                "expression": "math.sqrt(16) + 2 * 3",
                "variables": {}
            }
        }
        
        response = requests.post(f"{BASE_URL}/tools/execute", json=calc_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Calculator 실행 성공: {result['result']}")
        else:
            print(f"❌ Calculator 실행 실패: {response.status_code}")
        
        # 5.2. Text Processor 테스트
        print("\n5.2. Text Processor 테스트...")
        text_request = {
            "tool_name": "text_processor",
            "parameters": {
                "action": "transform",
                "data": {
                    "name": "john doe",
                    "city": "seoul",
                    "age": 30
                }
            }
        }
        
        response = requests.post(f"{BASE_URL}/tools/execute", json=text_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Text Processor 실행 성공: {result['result']}")
        else:
            print(f"❌ Text Processor 실행 실패: {response.status_code}")
        
        # 5.3. Custom Function Tool 테스트
        print("\n5.3. Custom Function Tool 테스트...")
        custom_func_request = {
            "tool_name": "data_analyzer",
            "parameters": {
                "action": "execute_function",
                "function_params": {}
            }
        }
        
        response = requests.post(f"{BASE_URL}/tools/execute", json=custom_func_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Custom Function Tool 실행 성공:")
            print(f"   분석 결과: {result['result']['analysis_result']}")
            print(f"   메시지: {result['result']['message']}")
        else:
            print(f"❌ Custom Function Tool 실행 실패: {response.status_code}, {response.text}")
        
        # 6. Agent 등록 (database tool + 새로운 tools 포함)
        print("\n6. 다중 Tool을 가진 Agent 등록...")
        agent_data = {
            "name": "multi_tool_analyst",
            "description": "다양한 도구를 활용하는 분석 전문가",
            "role_prompt": "당신은 다양한 도구를 활용하여 사용자의 요청을 처리하는 분석 전문가입니다. 데이터베이스 조회, 계산, 텍스트 처리, 데이터 분석 등 다양한 작업을 수행할 수 있습니다.",
            "tools": ["database_tool", "math_calculator", "text_processor", "data_analyzer"]
        }
        
        response = requests.post(f"{BASE_URL}/agents", json=agent_data)
        if response.status_code == 200:
            print(f"✅ Multi-tool Agent 등록 성공: {response.json()['name']}")
        else:
            print(f"❌ Multi-tool Agent 등록 실패: {response.status_code}, {response.text}")
        
        # 7. 등록된 Agent 목록 확인
        print("\n7. 등록된 Agent 목록 확인...")
        response = requests.get(f"{BASE_URL}/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ 등록된 Agent 수: {len(agents)}")
            for agent in agents:
                print(f"   - {agent['name']}: {agent['description']}")
                if agent['tools']:
                    print(f"     Tools: {', '.join(agent['tools'])}")
        
        # 8. Database Tool 직접 테스트
        print("\n8. Database Tool 직접 테스트...")
        tool_request = {
            "tool_name": "database_tool",
            "parameters": {
                "action": "list_tables"
            }
        }
        
        response = requests.post(f"{BASE_URL}/tools/execute", json=tool_request)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tool 실행 성공 (실행시간: {result.get('execution_time_ms', 'N/A')}ms)")
            if result['success']:
                tables = result['result'].get('tables', [])
                print(f"   데이터베이스 테이블 수: {len(tables)}")
                if tables:
                    print("   테이블 목록:")
                    for table in tables[:5]:  # 처음 5개만 표시
                        print(f"     - {table}")
                    if len(tables) > 5:
                        print(f"     ... 및 {len(tables) - 5}개 더")
            else:
                print(f"   Tool 실행 실패: {result.get('error_message')}")
        else:
            print(f"❌ Tool 실행 실패: {response.status_code}, {response.text}")
        
        # 9. Agent를 통한 자동 Tool 사용 테스트
        print("\n9. Agent를 통한 자동 Tool 사용 테스트...")
        
        test_queries = [
            "데이터베이스에 어떤 테이블들이 있나요?",
            "2의 10제곱을 계산해주세요",
            "제조 공정 관련 데이터를 보여주세요",
            "숫자 데이터를 분석해주세요"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n9.{i} 테스트 쿼리: '{query}'")
            
            agent_request = {
                "prompt": query,
                "max_tokens": 200,
                "temperature": 0.3,
                "use_tools": True
            }
            
            response = requests.post(f"{BASE_URL}/agents/multi_tool_analyst/invoke", json=agent_request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Agent 응답 생성 성공")
                print(f"   사용된 Tools: {result.get('tools_used', [])}")
                if result.get('tool_results'):
                    print(f"   Tool 결과 수: {len(result['tool_results'])}")
                print(f"   Agent 응답: {result['text'][:200]}{'...' if len(result['text']) > 200 else ''}")
            else:
                print(f"❌ Agent 호출 실패: {response.status_code}, {response.text}")
        
        # 10. Tool 정보 상세 조회
        print("\n10. Tool 정보 상세 조회...")
        for tool_name in ["database_tool", "math_calculator", "text_processor", "data_analyzer"]:
            response = requests.get(f"{BASE_URL}/tools/{tool_name}")
            if response.status_code == 200:
                tool_info = response.json()
                print(f"✅ {tool_name} 정보:")
                print(f"   타입: {tool_info.get('type', 'unknown')}")
                if tool_info.get('type') == 'dynamic':
                    print(f"   Tool 타입: {tool_info.get('tool_type')}")
                    if 'config' in tool_info and 'function_code' in tool_info['config']:
                        print(f"   사용자 정의 함수: 포함됨")
            else:
                print(f"❌ {tool_name} 정보 조회 실패")
        
        print("\n🎉 Client Tool 등록 Demo 완료!")
        print("\n📚 새로 추가된 API 엔드포인트:")
        print("   - POST /api/tools/register: 새로운 Tool 등록")
        print("   - GET /api/tools/{tool_name}: Tool 상세 정보 조회")
        print("   - DELETE /api/tools/{tool_name}: Tool 삭제")
        print("   - PUT /api/tools/{tool_name}/config: Tool 설정 업데이트")
        print("   - POST /api/agents: Agent 등록 (다중 Tool 지원)")
        print("   - POST /api/agents/{agent_name}/tools: Agent에 Tool 할당")
        print("   - POST /api/agents/{agent_name}/invoke: Agent 실행 (다중 Tool 자동 사용)")
        print("   - GET /api/tools: Tool 목록 조회")
        print("   - POST /api/tools/execute: Tool 직접 실행")
        print("   - Swagger UI: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 먼저 서버를 실행해주세요:")
        print("   docker-compose up -d")
        print("   또는")
        print("   ./run.sh")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 