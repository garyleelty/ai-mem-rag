from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import CORS_ORIGINS
from models import (
    CollectionCreate,
    CollectionsListResponse,
    CollectionResponse,
    DocumentsListResponse,
    DocumentResponse,
    DocumentChunksResponse,
    ChunkResponse,
    UploadResponse,
)
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

app = FastAPI(title="ChromaDB UI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/v1/documents/{document_id}")
def del_document(document_id: str):
    try:
        delete_document(document_id)
        return {"message": "文档删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/upload", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    chunk_size: int = Form(1000),
):
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        validate_file(file.filename, file_size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = process_file(file, collection_name, chunk_size)
        return UploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
