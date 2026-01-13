# Execution设计文档

## 1. 核心目标

**统一的执行引擎，集成Sandbox、Browser、文件系统，为Agent提供可靠的动作执行能力**

## 2. 执行引擎架构

```python
# packages/core/execution/engine.py

class ExecutionEngine:
    """统一执行引擎"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.sandbox = DockerSandbox(session_id)
        self.browser = BrowserAutomation()
        self.fs = AgentFileSystem(session_id)
        self.context_graph = ContextGraphRecorder()
    
    async def execute_action(self, action: Action) -> ExecutionResult:
        """执行动作"""
        
        # 记录到Context Graph
        action_node_id = await self.context_graph.record_action_start(
            session_id=self.session_id,
            action_type=action.type,
            action_data=action.data
        )
        
        try:
            # 根据动作类型路由到不同执行器
            if action.type == "code_execution":
                result = await self._execute_code(action)
            elif action.type == "web_browsing":
                result = await self._execute_web_action(action)
            elif action.type == "file_operation":
                result = await self._execute_file_operation(action)
            elif action.type == "tool_call":
                result = await self._execute_tool(action)
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
        """执行代码"""
        return await self.sandbox.execute_code(
            code=action.data["code"],
            language=action.data.get("language", "python"),
            timeout=action.data.get("timeout", 30)
        )
    
    async def _execute_web_action(self, action: Action) -> ExecutionResult:
        """执行Web动作"""
        if action.data["action"] == "navigate":
            result = await self.browser.navigate_and_extract(action.data["url"])
        elif action.data["action"] == "fill_form":
            result = await self.browser.fill_form(
                action.data["url"],
                action.data["form_data"]
            )
        return ExecutionResult(success=True, data=result)
    
    async def _execute_file_operation(self, action: Action) -> ExecutionResult:
        """执行文件操作"""
        if action.data["operation"] == "read":
            content = await self.fs.read(action.data["path"])
            return ExecutionResult(success=True, data={"content": content})
        elif action.data["operation"] == "write":
            await self.fs.write(action.data["path"], action.data["content"])
            return ExecutionResult(success=True)
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
