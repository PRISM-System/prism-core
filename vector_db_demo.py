#!/usr/bin/env python3
"""
Vector DB Utils Demo Script

PRISM Core의 Vector DB 유틸리티 사용법을 보여주는 데모 스크립트
RAG 구현을 위한 Vector Database 기능들을 테스트합니다.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from prism_core.core.vector_db import (
    WeaviateClient, DocumentSchema, SearchQuery, IndexConfig,
    EncoderManager, VectorDBAPI
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 테스트 데이터
SAMPLE_DOCUMENTS = [
    DocumentSchema(
        content="제조업에서 품질 관리는 매우 중요합니다. ISO 9001 표준을 따라 품질 시스템을 구축해야 합니다.",
        title="품질 관리 시스템",
        source="manufacturing_guide.pdf",
        metadata={"category": "quality", "language": "ko"}
    ),
    DocumentSchema(
        content="스마트 팩토리는 IoT, AI, 빅데이터 기술을 활용하여 생산성을 향상시킵니다.",
        title="스마트 팩토리 개요",
        source="smart_factory.pdf",
        metadata={"category": "technology", "language": "ko"}
    ),
    DocumentSchema(
        content="공정 자동화를 통해 인적 오류를 줄이고 일관된 품질을 유지할 수 있습니다.",
        title="공정 자동화",
        source="automation_guide.pdf",
        metadata={"category": "automation", "language": "ko"}
    ),
    DocumentSchema(
        content="예측 유지보수는 설비의 고장을 미리 예측하여 다운타임을 최소화합니다.",
        title="예측 유지보수",
        source="maintenance.pdf",
        metadata={"category": "maintenance", "language": "ko"}
    ),
    DocumentSchema(
        content="Supply chain management is crucial for manufacturing efficiency and cost reduction.",
        title="Supply Chain Management",
        source="scm_guide.pdf",
        metadata={"category": "logistics", "language": "en"}
    )
]


async def test_encoder_manager():
    """인코더 매니저 테스트"""
    print("\n" + "="*60)
    print("🤖 Encoder Manager 테스트")
    print("="*60)
    
    try:
        # 추천 모델 목록 출력
        print("\n📋 추천 인코더 모델:")
        recommended = EncoderManager.get_recommended_models()
        for name, info in recommended.items():
            print(f"  - {name}: {info['description']} (차원: {info['vector_dimension']})")
        
        # 간단한 인코더 테스트 (실제로는 모델을 다운로드해야 함)
        print(f"\n⚠️  실제 인코더 테스트는 모델 다운로드가 필요하므로 스킵합니다.")
        print("   사용 예시:")
        print("   encoder = EncoderManager('intfloat/multilingual-e5-base')")
        print("   embeddings = encoder.encode_texts(['안녕하세요', 'Hello world'])")
        
        return True
        
    except Exception as e:
        print(f"❌ 인코더 테스트 실패: {e}")
        return False


async def test_weaviate_client():
    """Weaviate 클라이언트 테스트 (Weaviate 서버 없이는 스킵)"""
    print("\n" + "="*60)
    print("🗄️  Weaviate Client 테스트")
    print("="*60)
    
    print("⚠️  실제 Weaviate 서버 테스트는 서버가 필요하므로 스킵합니다.")
    print("   사용 예시:")
    print("   client = WeaviateClient('http://localhost:8080')")
    print("   client.connect()")
    print("   client.add_document('Documents', document)")
    print("   results = client.search('Documents', query)")
    
    # 클라이언트 객체 생성만 테스트
    try:
        client = WeaviateClient()
        print(f"✅ Weaviate 클라이언트 객체 생성 성공")
        print(f"   URL: {client.url}")
        print(f"   연결 상태: {client.is_connected()}")
        return True
    except Exception as e:
        print(f"❌ 클라이언트 생성 실패: {e}")
        return False


async def test_schemas():
    """스키마 테스트"""
    print("\n" + "="*60)
    print("📋 Schema 테스트")
    print("="*60)
    
    try:
        # DocumentSchema 테스트
        doc = SAMPLE_DOCUMENTS[0]
        print(f"✅ DocumentSchema 생성 성공:")
        print(f"   제목: {doc.title}")
        print(f"   내용: {doc.content[:50]}...")
        print(f"   메타데이터: {doc.metadata}")
        
        # SearchQuery 테스트
        query = SearchQuery(
            query="품질 관리",
            limit=5,
            threshold=0.7,
            filters={"category": "quality"}
        )
        print(f"\n✅ SearchQuery 생성 성공:")
        print(f"   쿼리: {query.query}")
        print(f"   제한: {query.limit}")
        print(f"   임계값: {query.threshold}")
        
        # IndexConfig 테스트
        config = IndexConfig(
            class_name="Documents",
            description="Manufacturing documents",
            vector_dimension=768,
            encoder_model="intfloat/multilingual-e5-base"
        )
        print(f"\n✅ IndexConfig 생성 성공:")
        print(f"   클래스명: {config.class_name}")
        print(f"   벡터 차원: {config.vector_dimension}")
        print(f"   인코더: {config.encoder_model}")
        
        # Weaviate 스키마 변환 테스트
        weaviate_schema = config.get_weaviate_schema()
        print(f"\n✅ Weaviate 스키마 변환 성공:")
        print(f"   클래스: {weaviate_schema['class']}")
        print(f"   속성 수: {len(weaviate_schema['properties'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 스키마 테스트 실패: {e}")
        return False


async def demo_usage_patterns():
    """사용 패턴 데모"""
    print("\n" + "="*60)
    print("🎯 Vector DB Utils 사용 패턴 데모")
    print("="*60)
    
    print("1️⃣ 기본 사용 패턴:")
    print("""
