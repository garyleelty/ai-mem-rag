# ChromaDB RAG 全栈优化设计

日期: 2026-05-01

## 概述

对 ChromaDB 问答偏好数据库系统进行三方向优化：前端体验与工程化、代码质量与架构、性能与可扩展性。采用方案 A（Tailwind CSS + ES Modules 渐进重构），前端优先推进。

## 1. 前端视觉体系

### 1.1 技术选型

- CSS 框架：Tailwind CSS CDN（零构建）
- 字体：Inter（Google Fonts CDN）
- 图标：内联 SVG

### 1.2 设计令牌

```javascript
// tailwind.config (CDN 内联)
{
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe',
          300: '#a5b4fc', 400: '#818cf8', 500: '#6366f1',
          600: '#4f46e5', 700: '#4338ca', 800: '#3730a3',
        },
        surface: {
          0: '#ffffff', 50: '#f8fafc', 100: '#f1f5f9',
          200: '#e2e8f0', 300: '#cbd5e1',
          500: '#64748b', 600: '#475569', 800: '#1e293b', 900: '#0f172a',
        }
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'float': '0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.06)',
        'glow': '0 0 0 3px rgba(99,102,241,0.15)',
      },
      animation: {
        'slide-up': 'slideUp 0.25s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
      },
    }
  }
}
```

### 1.3 视觉改进

| 元素 | 现状 | 改进 |
|------|------|------|
| 导航栏 | 白底 + 文字 Tab | 毛玻璃效果 + 圆角胶囊 Tab + 品牌渐变 Logo |
| 卡片 | 白底 + 1px 边框 | 白底 + 微阴影 + hover 上浮动画 + 左侧品牌色条 |
| 按钮 | PicoCSS 默认 | 渐变主按钮 + 圆角 + 点击涟漪效果 |
| 弹窗 | `<dialog>` 原生 | 居中毛玻璃遮罩 + 圆角卡片 + 入场动画 |
| 空状态 | 纯文字 | 插画风格 SVG + 引导文案 + 操作按钮 |
| 状态标签 | 纯文字 | 圆角胶囊 + 脉冲动画 |
| 搜索框 | 简单 input | 左侧搜索图标 + 聚焦发光边框 |

### 1.4 动效体系

- 统一过渡：`transition-all duration-200 ease-out`
- 卡片 hover 上浮：`hover:-translate-y-0.5 hover:shadow-float`
- 弹窗入场：slideUp 动画（0.25s ease-out）
- 连接状态：脉冲动画

### 1.5 页面布局

- 问答页面：双栏布局（280px 会话侧边栏 + 弹性主内容区）
- 文档页面：三栏布局（260px 集合管理 + 弹性上传/预览 + 300px 文档列表）
- 偏好页面：居中单栏（max-w-2xl）

## 2. JS 模块化拆分

### 2.1 目标

将 857 行单文件 `app.js` 拆分为 8 个 ES Modules，使用 `<script type="module">` 加载，零构建。

### 2.2 目录结构

```
frontend/js/
├── app.js              # 入口：初始化 + 路由（~50行）
├── api.js              # API 请求封装 + 缓存（~80行）
├── state.js            # 全局状态管理（~40行）
├── auth.js             # 认证逻辑（~80行）
├── utils.js            # 工具函数（~30行）
└── pages/
    ├── qa.js           # 问答记录页（~250行）
    ├── documents.js    # 文档管理页（~250行）
    └── preferences.js  # 偏好设置页（~100行）
```

### 2.3 模块职责

| 模块 | 导出 | 依赖 |
|------|------|------|
| `state.js` | `state`, `setState()` | 无 |
| `api.js` | `api()`, `apiForm()`, `cachedApi()`, `invalidateCache()` | `state.js` |
| `auth.js` | `checkAuth()`, `handleLogin()`, `handleRegister()`, `handleLogout()`, `updateUserUI()` | `api.js`, `state.js` |
| `utils.js` | `escapeHtml()`, `formatDate()`, `setConnectionStatus()` | 无 |
| `pages/qa.js` | `render()`, `init()` | `api.js`, `state.js`, `utils.js` |
| `pages/documents.js` | `render()`, `init()` | `api.js`, `state.js`, `utils.js` |
| `pages/preferences.js` | `render()`, `init()` | `api.js`, `state.js`, `utils.js` |
| `app.js` | 入口 | `auth.js`, `state.js`, `pages/*` |

### 2.4 依赖规则

- `pages/*` → `api.js` / `state.js` / `utils.js`，页面间不互相引用
- `state.js` 不依赖任何其他模块（无循环依赖）
- ES Modules 不支持 `file://` 协议，需 HTTP 服务器（已有 start.sh）

