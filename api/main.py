from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api.routes import memories
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.services.dependencies import get_memory_engine
    get_memory_engine()
    yield


app = FastAPI(
    title="AI Memory RAG API",
    description="AI Memory RAG - 个人知识管理与 Agent 调用系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memories.router)


@app.get("/")
def root():
    return {
        "message": "AI Memory RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
