# MCP (Model Context Protocol) 模块设计

> MCP：AI 的 USB-C 接口 - 标准化的外部系统连接协议
> Version: 1.0 | Created: 2026-01-09
> Reference: Anthropic MCP Specification, Manus MCP Implementation

---

## 1. 设计理念

### 1.1 核心定位

**MCP = AI 的 USB-C 接口**

```
传统方式:
Agent ──> Custom API Integration ──> Google Drive
      ──> Another Custom Integration ──> GitHub
      ──> Yet Another Integration ──> Slack
      (每个集成都是独立开发，不可复用)

MCP 方式:
Agent ──> MCP Protocol ──┬──> MCP Server (Google Drive)
                         ├──> MCP Server (GitHub)
                         └──> MCP Server (Slack)
      (统一协议，即插即用)
```

### 1.2 设计原则

| 原则 | 说明 | 来源 |
|------|------|------|
| **标准化协议** | 所有 MCP Server 遵循统一接口规范 | Anthropic MCP Spec |
| **即插即用** | 新增 MCP Server 无需修改 Agent 代码 | Manus |
| **安全隔离** | 每个 MCP Server 独立运行，权限隔离 | 安全设计 |
| **可观测性** | 所有 MCP 调用记录到 Context Graph | TokenDance 特色 |
| **双层支持** | 预置 MCP + 自定义 MCP | Manus |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     TokenDance Agent                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              MCP Manager (核心协调器)                   │  │
│  │  - MCP Registry (注册表)                              │  │
│  │  - Connection Pool (连接池)                           │  │
│  │  - Auth Manager (认证管理)                            │  │
│  │  - Capability Discovery (能力发现)                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↕ MCP Protocol                      │
├─────────────────────────────────────────────────────────────┤
│                    MCP Server Layer                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ Google   │ GitHub   │  Slack   │  Notion  │  ...     │  │
│  │  Drive   │          │          │          │          │  │
│  │  MCP     │   MCP    │   MCP    │   MCP    │   MCP    │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│  ┌──────────┬──────────┬──────────────────────────────┐    │
│  │ Custom   │ Internal │  Private Database            │    │
│  │  API     │   CRM    │        MCP                   │    │
│  │  MCP     │   MCP    │                              │    │
│  └──────────┴──────────┴──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 MCP Protocol 核心概念

**MCP Server 提供三种能力**：

```typescript
interface MCPServer {
  // 1. Resources (资源) - 暴露数据供 Agent 读取
  resources: {
    list(): Resource[]
    read(uri: string): ResourceContent
    subscribe?(uri: string): ResourceStream
  }
  
  // 2. Tools (工具) - 暴露操作供 Agent 调用
  tools: {
    list(): Tool[]
    call(name: string, args: any): ToolResult
  }
  
  // 3. Prompts (提示词) - 暴露可复用的 Prompt 模板
  prompts: {
    list(): Prompt[]
    get(name: string, args: any): PromptContent
  }
}
```

---

## 3. 目录结构设计

### 3.1 项目目录

```bash
TokenDance/
├── backend/
│   └── app/
│       └── mcp/
│           ├── __init__.py
│           ├── manager.py           # MCP Manager 核心
│           ├── protocol.py          # MCP 协议实现
│           ├── registry.py          # MCP 注册表
│           ├── auth.py              # OAuth/API Key 管理
│           ├── client.py            # MCP Client（与 Server 通信）
│           └── schemas.py           # Pydantic 数据模型
│
├── mcp/                             # MCP Server 目录
│   ├── README.md                    # MCP 使用指南
│   │
│   ├── built-in/                    # 预置 MCP Servers
│   │   ├── google-drive/
│   │   │   ├── MCP.md              # MCP Metadata
│   │   │   ├── server.py           # MCP Server 实现
│   │   │   ├── config.yaml         # 配置文件
│   │   │   └── requirements.txt    # Python 依赖
│   │   │
│   │   ├── github/
│   │   │   ├── MCP.md
│   │   │   ├── server.py
│   │   │   └── config.yaml
│   │   │
│   │   ├── slack/
│   │   ├── notion/
│   │   ├── linear/
│   │   ├── jira/
│   │   └── confluence/
│   │
│   └── custom/                      # 自定义 MCP Servers
│       ├── .gitignore              # 忽略自定义 MCP（可选）
│       └── example/
│           ├── MCP.md
│           ├── server.py
│           └── config.yaml
│
└── docs/
    └── modules/
        └── MCP-Design.md           # 本设计文档
```

