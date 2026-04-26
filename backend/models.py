from pydantic import BaseModel
from typing import Optional

class CollectionCreate(BaseModel):
    name: str

class CollectionResponse(BaseModel):
    name: str
    count: int

class CollectionsListResponse(BaseModel):
    collections: list[CollectionResponse]

class DocumentResponse(BaseModel):
    id: str
    source: str
    chunk_count: int
    created_at: Optional[str] = None

class DocumentsListResponse(BaseModel):
    collection_name: str
    documents: list[DocumentResponse]

class ChunkResponse(BaseModel):
    chunk_id: str
    index: int
    content: str

class DocumentChunksResponse(BaseModel):
    document_id: str
    document_name: str
    chunks: list[ChunkResponse]

class UploadResponse(BaseModel):
    document_id: str
    filename: str
    collection_name: str
    chunk_count: int
    status: str = "completed"
