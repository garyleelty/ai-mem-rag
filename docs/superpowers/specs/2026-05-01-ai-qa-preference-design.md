# AI 问答记录偏好数据库 - 架构设计文档

> 版本：v1.0  
> 日期：2026-05-01  
> 方案：A（SQLite + ChromaDB 混合架构）  

---

## 1. 项目背景与目标

### 1.1 现有项目
基于 ChromaDB 的文档上传、分块、向量化和检索系统（FastAPI 后端 + 纯 HTML/JS 前端）。

### 1.2 新增目标
构建一个 **AI 问答记录偏好数据库**，支持：
- 对接外部 AI 服务（API 调用）记录问答
- 手动导入/录入问答记录
- 多用户系统，每个用户有自己的问答历史和偏好
- 用户对回答的反馈（点赞/点踩/修改/标签）
- 基于语义的历史问答检索
- 用户偏好画像管理

---

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (HTML/JS)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ 文档管理  │  │ 问答记录  │  │ 偏好设置  │  │  用户系统   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI 后端 (Python)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ 文档 API  │  │ 问答 API  │  │ 用户 API  │  │  偏好 API   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ 认证模块  │  │ 反馈模块  │  │ 搜索模块  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
┌─────────────────────────┐         ┌─────────────────────────┐
│      SQLite (关系数据)    │         │    ChromaDB (向量数据)   │
│  - users                │         │  - 文档向量              │
│  - conversations        │         │  - 问答记录向量          │
│  - qa_records           │         │                         │
│  - feedbacks            │         │                         │
│  - user_preferences     │         │                         │
│  - preset_tags          │         │                         │
└─────────────────────────┘         └─────────────────────────┘
```

### 2.2 存储分工

| 数据类型 | 存储 | 原因 |
|---------|------|------|
| 用户信息、会话、问答元数据 | SQLite | 结构化查询、事务支持 |
| 反馈、标签、偏好 | SQLite | 频繁读写、关系查询 |
| 文档/问答的文本向量 | ChromaDB | 语义检索能力 |

---

## 3. 数据库设计（SQLite）

### 3.1 用户表 `users`

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 对话会话表 `conversations`

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    source TEXT NOT NULL DEFAULT 'api',  -- 'api', 'import', 'manual'
    model_name TEXT,
    metadata TEXT,  -- JSON: 额外信息如 temperature, system_prompt 等
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 3.3 问答记录表 `qa_records`

```sql
CREATE TABLE qa_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER,
    user_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    model_name TEXT,
    temperature REAL,
    tokens_used INTEGER,
    latency_ms INTEGER,
    sequence_order INTEGER DEFAULT 0,  -- 在会话中的顺序
    chroma_doc_id TEXT,  -- 关联 ChromaDB 的 doc_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 3.4 用户反馈表 `feedbacks`

```sql
CREATE TABLE feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qa_record_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    feedback_type TEXT NOT NULL,  -- 'thumbs_up', 'thumbs_down', 'modified'
    modified_answer TEXT,  -- 用户修改后的答案
    preset_tags TEXT,  -- JSON 数组，预设标签
    custom_tags TEXT,  -- JSON 数组，用户自定义标签
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (qa_record_id) REFERENCES qa_records(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(qa_record_id, user_id)  -- 每个用户对每条记录只能有一条反馈
);
```

### 3.5 预设标签表 `preset_tags`

```sql
CREATE TABLE preset_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,   -- 内部名，如 'accurate'
    label TEXT NOT NULL,         -- 显示名，如 '准确'
    color TEXT DEFAULT '#3b82f6',
    category TEXT DEFAULT 'general',  -- 'quality', 'style', 'general'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.6 用户偏好表 `user_preferences`

```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    preferred_style TEXT DEFAULT 'balanced',  -- 'concise', 'detailed', 'technical', 'balanced'
    preferred_language TEXT DEFAULT 'zh',
    domain_interests TEXT,  -- JSON 数组，如 ["编程", "设计"]
    custom_prompt TEXT,
    auto_summary BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 3.7 ChromaDB 存储结构

问答记录存入 ChromaDB 时，metadata 结构：

```python
{
    "source": "qa_record",           # 标识类型
    "qa_id": "123",                  # qa_records.id
    "user_id": "456",                # users.id
    "conversation_id": "789",        # conversations.id
    "question_preview": "...",       # 问题前 100 字
    "created_at": "2024-01-01T10:00:00"
}
```

