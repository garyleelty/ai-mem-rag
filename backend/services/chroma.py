import chromadb
from config import CHROMA_DIR

_chroma_client = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma_client


def list_collections():
    client = get_chroma_client()
    collections = client.list_collections()
    result = []
    for col in collections:
        count = col.count()
        result.append({"name": col.name, "count": count})
    return result


def create_collection(name: str):
    client = get_chroma_client()
    client.create_collection(name=name)


def delete_collection(name: str):
    client = get_chroma_client()
    client.delete_collection(name=name)


def list_documents(collection_name: str):
    client = get_chroma_client()
    try:
        collection = client.get_collection(name=collection_name)
    except Exception:
        return {"collection_name": collection_name, "documents": []}

    all_data = collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas") or []

    docs_map = {}
    for meta in metadatas:
        if not meta:
            continue
        doc_id = meta.get("doc_id")
        if not doc_id:
            continue
        if doc_id not in docs_map:
            docs_map[doc_id] = {
                "id": doc_id,
                "source": meta.get("source", "unknown"),
                "chunk_count": meta.get("total_chunks", 0),
                "created_at": meta.get("created_at"),
            }

    documents = list(docs_map.values())
    documents.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return {"collection_name": collection_name, "documents": documents}


def get_document_chunks(document_id: str):
    client = get_chroma_client()
    collections = client.list_collections()

    target_collection = None
    for col in collections:
        try:
            result = col.get(
                where={"doc_id": document_id},
                include=["metadatas"],
                limit=1,
            )
            if result and result.get("ids"):
                target_collection = col
                break
        except Exception:
            continue

    if target_collection is None:
        raise ValueError(f"文档不存在: {document_id}")

    result = target_collection.get(
        where={"doc_id": document_id},
        include=["documents", "metadatas"],
    )
    docs = result.get("documents") or []
    metas = result.get("metadatas") or []
    ids = result.get("ids") or []

    chunks = []
    for i, chunk_id in enumerate(ids):
        meta = metas[i] if i < len(metas) else {}
        chunks.append({
            "chunk_id": chunk_id,
            "index": meta.get("chunk_index", i),
            "content": docs[i] if i < len(docs) else "",
        })
    chunks.sort(key=lambda x: x["index"])

    source = metas[0].get("source", "unknown") if metas else "unknown"
    return {
        "document_id": document_id,
        "document_name": source,
        "chunks": chunks,
    }


def delete_document(document_id: str):
    client = get_chroma_client()
    collections = client.list_collections()

    target_collection = None
    for col in collections:
        try:
            result = col.get(where={"doc_id": document_id}, limit=1)
            if result and result.get("ids"):
                target_collection = col
                break
        except Exception:
            continue

    if target_collection is None:
        raise ValueError(f"文档不存在: {document_id}")

    result = target_collection.get(where={"doc_id": document_id})
    target_collection.delete(ids=result["ids"])
    return True
