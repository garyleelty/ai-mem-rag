from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class RelationType(str, Enum):
    ASSOCIATION = "association"
    INCLUSION = "inclusion"
    CAUSATION = "causation"
    REFERENCE = "reference"


class MemoryUnitBase(BaseModel):
    content: str = Field(..., description="记忆内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")


class MemoryUnitCreate(MemoryUnitBase):
    pass


class MemoryUnitUpdate(BaseModel):
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class MemoryUnit(MemoryUnitBase):
    id: str
    created_at: datetime
    updated_at: datetime
    version: int
    embedding: Optional[List[float]] = None
    
    class Config:
        from_attributes = True


class MemoryRelationBase(BaseModel):
    source_id: str
    target_id: str
    relation_type: RelationType
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度")


class MemoryRelationCreate(MemoryRelationBase):
    pass


class MemoryRelation(MemoryRelationBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=10, ge=1, le=100, description="返回结果数量")
    threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="相似度阈值")
    tags: Optional[List[str]] = Field(default=None, description="标签过滤")


class SearchResult(BaseModel):
    memory: MemoryUnit
    score: float = Field(description="相似度得分")
