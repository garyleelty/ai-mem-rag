from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.models.memory import (
    MemoryUnit, MemoryUnitCreate, MemoryUnitUpdate,
    MemoryRelation, MemoryRelationCreate, SearchQuery, SearchResult
)
from core.memory_engine import MemoryEngine
from api.services.dependencies import get_memory_engine

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.post("", response_model=MemoryUnit, status_code=status.HTTP_201_CREATED)
def create_memory(
    memory: MemoryUnitCreate,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    return engine.create_memory(memory)


@router.get("", response_model=List[MemoryUnit])
def list_memories(
    limit: int = 100,
    offset: int = 0,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    return engine.list_memories(limit, offset)


@router.get("/{memory_id}", response_model=MemoryUnit)
def get_memory(
    memory_id: str,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    memory = engine.get_memory(memory_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return memory


@router.put("/{memory_id}", response_model=MemoryUnit)
def update_memory(
    memory_id: str,
    memory_update: MemoryUnitUpdate,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    memory = engine.update_memory(memory_id, memory_update)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: str,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    success = engine.delete_memory(memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )


@router.post("/search", response_model=List[SearchResult])
def search_memories(
    query: SearchQuery,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    return engine.search(query)


@router.post("/relations", response_model=MemoryRelation, status_code=status.HTTP_201_CREATED)
def add_relation(
    relation: MemoryRelationCreate,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    return engine.add_relation(relation)


@router.get("/{memory_id}/relations", response_model=List[MemoryRelation])
def get_relations(
    memory_id: str,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    return engine.get_relations(memory_id)


@router.delete("/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relation(
    relation_id: str,
    engine: MemoryEngine = Depends(get_memory_engine)
):
    success = engine.delete_relation(relation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relation not found"
        )