### 3.2 MCP.md 规范

```yaml
---
name: google-drive
version: 1.0.0
description: "Google Drive MCP Server - 文件读写、搜索、分享"
author: TokenDance Team
category: cloud-storage
auth_type: oauth2
capabilities:
  - resources    # 支持 Resources
  - tools        # 支持 Tools
  - prompts      # 支持 Prompts (可选)
status: stable   # stable | beta | experimental
---

# Google Drive MCP Server

## 功能说明

提供 Google Drive 文件操作能力：
- 列出文件和文件夹
- 读取文件内容
- 创建/更新/删除文件
- 搜索文件
- 分享文件

## Resources (资源)

| URI | 说明 | 示例 |
|-----|------|------|
| `drive://files` | 列出所有文件 | `drive://files?limit=10` |
| `drive://file/{id}` | 读取文件内容 | `drive://file/abc123` |
| `drive://search?q={query}` | 搜索文件 | `drive://search?q=report` |

## Tools (工具)

### create_file
创建文件到 Google Drive

**参数**：
```json
{
  "name": "report.pdf",
  "content": "base64_encoded_content",
  "folder_id": "folder_abc123" // 可选
}
```

### share_file
分享文件给他人

**参数**：
```json
{
  "file_id": "abc123",
  "email": "user@example.com",
  "role": "reader" // reader | writer | commenter
}
```

## Prompts (提示词)

### organize_files
整理文件到文件夹的提示词模板

**参数**：
```json
{
  "file_list": ["file1.pdf", "file2.docx"],
  "organization_strategy": "by_date" // by_date | by_type | by_name
}
```

## 认证配置

### OAuth 2.0 设置
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建 OAuth 2.0 客户端 ID
3. 添加重定向 URI: `http://localhost:8000/mcp/callback/google-drive`
4. 配置 Scopes:
   - `https://www.googleapis.com/auth/drive.file`
   - `https://www.googleapis.com/auth/drive.readonly`

### 环境变量
```bash
GOOGLE_DRIVE_CLIENT_ID=your_client_id
GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret
```

## 依赖项

```txt
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-api-python-client==2.115.0
```

## 使用示例

```python
# 在 Agent 中使用
tools = [
    {
        "name": "google_drive.create_file",
        "description": "创建文件到 Google Drive",
        "input_schema": {...}
    }
]

# Agent 调用
result = await mcp_manager.call_tool(
    server="google-drive",
    tool="create_file",
    args={
        "name": "research_report.pdf",
        "content": pdf_content
    }
)
```

## 故障排查

### 常见问题
1. **认证失败**: 检查 OAuth 配置和 Scopes
2. **权限不足**: 需要用户重新授权更高权限
3. **速率限制**: Google Drive API 每用户每日 1000 次请求

## 更新日志

### v1.0.0 (2026-01-09)
- 初始版本
- 支持基础文件操作
- OAuth 2.0 认证
```

---

## 4. 核心组件设计

### 4.1 MCP Manager

```python
# backend/app/mcp/manager.py
from typing import Dict, List, Optional
from .protocol import MCPServer, Resource, Tool, Prompt
from .registry import MCPRegistry
from .auth import AuthManager
from .client import MCPClient

