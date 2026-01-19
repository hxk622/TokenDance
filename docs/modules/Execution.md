# Execution设计文档

## 1. 核心目标

**统一的执行引擎，作为高层调度器，委托具体执行给专门的子系统**

## 2. 与 SandboxManager 的关系

### 2.1 职责划分

```
ExecutionEngine (Execution.md)        SandboxManager (Sandbox.md)
──────────────────────────────────────────────────────────────────
职责：高层调度                       职责：代码执行实现
- 动作类型路由                        - 风险评估 (UnifiedRiskPolicy)
- Context Graph 记录                  - Sandbox 选择 (Subprocess/Docker/AIO)
- 失败处理与重试                       - 容器池化 (AIOSandboxPool)
                                      - 安全隔离

关系：ExecutionEngine 调用 SandboxManager，不重复实现代码执行逻辑
```

### 2.2 调用关系图

```
                    Agent Tool 调用
                         │
                         ▼
┌───────────────────────────────────────────────┐
│               WorldInterface                      │
└───────────────────────┬───────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────┐
│           ExecutionEngine (调度器)                 │
│  - 动作路由                                        │
│  - Context Graph 记录                             │
│  - 失败处理与重试                                   │
└──────────┬────────────┬─────────────┬───────────┘
           │            │             │
           ▼            ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Sandbox  │  │ Browser  │  │  Agent   │
    │ Manager  │  │ Router   │  │Workspace │
    └────┬─────┘  └────┬─────┘  └──────────┘
         │            │
         │            ├───→ External Browser
         │            └───→ AIO Sandbox Browser
         │
         ├───→ Subprocess
         ├───→ DockerSimple
         └───→ AIOSandboxPool
```

## 3. 执行引擎架构

```python
# app/execution/engine.py

from app.sandbox.manager import SandboxManager
from app.sandbox.browser_router import BrowserRouter, BrowserAction
from app.sandbox.workspace import AgentWorkspace
from app.sandbox.pool import AIOSandboxPool
from app.sandbox.types import ExecutionRequest, ExecutionResult

class ExecutionEngine:
    """统一执行引擎 - 高层调度器
    
    设计原则：
    - 不重复实现子系统逻辑
    - 委托代码执行给 SandboxManager
    - 委托浏览器操作给 BrowserRouter
    - 委托文件操作给 AgentWorkspace
    """
    
    def __init__(self, session_id: str, aio_pool: AIOSandboxPool = None):
        self.session_id = session_id
        
        # 统一工作空间
        self.workspace = AgentWorkspace(session_id)
        
        # 子系统（委托，不重复实现）
        self.sandbox_manager = SandboxManager(
            session_id=session_id,
            workspace=self.workspace,
            aio_pool=aio_pool
        )
        self.browser_router = BrowserRouter(session_id=session_id)
        
        # Context Graph 记录
        self.context_graph = ContextGraphRecorder()
    
    async def execute_action(self, action: Action) -> ExecutionResult:
        """执行动作 - 统一入口"""
        
        # 记录到 Context Graph
        action_node_id = await self.context_graph.record_action_start(
            session_id=self.session_id,
            action_type=action.type,
            action_data=action.data
        )
        
        try:
            # 路由到子系统
            if action.type == ActionType.CODE_EXECUTION:
                result = await self._execute_code(action)
            elif action.type == ActionType.WEB_BROWSING:
                result = await self._execute_browser(action)
            elif action.type == ActionType.FILE_OPERATION:
                result = await self._execute_file(action)
            else:
                raise ValueError(f"Unknown action type: {action.type}")
            
            # 记录成功
            await self.context_graph.record_action_complete(
                action_node_id=action_node_id,
                result=result
            )
            
            return result
            
        except Exception as e:
            # 记录失败
            await self.context_graph.record_action_failure(
                action_node_id=action_node_id,
                error=str(e)
            )
            raise
    
    async def _execute_code(self, action: Action) -> ExecutionResult:
        """代码执行 - 委托给 SandboxManager
        
        注意：不直接调用 DockerSandbox，而是通过 SandboxManager
        SandboxManager 会：
        1. 风险评估 (UnifiedRiskPolicy)
        2. 智能选择 Sandbox 类型
        3. 执行并返回结果
        """
        request = ExecutionRequest(
            code=action.data["code"],
            language=action.data.get("language", "python"),
            timeout=action.data.get("timeout", 30),
            session_id=self.session_id
        )
        
        return await self.sandbox_manager.execute(request)
    
    async def _execute_browser(self, action: Action) -> ExecutionResult:
        """浏览器操作 - 委托给 BrowserRouter
        
        BrowserRouter 会根据上下文选择：
        - External Browser（简单操作）
        - AIO Sandbox 内置浏览器（需要文件系统共享）
        """
        browser_action = BrowserAction(
            action=action.data["action"],
            params=action.data.get("params", {})
        )
        context = {
            "needs_file_access": action.data.get("needs_file_access", False),
            "is_research": action.data.get("is_research", False)
        }
        result = await self.browser_router.execute(browser_action, context=context)
        return ExecutionResult(
            success=result.success,
            stdout=str(result.data) if result.data else "",
            error=result.error
        )
    
    async def _execute_file(self, action: Action) -> ExecutionResult:
        """文件操作 - 使用 AgentWorkspace"""
        op = action.data["operation"]
        path = action.data["path"]
        
        try:
            if op == "read":
                content = self.workspace.read_file(path)
                return ExecutionResult(success=True, stdout=content)
            elif op == "write":
                self.workspace.write_file(path, action.data["content"])
                return ExecutionResult(success=True)
            elif op == "list":
                files = self.workspace.list_files(path)
                return ExecutionResult(success=True, stdout="\n".join(files))
            else:
                return ExecutionResult(success=False, error=f"Unknown op: {op}")
        except Exception as e:
            return ExecutionResult(success=False, error=str(e))
    
    async def cleanup(self):
        """清理资源"""
        await self.sandbox_manager.cleanup()
        await self.browser_router.cleanup()
```

## 3. 与Planning集成

```python
# Planning生成的Plan由Execution执行

class PlanExecutor:
    """计划执行器"""
    
    async def execute_plan(self, plan: Plan):
        """执行计划"""
        engine = ExecutionEngine(self.session_id)
        
        for step in plan.steps:
            # 检查依赖
            if not await self._check_dependencies(step, plan):
                raise DependencyNotMetError(f"Step {step.id} dependencies not met")
            
            # 执行
            result = await engine.execute_action(step.action)
            
            # 记录结果
            step.result = result
            step.status = "completed" if result.success else "failed"
            
            # 失败处理
            if not result.success and not step.allow_failure:
                # 触发Re-planning
                await self._handle_step_failure(step, plan)
                break
```

## 4. 与Self-Reflection集成

```python
# Execution提供External-Loop反思的真实反馈

async def execute_with_reflection(action: Action, max_retries: int = 2):
    """带反思的执行"""
    
    engine = ExecutionEngine(session_id)
    
    for attempt in range(max_retries + 1):
        result = await engine.execute_action(action)
        
        if result.success:
            return result
        
        # 失败：反思
        reflection = await analyze_failure(action, result)
        
        # 修正动作
        action = await revise_action(action, reflection)
```

## 5. 总结

**Execution Engine职责**：
- 统一动作执行接口
- 路由到Sandbox/Browser/FileSystem
- 记录执行轨迹到Context Graph
- 为Planning和Reflection提供执行支持

**与其他模块关系**：
- Planning生成Plan → Execution执行
- Execution失败 → Self-Reflection介入
- 所有执行记录到Context Graph
- 结果存储到文件系统（Dual Streams）