**向量化策略**：将 `question + "\n" + answer` 拼接后生成向量，支持对问题和答案的语义搜索。

---

## 4. API 接口设计

### 4.1 认证模块

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | 否 |
| POST | `/api/v1/auth/login` | 登录获取 JWT | 否 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 | 是 |
| POST | `/api/v1/auth/logout` | 退出登录 | 是 |

**请求/响应示例**：

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "alice",
    "password": "secret123"
}

Response:
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
        "id": 1,
        "username": "alice",
        "email": "alice@example.com"
    }
}
```

### 4.2 对话会话模块

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/conversations` | 获取会话列表 | 是 |
| POST | `/api/v1/conversations` | 创建会话 | 是 |
| GET | `/api/v1/conversations/{id}` | 获取会话详情（含问答列表） | 是 |
| PUT | `/api/v1/conversations/{id}` | 更新会话标题/元数据 | 是 |
| DELETE | `/api/v1/conversations/{id}` | 删除会话（级联删除问答） | 是 |

### 4.3 问答记录模块

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/qa/records` | 创建问答记录 | 是 |
| GET | `/api/v1/qa/records` | 查询历史记录 | 是 |
| GET | `/api/v1/qa/records/{id}` | 获取单条详情 | 是 |
| DELETE | `/api/v1/qa/records/{id}` | 删除记录 | 是 |
| POST | `/api/v1/qa/import` | 批量导入 | 是 |

**创建问答记录请求**：
```json
{
    "conversation_id": 1,
    "question": "什么是向量数据库？",
    "answer": "向量数据库是一种专门用于存储和检索高维向量数据的数据库...",
    "model_name": "gpt-4",
    "temperature": 0.7,
    "tokens_used": 150,
    "latency_ms": 1200
}
```

**查询参数**：
- `conversation_id`: 按会话筛选
- `keyword`: 关键词搜索（SQL LIKE）
- `model_name`: 按模型筛选
- `date_from`, `date_to`: 时间范围
- `page`, `page_size`: 分页

### 4.4 语义搜索模块

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/qa/search` | 语义搜索历史问答 | 是 |
| GET | `/api/v1/qa/similar/{id}` | 查找相似问答 | 是 |

**语义搜索请求**：
```json
{
    "query": "如何优化数据库查询性能？",
    "top_k": 10,
    "conversation_id": null,
    "date_from": null,
    "date_to": null
}
```

**响应**：
```json
{
    "results": [
        {
            "qa_record_id": 123,
            "question": "数据库查询慢怎么办？",
            "answer": "可以通过添加索引、优化 SQL...",
            "similarity": 0.89,
            "created_at": "2024-01-01T10:00:00"
        }
    ]
}
```

### 4.5 反馈模块

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/qa/records/{id}/feedback` | 提交反馈 | 是 |
| GET | `/api/v1/qa/records/{id}/feedback` | 获取反馈 | 是 |
| PUT | `/api/v1/qa/records/{id}/feedback` | 更新反馈 | 是 |
| DELETE | `/api/v1/qa/records/{id}/feedback` | 删除反馈 | 是 |

**提交反馈请求**：
```json
{
    "feedback_type": "modified",
    "modified_answer": "优化后的答案...",
    "preset_tags": ["accurate", "concise"],
    "custom_tags": ["适合新手"],
    "comment": "这个回答更清楚了"
}
```

### 4.6 偏好模块

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/preferences` | 获取当前用户偏好 | 是 |
| PUT | `/api/v1/preferences` | 更新偏好 | 是 |

