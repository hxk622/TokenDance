# TokenDance MCP Servers

> MCP (Model Context Protocol) = AI 的 USB-C 接口
> 标准化的外部系统连接协议

---

## 快速开始

### 什么是 MCP？

MCP 是一个开放标准，允许 AI Agent 通过统一协议连接到各种外部系统（Google Drive、GitHub、Slack 等），就像 USB-C 可以连接任何设备一样。

**传统方式** vs **MCP 方式**：
```
❌ 传统：每个集成都需要单独开发
Agent ──> Custom Google Drive Integration
      ──> Custom GitHub Integration
      ──> Custom Slack Integration

✅ MCP：统一协议，即插即用
Agent ──> MCP Protocol ──┬──> Google Drive MCP
                         ├──> GitHub MCP
                         └──> Slack MCP
```

---

## 目录结构

```
mcp/
├── README.md              # 本文档
├── built-in/              # 预置 MCP Servers
│   ├── google-drive/      # Google Drive MCP
│   ├── github/            # GitHub MCP
│   ├── slack/             # Slack MCP
│   ├── notion/            # Notion MCP
│   └── linear/            # Linear MCP
│
└── custom/                # 自定义 MCP Servers
    └── example/           # 示例 MCP Server
```

---

## 预置 MCP Servers

### ✅ Google Drive
- **功能**：文件读写、搜索、分享
- **认证**：OAuth 2.0
- **Tools**：create_file, share_file, delete_file
- **Resources**：drive://files, drive://file/{id}, drive://search

### ✅ GitHub
- **功能**：仓库管理、Issue、Pull Request
- **认证**：OAuth 2.0
- **Tools**：create_issue, create_pr, merge_pr
- **Resources**：github://repos, github://issues

### ✅ Slack
- **功能**：发送消息、管理频道
- **认证**：OAuth 2.0
- **Tools**：send_message, create_channel
- **Resources**：slack://channels, slack://messages

### ✅ Notion
- **功能**：页面创建、数据库查询
- **认证**：OAuth 2.0
- **Tools**：create_page, query_database
- **Resources**：notion://pages, notion://databases

### ✅ Linear
- **功能**：Issue 管理、项目跟踪
- **认证**：API Key
- **Tools**：create_issue, update_issue
- **Resources**：linear://issues, linear://projects

---

## 使用 MCP

### 1. 在 TokenDance UI 中连接

1. 进入 **Settings → MCP Servers**
2. 找到想要连接的 MCP Server（如 Google Drive）
3. 点击 **Connect**
4. 完成 OAuth 授权（或输入 API Key）
5. 连接成功后，Agent 即可使用该 MCP 的工具

### 2. Agent 自动调用 MCP Tools

当你的任务需要时，Agent 会自动调用 MCP Tools：

**示例 1：保存文件到 Google Drive**
```
用户: 帮我把这份报告保存到 Google Drive
Agent: [自动调用] google-drive.create_file
结果: ✅ 文件已保存到 Google Drive
```

**示例 2：创建 GitHub Issue**
```
用户: 创建一个 Issue，标题是"修复登录 bug"
Agent: [自动调用] github.create_issue
结果: ✅ Issue #123 已创建
```

### 3. MCP Resources（Context 注入）

当任务涉及外部数据时，Agent 会自动注入 MCP Resources 到 Context：

```
用户: 分析我最近的 Google Drive 文件
Agent: [自动读取] drive://files?limit=10
Context: [Google Drive 文件列表已注入]
结果: 分析报告...
```

---

## 创建自定义 MCP Server

### Step 1: 创建目录

```bash
mkdir -p mcp/custom/my-api
cd mcp/custom/my-api
```

### Step 2: 创建 MCP.md

```yaml
---
name: my-api
version: 1.0.0
description: "My Custom API MCP Server"
author: Your Name
category: custom
auth_type: api_key  # oauth2 | api_key | none
capabilities:
  - tools           # resources | tools | prompts
status: stable      # stable | beta | experimental
---

# My API MCP Server

## 功能说明

连接到我的自定义 API，提供数据查询和操作能力。

## Tools

### fetch_data
从 API 获取数据

**参数**：
```json
{
  "endpoint": "/api/users",
  "params": {"limit": 10}
}
```

## 认证配置

在 TokenDance UI 中配置 API Key：
```
Settings → MCP Servers → my-api → Configure
```
```

### Step 3: 创建 server.py

```python
from typing import List
from mcp.protocol import Tool, ToolResult
import requests

class MyAPIMCPServer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.example.com"
    
    async def list_tools(self) -> List[Tool]:
        return [
            Tool(
                name="fetch_data",
                description="从 API 获取数据",
                input_schema={
                    "type": "object",
                    "properties": {
                        "endpoint": {"type": "string"},
                        "params": {"type": "object"}
                    },
                    "required": ["endpoint"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: dict) -> ToolResult:
        if name == "fetch_data":
            endpoint = arguments["endpoint"]
            params = arguments.get("params", {})
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            return ToolResult(
                content=[{
                    "type": "text",
                    "text": response.json()
                }],
                is_error=False
            )
```