class MCPManager:
    """
    MCP 核心管理器
    
    职责:
    1. MCP Server 注册与发现
    2. 连接管理与生命周期
    3. 能力查询与调用路由
    4. 认证与权限管理
    """
    
    def __init__(self):
        self.registry = MCPRegistry()
        self.auth_manager = AuthManager()
        self.clients: Dict[str, MCPClient] = {}
        
    async def initialize(self):
        """启动时加载所有 MCP Servers"""
        # 1. 扫描 mcp/built-in/ 目录
        built_in_servers = await self._scan_built_in_servers()
        
        # 2. 扫描 mcp/custom/ 目录
        custom_servers = await self._scan_custom_servers()
        
        # 3. 注册到 Registry
        for server in built_in_servers + custom_servers:
            await self.registry.register(server)
        
        # 4. 加载已保存的认证信息
        await self.auth_manager.load_credentials()
        
        print(f"Loaded {len(self.registry.list())} MCP Servers")
    
    async def connect(self, server_name: str) -> MCPClient:
        """
        连接到 MCP Server
        
        Args:
            server_name: MCP Server 名称 (e.g., "google-drive")
        
        Returns:
            MCPClient 实例
        """
        if server_name in self.clients:
            return self.clients[server_name]
        
        server_info = self.registry.get(server_name)
        if not server_info:
            raise ValueError(f"MCP Server '{server_name}' not found")
        
        # 检查认证
        if server_info.auth_type == "oauth2":
            credentials = await self.auth_manager.get_oauth_token(server_name)
            if not credentials:
                raise ValueError(f"MCP Server '{server_name}' requires OAuth authentication")
        elif server_info.auth_type == "api_key":
            credentials = await self.auth_manager.get_api_key(server_name)
        else:
            credentials = None
        
        # 启动 MCP Server 进程
        client = MCPClient(server_info, credentials)
        await client.start()
        
        self.clients[server_name] = client
        return client
    
    async def list_resources(self, server_name: str) -> List[Resource]:
        """列出 MCP Server 提供的所有资源"""
        client = await self.connect(server_name)
        return await client.list_resources()
    
    async def read_resource(self, server_name: str, uri: str) -> str:
        """读取资源内容"""
        client = await self.connect(server_name)
        return await client.read_resource(uri)
    
    async def list_tools(self, server_name: str) -> List[Tool]:
        """列出 MCP Server 提供的所有工具"""
        client = await self.connect(server_name)
        return await client.list_tools()
    
    async def call_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        arguments: dict
    ) -> dict:
        """
        调用 MCP Server 的工具
        
        Args:
            server_name: MCP Server 名称
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具执行结果
        """
        client = await self.connect(server_name)
        result = await client.call_tool(tool_name, arguments)
        
        # 记录到 Context Graph (TokenDance 特色)
        await self._log_to_context_graph(
            server_name=server_name,
            tool_name=tool_name,
            arguments=arguments,
            result=result
        )
        
        return result
    
    async def get_prompt(
        self, 
        server_name: str, 
        prompt_name: str, 
        arguments: dict = None
    ) -> str:
        """获取 MCP Server 的 Prompt 模板"""
        client = await self.connect(server_name)
        return await client.get_prompt(prompt_name, arguments or {})
    
    async def shutdown(self):
        """关闭所有 MCP Server 连接"""
        for client in self.clients.values():
            await client.stop()
        self.clients.clear()
```

### 4.2 MCP Registry

```python
# backend/app/mcp/registry.py
from typing import Dict, List, Optional
from pydantic import BaseModel
import yaml
from pathlib import Path

class MCPServerInfo(BaseModel):
    """MCP Server 元数据"""
    name: str
    version: str
    description: str
    author: str
    category: str
    auth_type: str  # oauth2 | api_key | none
    capabilities: List[str]  # resources | tools | prompts
    status: str  # stable | beta | experimental
    server_path: Path
    config_path: Path

