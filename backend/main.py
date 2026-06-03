from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.routers import chat
from backend.routers import search
from backend.routers import report

app = FastAPI(title="온누리 챗봇 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router,   prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.mount("/docs", StaticFiles(directory="docs"), name="docs")# docs/ 폴더를 /docs 경로로 정적 파일 서빙 추가 


@app.get("/health")
def health_check():
    return {"status": "ok"}
