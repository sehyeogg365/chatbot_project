from dotenv import load_dotenv
load_dotenv('../api_keys.txt')

import os
from langchain_community.vectorstores import Chroma
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
import search_engine as search
'''
목적: RAG 시스템 구축
내용:
- 문서 생성 (15만개)
- OpenAI 임베딩
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
# api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from langchain_core.prompts import ChatPromptTemplate

# 1.청킹
from langchain_text_splitters import RecursiveCharacterTextSplitter # chunk단위로 분리시키는 역할
text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap=200)# 이 두 요소도 매번 본인이 결정해야 함
# search.document_list를 잘게 쪼갠다.
splits = text_splitter.split_documents(search.document_list)

# 2. 임베딩 모델 설정 
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")#

# 3. 벡터DB 생성 및 저장 
vectorstore = Chroma.from_documents(documents=search.document_list[:1000], embedding=embeddings, persist_directory="vectordb/chroma_db")# 최대 1000데이터 저장
print(f'전체 문서 개수: {len(search.document_list)}')
# 15만개 가맹점 임베딩 생성 및 저장

# 4. 검색 테스트
query = "서울 음식점"
docs = vectorstore.similarity_search(query, k=100)

# print(docs[0].page_content)
print(f"--- '{query}' 검색 결과 (총 {len(docs)}개 찾음)---")
if not docs:
    print("검색 결과가 없습니다. DB에 데이터가 정상적으로 저장되었는지 확인하세요.")
else:
    for i, doc in enumerate(docs):
        print(f"[{i+1}] {doc.page_content}")
        print(f"메타데이터: {doc.metadata}")
        print("-" * 30)