### 4.7 预设标签模块

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/tags/preset` | 获取所有预设标签 | 是 |
| POST | `/api/v1/tags/preset` | 添加预设标签（管理员） | 是 |

---

## 5. 前端页面设计

### 5.1 整体布局改造

```
┌─────────────────────────────────────────────────────────────────────┐
│  🗄️ AI 问答偏好数据库          [💬 问答] [📁 文档] [⭐ 偏好] [👤 用户] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  【左侧边栏 - 导航】                                                  │
│  ┌─────────────┐                                                    │
│  │ 📁 文档管理  │                                                    │
│  │ 💬 问答记录  │  ← 默认选中                                         │
│  │ ⭐ 我的偏好  │                                                    │
│  └─────────────┘                                                    │
│                                                                     │
│  【中间主内容区】                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 🔍 [语义搜索...                    ] [🔍 搜索] [⚙️ 筛选]     │   │
│  │                                                             │   │
│  │ 会话: [全部会话 ▾]  模型: [全部 ▾]  时间: [最近7天 ▾]        │   │
│  │                                                             │   │
│  │ ┌─────────────────────────────────────────────────────────┐ │   │
│  │ │ 💬 会话: Python 学习笔记                                   │ │   │
│  │ │ Q: 什么是向量数据库？                                      │ │   │
│  │ │ A: 向量数据库是一种专门用于...                              │ │   │
│  │ │ 🤖 gpt-4 · 2小时前 · 👍 · 🏷️ 准确 简洁                    │ │   │
│  │ └─────────────────────────────────────────────────────────┘ │   │
│  │ ┌─────────────────────────────────────────────────────────┐ │   │
│  │ │ 💬 会话: 数据库优化                                        │ │   │
│  │ │ Q: 如何优化查询性能？                                      │ │   │
│  │ │ A: 可以通过添加索引...                                     │ │   │
│  │ │ 🤖 claude-3 · 昨天 · 👎 · 🏷️ 过于简单                     │ │   │
│  │ └─────────────────────────────────────────────────────────┘ │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  【右侧详情面板】（点击问答后展开）                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 问题                                                        │   │
│  │ ─────────────────────────────────────────────────────────   │   │
│  │ 什么是向量数据库？                                           │   │
│  │                                                             │   │
│  │ 回答                                                        │   │
│  │ ─────────────────────────────────────────────────────────   │   │
│  │ 向量数据库是一种专门用于存储和检索高维向量数据的数据库...      │   │
│  │                                                             │   │
│  │ 反馈                                                        │   │
│  │ ─────────────────────────────────────────────────────────   │   │
│  │ 👍 👎  [修改答案...]                                         │   │
│  │ 预设标签: [准确 ▢] [简洁 ▢] [详细 ▢] [有帮助 ▢]              │   │
│  │ 自定义标签: [适合新手] [x] [+ 添加标签]                       │   │
│  │ 备注: ______________________                                │   │
│  │ [提交反馈]                                                  │   │
│  │                                                             │   │
│  │ 相似问答                                                    │   │
│  │ • 向量数据库和关系数据库的区别？                              │   │
│  │ • 如何选择向量数据库？                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 页面路由（前端 hash 路由）

| 路径 | 页面 |
|------|------|
| `#/qa` | 问答记录列表（默认页） |
| `#/qa/{id}` | 单条问答详情 |
| `#/conversations` | 会话列表 |
| `#/conversations/{id}` | 会话详情（含该会话所有问答） |
| `#/documents` | 文档管理（现有功能） |
| `#/preferences` | 偏好设置 |
| `#/login` | 登录 |
| `#/register` | 注册 |

### 5.3 核心交互

#### 问答记录列表
- 支持关键词搜索（SQL LIKE）和语义搜索切换
- 筛选器：会话、模型、时间范围、反馈类型
- 列表项显示：会话标题、问题摘要、回答摘要、模型、时间、反馈、标签
- 点击展开右侧详情面板

#### 会话视图
- 左侧会话列表，右侧问答时间线
- 支持给会话打标签、修改标题
- 支持导出会话为 JSON/Markdown

#### 反馈交互
- 👍/👎 一键反馈
- 修改答案：展开文本框，用户编辑后保存
- 预设标签：点击选择/取消，多选
- 自定义标签：输入后回车添加，点击 x 删除

#### 导入功能
- 支持 JSON/CSV 格式
- 字段映射配置（如外部文件的 `prompt` 映射到 `question`）
- 预览导入数据，确认后批量写入

---

## 6. 数据流设计

### 6.1 创建问答记录（API 调用场景）

```
外部 AI API 调用
    │
    ▼
POST /api/v1/qa/records
    │
    ├──► SQLite: 插入 qa_records
    │
    ├──► ChromaDB: 生成向量，存入 collection
    │         metadata: {source: "qa_record", qa_id, user_id, ...}
    │
    └──► 返回 qa_record_id
```

### 6.2 语义搜索

