import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.relational_store import RelationalStore
from api.models.memory import MemoryRelation, RelationType


class SQLiteAdapter(RelationalStore):
    def __init__(self, db_path: str = "./ai-memory-rag.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_metadata (
                    memory_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    updated_at TEXT,
                    version INTEGER,
                    metadata_json TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id TEXT,
                    version INTEGER,
                    content TEXT,
                    created_at TEXT,
                    FOREIGN KEY (memory_id) REFERENCES memory_metadata (memory_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_relations (
                    relation_id TEXT PRIMARY KEY,
                    source_id TEXT,
                    target_id TEXT,
                    relation_type TEXT,
                    confidence REAL,
                    created_at TEXT,
                    FOREIGN KEY (source_id) REFERENCES memory_metadata (memory_id),
                    FOREIGN KEY (target_id) REFERENCES memory_metadata (memory_id)
                )
            ''')
            
            conn.commit()
    
    def save_memory_metadata(self, memory) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO memory_metadata 
                (memory_id, created_at, updated_at, version, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                memory.id,
                memory.created_at.isoformat(),
                memory.updated_at.isoformat(),
                memory.version,
                json.dumps(memory.metadata)
            ))
            conn.commit()
    
    def get_memory_metadata(self, memory_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT metadata_json FROM memory_metadata WHERE memory_id = ?
            ''', (memory_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
    
    def update_memory_metadata(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT metadata_json, updated_at FROM memory_metadata WHERE memory_id = ?
            ''', (memory_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            metadata = json.loads(row[0])
            for key, value in updates.items():
                if key != "metadata":
                    continue
                metadata.update(value)
            
            cursor.execute('''
                UPDATE memory_metadata 
                SET metadata_json = ?, updated_at = ? 
                WHERE memory_id = ?
            ''', (json.dumps(metadata), datetime.utcnow().isoformat(), memory_id))
            conn.commit()
            return True
    
    def delete_memory_metadata(self, memory_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM memory_relations WHERE source_id = ? OR target_id = ?', 
                         (memory_id, memory_id))
            cursor.execute('DELETE FROM memory_versions WHERE memory_id = ?', (memory_id,))
            cursor.execute('DELETE FROM memory_metadata WHERE memory_id = ?', (memory_id,))
            conn.commit()
            return True
    
    def record_version(self, memory_id: str, version: int, content: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memory_versions (memory_id, version, content, created_at)
                VALUES (?, ?, ?, ?)
            ''', (memory_id, version, content, datetime.utcnow().isoformat()))
            conn.commit()
    
    def get_memory_versions(self, memory_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT version, content, created_at 
                FROM memory_versions 
                WHERE memory_id = ? 
                ORDER BY version DESC
            ''', (memory_id,))
            rows = cursor.fetchall()
            return [{
                "version": row[0],
                "content": row[1],
                "created_at": row[2]
            } for row in rows]
    
    def add_relation(self, relation: MemoryRelation) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memory_relations 
                (relation_id, source_id, target_id, relation_type, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                relation.id,
                relation.source_id,
                relation.target_id,
                relation.relation_type.value,
                relation.confidence,
                relation.created_at.isoformat()
            ))
            conn.commit()
            return relation.id
    
    def get_relations(self, memory_id: str) -> List[MemoryRelation]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT relation_id, source_id, target_id, relation_type, confidence, created_at
                FROM memory_relations 
                WHERE source_id = ? OR target_id = ?
            ''', (memory_id, memory_id))
            rows = cursor.fetchall()
            
            relations = []
            for row in rows:
                relations.append(MemoryRelation(
                    id=row[0],
                    source_id=row[1],
                    target_id=row[2],
                    relation_type=RelationType(row[3]),
                    confidence=row[4],
                    created_at=datetime.fromisoformat(row[5])
                ))
            return relations
    
    def delete_relation(self, relation_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM memory_relations WHERE relation_id = ?', (relation_id,))
            conn.commit()
            return cursor.rowcount > 0
