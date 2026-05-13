import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np

from api.models.memory import (
    MemoryUnit, MemoryUnitCreate, MemoryUnitUpdate,
    MemoryRelation, MemoryRelationCreate, SearchQuery, SearchResult
)
from core.vector_store import VectorStore
from core.relational_store import RelationalStore
from config.settings import settings


class MemoryEngine:
    def __init__(self, vector_store: VectorStore, relational_store: RelationalStore):
        self.vector_store = vector_store
        self.relational_store = relational_store
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    
    def _generate_embedding(self, text: str) -> List[float]:
        return self.embedding_model.encode(text).tolist()
    
    def create_memory(self, memory_create: MemoryUnitCreate) -> MemoryUnit:
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        embedding = self._generate_embedding(memory_create.content)
        
        memory = MemoryUnit(
            id=memory_id,
            content=memory_create.content,
            metadata=memory_create.metadata or {},
            tags=memory_create.tags or [],
            created_at=now,
            updated_at=now,
            version=1,
            embedding=embedding
        )
        
        self.vector_store.add_memory(memory, embedding)
        self.relational_store.save_memory_metadata(memory)
        self.relational_store.record_version(memory_id, 1, memory.content)
        
        return memory
    
    def get_memory(self, memory_id: str) -> Optional[MemoryUnit]:
        memory = self.vector_store.get_memory(memory_id)
        if memory:
            metadata = self.relational_store.get_memory_metadata(memory_id)
            if metadata:
                memory.metadata = {**memory.metadata, **metadata}
        return memory
    
    def list_memories(self, limit: int = 100, offset: int = 0) -> List[MemoryUnit]:
        return self.vector_store.list_memories(limit, offset)
    
    def update_memory(self, memory_id: str, memory_update: MemoryUnitUpdate) -> Optional[MemoryUnit]:
        existing_memory = self.vector_store.get_memory(memory_id)
        if not existing_memory:
            return None
        
        now = datetime.utcnow()
        
        updates = {}
        if memory_update.content is not None:
            existing_memory.content = memory_update.content
            existing_memory.embedding = self._generate_embedding(memory_update.content)
            updates["content"] = memory_update.content
        if memory_update.metadata is not None:
            existing_memory.metadata = {**existing_memory.metadata, **memory_update.metadata}
            updates["metadata"] = existing_memory.metadata
        if memory_update.tags is not None:
            existing_memory.tags = memory_update.tags
            updates["tags"] = memory_update.tags
        
        existing_memory.updated_at = now
        existing_memory.version += 1
        
        self.vector_store.update(existing_memory, existing_memory.embedding)
        self.relational_store.update_memory_metadata(memory_id, updates)
        self.relational_store.record_version(memory_id, existing_memory.version, existing_memory.content)
        
        return existing_memory
    
    def delete_memory(self, memory_id: str) -> bool:
        success = self.vector_store.delete(memory_id)
        if success:
            self.relational_store.delete_memory_metadata(memory_id)
        return success
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        query_embedding = self._generate_embedding(query.query)
        
        search_results = self.vector_store.search(
            query_embedding, 
            limit=query.limit, 
            threshold=query.threshold
        )
        
        results = []
        for memory_id, score in search_results:
            memory = self.vector_store.get_memory(memory_id)
            if memory:
                if query.tags and not any(tag in memory.tags for tag in query.tags):
                    continue
                results.append(SearchResult(memory=memory, score=score))
        
        return results
    
    def add_relation(self, relation_create: MemoryRelationCreate) -> MemoryRelation:
        relation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        relation = MemoryRelation(
            id=relation_id,
            source_id=relation_create.source_id,
            target_id=relation_create.target_id,
            relation_type=relation_create.relation_type,
            confidence=relation_create.confidence,
            created_at=now
        )
        
        self.relational_store.add_relation(relation)
        return relation
    
    def get_relations(self, memory_id: str) -> List[MemoryRelation]:
        return self.relational_store.get_relations(memory_id)
    
    def delete_relation(self, relation_id: str) -> bool:
        return self.relational_store.delete_relation(relation_id)
