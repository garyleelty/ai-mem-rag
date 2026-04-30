from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from database import init_db
from routers import auth, conversations, qa_records, feedback, preferences, tags

# Import existing document routers
from services import (
    validate_file,
    process_file,
    list_collections,
    create_collection,
    delete_collection,
    list_documents,
    get_document_chunks,
    delete_document,
)
from models.schemas import (
    CollectionCreate,
    CollectionsListResponse,
    CollectionResponse,
    DocumentsListResponse,
    DocumentResponse,
    DocumentChunksResponse,
    ChunkResponse,
    UploadResponse,
)
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="ChromaDB QA Preference API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include new routers
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(qa_records.router)
app.include_router(feedback.router)
app.include_router(preferences.router)
app.include_router(tags.router)


# Existing document management endpoints (keep backward compatibility)
@app.get("/api/v1/collections", response_model=CollectionsListResponse)
def get_collections():
    collections = list_collections()
    return {
        "collections": [
            CollectionResponse(name=c["name"], count=c["count"])
            for c in collections
        ]
    }


@app.post("/api/v1/collections")
def post_collection(body: CollectionCreate):
    try:
        create_collection(body.name)
        return {"message": "集合创建成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/collections/{collection_name}")
def del_collection(collection_name: str):
    try:
        delete_collection(collection_name)
        return {"message": "集合删除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/collections/{collection_name}/documents", response_model=DocumentsListResponse)
def get_documents(collection_name: str):
    result = list_documents(collection_name)
    return DocumentsListResponse(
        collection_name=result["collection_name"],
        documents=[
            DocumentResponse(
                id=d["id"],
                source=d["source"],
                chunk_count=d["chunk_count"],
                created_at=d.get("created_at"),
            )
            for d in result["documents"]
        ],
    )


@app.get("/api/v1/documents/{document_id}/chunks", response_model=DocumentChunksResponse)
def get_chunks(document_id: str):
    try:
        result = get_document_chunks(document_id)
        return DocumentChunksResponse(
            document_id=result["document_id"],
            document_name=result["document_name"],
            chunks=[
                ChunkResponse(
                    chunk_id=c["chunk_id"],
                    index=c["index"],
                    content=c["content"],
                )
                for c in result["chunks"]
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/v1/documents/{document_id}")
def del_document(document_id: str):
    try:
        delete_document(document_id)
        return {"message": "文档删除成功"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/upload")
def upload_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    chunk_size: int = Form(1000),
):
    try:
        validate_file(file.filename, file.size if hasattr(file, "size") else 0)
        result = process_file(file, collection_name, chunk_size)
        return UploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
