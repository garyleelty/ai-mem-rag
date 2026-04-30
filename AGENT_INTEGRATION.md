# AI 问答记录偏好数据库 - 外部 Agent 集成指南

> 本文档说明如何让 OpenCode、Claude Code、Cursor 等 AI 编码助手自动记录问答到本系统。

---

## 1. 核心概念

你的 AI 问答偏好数据库是一个 **FastAPI 后端服务**，运行在 `http://localhost:8000`。外部 AI Agent（如 Claude Code）可以通过 HTTP API 将每次问答自动记录下来。

**数据流**：
```
用户提问 → AI Agent 生成回答 → Agent 调用 API 记录问答 → 存入 SQLite + ChromaDB
```

---

## 2. 快速开始

### 2.1 启动服务

```bash
cd /Users/tianyi/code/chromadb-rag/backend
pip install -r requirements.txt
python main.py
```

服务启动后：
- API 地址：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### 2.2 注册账号

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"agent_user","password":"secret123"}'
```

返回：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {"id":1,"username":"agent_user"}
}
```

保存 `access_token`，后续所有请求都需要它。

---

## 3. Agent 集成方式

### 3.1 Claude Code 集成

Claude Code 支持自定义 slash commands 和 MCP (Model Context Protocol)。推荐两种方式：

#### 方式 A：MCP Server（推荐）

创建一个 MCP server，让 Claude Code 自动记录每次对话。

**文件：`mcp_server.py`**

```python
#!/usr/bin/env python3
"""MCP Server for QA Preference Database"""

import os
import httpx
from mcp.server import Server
from mcp.types import TextContent, Tool

API_BASE = os.getenv("QA_API_URL", "http://localhost:8000/api/v1")
TOKEN = os.getenv("QA_API_TOKEN", "")

app = Server("qa-preference-db")

async def api_call(method: str, path: str, json=None):
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method,
            f"{API_BASE}{path}",
            json=json,
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        resp.raise_for_status()
        return resp.json()

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="record_qa",
            description="Record a Q&A pair to the preference database",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "User's question"},
                    "answer": {"type": "string", "description": "AI's answer"},
                    "conversation_title": {"type": "string", "description": "Optional conversation title"},
                    "model_name": {"type": "string", "description": "AI model name, e.g. claude-3-5-sonnet"},
                },
                "required": ["question", "answer"],
            },
        ),
        Tool(
            name="search_similar",
            description="Search for similar past Q&A records",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_user_preferences",
            description="Get current user's preference settings",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "record_qa":
        result = await api_call("POST", "/qa/records", {
            "question": arguments["question"],
            "answer": arguments["answer"],
            "model_name": arguments.get("model_name", "claude"),
        })
        return [TextContent(type="text", text=f"Recorded QA with ID: {result['id']}")]

    elif name == "search_similar":
        result = await api_call("POST", "/qa/search", {
            "query": arguments["query"],
            "top_k": arguments.get("top_k", 5),
        })
        texts = []
        for r in result["results"]:
            texts.append(f"Q: {r['question']}\nA: {r['answer'][:200]}...\n---")
        return [TextContent(type="text", text="\n".join(texts) or "No results")]

    elif name == "get_user_preferences":
        result = await api_call("GET", "/preferences")
        return [TextContent(type="text", text=str(result))]

    raise ValueError(f"Unknown tool: {name}")

if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read, write):
            await app.run(read, write)

    asyncio.run(main())
```

**配置 Claude Code 使用 MCP：**

在 `~/.claude/settings.json` 或项目根目录 `.claude/settings.json`：

