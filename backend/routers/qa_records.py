import uuid
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models.db_models import User, Conversation, QARecord
from models.schemas import (
    QARecordCreate,
    QARecordResponse,
    QARecordListResponse,
    QAImportRequest,
    QAImportResponse,
    QASearchRequest,
    QASearchResponse,
    QASearchResult,
)
from services import get_embedding_model, get_chroma_client

router = APIRouter(prefix="/api/v1/qa", tags=["qa_records"])

QA_COLLECTION_NAME = "qa_records"


def _ensure_qa_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=QA_COLLECTION_NAME)


def _index_qa_record(record: QARecord):
    collection = _ensure_qa_collection()
    text = f"{record.question}\n{record.answer}"
    embedding = get_embedding_model().encode([text])[0]
    doc_id = f"qa_{record.id}"
    collection.add(
        ids=[doc_id],
        embeddings=[embedding.tolist()],
        documents=[text],
        metadatas=[{
            "source": "qa_record",
            "qa_id": str(record.id),
            "user_id": str(record.user_id),
            "conversation_id": str(record.conversation_id) if record.conversation_id else "",
            "question_preview": record.question[:100],
            "created_at": record.created_at.isoformat() if record.created_at else datetime.utcnow().isoformat(),
        }],
    )
    return doc_id


def _delete_qa_index(record_id: int):
    collection = _ensure_qa_collection()
    doc_id = f"qa_{record_id}"
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass


@router.post("/records", response_model=QARecordResponse)
def create_qa_record(
    body: QARecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == body.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    record = QARecord(
        conversation_id=body.conversation_id,
        user_id=current_user.id,
        question=body.question,
        answer=body.answer,
        model_name=body.model_name,
        temperature=body.temperature,
        tokens_used=body.tokens_used,
        latency_ms=body.latency_ms,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        chroma_doc_id = _index_qa_record(record)
        record.chroma_doc_id = chroma_doc_id
        db.commit()
    except Exception as e:
        pass

    return record


@router.get("/records", response_model=QARecordListResponse)
def list_qa_records(
    conversation_id: Optional[int] = None,
    keyword: Optional[str] = None,
    model_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(QARecord).filter(QARecord.user_id == current_user.id)

    if conversation_id:
        query = query.filter(QARecord.conversation_id == conversation_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (QARecord.question.ilike(like)) | (QARecord.answer.ilike(like))
        )
    if model_name:
        query = query.filter(QARecord.model_name == model_name)
    if date_from:
        query = query.filter(QARecord.created_at >= date_from)
    if date_to:
        query = query.filter(QARecord.created_at <= date_to)

    total = query.count()
    items = (
        query.order_by(QARecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return QARecordListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/records/{record_id}", response_model=QARecordResponse)
def get_qa_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(QARecord)
        .filter(QARecord.id == record_id, QARecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")
    return record


@router.delete("/records/{record_id}")
def delete_qa_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(QARecord)
        .filter(QARecord.id == record_id, QARecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")

    _delete_qa_index(record_id)
    db.delete(record)
    db.commit()
    return {"message": "QA record deleted"}


@router.post("/import", response_model=QAImportResponse)
def import_qa_records(
    body: QAImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    imported_ids = []
    fail_count = 0

    for item in body.items:
        try:
            conv = None
            if item.conversation_title:
                conv = (
                    db.query(Conversation)
                    .filter(
                        Conversation.user_id == current_user.id,
                        Conversation.title == item.conversation_title,
                    )
                    .first()
                )
                if not conv:
                    conv = Conversation(
                        user_id=current_user.id,
                        title=item.conversation_title,
                        source=body.source,
                    )
                    db.add(conv)
                    db.flush()

            record = QARecord(
                conversation_id=conv.id if conv else None,
                user_id=current_user.id,
                question=item.question,
                answer=item.answer,
                model_name=item.model_name,
                created_at=item.created_at or datetime.utcnow(),
            )
            db.add(record)
            db.flush()

            try:
                chroma_doc_id = _index_qa_record(record)
                record.chroma_doc_id = chroma_doc_id
            except Exception:
                pass

            imported_ids.append(record.id)
        except Exception:
            fail_count += 1

    db.commit()
    return QAImportResponse(
        success_count=len(imported_ids),
        fail_count=fail_count,
        imported_ids=imported_ids,
    )


@router.post("/search", response_model=QASearchResponse)
def search_qa_records(
    body: QASearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    collection = _ensure_qa_collection()
    embedding = get_embedding_model().encode([body.query])[0]

    where_filter = {"user_id": str(current_user.id)}
    if body.conversation_id:
        where_filter["conversation_id"] = str(body.conversation_id)

    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=body.top_k,
        where=where_filter,
        include=["metadatas", "distances"],
    )

    items = []
    if results and results.get("ids") and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 1.0
            qa_id = int(meta.get("qa_id", 0))
            record = db.query(QARecord).filter(QARecord.id == qa_id).first()
            if record:
                similarity = 1.0 - min(distance, 1.0)
                items.append(QASearchResult(
                    qa_record_id=record.id,
                    question=record.question,
                    answer=record.answer[:500],
                    similarity=round(similarity, 4),
                    created_at=record.created_at,
                ))

    items.sort(key=lambda x: x.similarity, reverse=True)
    return QASearchResponse(results=items)


@router.get("/similar/{record_id}", response_model=QASearchResponse)
def find_similar(
    record_id: int,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(QARecord)
        .filter(QARecord.id == record_id, QARecord.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="QA record not found")

    text = f"{record.question}\n{record.answer}"
    embedding = get_embedding_model().encode([text])[0]
    collection = _ensure_qa_collection()

    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=top_k + 1,
        where={"user_id": str(current_user.id)},
        include=["metadatas", "distances"],
    )

    items = []
    if results and results.get("ids") and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 1.0
            qa_id = int(meta.get("qa_id", 0))
            if qa_id == record_id:
                continue
            similar = db.query(QARecord).filter(QARecord.id == qa_id).first()
            if similar:
                similarity = 1.0 - min(distance, 1.0)
                items.append(QASearchResult(
                    qa_record_id=similar.id,
                    question=similar.question,
                    answer=similar.answer[:500],
                    similarity=round(similarity, 4),
                    created_at=similar.created_at,
                ))

    items.sort(key=lambda x: x.similarity, reverse=True)
    return QASearchResponse(results=items[:top_k])
