# ChromaDB 文档管理器

基于 ChromaDB 的文档上传、分块、向量化和检索系统。支持 PDF 和 DOCX 格式，提供 Web 界面管理文档集合。

## 功能特性

- 📄 支持 PDF / DOCX 文件上传与解析
- 🗂️ 文档集合（Collection）管理
- ✂️ 智能文本分块（支持段落/句子边界）
- 🔍 文档内容预览与分块查看
- 🗑️ 文档删除与集合清理

## 快速开始

### 环境要求

- Python 3.9+
- 建议创建虚拟环境

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 启动服务

```bash
cd backend
python main.py
```

服务默认运行在 `http://localhost:8000`。

### 访问前端

直接打开 `frontend/index.html`，或使用任意静态文件服务器：

```bash
cd frontend
python -m http.server 8080
```

然后访问 `http://localhost:8080`。

## 配置说明

复制 `.env.example` 为 `.env` 并修改：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `CHROMA_PERSIST_DIR` | `./data/chroma_storage` | ChromaDB 持久化目录 |
| `EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 向量模型名称 |
| `EMBEDDING_DEVICE` | `cpu` | 运行设备（cpu/cuda） |
| `MAX_UPLOAD_SIZE_MB` | `20` | 单文件大小限制 |
| `HOST` | `0.0.0.0` | 服务绑定地址 |
| `PORT` | `8000` | 服务端口 |
| `CORS_ORIGINS` | `*` | 允许的跨域来源 |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/collections` | 列出所有集合 |
| POST | `/api/v1/collections` | 创建集合 |
| DELETE | `/api/v1/collections/{name}` | 删除集合 |
| GET | `/api/v1/collections/{name}/documents` | 列出集合内文档 |
| GET | `/api/v1/documents/{id}/chunks` | 查看文档分块 |
| DELETE | `/api/v1/documents/{id}` | 删除文档 |
| POST | `/api/v1/upload` | 上传文件 |

## 项目结构

```
chromadb-rag/
├── backend/          # FastAPI 后端
│   ├── main.py       # API 入口
│   ├── services.py   # 业务逻辑
│   ├── models.py     # 数据模型
│   └── config.py     # 配置管理
├── frontend/         # 前端页面
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
└── data/             # 数据存储
    ├── uploads/      # 临时上传文件
    └── chroma_storage/  # ChromaDB 数据
```

## 部署提示

前端默认连接 `http://localhost:8000`。部署时修改 `frontend/index.html` 中的 `window.API_BASE_URL` 为实际后端地址。