class MCPRegistry:
    """MCP Server 注册表"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerInfo] = {}
    
    async def register(self, server_info: MCPServerInfo):
        """注册 MCP Server"""
        self.servers[server_info.name] = server_info
        print(f"Registered MCP Server: {server_info.name} v{server_info.version}")
    
    def get(self, name: str) -> Optional[MCPServerInfo]:
        """获取 MCP Server 信息"""
        return self.servers.get(name)
    
    def list(self, category: str = None) -> List[MCPServerInfo]:
        """列出所有 MCP Servers"""
        if category:
            return [s for s in self.servers.values() if s.category == category]
        return list(self.servers.values())
    
    def search(self, query: str) -> List[MCPServerInfo]:
        """搜索 MCP Servers"""
        query_lower = query.lower()
        return [
            s for s in self.servers.values()
            if query_lower in s.name.lower() or query_lower in s.description.lower()
        ]
```

### 4.3 Auth Manager

```python
# backend/app/mcp/auth.py
from typing import Optional, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import json
from pathlib import Path

class AuthManager:
    """
    MCP 认证管理器
    
    支持:
    1. OAuth 2.0 (Google, GitHub, Slack, etc.)
    2. API Key (OpenAI, Anthropic, etc.)
    3. Bearer Token (Custom APIs)
    """
    
    def __init__(self):
        self.credentials_path = Path("data/mcp_credentials.json")
        self.credentials: Dict[str, dict] = {}
    
    async def load_credentials(self):
        """加载已保存的认证信息"""
        if self.credentials_path.exists():
            with open(self.credentials_path, "r") as f:
                self.credentials = json.load(f)
    
    async def save_credentials(self):
        """保存认证信息"""
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.credentials_path, "w") as f:
            json.dump(self.credentials, f, indent=2)
    
    async def start_oauth_flow(
        self, 
        server_name: str, 
        client_id: str, 
        client_secret: str,
        scopes: List[str],
        redirect_uri: str
    ) -> str:
        """
        启动 OAuth 2.0 认证流程
        
        Returns:
            授权 URL
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true"
        )
        
        # 保存 state 用于验证
        self.credentials[f"{server_name}_oauth_state"] = state
        await self.save_credentials()
        
        return auth_url
    
    async def complete_oauth_flow(
        self, 
        server_name: str, 
        code: str
    ) -> Credentials:
        """完成 OAuth 2.0 认证"""
        # 实现 OAuth 回调处理
        # 保存 access_token 和 refresh_token
        pass
    
    async def get_oauth_token(self, server_name: str) -> Optional[str]:
        """获取 OAuth Access Token"""
        creds = self.credentials.get(f"{server_name}_oauth")
        if not creds:
            return None
        
        # 检查 token 是否过期，如需刷新
        # ...
        
        return creds.get("access_token")
    
    async def set_api_key(self, server_name: str, api_key: str):
        """设置 API Key"""
        self.credentials[f"{server_name}_api_key"] = api_key
        await self.save_credentials()
    
    async def get_api_key(self, server_name: str) -> Optional[str]:
        """获取 API Key"""
        return self.credentials.get(f"{server_name}_api_key")
```

---

## 5. 预置 MCP Servers

### 5.1 优先级列表

| 优先级 | MCP Server | 用途 | 认证方式 | 预计工作量 |
|--------|-----------|------|---------|-----------|
| **P0** | **google-drive** | 文件存储、协作 | OAuth 2.0 | 2 天 |
| **P0** | **github** | 代码托管、Issue | OAuth 2.0 | 2 天 |
| **P0** | **slack** | 团队通信、通知 | OAuth 2.0 | 1.5 天 |
| **P1** | **notion** | 知识库、文档 | OAuth 2.0 | 2 天 |
| **P1** | **linear** | 项目管理 | API Key | 1 天 |
| **P1** | **jira** | Bug 跟踪 | API Key | 1.5 天 |
| **P2** | **confluence** | 文档协作 | API Key | 1 天 |
| **P2** | **google-calendar** | 日程管理 | OAuth 2.0 | 1 天 |
| **P2** | **gmail** | 邮件发送 | OAuth 2.0 | 1 天 |
| **P3** | **trello** | 看板管理 | API Key | 0.5 天 |

### 5.2 Google Drive MCP Server 实现示例

```python
# mcp/built-in/google-drive/server.py
from typing import List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.protocol import Resource, Tool, ToolResult

