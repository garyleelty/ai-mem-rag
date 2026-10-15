from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from api.models.memory import MemoryUnit, MemoryRelation
from datetime import datetime


class RelationalStore(ABC):
    @abstractmethod
    def save_memory_metadata(self, memory: MemoryUnit) -> None:
        """保存记忆元数据"""
    
    @abstractmethod
    def get_memory_metadata(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取记忆元数据"""
    
    @abstractmethod
    def update_memory_metadata(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆元数据"""
    
    @abstractmethod
    def delete_memory_metadata(self, memory_id: str) -> bool:
        """删除记忆元数据"""
    
    @abstractmethod
    def record_version(self, memory_id: str, version: int, content: str) -> None:
        """记录版本变更"""
    
    @abstractmethod
    def get_memory_versions(self, memory_id: str) -> List[Dict[str, Any]]:
        """获取记忆的所有版本"""
    
    @abstractmethod
    def add_relation(self, relation: MemoryRelation) -> str:
        """添加记忆关系"""
    
    @abstractmethod
    def get_relations(self, memory_id: str) -> List[MemoryRelation]:
        """获取记忆的所有关系"""
    
    @abstractmethod
    def delete_relation(self, relation_id: str) -> bool:
        """删除记忆关系"""