```json
{
  "mcpServers": {
    "qa-preference-db": {
      "command": "python3",
      "args": ["/Users/tianyi/code/chromadb-rag/mcp_server.py"],
      "env": {
        "QA_API_URL": "http://localhost:8000/api/v1",
        "QA_API_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

配置后，Claude Code 会自动在每次对话后调用 `record_qa` 工具记录问答。

#### 方式 B：自定义 Slash Command

在 Claude Code 中创建自定义命令：

```json
{
  "customCommands": [
    {
      "name": "/saveqa",
      "description": "Save current Q&A to preference database",
      "prompt": "Call the record_qa MCP tool with the last user message and your response."
    }
  ]
}
```

### 3.2 OpenCode 集成

OpenCode 支持通过 `~/.config/opencode/config.json` 配置外部工具：

```json
{
  "tools": [
    {
      "name": "qa_db",
      "type": "http",
      "url": "http://localhost:8000/api/v1",
      "headers": {
        "Authorization": "Bearer YOUR_JWT_TOKEN"
      },
      "actions": {
        "record": {
          "endpoint": "/qa/records",
          "method": "POST",
          "body": {
            "question": "{{user_input}}",
            "answer": "{{assistant_output}}",
            "model_name": "opencode"
          }
        },
        "search": {
          "endpoint": "/qa/search",
          "method": "POST",
          "body": {
            "query": "{{user_input}}",
            "top_k": 5
          }
        }
      }
    }
  ]
}
```

### 3.3 Cursor 集成

Cursor 支持 `.cursorrules` 文件定义规则，以及自定义命令：

**`.cursorrules`**（放在项目根目录）：

```
After each significant Q&A exchange, automatically record it to the local QA preference database.

API Endpoint: http://localhost:8000/api/v1/qa/records
Headers: Authorization: Bearer YOUR_JWT_TOKEN

Body format:
{
  "question": "<user question>",
  "answer": "<your answer>",
  "model_name": "cursor"
}
```

### 3.4 通用 Shell 脚本方式

任何 AI Agent 都可以通过调用 shell 脚本集成：

**`record_qa.sh`**

```bash
#!/bin/bash
# Usage: ./record_qa.sh "question" "answer" [model_name]

API_URL="http://localhost:8000/api/v1"
TOKEN="YOUR_JWT_TOKEN"

QUESTION="$1"
ANSWER="$2"
MODEL="${3:-unknown}"

curl -s -X POST "${API_URL}/qa/records" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d "{
    \"question\": $(echo "$QUESTION" | jq -R -s .),
    \"answer\": $(echo "$ANSWER" | jq -R -s .),
    \"model_name\": \"$MODEL\"
  }"
```

---

## 4. 批量导入历史记录

如果你已有历史问答记录（如从 ChatGPT、Claude 导出），可以批量导入：

### 4.1 JSON 格式导入

```bash
curl -X POST http://localhost:8000/api/v1/qa/import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "source": "import",
    "items": [
      {
        "question": "什么是向量数据库？",
        "answer": "向量数据库是专门存储高维向量的数据库...",
        "model_name": "gpt-4",
        "conversation_title": "数据库学习"
      },
      {
        "question": "如何优化 Python 性能？",
        "answer": "可以使用多进程、Cython、Numba 等工具...",
        "model_name": "claude-3",
        "conversation_title": "Python 优化"
      }
    ]
  }'
```

### 4.2 从 ChatGPT 导出导入

ChatGPT 导出格式为 JSON，转换脚本：

```python
import json
import requests

TOKEN = "your-token"
API = "http://localhost:8000/api/v1"

def import_chatgpt_export(filepath: str):
    with open(filepath) as f:
        data = json.load(f)

    items = []
    for conv in data:
        title = conv.get("title", "Untitled")
        for msg in conv.get("mapping", {}).values():
            msg_data = msg.get("message")
            if not msg_data:
                continue
            role = msg_data.get("author", {}).get("role")
            content = msg_data.get("content", {}).get("parts", [""])[0]
            # ChatGPT 格式需要配对处理
            # 这里简化处理，实际需根据具体格式调整

    resp = requests.post(
        f"{API}/qa/import",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"source": "import", "items": items}
    )
    print(resp.json())

import_chatgpt_export("conversations.json")
```

---

## 5. 查询历史记录

### 5.1 关键词搜索

```bash
curl "http://localhost:8000/api/v1/qa/records?keyword=向量数据库" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5.2 语义搜索

