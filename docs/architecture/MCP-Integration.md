# TokenDance MCP 集成架构设计

> Version: 1.0.0  
> Last Updated: 2026-01-14  
> Status: Design Phase

## 1. 概述

### 1.1 什么是MCP

**MCP (Model Context Protocol)** 是Anthropic推出的标准化协议，用于AI模型与外部工具/数据源之间的通信。

**核心价值**：
- 标准化的工具定义格式
- 统一的通信协议（JSON-RPC 2.0）
- 安全的沙箱执行环境
- 可扩展的资源管理

### 1.2 为什么TokenDance需要MCP

TokenDance的**Vibe-Agentic Workflow**理念要求将**Manus（执行大脑）+ Coworker（执行双手）**的能力进行标准化封装。MCP正是实现这一目标的最佳载体：

| 需求 | MCP解决方案 |
|------|------------|
| Agent能力标准化 | MCP Tools定义 |
| 跨平台工具复用 | MCP Server可被多个Client调用 |
| 安全执行隔离 | MCP Server独立进程 + 权限控制 |
| 动态工具加载 | MCP Server热插拔 |
| 浏览器自动化 | MCP Server for Chrome DevTools |
| 本地文件操作 | MCP Server for FileSystem |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        TokenDance Frontend                       │
│                    (Vue3 + ExecutionPage UI)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ WebSocket / SSE
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TokenDance API Gateway                        │
│                          (FastAPI)                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Engine Core                           │
│  ┌────────────────────────────────────────────────────────┐     │
│  │               Agent Orchestrator                        │     │
│  │  - Task Planning (task_plan.md)                        │     │
│  │  - Context Management                                   │     │
│  │  - Tool Routing                                         │     │
│  └────────────┬───────────────────────────────────────────┘     │
│               │                                                  │
│               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              MCP Manager (NEW)                          │    │
│  │  - Server Registry                                      │    │
│  │  - Connection Pool                                      │    │
│  │  - Request Router                                       │    │
│  │  - Result Aggregator                                    │    │
│  └────────────┬────────────────────────────────────────────┘    │
└───────────────┼─────────────────────────────────────────────────┘
                │
                │ stdio / HTTP
                │
    ┌───────────┼───────────┬───────────────┬─────────────────┐
    │           │           │               │                 │
    ▼           ▼           ▼               ▼                 ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐ ┌──────────────┐
│  MCP    │ │  MCP    │ │  MCP    │ │     MCP      │ │     MCP      │
│ Server  │ │ Server  │ │ Server  │ │   Server     │ │   Server     │
│  (FS)   │ │ (Web)   │ │(Chrome) │ │   (Custom)   │ │   (Manus)    │
└─────────┘ └─────────┘ └─────────┘ └──────────────┘ └──────────────┘
    │           │           │               │                 │
    ▼           ▼           ▼               ▼                 ▼
 Local FS   Web APIs   Chrome        Custom Tools      Manus API
            (Tavily)   DevTools
```

### 2.2 MCP Manager 核心职责

#### 2.2.1 Server Registry（服务注册表）

```python
# backend/app/mcp/registry.py
from typing import Dict, List, Optional
from pydantic import BaseModel

class MCPServerConfig(BaseModel):
    """MCP Server配置"""
    name: str                    # e.g. "filesystem"
    description: str             # 服务描述
    command: str                 # 启动命令，e.g. "node /path/to/server.js"
    args: List[str] = []        # 启动参数
    env: Dict[str, str] = {}    # 环境变量
    transport: str = "stdio"     # stdio | http
    capabilities: List[str]      # ["tools", "resources", "prompts"]
    enabled: bool = True
    auto_start: bool = True      # 是否随TokenDance启动
    
