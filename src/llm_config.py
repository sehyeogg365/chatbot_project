from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings


def get_llm(temperature: float = 0.7) -> ChatGoogleGenerativeAI:# -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=temperature,
    )


def get_embeddings() -> GoogleGenerativeAIEmbeddings:# -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
    )
