from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Document schemas (existing)
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


# Auth schemas
class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: Optional[str] = None
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Conversation schemas
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    source: str = "api"
    model_name: Optional[str] = None
    metadata_json: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    model_name: Optional[str] = None
    metadata_json: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    source: str
    model_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    qa_records: List["QARecordResponse"] = []


# QA Record schemas
class QARecordCreate(BaseModel):
    conversation_id: Optional[int] = None
    question: str
    answer: str
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None


class QARecordResponse(BaseModel):
    id: int
    conversation_id: Optional[int]
    user_id: int
    question: str
    answer: str
    model_name: Optional[str]
    temperature: Optional[float]
    tokens_used: Optional[int]
    latency_ms: Optional[int]
    sequence_order: int
    chroma_doc_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class QARecordListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[QARecordResponse]


class QAImportItem(BaseModel):
    question: str
    answer: str
    model_name: Optional[str] = None
    conversation_title: Optional[str] = None
    created_at: Optional[datetime] = None


class QAImportRequest(BaseModel):
    items: List[QAImportItem]
    source: str = "import"


class QAImportResponse(BaseModel):
    success_count: int
    fail_count: int
    imported_ids: List[int]


# Search schemas
class QASearchRequest(BaseModel):
    query: str
    top_k: int = 10
    conversation_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class QASearchResult(BaseModel):
    qa_record_id: int
    question: str
    answer: str
    similarity: float
    created_at: datetime


class QASearchResponse(BaseModel):
    results: List[QASearchResult]


# Feedback schemas
class FeedbackCreate(BaseModel):
    feedback_type: str = Field(pattern=r"^(thumbs_up|thumbs_down|modified)$")
    modified_answer: Optional[str] = None
    preset_tags: Optional[List[str]] = None
    custom_tags: Optional[List[str]] = None
    comment: Optional[str] = None


class FeedbackUpdate(BaseModel):
    feedback_type: Optional[str] = None
    modified_answer: Optional[str] = None
    preset_tags: Optional[List[str]] = None
    custom_tags: Optional[List[str]] = None
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    qa_record_id: int
    user_id: int
    feedback_type: str
    modified_answer: Optional[str]
    preset_tags: Optional[str]
    custom_tags: Optional[str]
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Preference schemas
class PreferenceUpdate(BaseModel):
    preferred_style: Optional[str] = None
    preferred_language: Optional[str] = None
    domain_interests: Optional[List[str]] = None
    custom_prompt: Optional[str] = None
    auto_summary: Optional[bool] = None


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    preferred_style: str
    preferred_language: str
    domain_interests: Optional[str]
    custom_prompt: Optional[str]
    auto_summary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Preset Tag schemas
class PresetTagResponse(BaseModel):
    id: int
    name: str
    label: str
    color: str
    category: str

    class Config:
        from_attributes = True


class PresetTagCreate(BaseModel):
    name: str
    label: str
    color: Optional[str] = "#3b82f6"
    category: Optional[str] = "general"