class MCPServerRegistry:
    """MCP Server注册表"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self._load_builtin_servers()
    
    def _load_builtin_servers(self):
        """加载内置MCP Servers"""
        self.register(MCPServerConfig(
            name="filesystem",
            description="本地文件系统操作（Coworker能力）",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", 
                  "/workspace"],
            capabilities=["tools"],
        ))
        
        self.register(MCPServerConfig(
            name="web-search",
            description="Web搜索能力（Manus能力）",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env={"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
            capabilities=["tools"],
        ))
        
        self.register(MCPServerConfig(
            name="chrome-devtools",
            description="Chrome浏览器自动化",
            command="npx",
            args=["-y", "@mcp/server-chrome-devtools"],
            capabilities=["tools"],
            enabled=False,  # 默认禁用，按需启用
        ))
    
    def register(self, config: MCPServerConfig):
        self.servers[config.name] = config
    
    def get(self, name: str) -> Optional[MCPServerConfig]:
        return self.servers.get(name)
    
    def list_enabled(self) -> List[MCPServerConfig]:
        return [s for s in self.servers.values() if s.enabled]
```

#### 2.2.2 Connection Pool（连接池）

```python
# backend/app/mcp/connection_pool.py
import asyncio
from typing import Dict, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPConnectionPool:
    """MCP Server连接池"""
    
    def __init__(self, registry: MCPServerRegistry):
        self.registry = registry
        self.connections: Dict[str, ClientSession] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, server_name: str) -> ClientSession:
        """连接到MCP Server"""
        async with self._lock:
            if server_name in self.connections:
                return self.connections[server_name]
            
            config = self.registry.get(server_name)
            if not config or not config.enabled:
                raise ValueError(f"MCP Server '{server_name}' not found or disabled")
            
            # 创建stdio连接
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env
            )
            
            # 使用context manager管理连接
            stdio_transport = await stdio_client(server_params)
            session = ClientSession(stdio_transport[0], stdio_transport[1])
            
            await session.initialize()
            
            self.connections[server_name] = session
            return session
    
    async def disconnect(self, server_name: str):
        """断开连接"""
        async with self._lock:
            if server_name in self.connections:
                session = self.connections.pop(server_name)
                # MCP session没有显式close方法，依赖transport关闭
    
    async def disconnect_all(self):
        """断开所有连接"""
        for server_name in list(self.connections.keys()):
            await self.disconnect(server_name)
```

#### 2.2.3 Tool Router（工具路由）

```python
# backend/app/mcp/tool_router.py
from typing import List, Dict, Any
from pydantic import BaseModel

class MCPTool(BaseModel):
    """MCP工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str  # 所属MCP Server

class MCPToolRouter:
    """MCP工具路由器"""
    
    def __init__(self, connection_pool: MCPConnectionPool):
        self.pool = connection_pool
        self.tools_cache: Dict[str, MCPTool] = {}
    
    async def discover_tools(self) -> List[MCPTool]:
        """从所有已连接的MCP Server发现工具"""
        all_tools = []
        
        for server_name in self.pool.connections.keys():
            session = self.pool.connections[server_name]
            
            # 调用MCP list_tools
            tools_result = await session.list_tools()
            
            for tool in tools_result.tools:
                mcp_tool = MCPTool(
                    name=f"{server_name}_{tool.name}",  # 加前缀避免冲突
                    description=tool.description,
                    input_schema=tool.inputSchema,
                    server_name=server_name
                )
                all_tools.append(mcp_tool)
                self.tools_cache[mcp_tool.name] = mcp_tool
        
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """调用MCP工具"""
        tool = self.tools_cache.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        session = await self.pool.connect(tool.server_name)
        
        # 移除server前缀，调用原始tool name
        original_tool_name = tool_name.replace(f"{tool.server_name}_", "")
        
        # 调用MCP call_tool
        result = await session.call_tool(original_tool_name, arguments)
        
        return result.content
```

---

## 3. 与TokenDance现有架构集成

### 3.1 Agent Engine集成点

```python
# backend/app/agent/engine.py (修改)
from app.mcp import MCPManager

