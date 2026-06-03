from fastapi import APIRouter
from pydantic import BaseModel
from src.chatbot import process_query

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[list[str]] = []  # [[user, bot], [user, bot], ...]


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    history = [tuple(pair) for pair in req.history]
    reply = process_query(req.message, history)
    return ChatResponse(reply=reply)