class GoogleDriveMCPServer:
    """Google Drive MCP Server"""
    
    def __init__(self, credentials: Credentials):
        self.service = build('drive', 'v3', credentials=credentials)
    
    # ===== Resources =====
    
    async def list_resources(self) -> List[Resource]:
        """列出可用资源"""
        return [
            Resource(
                uri="drive://files",
                name="All Files",
                description="列出所有文件",
                mime_type="application/json"
            ),
            Resource(
                uri="drive://search",
                name="Search Files",
                description="搜索文件",
                mime_type="application/json"
            )
        ]
    
    async def read_resource(self, uri: str) -> str:
        """读取资源内容"""
        if uri.startswith("drive://files"):
            # 列出文件
            results = self.service.files().list(
                pageSize=10,
                fields="files(id, name, mimeType)"
            ).execute()
            return json.dumps(results.get('files', []))
        
        elif uri.startswith("drive://file/"):
            # 读取文件内容
            file_id = uri.split("/")[-1]
            content = self.service.files().get_media(fileId=file_id).execute()
            return content.decode('utf-8')
        
        elif uri.startswith("drive://search"):
            # 搜索文件
            query = uri.split("?q=")[1]
            results = self.service.files().list(
                q=f"name contains '{query}'",
                fields="files(id, name)"
            ).execute()
            return json.dumps(results.get('files', []))
    
    # ===== Tools =====
    
    async def list_tools(self) -> List[Tool]:
        """列出可用工具"""
        return [
            Tool(
                name="create_file",
                description="创建文件到 Google Drive",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "content": {"type": "string"},
                        "mime_type": {"type": "string", "default": "text/plain"},
                        "folder_id": {"type": "string"}
                    },
                    "required": ["name", "content"]
                }
            ),
            Tool(
                name="share_file",
                description="分享文件给他人",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string"},
                        "email": {"type": "string"},
                        "role": {
                            "type": "string",
                            "enum": ["reader", "writer", "commenter"]
                        }
                    },
                    "required": ["file_id", "email", "role"]
                }
            ),
            Tool(
                name="delete_file",
                description="删除文件",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_id": {"type": "string"}
                    },
                    "required": ["file_id"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: dict) -> ToolResult:
        """调用工具"""
        if name == "create_file":
            return await self._create_file(**arguments)
        elif name == "share_file":
            return await self._share_file(**arguments)
        elif name == "delete_file":
            return await self._delete_file(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def _create_file(
        self, 
        name: str, 
        content: str, 
        mime_type: str = "text/plain",
        folder_id: Optional[str] = None
    ) -> ToolResult:
        """创建文件"""
        file_metadata = {'name': name}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode('utf-8')),
            mimetype=mime_type
        )
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return ToolResult(
            content=[{
                "type": "text",
                "text": f"File created successfully: {file.get('webViewLink')}"
            }],
            is_error=False
        )
    
    async def _share_file(self, file_id: str, email: str, role: str) -> ToolResult:
        """分享文件"""
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        
        self.service.permissions().create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()
        
        return ToolResult(
            content=[{
                "type": "text",
                "text": f"File shared with {email} as {role}"
            }],
            is_error=False
        )
    
    async def _delete_file(self, file_id: str) -> ToolResult:
        """删除文件"""
        self.service.files().delete(fileId=file_id).execute()
        
        return ToolResult(
            content=[{
                "type": "text",
                "text": "File deleted successfully"
            }],
            is_error=False
        )
```

---

## 6. 与 Agent 集成

### 6.1 Tool-Use 层集成

```python
# backend/app/agent/tool_use.py
from app.mcp.manager import MCPManager

class ToolUseModule:
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
    
    async def get_available_tools(self) -> List[dict]:
        """获取所有可用工具（包括 MCP Tools）"""
        tools = []
        
        # 1. 内置工具
        tools.extend(self._get_built_in_tools())
        
        # 2. MCP 工具
        mcp_servers = self.mcp_manager.registry.list()
        for server in mcp_servers:
            if "tools" in server.capabilities:
                mcp_tools = await self.mcp_manager.list_tools(server.name)
                for tool in mcp_tools:
                    tools.append({
                        "name": f"{server.name}.{tool.name}",
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "source": "mcp"
                    })
        
        return tools
    
    async def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """执行工具（支持 MCP Tools）"""
        if "." in tool_name:
            # MCP Tool: server_name.tool_name
            server_name, tool_name_only = tool_name.split(".", 1)
            return await self.mcp_manager.call_tool(
                server_name=server_name,
                tool_name=tool_name_only,
                arguments=arguments
            )
        else:
            # 内置工具
            return await self._execute_built_in_tool(tool_name, arguments)
