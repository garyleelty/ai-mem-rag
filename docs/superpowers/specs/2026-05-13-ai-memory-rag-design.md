# MemoryLake 设计文档

## 项目概述

MemoryLake 是一个集个人知识管理与 Agent 调用于一体的认知记忆系统。它模拟人脑对记忆进行智能组织、计算、演化，提供持久、连贯、可追溯的长期记忆能力。

### 核心定位
- **个人知识管理工具**：用户导入文档、笔记、聊天记录等，系统帮助整理、关联和检索长期记忆
- **Agent 长期记忆服务**：提供标准化 API/MCP 接口，供外部 Agent 调用，实现记忆存储和检索

---

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI Layer                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Streamlit UI   │  │   API Gateway   │  │    MCP Server   │ │
│  │  (可视化界面)    │  │  (REST/WebSocket)│  │  (Agent调用接口)│ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
┌───────────▼────────────────────▼────────────────────▼───────────┐
│                      Business Logic Layer                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Memory Engine (记忆引擎)                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │ 语义检索 │  │ 知识图谱 │  │ 时间线   │  │ 版本控制 │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────┘
                               │
┌───────────────────────────────▼─────────────────────────────────┐
│                       Storage Layer                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    统一抽象层                              │  │
│  │  ┌─────────────┐          ┌─────────────┐                 │  │
│  │  │ VectorStore │          │ Relational  │                 │  │
│  │  │  (向量存储)   │          │   Store    │                 │  │
│  │  │ Chroma/Pinecone│       │ SQLite/PG  │                 │  │
│  │  └─────────────┘          └─────────────┘                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心组件设计

### 1. Memory Engine（记忆引擎）

| 组件 | 职责 | 关键特性 |
|------|------|----------|
| **语义检索** | 向量相似度匹配 | 支持多模态检索、自定义阈值 |
| **知识图谱** | 概念关联网络构建 | 动态更新、多跳推理 |
| **时间线** | 记忆演化追踪 | 版本回溯、冲突合并 |
| **版本控制** | 记忆版本管理 | 血缘追溯、自动淘汰 |

### 2. Storage Abstraction（存储抽象层）

#### VectorStore 接口
```python
class VectorStore(ABC):
    @abstractmethod
    def add_memory(self, memory: MemoryUnit) -> str:
        """添加记忆单元，返回ID"""
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[MemoryUnit]:
        """语义搜索，返回匹配的记忆单元"""
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """删除指定记忆单元"""
    
    @abstractmethod
    def update(self, memory: MemoryUnit) -> bool:
        """更新记忆单元"""
```

#### RelationalStore 接口
```python
class RelationalStore(ABC):
    @abstractmethod
    def create_user(self, user: User) -> str:
        """创建用户"""
    
    @abstractmethod
    def get_memory_metadata(self, memory_id: str) -> dict:
        """获取记忆元数据"""
    
    @abstractmethod
    def record_version(self, memory_id: str, version: int):
        """记录版本变更"""
```

---

## 数据模型设计

### MemoryUnit（记忆单元）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 唯一标识 |
| `content` | Text | 记忆内容 |
| `embedding` | Vector | 向量表示 |
| `metadata` | JSON | 元数据（来源、时间、标签等） |
| `created_at` | Datetime | 创建时间 |
| `updated_at` | Datetime | 更新时间 |
| `version` | Int | 版本号 |

### MemoryRelation（记忆关系）

| 字段 | 类型 | 说明 |
|------|------|------|
| `source_id` | UUID | 源记忆ID |
| `target_id` | UUID | 目标记忆ID |
| `relation_type` | Enum | 关系类型（关联、包含、因果等） |
| `confidence` | Float | 置信度 |

---

## API 设计

### REST API Endpoints

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/memories` | 创建记忆单元 |
| GET | `/api/memories` | 获取记忆列表 |
| GET | `/api/memories/{id}` | 获取单个记忆 |
| PUT | `/api/memories/{id}` | 更新记忆单元 |
| DELETE | `/api/memories/{id}` | 删除记忆单元 |
| POST | `/api/search` | 语义检索 |
| GET | `/api/timeline` | 获取时间线 |
| GET | `/api/graph` | 获取知识图谱 |

### MCP 接口

| 操作 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `add_memory` | content, metadata | memory_id | 添加记忆 |
| `search_memory` | query, limit | List[MemoryUnit] | 搜索记忆 |
| `update_memory` | memory_id, content | success | 更新记忆 |
| `delete_memory` | memory_id | success | 删除记忆 |
| `get_timeline` | memory_id | Timeline | 获取时间线 |

---

## UI 设计（Streamlit）

### 页面结构

| 页面 | 功能 | 核心组件 |
|------|------|----------|
| **首页** | 记忆概览 | 统计卡片、快速搜索 |
| **记忆管理** | CRUD操作 | 表单、列表、编辑器 |
| **语义搜索** | 搜索界面 | 搜索框、结果列表、相似度展示 |
| **知识图谱** | 可视化 | 图谱图、节点关系 |
| **时间线** | 演化追踪 | 时间轴、版本对比 |

---

## 项目目录结构

```
ai-mem-rag/
├── api/                    # FastAPI 后端
│   ├── main.py             # API 入口
│   ├── routes/             # 路由定义
│   ├── models/             # Pydantic 模型
│   └── services/           # 业务逻辑
├── ui/                     # Streamlit 前端
│   ├── main.py             # UI 入口
│   ├── pages/              # 页面组件
│   └── components/         # 可复用组件
├── core/                   # 核心引擎
│   ├── memory_engine.py    # 记忆引擎
│   ├── vector_store.py     # 向量存储抽象
│   └── relational_store.py # 关系存储抽象
├── adapters/               # 存储适配器
│   ├── chroma_adapter.py   # Chroma 实现
│   ├── pinecone_adapter.py # Pinecone 实现
│   └── sqlite_adapter.py   # SQLite 实现
├── mcp/                    # MCP Server
│   ├── main.py             # MCP 入口
│   └── handlers.py         # 操作处理器
├── config/                 # 配置文件
│   └── settings.py         # 可配置数据库等
└── requirements.txt        # 依赖清单
```

---

## 配置设计

`config/settings.py` 支持通过环境变量或配置文件切换数据库：

```python
class Settings:
    # 向量数据库配置
    VECTOR_STORE_TYPE: str = "chroma"  # chroma | pinecone
    CHROMA_PATH: str = "./chroma_db"
    PINECONE_API_KEY: Optional[str] = None
    
    # 关系数据库配置
    RELATIONAL_STORE_TYPE: str = "sqlite"  # sqlite | postgresql
    DATABASE_URL: str = "sqlite:///./ai-memory-rag.db"
```

---

## 技术栈

- **后端框架**：FastAPI
- **前端框架**：Streamlit
- **向量数据库**：Chroma（默认），支持 Pinecone
- **关系数据库**：SQLite（默认），支持 PostgreSQL
- **MCP**：符合 Model Context Protocol 标准的接口

---

## 开发阶段规划

1. **MVP 阶段**：
   - 基础记忆 CRUD
   - 语义检索
   - REST API
   - Streamlit UI

2. **进阶阶段**：
   - 知识图谱可视化
   - 时间线和版本控制
   - MCP 接口

3. **优化阶段**：
   - 性能优化
   - 插件系统
   - 多 Agent 协作

