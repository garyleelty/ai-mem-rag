import chromadb
from chromadb.config import Settings
from typing import List, Optional
from datetime import datetime
import json

from core.vector_store import VectorStore
from api.models.memory import MemoryUnit
from config.settings import settings


class ChromaAdapter(VectorStore):
    def __init__(self, collection_name: str = "ai-memory-rag"):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)
    
    def add_memory(self, memory: MemoryUnit, embedding: List[float]) -> str:
        metadata = {
            "content": memory.content,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "version": memory.version,
            "tags": json.dumps(memory.tags) if memory.tags else "[]",
            **memory.metadata
        }
        
        self.collection.add(
            ids=[memory.id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[memory.content]
        )
        return memory.id
    
    def search(self, query_embedding: List[float], limit: int = 10, threshold: Optional[float] = None) -> List[tuple]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["metadatas", "distances"]
        )
        
        if not results["ids"][0]:
            return []
        
        memory_ids = results["ids"][0]
        distances = results["distances"][0]
        
        search_results = []
        for mem_id, dist in zip(memory_ids, distances):
            score = 1.0 - dist
            if threshold is None or score >= threshold:
                search_results.append((mem_id, score))
        
        return search_results
    
    def delete(self, memory_id: str) -> bool:
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception:
            return False
    
    def update(self, memory: MemoryUnit, embedding: List[float]) -> bool:
        metadata = {
            "content": memory.content,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "version": memory.version,
            "tags": json.dumps(memory.tags) if memory.tags else "[]",
            **memory.metadata
        }
        
        try:
            self.collection.update(
                ids=[memory.id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[memory.content]
            )
            return True
        except Exception:
            return False
    
    def get_memory(self, memory_id: str) -> Optional[MemoryUnit]:
        results = self.collection.get(
            ids=[memory_id],
            include=["metadatas", "documents", "embeddings"]
        )
        
        if not results["ids"]:
            return None
        
        metadata = results["metadatas"][0]
        return MemoryUnit(
            id=results["ids"][0],
            content=results["documents"][0],
            metadata={k: v for k, v in metadata.items() 
                     if k not in ["content", "created_at", "updated_at", "version", "tags"]},
            tags=json.loads(metadata.get("tags", "[]")),
            created_at=datetime.fromisoformat(metadata["created_at"]),
            updated_at=datetime.fromisoformat(metadata["updated_at"]),
            version=metadata["version"],
            embedding=results["embeddings"][0] if results.get("embeddings") else None
        )
    
    def list_memories(self, limit: int = 100, offset: int = 0) -> List[MemoryUnit]:
        results = self.collection.get(
            limit=limit,
            offset=offset,
            include=["metadatas", "documents", "embeddings"]
        )
        
        memories = []
        for idx, mem_id in enumerate(results["ids"]):
            metadata = results["metadatas"][idx]
            memories.append(MemoryUnit(
                id=mem_id,
                content=results["documents"][idx],
                metadata={k: v for k, v in metadata.items() 
                         if k not in ["content", "created_at", "updated_at", "version", "tags"]},
                tags=json.loads(metadata.get("tags", "[]")),
                created_at=datetime.fromisoformat(metadata["created_at"]),
                updated_at=datetime.fromisoformat(metadata["updated_at"]),
                version=metadata["version"],
                embedding=results["embeddings"][idx] if results.get("embeddings") else None
            ))
        
        return memories
    
    def delete_all(self) -> None:
        self.collection.delete(ids=self.collection.get()["ids"])
