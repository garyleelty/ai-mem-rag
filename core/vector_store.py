from abc import ABC, abstractmethod
from typing import List, Optional
from api.models.memory import MemoryUnit


class VectorStore(ABC):
    @abstractmethod
    def add_memory(self, memory: MemoryUnit, embedding: List[float]) -> str:
        """添加记忆单元，返回ID"""
    
    @abstractmethod
    def search(self, query_embedding: List[float], limit: int = 10, threshold: Optional[float] = None) -> List[tuple]:
        """语义搜索，返回(记忆ID, 相似度得分)列表"""
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """删除指定记忆单元"""
    
    @abstractmethod
    def update(self, memory: MemoryUnit, embedding: List[float]) -> bool:
        """更新记忆单元"""
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[MemoryUnit]:
        """获取单个记忆单元"""
    
    @abstractmethod
    def list_memories(self, limit: int = 100, offset: int = 0) -> List[MemoryUnit]:
        """列出记忆单元"""
    
    @abstractmethod
    def delete_all(self) -> None:
        """删除所有记忆"""