```

### 6.2 Context Manager 集成

```python
# backend/app/agent/context_manager.py
from app.mcp.manager import MCPManager

class ContextManager:
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
    
    async def inject_mcp_resources(self, task_context: str) -> str:
        """
        根据任务上下文注入相关 MCP Resources
        
        Example:
        - 任务提到 "Google Drive"，自动注入 drive://files 资源
        - 任务提到 "GitHub"，自动注入 github://repos 资源
        """
        # 1. 分析任务上下文，识别需要的资源
        required_servers = self._identify_required_servers(task_context)
        
        # 2. 注入相关资源
        injected_resources = []
        for server_name in required_servers:
            resources = await self.mcp_manager.list_resources(server_name)
            for resource in resources:
                content = await self.mcp_manager.read_resource(
                    server_name, 
                    resource.uri
                )
                injected_resources.append({
                    "source": f"{server_name}/{resource.name}",
                    "content": content
                })
        
        # 3. 附加到 Context
        if injected_resources:
            context_addition = "\n\n=== External Resources (via MCP) ===\n"
            for res in injected_resources:
                context_addition += f"\n[{res['source']}]\n{res['content']}\n"
            return task_context + context_addition
        
        return task_context
```

---

## 7. 前端 UI 设计

### 7.1 MCP 管理页面

```
┌──────────────────────────────────────────────────────────┐
│  📦 MCP Servers                                 [+ Add]  │
├──────────────────────────────────────────────────────────┤
│  🔍 Search: [____________]      Filter: [All ▼]         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  ✅ Google Drive                  [Connected]   │    │
│  │  云存储 · OAuth 2.0 · v1.0.0                    │    │
│  │  Tools: 5 | Resources: 3 | Prompts: 2          │    │
│  │  [Settings] [Reconnect] [Disconnect]            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  ⚠️  GitHub                       [Not Connected] │  │
│  │  代码托管 · OAuth 2.0 · v1.0.0                   │    │
│  │  [Connect with GitHub]                           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  ✅ Slack                         [Connected]   │    │
│  │  团队通信 · OAuth 2.0 · v1.0.0                   │    │
│  │  Tools: 3 | Resources: 2                        │    │
│  │  [Settings] [Reconnect] [Disconnect]            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  📌 Custom API                    [Not Configured]│   │
│  │  自定义 MCP · API Key · v0.1.0                   │    │
│  │  [Configure]                                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 7.2 MCP Tool 调用记录

```
┌──────────────────────────────────────────────────────────┐
│  📊 MCP Activity Log                                     │
├──────────────────────────────────────────────────────────┤
│  🔍 Filter: [All Servers ▼] [All Tools ▼] [Last 7 Days ▼]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  2026-01-09 10:05:32                                    │
│  google-drive.create_file                                │
│  ✅ Success · 1.2s                                       │
│  Created: research_report.pdf                            │
│  [View Details]                                          │
│                                                          │
│  ────────────────────────────────────────────────────   │
│                                                          │
│  2026-01-09 10:03:15                                    │
│  slack.send_message                                      │
│  ✅ Success · 0.8s                                       │
│  Sent message to #engineering                            │
│  [View Details]                                          │
│                                                          │
│  ────────────────────────────────────────────────────   │
│                                                          │
│  2026-01-09 09:58:42                                    │
│  github.create_issue                                     │
│  ❌ Failed · 2.3s                                        │
│  Error: Unauthorized - token expired                     │
│  [Retry] [View Details]                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 8. 安全设计

### 8.1 权限隔离

```python
# 每个 MCP Server 独立进程，权限隔离
# backend/app/mcp/client.py

