# Sandbox 设计文档

## 1. 核心目标

**为 Agent 提供安全、隔离、统一的代码执行环境**

```
统一入口 + 智能路由 + 分层安全 + 容器池化 = 可信的执行基础设施
```

## 2. 实现状态

✅ **已实现** - 所有核心模块已完成

| 模块 | 文件 | 状态 |
|------|------|------|
| 统一风险评估 | `app/sandbox/risk_policy.py` | ✅ |
| 统一工作空间 | `app/sandbox/workspace.py` | ✅ |
| Sandbox 管理器 | `app/sandbox/manager.py` | ✅ |
| 容器池 | `app/sandbox/pool.py` | ✅ |
| 浏览器路由 | `app/sandbox/browser_router.py` | ✅ |
| 确认服务 | `app/sandbox/confirmation.py` | ✅ |
| 执行器 | `app/sandbox/executors/` | ✅ |
| run_code 工具 | `app/agent/tools/builtin/run_code.py` | ✅ |

## 3. 架构总览

```
                          Agent Tool 调用
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    WorldInterface.execute()                       │
│                    (工具是世界接口，不是插件)                        │
└──────────────────────────────────────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
       run_code            browser_*         file_ops
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│  SandboxManager   │  │   BrowserRouter   │  │  AgentWorkspace   │
│  (统一代码执行)    │  │  (统一浏览器)      │  │  (统一文件系统)    │
└─────────┬─────────┘  └─────────┬─────────┘  └───────────────────┘
          │                      │
          │  UnifiedRiskPolicy   │
          │  + SecurityMode      │
          │                      │
          ├─→ Subprocess         ├─→ External Browser
          ├─→ DockerSimple       └─→ AIO Sandbox Browser
          └─→ AIOSandboxPool
```

## 4. 核心组件

### 4.1 SandboxManager - 统一入口

**文件**: `app/sandbox/manager.py`

所有代码执行的统一入口，职责：
1. 风险评估 (UnifiedRiskPolicy)
2. 请求确认 (ConfirmationService)
3. Sandbox 选择 (SecurityMode)
4. 执行并返回结果

```python
from app.sandbox.manager import SandboxManager
from app.sandbox.types import ExecutionRequest, SecurityMode

# 创建管理器
manager = SandboxManager(
    session_id="session_123",
    security_mode=SecurityMode.STRICT  # 生产环境
)

# 执行代码
result = await manager.execute(
    ExecutionRequest(code="print('Hello')", language="python")
)

print(result.success, result.stdout)
```

### 4.2 UnifiedRiskPolicy - 分层安全

**文件**: `app/sandbox/risk_policy.py`

**核心原则**：
- 静态分析**仅用于提示**，不作为安全边界
- 真正的安全边界是 Docker/AIO 隔离
- `SecurityMode` 控制是否强制隔离

```python
from app.sandbox.risk_policy import UnifiedRiskPolicy, SecurityMode
from app.sandbox.types import SandboxType

# 风险评估（用于提示）
risk = UnifiedRiskPolicy.assess("import os", "python")
print(risk.level, risk.detected_patterns)

# 安全决策（真正的边界）
sandbox_type = UnifiedRiskPolicy.get_required_sandbox(
    risk, 
    mode=SecurityMode.STRICT  # 非 SAFE 代码强制 Docker
)
```

**SecurityMode**:
- `PERMISSIVE`: 开发环境，按静态分析建议选择 Sandbox
- `STRICT`: 生产环境，非 SAFE 代码强制使用 Docker 隔离

### 4.3 AgentWorkspace - 路径安全

**文件**: `app/sandbox/workspace.py`

统一所有 Sandbox 的文件路径，带**路径遍历保护**。

```python
from app.sandbox.workspace import AgentWorkspace

workspace = AgentWorkspace("session_123")

# 安全的文件操作
workspace.write_file("output/result.txt", "Hello")
content = workspace.read_file("output/result.txt")

# 路径遍历攻击会被阻止
workspace.write_file("../../etc/passwd", "hack")  # 抛出 PathTraversalError
```

**安全检查**：
1. 禁止绝对路径 (`/etc/passwd`)
2. 禁止 `..` 遍历 (`../../secret`)
3. `resolve().relative_to()` 验证

### 4.4 AIOSandboxPool - 容器池

**文件**: `app/sandbox/pool.py`

管理 AIO Sandbox 容器生命周期，修复了 **TOCTOU 并发问题**。

```python
from app.sandbox.pool import AIOSandboxPool, PoolConfig

pool = AIOSandboxPool(
    config=PoolConfig(max_instances=10, min_instances=2)
)
await pool.start()

# 获取实例（自动绑定到 session）
sandbox = await pool.acquire("session_123")
result = await sandbox.execute(request)
await pool.release("session_123")
```

**SessionState**:
- `IDLE`: 空闲，可分配
- `ACQUIRING`: 正在创建中（防止重复创建）
- `BUSY`: 正在使用

### 4.5 BrowserRouter - 单实例浏览器

**文件**: `app/sandbox/browser_router.py`

统一浏览器操作入口，**单实例模式**。

