from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import init_db
from exceptions import AppError, app_error_handler
from routers import auth, conversations, qa_records, feedback, preferences, tags
from routers import documents
from services.embedding import warmup

app = FastAPI(title="ChromaDB QA Preference API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(documents.router)
app.include_router(feedback.router)
app.include_router(preferences.router)
app.include_router(qa_records.router)
app.include_router(tags.router)


@app.on_event("startup")
def on_startup():
    init_db()
    warmup()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
