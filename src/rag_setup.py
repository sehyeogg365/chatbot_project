from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import os
import shutil
import time
from tqdm import tqdm
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import search_engine as se
'''
목적: RAG 시스템 구축
내용:
- 문서 생성 (15만개)
- Google 임베딩
- ChromaDB 저장
- 검색 테스트
- 파라미터 튜닝 (k값 등)

출력: chroma_db/

1단계: 임베딩 (Embedding) - "글자를 숫자로 바꾸기"

2단계: 벡터 디비 (Vector DB) - "숫자 창고에 저장하기"

3단계: 리트리버 (Retriever) - "똑똑한 검색 대리인"

4단계: 프롬프트 (Prompt) - "AI에게 주는 지시서"

5단계: LLM 응답 - "최종 답변 생성"
'''
# 임베딩 모델 설정
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

db_path = "vectordb/chroma_db"

# 기존 DB 삭제 (차원 불일치 방지)
if os.path.exists(db_path):
    shutil.rmtree(db_path)
    print(f"기존 DB 삭제 완료: {db_path}")

# 청킹
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(se.document_list[:5000])

batch_size = 1000
sample_docs = splits

print(f"원본 문서: {len(se.document_list)}, 청킹 후: {len(sample_docs)}개")
print("1번째 배치로 DB 생성 중... (Google API 호출)")

vectorstore = Chroma.from_documents(
    documents=sample_docs[:batch_size],# 처음 1000개로 DB 생성
    embedding=embeddings,# 임베딩 모델
    persist_directory=db_path,# DB 저장 경로
)
print(f"  → {batch_size}개 저장 완료")

for i in tqdm(range(batch_size, len(sample_docs), batch_size), desc="배치 추가"):
    batch = sample_docs[i : i + batch_size]
    vectorstore.add_documents(batch)
    time.sleep(0.5)

print(f"\nDB 생성 완료! 총 {len(sample_docs)}개 문서 저장")

# 검색 테스트
query = "서울 음식점"
docs = vectorstore.similarity_search(query, k=3)
print(f"\n--- '{query}' 검색 결과 ({len(docs)}개) ---")
for i, doc in enumerate(docs, 1):
    print(f"[{i}] {doc.page_content}")
    print(f"    메타데이터: {doc.metadata}")
    print("-" * 30)