# 1. 클라이언트 초기화
from prism_core.core.vector_db import WeaviateClient, EncoderManager, IndexConfig

client = WeaviateClient('http://localhost:8080')
encoder = EncoderManager('intfloat/multilingual-e5-base')
client.encoder = encoder

# 2. 인덱스 생성
config = IndexConfig(
    class_name="Documents",
    description="Manufacturing documents",
    vector_dimension=768,
    encoder_model="intfloat/multilingual-e5-base"
)
client.create_index(config)

# 3. 문서 추가
documents = [
    DocumentSchema(content="...", title="...", metadata={"category": "..."})
]
client.add_documents("Documents", documents)

# 4. 검색
query = SearchQuery(query="품질 관리", limit=10)
results = client.search("Documents", query)
""")
    
    print("\n2️⃣ API 사용 패턴:")
    print("""
# FastAPI 앱에 Vector DB API 추가
from prism_core.core.vector_db import create_vector_db_router

app = FastAPI()
vector_db_router = create_vector_db_router("http://localhost:8080")
app.include_router(vector_db_router)

# API 엔드포인트:
# POST /vector-db/indices - 인덱스 생성
# POST /vector-db/documents/{class_name} - 문서 추가
# POST /vector-db/search/{class_name} - 검색
# DELETE /vector-db/documents/{class_name}/{doc_id} - 문서 삭제
""")
    
    print("\n3️⃣ 컨텍스트 매니저 사용:")
    print("""
# 자동 연결 관리
with WeaviateClient('http://localhost:8080') as client:
    client.encoder = EncoderManager('intfloat/multilingual-e5-base')
    results = client.search("Documents", query)
""")


async def demo_rag_implementation():
    """RAG 구현 예시"""
    print("\n" + "="*60)
    print("🧠 RAG 구현 예시")
    print("="*60)
    
    print("""
RAG (Retrieval-Augmented Generation) 구현 예시:

1. 문서 인덱싱:
   - 제조업 관련 문서들을 Vector DB에 저장
   - 각 문서는 벡터로 변환되어 유사도 검색 가능

2. 검색 단계:
   - 사용자 질문을 벡터로 변환
   - Vector DB에서 관련 문서 검색
   - 유사도 점수 기반 필터링

3. 생성 단계:
   - 검색된 문서를 컨텍스트로 활용
   - LLM에게 질문과 컨텍스트 제공
   - 정확하고 근거 있는 답변 생성

구현 코드 예시:
```python
async def rag_query(question: str, class_name: str = "Documents"):
    # 1. 검색
    query = SearchQuery(query=question, limit=5, threshold=0.7)
    search_results = client.search(class_name, query)
    
    # 2. 컨텍스트 구성
    context = "\\n\\n".join([result.content for result in search_results])
    
    # 3. LLM 프롬프트 구성
    prompt = f'''
    다음 문서들을 참고하여 질문에 답변해주세요:
    
    {context}
    
    질문: {question}
    '''
    
    # 4. LLM 호출 (PRISM Core의 LLM 서비스 사용)
    response = await llm_service.generate(prompt)
    
    return {{
        "answer": response,
        "sources": [result.source for result in search_results],
        "relevance_scores": [result.score for result in search_results]
    }}
```
""")


async def main():
    """메인 데모 함수"""
    print("🚀 PRISM Core Vector DB Utils Demo")
    print("=" * 60)
    print("RAG 구현을 위한 Vector Database 유틸리티 기능을 테스트합니다.")
    
    # 테스트 실행
    tests = [
        ("스키마 테스트", test_schemas),
        ("인코더 매니저 테스트", test_encoder_manager),
        ("Weaviate 클라이언트 테스트", test_weaviate_client),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 중 오류 발생: {e}")
            results.append((test_name, False))
    
    # 사용 패턴 데모
    await demo_usage_patterns()
    await demo_rag_implementation()
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n총 {len(results)}개 테스트 중 {success_count}개 성공")
    
    print("\n" + "="*60)
    print("🎉 Vector DB Utils Demo 완료!")
    print("="*60)
    
    print("\n📚 주요 기능:")
    print("  ✅ Weaviate 기반 Vector Database 클라이언트")
    print("  ✅ 다양한 인코더 모델 지원 (HuggingFace, OpenAI)")
    print("  ✅ 문서 인덱싱 및 배치 처리")
    print("  ✅ 유사도 기반 검색")
    print("  ✅ 문서 삭제 및 관리")
    print("  ✅ REST API 인터페이스")
    print("  ✅ RAG 구현 지원")
    
    print("\n📋 API 엔드포인트:")
    print("  - GET  /vector-db/status - Vector DB 상태 조회")
    print("  - POST /vector-db/indices - 인덱스 생성")
    print("  - DELETE /vector-db/indices/{class_name} - 인덱스 삭제")
    print("  - POST /vector-db/documents/{class_name} - 문서 추가")
    print("  - POST /vector-db/documents/{class_name}/batch - 배치 문서 추가")
    print("  - POST /vector-db/search/{class_name} - 문서 검색")
    print("  - DELETE /vector-db/documents/{class_name}/{doc_id} - 문서 삭제")
    print("  - GET  /vector-db/encoders/recommended - 추천 인코더 목록")
    print("  - POST /vector-db/encoders/test - 인코더 테스트")
    
    print("\n🔧 설치 및 설정:")
    print("  1. Weaviate 서버 실행: docker run -p 8080:8080 semitechnologies/weaviate:latest")
    print("  2. 필요한 패키지 설치: pip install -r requirements.txt")
    print("  3. 인코더 모델 다운로드 (자동)")
    print("  4. API 서버에 Vector DB 라우터 추가")


if __name__ == "__main__":
    asyncio.run(main()) 