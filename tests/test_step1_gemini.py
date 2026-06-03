"""Step 1 테스트: Gemini 2.5 Flash 연결 및 RAG 체인 검증"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from src.llm_config import get_embeddings, get_llm


def test_gemini_basic():
    """Gemini API 연결 기본 테스트"""
    print("\n[테스트 1] Gemini 2.5 Flash API 연결 확인...")
    llm = get_llm()
    response = llm.invoke("'온누리상품권'이 무엇인지 한 문장으로 설명해 주세요.")
    print(f"  → 응답: {response.content}")
    assert response.content, "응답이 비어있습니다"
    print("  ✅ Gemini 기본 연결 성공")


def test_chromadb_load():
    """기존 ChromaDB 로드 확인"""
    print("\n[테스트 2] 기존 ChromaDB 로드 확인...")
    vectorstore_path = Path(__file__).resolve().parent.parent / "vectordb" / "chroma_db"
    embeddings = get_embeddings()
    vectorstore = Chroma(
        persist_directory=str(vectorstore_path),
        embedding_function=embeddings,
    )
    doc_count = vectorstore._collection.count()
    print(f"  → 저장된 문서: {doc_count}개")
    assert doc_count > 0, "ChromaDB에 문서가 없습니다"
    print("  ✅ ChromaDB 로드 성공")
    return vectorstore


def test_rag_with_gemini():
    """ChromaDB + Gemini 2.5 Flash RAG 체인 테스트"""
    print("\n[테스트 3] ChromaDB + Gemini RAG 체인 검증...")
    vectorstore = test_chromadb_load()
    llm = get_llm()

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 온누리상품권 가맹점 안내 전문 챗봇입니다.
검색된 가맹점 정보를 바탕으로 정확하고 친절하게 답변하세요."""),
        ("human", "검색된 가맹점 정보:\n{context}\n\n사용자 질문: {question}\n\n답변해 주세요."),
    ])

    def format_docs(docs):
        return "\n\n".join([doc.page_content for doc in docs])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    query = "서울 음식점 추천해줘"
    response = chain.invoke(query)
    print(f"  → 질문: {query}")
    print(f"  → 응답 (앞 200자): {response[:200]}...")
    assert response, "RAG 응답이 비어있습니다"
    print("  ✅ RAG 체인 성공")


if __name__ == "__main__":
    print("=" * 60)
    print("Step 1: Gemini 2.5 Flash 연결 테스트")
    print("=" * 60)

    test_gemini_basic()
    test_rag_with_gemini()

    print("\n" + "=" * 60)
    print("✅ Step 1 모든 테스트 통과! Step 2 진행 가능합니다.")
    print("=" * 60)