```bash
curl -X POST http://localhost:8000/api/v1/qa/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "怎么优化数据库查询？",
    "top_k": 5
  }'
```

### 5.3 查找相似记录

```bash
curl http://localhost:8000/api/v1/qa/similar/123?top_k=5 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 6. 提交反馈

记录问答后，可以提交反馈：

```bash
curl -X POST http://localhost:8000/api/v1/qa/records/123/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "feedback_type": "thumbs_up",
    "preset_tags": ["accurate", "concise"],
    "custom_tags": ["适合新手"],
    "comment": "回答得很清楚"
  }'
```

---

## 7. 获取用户偏好

Agent 可以在回答前获取用户偏好，调整回答风格：

```bash
curl http://localhost:8000/api/v1/preferences \
  -H "Authorization: Bearer YOUR_TOKEN"
```

返回示例：
```json
{
  "preferred_style": "detailed",
  "preferred_language": "zh",
  "domain_interests": "[\"编程\", \"数据库\"]",
  "custom_prompt": "请用中文回答，尽量详细"
}
```

Agent 可以根据这些偏好调整回答策略。

---

## 8. 预设标签列表

```bash
curl http://localhost:8000/api/v1/tags/preset \
  -H "Authorization: Bearer YOUR_TOKEN"
```

返回：
```json
[
  {"name":"accurate","label":"准确","color":"#22c55e","category":"quality"},
  {"name":"concise","label":"简洁","color":"#3b82f6","category":"style"},
  {"name":"detailed","label":"详细","color":"#8b5cf6","category":"style"},
  {"name":"helpful","label":"有帮助","color":"#22c55e","category":"quality"}
]
```

---

## 9. 完整工作流示例

```python
import httpx

class QAPreferenceClient:
    def __init__(self, token: str, base_url: str = "http://localhost:8000/api/v1"):
        self.token = token
        self.base = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    async def record(self, question: str, answer: str, model: str = "claude"):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base}/qa/records",
                headers=self.headers,
                json={"question": question, "answer": answer, "model_name": model},
            )
            return resp.json()

    async def search(self, query: str, top_k: int = 5):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base}/qa/search",
                headers=self.headers,
                json={"query": query, "top_k": top_k},
            )
            return resp.json()

    async def feedback(self, record_id: int, feedback_type: str, tags: list = None):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base}/qa/records/{record_id}/feedback",
                headers=self.headers,
                json={"feedback_type": feedback_type, "preset_tags": tags or []},
            )
            return resp.json()

    async def get_preferences(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base}/preferences", headers=self.headers)
            return resp.json()


# 使用示例
async def main():
    client = QAPreferenceClient(token="your-jwt-token")

    # 记录问答
    record = await client.record(
        question="什么是 RAG？",
        answer="RAG (Retrieval-Augmented Generation) 是一种...",
        model="claude-3-5-sonnet",
    )
    print(f"Recorded with ID: {record['id']}")

    # 搜索相关历史
    similar = await client.search("检索增强生成")
    for r in similar["results"]:
        print(f"Q: {r['question']} (similarity: {r['similarity']})")

    # 提交反馈
    await client.feedback(record["id"], "thumbs_up", ["accurate", "helpful"])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 10. 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `JWT_SECRET` | `change-me-in-production` | JWT 签名密钥 |
| `JWT_EXPIRE_HOURS` | `24` | Token 有效期 |
| `SQLITE_PATH` | `./data/app.db` | SQLite 数据库路径 |
| `CHROMA_PERSIST_DIR` | `./data/chroma_storage` | ChromaDB 存储路径 |
| `EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 向量模型 |

---

## 11. 安全建议

1. **生产环境**：修改 `JWT_SECRET` 为强随机字符串
2. **HTTPS**：生产环境使用 HTTPS，避免 Token 被截获
3. **Token 管理**：Agent 的 Token 可以单独创建一个专用账号
4. **CORS**：生产环境限制 `CORS_ORIGINS` 为实际域名