class MCPClient:
    async def start(self):
        """启动 MCP Server（独立进程）"""
        self.process = await asyncio.create_subprocess_exec(
            "python", self.server_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            # 安全隔离：限制资源
            preexec_fn=self._set_process_limits
        )
    
    def _set_process_limits(self):
        """设置进程资源限制"""
        import resource
        # 限制内存：512MB
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, -1))
        # 限制 CPU 时间：60s
        resource.setrlimit(resource.RLIMIT_CPU, (60, -1))
```

### 8.2 敏感信息保护

```python
# 认证信息加密存储
import cryptography.fernet

class AuthManager:
    def __init__(self, encryption_key: bytes):
        self.fernet = Fernet(encryption_key)
    
    async def save_credentials(self):
        """加密保存认证信息"""
        encrypted = self.fernet.encrypt(
            json.dumps(self.credentials).encode()
        )
        with open(self.credentials_path, "wb") as f:
            f.write(encrypted)
    
    async def load_credentials(self):
        """解密加载认证信息"""
        with open(self.credentials_path, "rb") as f:
            encrypted = f.read()
        decrypted = self.fernet.decrypt(encrypted)
        self.credentials = json.loads(decrypted)
```

### 8.3 HITL (Human-in-the-Loop)

```python
# 高风险 MCP 操作需要人工确认
RISKY_OPERATIONS = [
    "google-drive.delete_file",
    "github.delete_repository",
    "slack.archive_channel",
    "notion.delete_page"
]

async def call_tool_with_confirmation(
    server_name: str, 
    tool_name: str, 
    arguments: dict
) -> dict:
    """调用工具（高风险操作需确认）"""
    tool_full_name = f"{server_name}.{tool_name}"
    
    if tool_full_name in RISKY_OPERATIONS:
        # 发送确认请求给用户
        confirmed = await request_user_confirmation(
            action=tool_full_name,
            details=arguments
        )
        
        if not confirmed:
            return {"error": "User cancelled operation"}
    
    # 执行工具
    return await mcp_manager.call_tool(server_name, tool_name, arguments)
```

---

## 9. 可观测性

### 9.1 Context Graph 集成

```python
# 所有 MCP 调用记录到 Context Graph
async def _log_to_context_graph(
    self,
    server_name: str,
    tool_name: str,
    arguments: dict,
    result: dict
):
    """记录 MCP 调用到 Context Graph"""
    await self.context_graph.add_node(
        type="mcp_call",
        data={
            "server": server_name,
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": result.get("duration_ms")
        }
    )
    
    # 关联到当前 Task
    await self.context_graph.add_edge(
        from_node=current_task_id,
        to_node=mcp_call_node_id,
        relation="used_mcp"
    )
```

### 9.2 监控指标

```python
# backend/app/mcp/metrics.py
from prometheus_client import Counter, Histogram

# MCP 调用次数
mcp_calls_total = Counter(
    'mcp_calls_total',
    'Total MCP tool calls',
    ['server', 'tool', 'status']
)

# MCP 调用延迟
mcp_call_duration = Histogram(
    'mcp_call_duration_seconds',
    'MCP tool call duration',
    ['server', 'tool']
)

# MCP 认证失败
mcp_auth_failures = Counter(
    'mcp_auth_failures_total',
    'Total MCP authentication failures',
    ['server']
)
```

---

## 10. 开发指南

### 10.1 创建自定义 MCP Server

```bash
# 1. 创建目录
mkdir -p mcp/custom/my-api

# 2. 创建 MCP.md
cat > mcp/custom/my-api/MCP.md << EOF
---
name: my-api
version: 1.0.0
description: "My Custom API MCP Server"
author: Your Name
category: custom
auth_type: api_key
capabilities:
  - tools
status: experimental
---

# My API MCP Server

## Tools

### fetch_data
Fetch data from my API

**Parameters**:
- endpoint: API endpoint path
- params: Query parameters
EOF

