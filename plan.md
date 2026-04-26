# ChromaDB UI - MVP 架构设计文档

> 版本：v1.0 MVP（最小可用版本）  
> 前端：纯 HTML + CSS + JS（零构建）  
> 后端：Python FastAPI  
> 设计目标：拖拽上传文档 → 向量化存入 ChromaDB → 浏览/删除文档

---

## 1. 项目目录结构（精简后）

```
chromadb-rag/
├── frontend/                    # 前端（3个文件）
│   ├── index.html               # 主页面（结构 + CDN引用）
│   ├── css/
│   │   └── style.css            # 自定义样式
│   └── js/
│       └── app.js               # 全部业务逻辑
│
├── backend/                     # 后端 FastAPI
│   ├── main.py                  # 应用入口 + 路由
│   ├── services.py              # 核心服务（解析/切割/向量化/ChromaDB）
│   ├── models.py                # Pydantic 模型
│   ├── config.py                # 配置读取
│   └── requirements.txt
│
├── data/
│   ├── uploads/                 # 上传文件临时存储
│   └── chroma_storage/          # ChromaDB 持久化存储
│
├── .env.example
├── .gitignore
└── plan.md                      # 本文档
```

> **MVP 精简说明**：
> - 所有路由集中到 `main.py`（MVP 阶段不拆分 api/ 目录）
> - 所有服务集中到 `services.py`（不拆分 parser/splitter/embedding）
> - 不引入 LangChain，直接用 `sentence-transformers` + 简单文本切割
> - 不引入任务队列，上传接口同步处理

---

## 2. 技术栈选型

### 2.1 前端
| 技术 | 来源 | 用途 |
|------|------|------|
| HTML5 | 原生 | 页面结构 |
| CSS3 | 原生 + Pico.css（CDN） | 样式 |
| JavaScript ES6+ | 原生 | 业务逻辑 |

### 2.2 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.11 | 运行环境 |
| FastAPI | ≥0.112 | Web 框架 |
| ChromaDB | ≥0.5 | 向量数据库 |
| Sentence Transformers | ≥3.0 | 本地 Embedding 模型 |
| Uvicorn | ≥0.30 | ASGI 服务器 |
| PyPDF2 | ≥3.0 | PDF 文本提取 |
| python-docx | ≥1.1 | Word 文本提取 |
| python-dotenv | ≥1.0 | 环境变量管理 |

> **MVP 移除**：OpenAI SDK、LangChain、LangChain Community、异步任务队列

---

## 3. 前端页面设计（单页面）

### 3.1 整体布局

```
┌──────────────────────────────────────────────────────────────┐
│  🗄️ ChromaDB 文档管理器                                      │
├─────────────┬────────────────────┬───────────────────────────┤
│ 📁 配置面板  │   📤 上传区域      │   📚 文档浏览面板         │
│             │                    │                          │
│ 目标集合:    │  ┌──────────────┐ │ 集合: [技术文档库 ▾]     │
│ [选择框 ▾]   │  │              │ │ ─────────────────────    │
│ [+ 新建]    │  │  拖拽文件到   │ │ ┌─────────────────────┐ │
│             │  │  此处        │ │ │ 📄 report.pdf       │ │
│ 分块大小:    │  │              │ │ │   1.2MB · 45块      │ │
│ [1000 ▾]    │  │  PDF / DOCX  │ │ │   [删除]           │ │
│             │  │              │ │ ├─────────────────────┤ │
│ [🚀 上传]   │  └──────────────┘ │ │ 📄 manual.docx     │ │
│             │                  │ │   856KB · 32块     │ │
│             │  或点击选择文件:    │ │   [删除]           │ │
│             │  [📁 选择文件]     │ │─────────────────────  │
│             │                  │ │ 共 8 个文档           │
│             │                  │ │                       │
└─────────────┴────────────────────┴───────────────────────────┘
│  📋 文档内容预览（点击文档后展开）                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 文档: report.pdf | 总块数: 45                          │  │
│  │ ──────────────────────────────────────────────────── │  │
│  │ [块 #1] 这是文档的第一段内容...                        │  │
│  │ [块 #2] 第二章介绍了系统架构设计...                    │  │
│  │ ...                                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 核心交互（MVP 简化版）

- **左侧配置面板**：选择/创建集合、设置分块大小（固定几种选项）
- **中间拖拽区**：支持多文件上传，显示上传+处理状态（同步等待，显示 spinner）
- **右侧文档列表**：切换集合查看文档，支持删除单个文档
- **底部预览区**：点击文档显示所有分块内容

> **MVP 移除**：embedding 模型切换、切割方式选择、重叠大小配置、批量删除、上传进度条、localStorage 持久化

---

## 4. 后端 API 接口设计

### 4.1 基础信息
- **Base URL**: `http://localhost:8000/api/v1`
- **认证**: 无（开发阶段）