```
用户输入查询
    │
    ▼
POST /api/v1/qa/search
    │
    ├──► ChromaDB: query_embedding → 相似向量检索
    │         where: {user_id: current_user_id}
    │
    ├──► SQLite: 根据返回的 qa_ids 查询完整数据
    │
    └──► 返回排序后的结果列表
```

### 6.3 批量导入

```
用户上传 JSON/CSV
    │
    ▼
POST /api/v1/qa/import
    │
    ├──► 解析文件，字段映射
    │
    ├──► 按 conversation 分组
    │
    ├──► SQLite: 批量插入 conversations + qa_records
    │
    ├──► ChromaDB: 批量生成向量并存储
    │
    └──► 返回导入统计（成功/失败数）
```

---

## 7. 安全设计

### 7.1 认证
- JWT Token（access token），有效期 24 小时
- 密码使用 bcrypt 哈希存储
- 所有写操作必须携带有效 Token

### 7.2 数据隔离
- 所有查询自动过滤 `user_id = current_user_id`
- 用户只能访问自己的问答记录和偏好
- ChromaDB 查询使用 `where={"user_id": "xxx"}` 过滤

### 7.3 输入校验
- SQL 注入防护：使用 ORM/参数化查询
- XSS 防护：前端输出转义
- 文件上传：限制格式和大小

---

## 8. 扩展预留

### 8.1 偏好分析（后续迭代）
- 基于用户反馈数据自动生成偏好画像
- 分析高频标签、喜欢的回答风格
- 自动推荐偏好设置

### 8.2 多模型支持
- `model_name` 字段已预留
- 后续可扩展模型配置管理

### 8.3 数据导出
- 支持按会话/时间范围导出
- 格式：JSON、CSV、Markdown

### 8.4 统计报表
- 问答频次统计
- 模型使用分布
- 反馈统计（好评率等）

---

## 9. 文件变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `backend/database.py` | SQLite 数据库连接和初始化 |
| `backend/auth.py` | JWT 认证、密码哈希 |
| `backend/routers/users.py` | 用户相关 API |
| `backend/routers/conversations.py` | 会话相关 API |
| `backend/routers/qa_records.py` | 问答记录 API |
| `backend/routers/feedback.py` | 反馈 API |
| `backend/routers/preferences.py` | 偏好 API |
| `backend/routers/tags.py` | 预设标签 API |
| `backend/models/qa_models.py` | 问答相关 Pydantic 模型 |
| `backend/models/auth_models.py` | 认证相关 Pydantic 模型 |
| `frontend/js/router.js` | 前端路由 |
| `frontend/js/auth.js` | 登录状态管理 |
| `frontend/js/qa.js` | 问答页面逻辑 |
| `frontend/js/conversation.js` | 会话页面逻辑 |
| `frontend/js/preference.js` | 偏好设置逻辑 |
| `frontend/pages/qa.html` | 问答页面模板 |
| `frontend/pages/login.html` | 登录页面 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `backend/main.py` | 注册新路由、添加认证中间件 |
| `backend/services.py` | 新增问答向量化逻辑 |
| `backend/models.py` | 扩展模型定义 |
| `backend/config.py` | 添加 JWT 密钥等配置 |
| `frontend/index.html` | 添加导航、路由容器 |
| `frontend/js/app.js` | 集成路由、认证状态 |
| `frontend/css/style.css` | 新增页面样式 |

---

## 10. 启动与迁移

### 10.1 首次启动
```bash
cd backend
pip install -r requirements.txt  # 新增依赖: sqlalchemy, bcrypt, pyjwt

# 自动创建 SQLite 数据库和表
python main.py
```

### 10.2 依赖变更

`requirements.txt` 新增：
```
sqlalchemy>=2.0
bcrypt>=4.0
pyjwt>=2.8
python-multipart>=0.0.9  # OAuth2 表单
```

---

## 11. 验收标准

- [ ] 用户可以注册、登录、退出
- [ ] 可以创建/查看/删除对话会话
- [ ] 可以手动录入问答记录
- [ ] 可以通过 API 方式创建问答记录
- [ ] 可以对问答进行点赞/点踩/修改/标签反馈
- [ ] 支持语义搜索历史问答
- [ ] 支持批量导入外部问答记录
- [ ] 可以设置和更新个人偏好
- [ ] 数据按用户隔离，只能看到自己的记录
- [ ] 文档管理功能保持原有能力
