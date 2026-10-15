from typing import Generator
from core.memory_engine import MemoryEngine
from adapters.factory import get_vector_store, get_relational_store


_memory_engine: MemoryEngine = None


def get_memory_engine() -> MemoryEngine:
    global _memory_engine
    if _memory_engine is None:
        vector_store = get_vector_store()
        relational_store = get_relational_store()
        _memory_engine = MemoryEngine(vector_store, relational_store)
    return _memory_engine
