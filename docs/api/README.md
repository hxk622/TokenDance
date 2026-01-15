# TokenDance API 文档

## 概览

TokenDance 后端基于 FastAPI 构建，提供 RESTful API 和 SSE 流式接口。

**Base URL**: `http://localhost:8000/api/v1`

**认证方式**: Bearer Token (JWT)

---

## 目录

- [Sessions API](#sessions-api)
- [Chat API](#chat-api)
- [HITL API](#hitl-api)
- [Stream API](#stream-api)
- [MCP API](#mcp-api)
- [Auth API](#auth-api)

---

## Sessions API

会话管理接口。

### 创建会话

```http
POST /api/v1/sessions
```

**Request Body**:
```json
{
  "workspace_id": "uuid",
  "title": "新会话",
  "task_type": "deep-research"
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "title": "新会话",
  "status": "created",
  "created_at": "2026-01-15T00:00:00Z"
}
```

### 获取会话列表

```http
GET /api/v1/sessions?workspace_id={uuid}&limit=20&offset=0&status=running
```

**Query Parameters**:
- `workspace_id` (required): 工作区 ID
- `limit`: 返回数量 (1-100, 默认 20)
- `offset`: 偏移量 (默认 0)
- `status`: 过滤状态 (created/running/completed/error)

**Response**: `200 OK`
```json
{
  "items": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### 获取会话详情

```http
GET /api/v1/sessions/{session_id}?include_details=true
```

**Query Parameters**:
- `include_details`: 是否包含详细信息

### 更新会话

```http
PATCH /api/v1/sessions/{session_id}
```

**Request Body**:
```json
{
  "title": "新标题",
  "status": "running"
}
```

### 删除会话

```http
DELETE /api/v1/sessions/{session_id}
```

**Response**: `204 No Content`

### 标记会话完成

```http
POST /api/v1/sessions/{session_id}/complete
```

### 获取会话消息

```http
GET /api/v1/sessions/{session_id}/messages?limit=100
```

### 获取会话 Artifacts

```http
GET /api/v1/sessions/{session_id}/artifacts
```

---

## Chat API

Agent 对话接口，支持 SSE 流式响应。

### 发送消息

```http
POST /api/v1/chat/{session_id}/message
```

**Request Body**:
```json
{
  "content": "帮我分析 AI Agent 市场",
  "attachments": []
}
```

**Response**: SSE Stream

SSE 事件类型：
- `thinking`: Agent 推理过程
- `tool_call`: 工具调用开始
- `tool_result`: 工具执行结果
- `content`: 内容生成
- `confirm_required`: 需要 HITL 确认
- `done`: 任务完成
- `error`: 错误发生

**SSE 示例**:
```
event: thinking
data: {"iteration": 1, "reasoning": "分析用户需求..."}

event: tool_call
data: {"tool": "web_search", "args": {"query": "AI Agent market"}}

event: tool_result
data: {"tool": "web_search", "result": "...", "success": true}

event: content
data: {"text": "根据市场分析..."}

event: done
data: {"message": "任务完成", "artifacts": [...]}
```

### 确认 HITL 操作

```http
POST /api/v1/chat/{session_id}/confirm
```

**Request Body**:
```json
{
  "action_id": "uuid",
  "confirmed": true,
  "feedback": "可选反馈"
}
```

### 停止执行

```http
POST /api/v1/chat/{session_id}/stop
```

### 获取 Working Memory

```http
GET /api/v1/chat/{session_id}/working-memory
```

**Response**:
```json
{
  "session_id": "uuid",
  "task_plan": {
    "content": "# Task Plan...",
    "metadata": {}
  },
  "findings": {
    "content": "# Findings...",
    "metadata": {}
  },
  "progress": {
    "content": "# Progress...",
    "metadata": {}
  }
}
```

---

## HITL API

Human-in-the-Loop 确认机制。

### 获取待确认请求

```http
GET /api/v1/sessions/{session_id}/hitl/pending
```

**Response**:
```json
[
  {
    "request_id": "uuid",
    "session_id": "uuid",
    "operation": "file_delete",
    "description": "删除文件 /path/to/file",
    "context": {"file_path": "/path/to/file"},
    "created_at": "2026-01-15T00:00:00Z"
  }
]
```

### 提交确认

```http
POST /api/v1/hitl/{request_id}/confirm
```

**Request Body**:
```json
{
  "approved": true,
  "user_feedback": "可选反馈"
}
```

**Response**:
```json
{
  "request_id": "uuid",
  "approved": true,
  "user_feedback": null,
  "responded_at": "2026-01-15T00:00:00Z"
}
```

### 获取请求详情

```http
GET /api/v1/hitl/{request_id}
```

---

## Stream API

SSE 流式接口，用于实时执行状态推送。

### 连接执行流

```http
GET /api/v1/sessions/{session_id}/stream
```

**Response**: SSE Stream

连接后将持续推送执行状态更新。

---

## MCP API

Model Context Protocol 工具管理。

### 列出可用工具

```http
GET /api/v1/mcp/tools
```

### 执行工具

```http
POST /api/v1/mcp/tools/{tool_name}/execute
```

### 获取工具 Schema

```http
GET /api/v1/mcp/tools/{tool_name}/schema
```

---

## Auth API

认证接口。

### 登录

```http
POST /api/v1/auth/login
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response**:
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 注册

```http
POST /api/v1/auth/register
```

### 刷新 Token

```http
POST /api/v1/auth/refresh
```

### 登出

```http
POST /api/v1/auth/logout
```

---

## 错误响应

所有错误响应遵循以下格式：

```json
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2026-01-15T00:00:00Z"
}
```

### 常见错误码

| HTTP 状态码 | 错误码 | 说明 |
|------------|--------|------|
| 400 | VALIDATION_ERROR | 请求参数验证失败 |
| 401 | UNAUTHORIZED | 未认证或 Token 过期 |
| 403 | FORBIDDEN | 无权限访问 |
| 404 | NOT_FOUND | 资源不存在 |
| 429 | RATE_LIMITED | 请求频率超限 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 速率限制

- 普通接口: 100 次/分钟
- SSE 连接: 10 个并发
- 文件上传: 10 次/分钟

超限后返回 `429 Too Many Requests`。

---

## WebSocket (规划中)

未来版本将支持 WebSocket 双向通信，替代部分 SSE 场景。

---

## 版本历史

- **v1.0.0** (2026-01-15): 初始版本
  - Sessions CRUD
  - Chat SSE 流式响应
  - HITL 确认机制
  - Working Memory API