### 4.2 接口列表

#### 4.2.1 集合管理

**GET /collections** – 获取所有集合

响应：
```json
{
  "collections": [
    {
      "name": "技术文档库",
      "count": 42
    }
  ]
}
```

**POST /collections** – 创建集合

请求：
```json
{
  "name": "新集合"
}
```

**DELETE /collections/{collection_name}** – 删除集合

#### 4.2.2 文档管理

**GET /collections/{collection_name}/documents** – 获取文档列表

响应：
```json
{
  "collection_name": "技术文档库",
  "documents": [
    {
      "id": "doc-001",
      "source": "report.pdf",
      "chunk_count": 45,
      "created_at": "2024-01-01T10:00:00"
    }
  ]
}
```

> **实现说明**：ChromaDB 不原生支持"文档"概念。MVP 通过在 metadata 中存储 `source` 字段，查询时按 `source` 分组聚合来模拟文档列表。

**GET /documents/{document_id}/chunks** – 获取文档分块内容

响应：
```json
{
  "document_id": "doc-001",
  "document_name": "report.pdf",
  "chunks": [
    {
      "chunk_id": "chunk-001",
      "index": 0,
      "content": "文本内容..."
    }
  ]
}
```

**DELETE /documents/{document_id}** – 删除单个文档（删除该文档的所有 chunks）

#### 4.2.3 文件上传与处理

**POST /upload** – 上传文档并同步处理

请求：`multipart/form-data`
字段：
- `file` (文件)
- `collection_name` (string)
- `chunk_size` (int, 可选, 默认 1000)

响应（200，同步完成）：
```json
{
  "document_id": "doc-001",
  "filename": "report.pdf",
  "collection_name": "技术文档库",
  "chunk_count": 45,
  "status": "completed"
}
```

> **MVP 说明**：同步处理，不返回 task_id，前端显示 spinner 等待即可。处理流程：保存文件 → 解析文本 → 按字符数切割 → 生成向量 → 存入 ChromaDB。

### 4.3 错误格式

```json
{
  "detail": "错误描述"
}
```

---

## 5. 数据流设计

### 5.1 文件上传 → 向量存储（同步流程）

```
用户拖拽/选择文件
  │
  ▼
前端 POST /api/v1/upload (multipart)
  │
  ▼
后端同步处理：
  ① 保存文件到 data/uploads/
  ② 解析文档 (PDF/DOCX → 纯文本)
  ③ 按 chunk_size 切割文本
  ④ 调用 sentence-transformers 生成向量
  ⑤ 存入 ChromaDB Collection（metadata 包含 source, chunk_index）
  │
  ▼
返回 200，前端刷新文档列表
```

### 5.2 文档浏览流程

```
用户切换右侧集合下拉框
  → GET /collections/{name}/documents
  → 渲染文档列表（按 source 分组聚合）

用户点击 [查看] 某文档
  → GET /documents/{id}/chunks
  → 展开底部预览面板，显示分块列表
```

### 5.3 前端全局状态（简化）

```js
const AppState = {
  collections: [],
  selectedCollection: null,
  chunkSize: 1000,
  documents: [],
  previewDocId: null,
  isUploading: false
};
```

---

## 6. 配置管理

### 6.1 后端环境变量（.env）

```env
# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma_storage

# Embedding 模型（MVP 只支持本地模型）
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu

# 上传限制
MAX_UPLOAD_SIZE_MB=20
ALLOWED_EXTENSIONS=.pdf,.docx

# 服务
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=*
```