class AgentEngine:
    def __init__(self, session_id: str, workspace_path: str):
        self.session_id = session_id
        self.workspace_path = workspace_path
        
        # 初始化MCP Manager
        self.mcp_manager = MCPManager(workspace_path)
        
        # 启动内置MCP Servers
        await self.mcp_manager.start_servers([
            "filesystem",   # Coworker能力
            "web-search",   # Manus能力
        ])
    
    async def build_tools_definition(self) -> List[Dict]:
        """构建工具定义（包含MCP工具）"""
        tools = []
        
        # 1. 原有的内置工具
        tools.extend(self._get_builtin_tools())
        
        # 2. MCP工具
        mcp_tools = await self.mcp_manager.discover_tools()
        tools.extend([self._convert_mcp_tool(t) for t in mcp_tools])
        
        return tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict) -> Any:
        """执行工具（路由到MCP或内置）"""
        if tool_name.startswith("filesystem_") or tool_name.startswith("web-search_"):
            # 路由到MCP
            return await self.mcp_manager.call_tool(tool_name, arguments)
        else:
            # 内置工具
            return await self._execute_builtin_tool(tool_name, arguments)
```

### 3.2 三文件工作法集成

MCP Server可以直接读写三文件：

```python
# MCP filesystem工具自动支持
# - read_file("task_plan.md")
# - write_file("findings.md", content)
# - append_file("progress.md", log_entry)

# Agent可以在Prompt中引导：
SYSTEM_PROMPT = """
You have access to three working memory files:
1. task_plan.md - Your roadmap
2. findings.md - Your research notes
3. progress.md - Your execution log

Use filesystem_read_file and filesystem_write_file to manage them.
"""
```

---

## 4. 实施计划

### Phase 1: 基础架构（Week 1-2）

- [ ] 实现MCPServerRegistry
- [ ] 实现MCPConnectionPool
- [ ] 实现MCPToolRouter
- [ ] 集成到AgentEngine
- [ ] 单元测试

### Phase 2: 内置Servers（Week 3）

- [ ] 集成@modelcontextprotocol/server-filesystem
- [ ] 集成@modelcontextprotocol/server-brave-search
- [ ] 配置环境变量管理
- [ ] 测试文件操作能力

### Phase 3: Chrome DevTools集成（Week 4）

- [ ] 集成@mcp/server-chrome-devtools
- [ ] 实现浏览器自动化场景
- [ ] UI中显示浏览器操作日志
- [ ] 测试UI测试能力

### Phase 4: 自定义MCP Server（Week 5-6）

- [ ] 开发TokenDance专用MCP Server
  - Manus API封装
  - Coworker高级能力
  - PPT生成能力
- [ ] 部署和测试

---

## 5. 技术栈

### 5.1 依赖

```json
// package.json (backend)
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0",
    "@modelcontextprotocol/server-filesystem": "^0.5.0",
    "@modelcontextprotocol/server-brave-search": "^0.5.0",
    "@mcp/server-chrome-devtools": "latest"
  }
}
```

### 5.2 Python MCP Client

```txt
# requirements.txt
mcp>=0.9.0
```

---

## 6. 安全考虑

### 6.1 权限控制

- MCP Server运行在独立进程，通过stdio通信
- FileSystem Server限制访问路径为`/workspace/{org_id}/{team_id}/{workspace_id}`
- Chrome DevTools Server需要用户授权才能启动

### 6.2 资源限制

- 每个MCP Server进程限制内存（512MB）
- 超时控制：单次工具调用不超过30秒
- 并发限制：同时最多5个MCP请求

---

## 7. 监控与日志

### 7.1 指标

- `mcp_server_connections` - 活跃连接数
- `mcp_tool_calls_total` - 工具调用次数
- `mcp_tool_call_duration` - 工具调用延迟
- `mcp_tool_errors_total` - 工具错误次数

### 7.2 日志

```python
# 记录所有MCP调用
logger.info(
    "MCP Tool Call",
    extra={
        "server": "filesystem",
        "tool": "read_file",
        "arguments": {"path": "task_plan.md"},
        "duration_ms": 45,
        "success": True
    }
)
```

---

## 8. 参考资源

- [MCP Specification](https://modelcontextprotocol.io/introduction)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Servers Collection](https://github.com/modelcontextprotocol/servers)
- [Claude Desktop MCP Integration](https://docs.anthropic.com/en/docs/build-with-claude/mcp)
