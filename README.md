# AI Memory RAG

AI Memory RAG 是一个集个人知识管理与 Agent 调用于一体的认知记忆系统，模拟人脑对记忆进行智能组织、计算、演化，提供持久、连贯、可追溯的长期记忆能力。

## 功能特性

- **记忆管理**: 创建、编辑、删除、查看记忆
- **语义搜索**: 使用自然语言搜索记忆，支持自定义阈值
- **知识图谱**: 记忆关系可视化（开发中）
- **版本控制**: 自动记录记忆变更历史
- **可配置存储**: 支持多种向量数据库和关系数据库
- **REST API**: 完整的 API 接口
- **Streamlit UI**: 直观的用户界面
- **MCP 集成**: 支持与 Trae IDE 等 AI 助手集成

## 技术栈

- **后端**: FastAPI
- **前端**: Streamlit
- **向量数据库**: ChromaDB (默认)
- **关系数据库**: SQLite (默认)
- **嵌入模型**: sentence-transformers

## 项目结构

```
ai-mem-rag/
├── api/                    # FastAPI 后端
│   ├── main.py             # API 入口
│   ├── routes/             # 路由定义
│   ├── models/             # Pydantic 模型
│   └── services/           # 业务逻辑
├── ui/                     # Streamlit 前端
│   └── main.py             # UI 入口
├── core/                   # 核心引擎
│   ├── memory_engine.py    # 记忆引擎
│   ├── vector_store.py     # 向量存储抽象
│   └── relational_store.py # 关系存储抽象
├── adapters/               # 存储适配器
│   ├── chroma_adapter.py   # Chroma 实现
│   └── sqlite_adapter.py   # SQLite 实现
├── config/                 # 配置文件
│   └── settings.py         # 可配置数据库等
├── docs/                   # 文档
└── requirements.txt        # 依赖清单
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境

复制示例配置文件：

```bash
cp .env.example .env
```

根据需要修改 `.env` 文件中的配置项。

### 运行后端 API

```bash
python -m api.main
```

API 将在 `http://localhost:8000` 启动，访问 `http://localhost:8000/docs` 查看 Swagger 文档。

### 运行前端 UI

打开新的终端窗口：

```bash
streamlit run ui/main.py
```

UI 将在 `http://localhost:8501` 启动。

### 与 Trae IDE 集成 (MCP)

我们的 AI Memory RAG 支持通过 MCP (Model Context Protocol) 与 Trae IDE 集成！

#### 步骤 1: 确保依赖已安装

```bash
pip install -r requirements.txt
```

#### 步骤 2: 配置 Trae

方法一: 从市场添加 (推荐)

1. 在 Trae IDE 的 AI 侧边对话框右上角，点击 **设置** 图标
2. 选择 **MCP** 页签
3. 点击 **+ 添加 MCP Servers** 按钮
4. 搜索并添加 ai-memory-rag (如果有)

方法二: 手动添加

1. 复制 `trae_mcp_config.json` 内容
2. 在 Trae IDE 中，点击 AI 侧边对话框右上角的 **设置** 图标
3. 选择 **MCP** 页签
4. 点击右上角的 **+ 添加** 按钮，选择 **手动添加**
5. 复制并粘贴配置，修改 `cwd` 路径为你实际的项目路径
6. 点击 **确认** 保存

配置文件内容 (`trae_mcp_config.json`):

```json
{
  "mcpServers": {
    "ai-memory-rag": {
      "command": [
        "python",
        "-m",
        "mcp.main"
      ],
      "cwd": "/Users/tianyi/code/ai-mem-rag",
      "env": {
        "PYTHONPATH": "/Users/tianyi/code/ai-mem-rag"
      }
    }
  }
}
```

#### 可用的 MCP 工具

| 工具名称 | 描述 |
|---------|------|
| `add_memory` | 添加新记忆 |
| `search_memory` | 搜索记忆 |
| `list_memories` | 列出所有记忆 |
| `delete_memory` | 删除记忆 |
| `get_memory_versions` | 获取记忆版本历史 |

#### 使用示例

在 Trae IDE 中，你可以直接对 AI 说：

> "帮我添加一条记忆：今天学习了 Python 编程基础"
>
> "搜索一下关于机器学习的记忆"
>
> "列出我所有的记忆"

## 配置说明

可以通过环境变量或 `.env` 文件配置以下选项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `VECTOR_STORE_TYPE` | 向量数据库类型 | `chroma` |
| `CHROMA_PATH` | Chroma 数据库路径 | `./chroma_db` |
| `RELATIONAL_STORE_TYPE` | 关系数据库类型 | `sqlite` |
| `DATABASE_URL` | 关系数据库 URL | `sqlite:///./ai-memory-rag.db` |
| `EMBEDDING_MODEL` | 嵌入模型名称 | `all-MiniLM-L6-v2` |
| `API_HOST` | API 监听地址 | `0.0.0.0` |
| `API_PORT` | API 监听端口 | `8000` |

## API 使用

### 创建记忆

```bash
curl -X POST http://localhost:8000/api/memories \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "这是一条测试记忆",
    "tags": ["测试", "示例"],
    "metadata": {"source": "manual"}
  }'
```

### 搜索记忆

```bash
curl -X POST http://localhost:8000/api/memories/search \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "测试内容",
    "limit": 10,
    "threshold": 0.7
  }'
```

## 开发计划

- [x] 基础记忆 CRUD
- [x] 语义搜索
- [x] REST API
- [x] Streamlit UI
- [x] MCP 接口
- [ ] 知识图谱可视化
- [ ] 时间线和版本历史查看

## 许可证

MIT License