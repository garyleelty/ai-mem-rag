from config.settings import settings
from core.vector_store import VectorStore
from core.relational_store import RelationalStore


def get_vector_store() -> VectorStore:
    store_type = settings.VECTOR_STORE_TYPE.lower()
    
    if store_type == "chroma":
        from adapters.chroma_adapter import ChromaAdapter
        return ChromaAdapter()
    elif store_type == "pinecone":
        from adapters.pinecone_adapter import PineconeAdapter
        return PineconeAdapter()
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")


def get_relational_store() -> RelationalStore:
    store_type = settings.RELATIONAL_STORE_TYPE.lower()
    
    if store_type == "sqlite":
        from adapters.sqlite_adapter import SQLiteAdapter
        return SQLiteAdapter(settings.DATABASE_URL.replace("sqlite:///./", ""))
    elif store_type == "postgresql":
        raise NotImplementedError("PostgreSQL adapter not yet implemented")
    else:
        raise ValueError(f"Unsupported relational store type: {store_type}")