> **MVP 移除**：OpenAI 配置、CHROMA_HOST/PORT（使用本地持久化）、切割方式配置

---

## 7. 启动方式

### 7.1 开发环境

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env

# 3. 启动后端
uvicorn main:app --reload --port 8000

# 4. 启动前端（新终端）
cd frontend
python -m http.server 5173
```

### 7.2 访问
- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

---

## 8. MVP 功能边界

### ✅ 包含功能
- [x] 集合的增删查
- [x] PDF/DOCX 文件上传
- [x] 文本解析与按字符数切割
- [x] 本地 Embedding 模型生成向量
- [x] 存入 ChromaDB
- [x] 按集合查看文档列表
- [x] 查看文档分块内容
- [x] 删除单个文档

### ❌ 不包含功能（后续迭代）
- [ ] 异步任务队列与进度追踪
- [ ] 多 Embedding 模型切换（OpenAI/本地）
- [ ] 多种文本切割方式
- [ ] 语义搜索
- [ ] 批量删除
- [ ] 系统配置接口
- [ ] Docker 部署
- [ ] 用户认证
- [ ] 上传历史/任务管理
- [ ] localStorage 持久化

---

## 9. 关键实现注意事项

### 9.1 文档在 ChromaDB 中的存储方式

MVP 不引入额外的数据库，直接在 ChromaDB 的 metadata 中标记文档来源：

```python
# 每个 chunk 的 metadata 结构
{
    "source": "report.pdf",           # 文档名称
    "doc_id": "doc-001",              # 文档 ID（由后端生成）
    "chunk_index": 0,                 # 在文档中的序号
    "total_chunks": 45                # 文档总块数
}
```

查询文档列表时，对 collection 的所有数据按 `doc_id` 分组聚合即可。

### 9.2 文本切割策略（MVP 简化）

不使用 LangChain，直接按字符数切割：

```python
def simple_split(text: str, chunk_size: int = 1000) -> list[str]:
    """按固定字符数切割文本，优先在段落边界切割"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # 尝试在段落边界切割
        paragraph_end = text.rfind('\n\n', start, end)
        if paragraph_end != -1 and paragraph_end > start + chunk_size * 0.5:
            end = paragraph_end + 2
        else:
            # 尝试在句子边界切割
            sentence_end = text.rfind('. ', start, end)
            if sentence_end != -1 and sentence_end > start + chunk_size * 0.5:
                end = sentence_end + 2
        chunks.append(text[start:end])
        start = end
    return chunks
```

### 9.3 文件处理流程

```python
# services.py 中的核心流程
async def process_file(file, collection_name: str, chunk_size: int):
    # 1. 保存文件
    file_path = save_upload(file)
    
    # 2. 解析文本
    text = parse_document(file_path)  # PDF/DOCX → text
    
    # 3. 切割
    chunks = simple_split(text, chunk_size)
    
    # 4. 生成向量
    embeddings = model.encode(chunks)
    
    # 5. 存入 ChromaDB
    doc_id = generate_doc_id()
    collection = chroma_client.get_or_create_collection(collection_name)
    collection.add(
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
        embeddings=embeddings.tolist(),
        documents=chunks,
        metadatas=[{
            "source": file.filename,
            "doc_id": doc_id,
            "chunk_index": i,
            "total_chunks": len(chunks)
        } for i in range(len(chunks))]
    )
    
    return {"document_id": doc_id, "chunk_count": len(chunks)}
```

---

## 10. 项目文件清单

| 文件 | 说明 |
|------|------|
| `frontend/index.html` | 页面结构，CDN 加载 Pico.css |
| `frontend/css/style.css` | 拖拽区域高亮、布局等自定义样式 |
| `frontend/js/app.js` | API 调用、DOM 渲染、事件绑定 |
| `backend/main.py` | FastAPI 应用 + 所有路由 |
| `backend/services.py` | 文档解析、文本切割、向量化、ChromaDB 操作 |
| `backend/models.py` | Pydantic 请求/响应模型 |
| `backend/config.py` | Pydantic Settings 读取 .env |
| `backend/requirements.txt` | Python 依赖 |
| `data/uploads/` | 上传文件临时目录 |
| `data/chroma_storage/` | ChromaDB 持久化目录 |
