## 项目简介

一个全栈 AI 助手与个人效率应用，包含：

- **后端**: Django 5 + DRF + JWT（djangorestframework-simplejwt）
- **前端**: Vue 3 + Vite + Element Plus + Pinia
- **AI 能力**: LangChain + DeepSeek，大模型对话 + 本地知识库检索（Qdrant 本地存储）
- **功能模块**:
  - 用户注册/登录（JWT）
  - 待办事项 todo
  - 记账（账户/分类/交易）
  - AI 聊天与知识库（网页内容向量化、检索问答）
  - 力扣题库浏览


## 目录结构

```
ai2plan/                  # 后端 Django 项目
  config/                 # Django 配置（urls 暴露全部 API）
  users/ todo/ accounting/ chat/ leetcode/
frontend/                 # 前端 Vue 3 + Vite
vector_db/                # 可选：本地向量库持久化目录
```


## 环境要求

- Python 3.10+
- Node.js 20+（前端 package.json 指定 ^20.19.0 || >=22.12.0）
- SQLite（开发环境默认）
- 可选：本地磁盘版 Qdrant（通过 `QdrantClient(path=...)` 使用）


## 后端快速开始（Django）

1) 创建虚拟环境并激活（macOS zsh 示例）

```bash
cd ai2plan
python3 -m venv .venv
source .venv/bin/activate
```

2) 安装依赖（若仓库未附 `requirements.txt`，可按下列安装）

```bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers python-dotenv pydantic
pip install langchain langchain-community langchain-core langchain-deepseek langchain-qdrant langchain-huggingface qdrant-client
pip install sentence-transformers
```

3) 配置环境变量：在 `ai2plan/` 下新建 `.env`

```bash
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL_NAME=deepseek-chat
SERPAPI_API_KEY=

EMBEDDING_MODEL=BAAI/bge-large-en-v1.5

EMBEDDING_COLLECTION=xiaolang_document

COLLECTION_NAME=xiaolang_document

PERSIST_DIR=./vector_db
CHUNCK_SIZE=800
CHUN_OVERLAP=50
MEMORY_KEY=chat_history
```

4) 迁移并启动（默认端口 8000）

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

说明：

- 当前 `config/settings.py` 中 `DEBUG=True`、`CORS_ALLOW_ALL_ORIGINS=True`、`SECRET_KEY` 为明文，仅适合开发环境。
- 数据库为 SQLite，文件默认在 `ai2plan/db.sqlite3`。


## 前端快速开始（Vue 3 + Vite）

1) 安装依赖并启动开发服务器

```bash
cd frontend
npm install
npm run dev
```

2) 后端地址配置

- 默认在 `frontend/src/services/api.js`：
  - `baseURL: 'http://127.0.0.1:8000'`
  - 刷新令牌接口在拦截器中写死：`http://127.0.0.1:8000/api/refresh-token/`
- 如后端域名/端口变更，请同步修改上述两处，或改造为 Vite 环境变量（如 `VITE_API_BASE`）。


## 主要 API（节选）

所有路由在 `ai2plan/config/urls.py` 注册：

- 认证与用户
  - `POST /api/register/` 注册
  - `POST /api/login/` 登录，返回 `access`、`refresh`
  - `POST /api/refresh-token/` 刷新 `access`
- 聊天与知识库（需登录，除添加文档接口）
  - `POST /api/chat/` 发送消息，返回 AI 回复
  - `POST /api/add-doc/` 批量添加 URL 到本地向量库（默认允许）
  - `GET/POST /api/histories/` 会话历史，按用户隔离
- 待办 todo
  - `GET/POST /api/todos/`，`GET/PUT/PATCH/DELETE /api/todos/{id}/`
- 记账 accounting
  - `GET/POST /api/accounts/`、`/api/categories/`、`/api/transactions/`
- 力扣 leetcode
  - `GET /api/leetcode/`、`GET /api/leetcode/{id}/`

示例：登录并访问受保护接口

```bash
curl -X POST http://127.0.0.1:8000/api/login/ -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

curl http://127.0.0.1:8000/api/todos/ -H "Authorization: Bearer <access>"
```


## AI 与检索说明

- 嵌入：`HuggingFaceEmbeddings(model=os.getenv("EMBEDDING_MODEL"))`
- 向量库：`QdrantClient(path=os.getenv("PERSIST_DIR","./vector_store"))`
- 集合名：`EMBEDDING_COLLECTION`
- 文档添加：`POST /api/add-doc/`，请求体：`{"urls": ["https://..."]}`

若首次运行会在 `PERSIST_DIR` 下创建本地存储；国内网络建议配置镜像或预下载模型以加速。


## 前端认证与自动刷新

- 登录后 `access`/`refresh` 与用户信息持久化在 `localStorage`。
- Axios 拦截器在 401 时自动调用 `/api/refresh-token/` 刷新 `access` 并重放请求。
- Pinia `auth` store 提供 `login`、`register`、`logout` 与 `isAuthenticated` 计算属性。



## 常见问题

- 报缺少环境变量：`ai2plan/chat/src/Tools.py` 会校验 `SERPAPI_API_KEY`、`DEEPSEEK_API_KEY`、`DEEPSEEK_API_BASE`。
- 刷新令牌失败：前端会清空本地状态并需要重新登录。
- 嵌入模型下载慢：使用国内镜像或预下载模型。