```python
from app.sandbox.browser_router import BrowserRouter, BrowserAction

router = BrowserRouter("session_123")

# 执行浏览器操作
result = await router.execute(
    BrowserAction(action="navigate", params={"url": "https://example.com"}),
    context={"is_research": True}  # 使用 AIO Sandbox Browser
)
```

**路由策略**：
- `needs_file_access=True` → AIO Sandbox Browser
- `is_research=True` → AIO Sandbox Browser
- 其他 → External Browser (更轻量)

### 4.6 ConfirmationService - Human-in-the-Loop

**文件**: `app/sandbox/confirmation.py`

高风险操作的用户确认机制。

```python
from app.sandbox.confirmation import (
    WebSocketConfirmationService,
    AutoApproveConfirmationService,
)

# 生产环境：通过 WebSocket 请求用户确认
confirmation = WebSocketConfirmationService(ws_manager)

# 开发环境：自动批准
confirmation = AutoApproveConfirmationService()

# 集成到 SandboxManager
manager = SandboxManager(
    session_id="session_123",
    confirmation_service=confirmation
)
```

## 5. 执行器

### 5.1 SubprocessExecutor

**文件**: `app/sandbox/executors/subprocess_executor.py`

直接子进程执行，最轻量，仅用于 `RiskLevel.SAFE` 代码。

### 5.2 DockerSimpleSandbox

**文件**: `app/sandbox/executors/docker.py`

Docker 容器隔离，每次执行创建新容器。

特点：
- Volume 挂载工作空间
- 禁用网络 (`network_mode="none"`)
- 内存限制

### 5.3 AIOSandboxClient

**文件**: `app/sandbox/executors/aio.py`

连接 AIO Sandbox 服务，完整执行环境。

特点：
- 支持浏览器操作
- 文件系统持久化
- 通过 HTTP API 通信

## 6. 工具集成

### run_code 工具

**文件**: `app/agent/tools/builtin/run_code.py`

核心 4 工具之一，通过 SandboxManager 执行。

```python
from app.sandbox.manager import SandboxManager
from app.agent.tools.builtin.run_code import RunCodeTool

manager = SandboxManager("session_123")
run_code = RunCodeTool(manager)

result = await run_code.execute(
    code="print('Hello')",
    language="python",
    timeout=30
)
```

## 7. 解决的安全问题

| # | 问题 | 修复方案 | 关键代码 |
|---|------|---------|---------|
| 1 | 静态分析可绕过 | 分层安全：静态分析仅提示，SecurityMode.STRICT 强制隔离 | `risk_policy.py` |
| 2 | 路径遍历漏洞 | `_safe_path()` 验证所有文件操作 | `workspace.py` |
| 3 | TOCTOU 并发问题 | `SessionState.ACQUIRING` 锁内标记 | `pool.py` |
| 4 | 浏览器多实例 | 单实例模式，切换时自动关闭 | `browser_router.py` |
| 5 | 确认机制缺失 | `ConfirmationService` 集成 | `confirmation.py` |
| 6 | 工具与 Sandbox 割裂 | `SandboxManager` 统一入口 | `manager.py` |
| 7 | 文件路径不一致 | `AgentWorkspace` 统一路径 | `workspace.py` |

## 8. 目录结构

```
backend/app/sandbox/
├── __init__.py           # 模块导出
├── exceptions.py         # 自定义异常
├── types.py              # 核心类型
├── risk_policy.py        # 统一风险评估
├── workspace.py          # 统一工作空间
├── manager.py            # Sandbox 管理器
├── pool.py               # AIO 容器池
├── browser_router.py     # 浏览器路由
├── confirmation.py       # 确认服务
└── executors/
    ├── __init__.py
    ├── base.py           # 执行器基类
    ├── subprocess_executor.py
    ├── docker.py
    └── aio.py
```

## 9. 使用示例

### 基本使用

```python
from app.sandbox.manager import SandboxManager
from app.sandbox.types import ExecutionRequest, SecurityMode

async def execute_code():
    manager = SandboxManager(
        session_id="user_session_123",
        security_mode=SecurityMode.STRICT
    )
    
    result = await manager.execute(
        ExecutionRequest(
            code="import pandas as pd; print(pd.__version__)",
            language="python",
            timeout=30
        )
    )
    
    if result.success:
        print(f"输出: {result.stdout}")
        print(f"使用的 Sandbox: {result.sandbox_type.value}")
    else:
        print(f"错误: {result.error}")
    
    await manager.cleanup()
```

### 带确认服务

```python
from app.sandbox.confirmation import AutoApproveConfirmationService

manager = SandboxManager(
    session_id="session_123",
    confirmation_service=AutoApproveConfirmationService(),  # 开发模式
    security_mode=SecurityMode.PERMISSIVE
)
```

### 使用容器池

```python
from app.sandbox.pool import AIOSandboxPool

pool = AIOSandboxPool()
await pool.start()

manager = SandboxManager(
    session_id="session_123",
    aio_pool=pool  # 使用池化的 AIO Sandbox
)

# ... 执行代码 ...

await pool.stop()
```