### 2.5 HTML 变化

```html
<!-- 旧 -->
<script src="js/app.js"></script>
<!-- 新 -->
<script type="module" src="js/app.js"></script>
```

## 3. 后端架构优化

### 3.1 拆分 services.py

将 272 行的 `services.py` 按领域拆分为 4 个模块：

```
backend/services/
├── __init__.py          # 统一导出
├── chroma.py            # ChromaDB 客户端 + 集合操作
├── embedding.py         # Embedding 模型加载 + 编码
├── document.py          # 文档解析 + 分块 + 上传处理
└── search.py            # 语义搜索逻辑
```

| 模块 | 职责 |
|------|------|
| `chroma.py` | ChromaDB 客户端单例、集合 CRUD、文档列表/分块/删除 |
| `embedding.py` | 模型单例、编码函数、预热函数 |
| `document.py` | 文件校验、保存、PDF/DOCX 解析、分块、上传处理 |
| `search.py` | QA 记录索引、删除索引、语义搜索、相似查找 |

### 3.2 迁移旧路由

将 `main.py` 中的文档管理端点迁移到 `routers/documents.py`，使 `main.py` 变为极简入口（仅注册路由和中间件）。

### 3.3 文档 API 加认证

`routers/documents.py` 所有端点添加 `Depends(get_current_user)` 认证依赖。

### 3.4 统一错误处理

新增 `exceptions.py`，定义 `AppError` 异常类和全局异常处理器，统一错误响应格式：

```json
{"detail": "错误信息", "code": 400}
```

### 3.5 清理残留

- 删除 `backend/models.py`（旧版，已被 `models/` 目录替代）

### 3.6 优化后目录结构

```
backend/
├── main.py              # 极简入口
├── config.py            # 配置（不变）
├── database.py          # 数据库（不变）
├── auth.py              # 认证（不变）
├── exceptions.py        # 新增：统一错误处理
├── models/
│   ├── __init__.py
│   ├── db_models.py     # 新增 DocumentIndex 模型
│   └── schemas.py       # 新增 UploadStatusResponse
├── routers/
│   ├── auth.py
│   ├── conversations.py
│   ├── documents.py     # 新增：从 main.py 迁移
│   ├── feedback.py
│   ├── preferences.py
│   ├── qa_records.py    # 重构：使用 services/search.py
│   └── tags.py
└── services/
    ├── __init__.py
    ├── chroma.py
    ├── embedding.py
    ├── document.py
    └── search.py
```

## 4. 性能与可扩展性优化

### 4.1 Embedding 模型预热

在 FastAPI startup 事件中预加载模型并做一次推理，避免首次请求阻塞（3-10 秒 → < 100ms）。

### 4.2 文档上传异步化

使用 FastAPI `BackgroundTasks` 将文件处理改为后台任务，上传接口立即返回任务 ID，前端可轮询 `/upload/status/{task_id}` 获取进度。

### 4.3 问答记录批量编码

新增 `batch_index_qa_records()` 函数，批量编码比逐条快 5-10 倍。导入 100 条问答从 ~30 秒降至 ~5 秒。

### 4.4 文档定位优化

新增 `DocumentIndex` 表（SQLite），维护 `chroma_doc_id → collection_name` 映射。查询文档分块从 O(n) 集合扫描优化为 O(1) 索引查询。

### 4.5 SQLite 索引优化

补充复合索引：
- `qa_records(user_id, created_at DESC)`
- `qa_records(conversation_id)`
- `feedbacks(qa_record_id)`
- `conversations(user_id, updated_at DESC)`

### 4.6 前端请求缓存

在 `api.js` 中加入 30 秒 TTL 的简易缓存层，Tab 切换时命中缓存避免重复请求。写入操作后自动清除相关缓存。

### 4.7 预期效果

| 优化项 | 优化前 | 优化后 |
|--------|--------|--------|
| 首次 API 请求 | 3-10 秒 | < 100ms |
| 文档上传 10MB PDF | 可能超时 | 立即返回，后台处理 |
| 批量导入 100 条问答 | ~30 秒 | ~5 秒 |
| 查询文档分块 | O(n) 集合扫描 | O(1) 索引查询 |
| 切换 Tab 回到问答页 | 重新请求全部数据 | 30 秒内命中缓存 |

## 5. 实施顺序

1. **阶段一：前端重构** — Tailwind CSS 视觉重写 + JS 模块化拆分
2. **阶段二：后端重构** — services 拆分 + 路由迁移 + 认证补全 + 统一错误处理
3. **阶段三：性能优化** — 模型预热 + 上传异步化 + 批量编码 + 索引优化 + 前端缓存
