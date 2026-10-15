from datetime import datetime

from services.chroma import get_chroma_client
from services.embedding import get_embedding_model

QA_COLLECTION_NAME = "qa_records"


def _ensure_qa_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=QA_COLLECTION_NAME)


def index_qa_record(record):
    collection = _ensure_qa_collection()
    text = f"{record.question}\n{record.answer}"
    try:
        embedding = get_embedding_model().encode([text])[0]
    except Exception:
        raise RuntimeError("Embedding model unavailable")
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


def delete_qa_index(record_id: int):
    collection = _ensure_qa_collection()
    doc_id = f"qa_{record_id}"
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass


def batch_index_qa_records(records: list):
    if not records:
        return
    texts = [f"{r.question}\n{r.answer}" for r in records]
    try:
        embeddings = get_embedding_model().encode(texts)
    except Exception:
        raise RuntimeError("Embedding model unavailable")
    collection = _ensure_qa_collection()
    ids = [f"qa_{r.id}" for r in records]
    metadatas = [{
        "source": "qa_record",
        "qa_id": str(r.id),
        "user_id": str(r.user_id),
        "conversation_id": str(r.conversation_id) if r.conversation_id else "",
        "question_preview": r.question[:100],
        "created_at": r.created_at.isoformat() if r.created_at else datetime.utcnow().isoformat(),
    } for r in records]
    collection.add(ids=ids, embeddings=embeddings.tolist(), documents=texts, metadatas=metadatas)


def search_qa(query: str, user_id: int, top_k: int = 10, conversation_id: int = None):
    collection = _ensure_qa_collection()
    try:
        embedding = get_embedding_model().encode([query])[0]
    except Exception:
        raise RuntimeError("Embedding model unavailable")

    where_filter = {"user_id": str(user_id)}
    if conversation_id:
        where_filter["conversation_id"] = str(conversation_id)

    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=top_k,
        where=where_filter,
        include=["metadatas", "distances"],
    )
    return results


def find_similar(record, user_id: int, top_k: int = 5):
    text = f"{record.question}\n{record.answer}"
    try:
        embedding = get_embedding_model().encode([text])[0]
    except Exception:
        raise RuntimeError("Embedding model unavailable")
    collection = _ensure_qa_collection()

    results = collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=top_k + 1,
        where={"user_id": str(user_id)},
        include=["metadatas", "distances"],
    )
    return results
