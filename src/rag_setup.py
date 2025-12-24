from dotenv import load_dotenv
load_dotenv('../api_keys.txt')

import os
from langchain_community.vectorstores import Chroma
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
import search_engine as se
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

# 1.청킹
from langchain_text_splitters import RecursiveCharacterTextSplitter # chunk단위로 분리시키는 역할
text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap=200)# 이 두 요소도 매번 본인이 결정해야 함
# search.document_list를 잘게 쪼갠다.
splits = text_splitter.split_documents(se.document_list)

# 2. 임베딩 모델 설정 
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")#

# 3. 벡터DB 생성 및 저장 

db_path = "vectordb/chroma_db"

# 만약 DB 폴더가 이미 존재한다면? -> 불러오기 (공짜!)
if os.path.exists(db_path):
    print("이미 생성된 DB가 있네요. 로컬에서 불러옵니다 (비용 $0)")
    vectorstore = Chroma(embedding_function=embeddings, persist_directory="vectordb/chroma_db")# 최대 1000데이터 저장

# 만약 DB 폴더가 없다면? -> 새로 만들기 (OpenAI 비용 발생)
else:
    print("DB가 없어서 새로 생성합니다. (OpenAI API 호출 시작)")
    vectorstore = Chroma.from_documents(
        documents=se.document_list[:1000], # 테스트를 위해 1000개로
        embedding=embeddings, 
        persist_directory=db_path
    )
    print("DB 생성 및 저장 완료!")

print(f'전체 문서 개수: {len(se.document_list)}')


# 4. 검색 테스트
query = "서울 음식점"
docs = vectorstore.similarity_search(query, k=3)#k = 몇개의 결과를 가져올 것인가?

# print(docs[0].page_content)
print(f"--- '{query}' 검색 결과 (총 {len(docs)}개 찾음)---")
if not docs:
    print("검색 결과가 없습니다. DB에 데이터가 정상적으로 저장되었는지 확인하세요.")
else:
    for i, doc in enumerate(docs):
        print(f"[{i+1}] {doc.page_content}")
        print(f"메타데이터: {doc.metadata}")
        print("-" * 30)


# 15만개 가맹점 임베딩 생성 및 저장
from tqdm import tqdm # 진행창을 보기 위한 라이브러리
import time
# 15만 개 데이터를 1,000개씩 나눠서 넣기 (Batch)
batch_size = 1000
sample_docs = se.document_list[:5000] # 15만 개 리스트 중 5000개, 전체 15만 건의 데이터를 모두 임베딩하는 것은 비용과 성능 측면에서 비효율적이라 판단

for i in tqdm(range(0, len(sample_docs), batch_size)):
    batch = sample_docs[i : i + batch_size]
    vectorstore.add_documents(batch)
    time.sleep(1)
    # 한 번 넣을 때마다 자동으로 저장됩니다.

