from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings


def get_llm(temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=temperature,
    )


def get_embeddings() -> OpenAIEmbeddings:
    # ChromaDB가 OpenAI 임베딩으로 생성되어 있으므로 동일 모델 유지
    return OpenAIEmbeddings(model="text-embedding-3-small")
