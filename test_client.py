import requests
import json

def test_llm_agent():
    """
    Sends a request to the LLM agent and prints the response.
    """
    url = "http://127.0.0.1:8000/api/generate"
    headers = {"Content-Type": "application/json"}
    
    # 여기서 프롬프트와 다른 파라미터를 수정할 수 있습니다.
    data = {
        "prompt": "안녕하세요! 자기소개 부탁해요.",
        "max_tokens": 128,
        "temperature": 0.7
    }

    try:
        print("LLM 에이전트로 요청을 보냅니다...")
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # 오류가 발생하면 예외를 발생시킵니다.

        print("응답을 받았습니다:")
        response_data = response.json()
        print(response_data.get("text"))

    except requests.exceptions.RequestException as e:
        print(f"오류가 발생했습니다: {e}")
        print("서버가 실행 중인지 확인해주세요. 'codes/PRISM-Orch/run.sh'를 실행하여 서버를 시작할 수 있습니다.")

if __name__ == "__main__":
    test_llm_agent() 