# 3. 创建 server.py
cat > mcp/custom/my-api/server.py << 'EOF'
class MyAPIMCPServer:
    async def list_tools(self):
        return [
            Tool(
                name="fetch_data",
                description="Fetch data from my API",
                input_schema={...}
            )
        ]
    
    async def call_tool(self, name, arguments):
        if name == "fetch_data":
            # 实现逻辑
            pass
EOF

# 4. 重启 TokenDance
# MCP Manager 会自动发现并加载新 MCP Server
```

### 10.2 测试 MCP Server

```python
# tests/test_mcp_google_drive.py
import pytest
from app.mcp.manager import MCPManager

@pytest.mark.asyncio
async def test_google_drive_create_file():
    mcp_manager = MCPManager()
    await mcp_manager.initialize()
    
    result = await mcp_manager.call_tool(
        server_name="google-drive",
        tool_name="create_file",
        arguments={
            "name": "test.txt",
            "content": "Hello MCP!"
        }
    )
    
    assert result["is_error"] == False
    assert "File created" in result["content"][0]["text"]
```

---

## 11. 实施计划

### Phase 1: MCP 基础框架（Week 1-2）
- [ ] MCP Manager 核心实现
- [ ] MCP Registry 实现
- [ ] Auth Manager（OAuth 2.0 + API Key）
- [ ] MCP Client（进程通信）
- [ ] 数据库 Schema（mcp_servers, mcp_credentials）

### Phase 2: 预置 MCP Servers（Week 3-4）
- [ ] Google Drive MCP Server（P0）
- [ ] GitHub MCP Server（P0）
- [ ] Slack MCP Server（P0）
- [ ] Notion MCP Server（P1）
- [ ] Linear MCP Server（P1）

### Phase 3: 前端 UI（Week 5）
- [ ] MCP 管理页面
- [ ] OAuth 认证流程
- [ ] MCP Activity Log
- [ ] MCP Settings

### Phase 4: 集成与测试（Week 6）
- [ ] Tool-Use 层集成
- [ ] Context Manager 集成
- [ ] HITL 确认机制
- [ ] 单元测试 + 集成测试

---

## 12. 对比与参考

### 12.1 TokenDance vs Manus MCP

| 维度 | Manus | TokenDance (设计) |
|------|-------|-------------------|
| **预置 MCP** | Google Drive, GitHub, Slack | 相同 + Notion, Linear |
| **自定义 MCP** | 支持 | 支持（mcp/custom/） |
| **认证方式** | OAuth 2.0 | OAuth 2.0 + API Key |
| **能力发现** | 自动发现 | 自动发现 + Registry |
| **可观测性** | 基础日志 | Context Graph 深度集成 ✨ |
| **安全隔离** | 未知 | 独立进程 + 资源限制 ✨ |
| **HITL** | 支持 | 支持（高风险操作） |

### 12.2 TokenDance 创新点

1. **Context Graph 集成**：所有 MCP 调用自动记录到图谱，可追溯
2. **资源限制**：每个 MCP Server 独立进程，限制内存/CPU
3. **Prompts 支持**：除 Resources/Tools 外，支持 Prompt 模板复用
4. **分类管理**：MCP Servers 按 category 分类（cloud-storage, code, communication）

---

## 13. 附录

### A. MCP Protocol 参考

- [Anthropic MCP Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/anthropics/mcp-python)

### B. OAuth 2.0 配置指南

**Google Cloud Console**:
1. 创建项目
2. 启用 Google Drive API
3. 创建 OAuth 2.0 客户端 ID
4. 配置重定向 URI: `http://localhost:8000/mcp/callback/google-drive`

**GitHub OAuth App**:
1. Settings → Developer settings → OAuth Apps
2. 创建 New OAuth App
3. 配置 Callback URL: `http://localhost:8000/mcp/callback/github`

### C. 相关文档

- [Tool-Use 设计](./Tool-Use.md)
- [Context Management](./Context-Management.md)
- [Execution 设计](./Execution.md)

---

**文档版本**：v1.0
**最后更新**：2026-01-09
**作者**：TokenDance Team
**参考来源**：Anthropic MCP Spec, Manus Documentation