### Step 4: 创建 config.yaml

```yaml
server:
  host: localhost
  port: 3000

auth:
  type: api_key
  env_var: MY_API_KEY

timeout: 30
retry: 3
```

### Step 5: 创建 requirements.txt

```txt
requests==2.31.0
mcp-python-sdk==0.1.0
```

### Step 6: 重启 TokenDance

MCP Manager 会自动发现并加载新的 MCP Server！

---

## MCP Server 开发规范

### MCP.md 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | MCP Server 名称（唯一） |
| version | string | 版本号（Semantic Versioning） |
| description | string | 简短描述 |
| author | string | 作者 |
| category | string | 分类（cloud-storage, code, communication, custom） |
| auth_type | string | 认证方式（oauth2, api_key, none） |
| capabilities | array | 能力列表（resources, tools, prompts） |
| status | string | 状态（stable, beta, experimental） |

### MCP Server 三大能力

#### 1. Resources（资源）
暴露数据供 Agent 读取，格式：`scheme://path`

**示例**：
- `drive://files` - 列出所有文件
- `github://repos` - 列出所有仓库
- `slack://channels` - 列出所有频道

#### 2. Tools（工具）
暴露操作供 Agent 调用

**必须实现**：
- `list_tools()` - 列出所有工具
- `call_tool(name, arguments)` - 执行工具

#### 3. Prompts（提示词）
暴露可复用的 Prompt 模板（可选）

**示例**：
```python
async def get_prompt(self, name: str, arguments: dict) -> str:
    if name == "organize_files":
        return f"请将以下文件按{arguments['strategy']}整理..."
```

---

## 安全注意事项

### 1. 敏感操作需 HITL 确认

以下操作会触发用户确认：
- 删除操作（delete_file, delete_repository）
- 归档操作（archive_channel）
- 权限变更（change_permissions）

### 2. API Key 加密存储

所有认证信息（OAuth Token、API Key）都会加密存储在：
```
data/mcp_credentials.json (encrypted)
```

### 3. 进程隔离

每个 MCP Server 运行在独立进程中，限制：
- 最大内存：512MB
- 最大 CPU 时间：60s
- 无网络访问权限（除 MCP Server 本身）

---

## 故障排查

### MCP Server 无法连接

1. 检查认证配置
   - OAuth 2.0：检查 Client ID/Secret
   - API Key：检查 Key 是否有效

2. 查看日志
   ```bash
   tail -f logs/mcp.log
   ```

3. 重启 MCP Server
   ```
   Settings → MCP Servers → [Server Name] → Reconnect
   ```

### MCP Tool 调用失败

1. 查看 MCP Activity Log
   ```
   Settings → MCP Servers → Activity Log
   ```

2. 检查参数是否正确
   - 参考 `MCP.md` 中的 Tools 定义
   - 确保必填参数都已提供

3. 检查 API 速率限制
   - Google Drive：1000 次/天/用户
   - GitHub：5000 次/小时
   - Slack：Tier 2+: 100+ 次/分钟

---

## 监控与可观测性

### MCP Activity Log

所有 MCP 调用都会记录到 Activity Log：
- 调用时间
- 调用的 Server 和 Tool
- 参数和结果
- 执行时长
- 成功/失败状态

### Context Graph 集成

所有 MCP 调用自动记录到 Context Graph，可追溯：
```cypher
// 查询某个任务使用的所有 MCP 调用
MATCH (task:Task)-[:USED_MCP]->(mcp:MCPCall)
WHERE task.id = "task_123"
RETURN mcp
```

---

## 常见问题

### Q: MCP 和内置工具有什么区别？

**内置工具**：TokenDance 自带的工具（web_search, file_read 等）
**MCP 工具**：通过 MCP 协议连接的外部系统（Google Drive, GitHub 等）

优先使用 MCP 工具，因为：
- 标准化协议，易扩展
- 独立进程，更安全
- 可复用，社区生态

### Q: 我可以禁用某个 MCP Server 吗？

可以。在 Settings → MCP Servers 中，点击 **Disconnect** 即可。

### Q: 自定义 MCP Server 会被提交到 Git 吗？

默认情况下，`mcp/custom/` 目录不会被提交到 Git（已在 .gitignore 中）。如果你想提交，可以修改 `.gitignore`。

### Q: MCP Server 崩溃了怎么办？

MCP Manager 会自动重启崩溃的 MCP Server（最多重试 3 次）。如果仍然失败，会记录错误日志并通知用户。

---

## 参考资源

- **Anthropic MCP Specification**: https://modelcontextprotocol.io/
- **MCP Python SDK**: https://github.com/anthropics/mcp-python
- **MCP 设计文档**: [../docs/modules/MCP-Design.md](../docs/modules/MCP-Design.md)
- **Tool-Use 设计文档**: [../docs/modules/Tool-Use.md](../docs/modules/Tool-Use.md)

---

**版本**：v1.0
**最后更新**：2026-01-09
**维护者**：TokenDance Team
