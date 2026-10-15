import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks

from auth import get_current_user
from models.db_models import User
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
from services.document import validate_file, process_file
from services.chroma import (
    list_collections,
    create_collection,
    delete_collection,
    list_documents,
    get_document_chunks,
    delete_document,
)

_upload_tasks = {}

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.get("/collections", response_model=CollectionsListResponse)
def get_collections(current_user: User = Depends(get_current_user)):
    collections = list_collections()
    return {
        "collections": [
            CollectionResponse(name=c["name"], count=c["count"])
            for c in collections
        ]
    }


@router.post("/collections")
def post_collection(
    body: CollectionCreate,
    current_user: User = Depends(get_current_user),
):
    try:
        create_collection(body.name)
        return {"message": "集合创建成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/collections/{collection_name}")
def del_collection(
    collection_name: str,
    current_user: User = Depends(get_current_user),
):
    try:
        delete_collection(collection_name)
        return {"message": "集合删除成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/collections/{collection_name}/documents", response_model=DocumentsListResponse)
def get_documents(
    collection_name: str,
    current_user: User = Depends(get_current_user),
):
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


@router.get("/documents/{document_id}/chunks", response_model=DocumentChunksResponse)
def get_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
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


@router.delete("/documents/{document_id}")
def del_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        delete_document(document_id)
        return {"message": "文档删除成功"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/upload")
def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    chunk_size: int = Form(1000),
    current_user: User = Depends(get_current_user),
):
    try:
        validate_file(file.filename, file.size if hasattr(file, "size") else 0)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    task_id = str(uuid.uuid4())[:8]
    _upload_tasks[task_id] = {"status": "processing", "filename": file.filename, "task_id": task_id}

    def _process():
        try:
            result = process_file(file, collection_name, chunk_size)
            _upload_tasks[task_id] = {"status": "completed", **result}
        except Exception as e:
            _upload_tasks[task_id] = {"status": "failed", "error": str(e), "filename": file.filename, "task_id": task_id}

    background_tasks.add_task(_process)
    return {"task_id": task_id, "status": "processing", "filename": file.filename}


@router.get("/upload/status/{task_id}")
def get_upload_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    return _upload_tasks.get(task_id, {"status": "not_found"})
