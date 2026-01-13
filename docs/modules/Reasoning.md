# Reasoning设计文档

## 1. 核心问题

**大模型推理的根本矛盾**：
- 单次推理成功率：60-80%
- 复杂任务需要多步推理，错误累积
- 缺乏自我纠错机制

## 2. Self-Reflection三大模式

### 模式A：Reflexion（内部循环模式）

```python
# 原理：Agent在同一个Context中自我迭代

async def reflexion_mode(task, max_iterations=3):
    context = []
    for i in range(max_iterations):
        # 尝试执行
        result = await agent.execute(task, context)
        
        if result.success:
            return result
        
        # 失败：自我反思
        reflection = await agent.reflect(
            task=task,
            attempt=result,
            error=result.error
        )
        
        # 将反思添加到Context
        context.append({
            "role": "assistant",
            "content": f"尝试{i+1}失败：{result.error}"
        })
        context.append({
            "role": "system",
            "content": f"反思：{reflection}"
        })
    
    return result  # 最后一次尝试

# 优点：Context连贯，Agent能看到完整历史
# 缺点：Context膨胀，KV Cache失效
```

### 模式B：Actor-Critic（批判者-执行者模式）

```python
# 原理：两个独立Agent，一个执行一个评估

class ActorCriticSystem:
    def __init__(self, actor_llm, critic_llm):
        self.actor = actor_llm   # 执行者
        self.critic = critic_llm  # 批判者
    
    async def execute(self, task, max_iterations=3):
        for i in range(max_iterations):
            # Actor执行
            action = await self.actor.plan_and_execute(task)
            
            # Critic评估
            evaluation = await self.critic.evaluate(
                task=task,
                action=action,
                result=action.result
            )
            
            if evaluation.is_good:
                return action
            
            # Critic提出改进建议
            feedback = evaluation.suggestions
            
            # 反馈给Actor
            task.context.append(f"批判意见：{feedback}")
        
        return action

# 优点：职责分离，Critic可用小模型降低成本
# 缺点：两个模型，延迟增加
```

### 模式C：External-Loop（外部信号反馈模式）

```python
# 原理：依赖外部真实反馈（测试、用户、工具）

async def external_loop(task, max_iterations=3):
    for i in range(max_iterations):
        # 执行
        code = await agent.generate_code(task)
        
        # 外部验证
        test_result = await run_tests(code)
        
        if test_result.all_passed:
            return code
        
        # 失败：将真实错误反馈给Agent
        task.context.append({
            "role": "tool",
            "name": "test_runner",
            "content": f"测试失败：\n{test_result.failures}"
        })
    
    return code

# 优点：反馈真实可靠，不是LLM自说自话
# 缺点：需要可执行的验证环境
```

## 3. TokenDance的Reasoning架构

### 3.1 核心组件

```python
# packages/core/reasoning/engine.py

from enum import Enum

class ReflectionMode(str, Enum):
    REFLEXION = "reflexion"
    ACTOR_CRITIC = "actor_critic"
    EXTERNAL_LOOP = "external_loop"

class ReasoningEngine:
    """推理引擎"""
    
    def __init__(self, llm, mode: ReflectionMode = ReflectionMode.EXTERNAL_LOOP):
        self.llm = llm
        self.mode = mode
    
    async def reason_with_retry(
        self, 
        task: str,
        max_iterations: int = 3
    ):
        """带重试的推理"""
        
        if self.mode == ReflectionMode.REFLEXION:
            return await self._reflexion_loop(task, max_iterations)
        elif self.mode == ReflectionMode.ACTOR_CRITIC:
            return await self._actor_critic_loop(task, max_iterations)
        else:
            return await self._external_loop(task, max_iterations)
    
    async def _external_loop(self, task: str, max_iterations: int):
        """外部反馈循环（推荐）"""
        
        context = []
        for i in range(max_iterations):
            # 生成方案
            solution = await self.llm.generate(
                system="You are a helpful assistant.",
                messages=context + [{"role": "user", "content": task}]
            )
            
            # 执行并获取真实反馈
            execution_result = await self._execute_solution(solution)
            
            if execution_result.success:
                return solution
            
            # 失败：添加真实错误到Context
            context.append({
                "role": "assistant",
                "content": solution.content
            })
            context.append({
                "role": "tool",
                "name": execution_result.tool_name,
                "content": f"执行失败：{execution_result.error}\n\n请修正并重试。"
            })
        
        return solution
    
    async def _execute_solution(self, solution):
        """执行方案并返回真实结果"""
        # 根据任务类型选择验证方式
        if solution.contains_code:
            return await self._run_code(solution.code)
        elif solution.contains_tool_calls:
            return await self._execute_tools(solution.tool_calls)
        else:
            # 无法验证，直接返回成功
            return ExecutionResult(success=True)
```

### 3.2 与Tool-Use集成

```python
# 工具调用失败自动重试

class ToolExecutor:
    async def execute_with_retry(
        self, 
        tool_name: str,
        args: dict,
        max_retries: int = 2
    ):
        """工具执行带自动重试"""
        
        for attempt in range(max_retries + 1):
            try:
                result = await self.tools[tool_name].execute(**args)
                return result
            except Exception as e:
                if attempt == max_retries:
                    # 最后一次尝试也失败，返回错误
                    return ToolResult(
                        status="error",
                        error=str(e),
                        suggestions=self._suggest_fix(tool_name, e)
                    )
                
                # 记录失败到Context Graph
                await self.context_graph.record_tool_failure(
                    tool_name=tool_name,
                    args=args,
                    error=str(e),
                    attempt=attempt + 1
                )
    
    def _suggest_fix(self, tool_name: str, error: Exception) -> str:
        """根据错误类型提供修复建议"""
        if "timeout" in str(error).lower():
            return "建议：增加超时时间或检查网络连接"
        elif "auth" in str(error).lower():
            return "建议：检查API密钥是否正确"
        else:
            return f"建议：检查{tool_name}的参数是否正确"
```

### 3.3 与Planning集成

```python
# Planning失败触发Re-planning

class PlanningEngine:
    async def plan_with_reflection(self, goal: str):
        """带反思的规划"""
        
        plan = await self.create_initial_plan(goal)
        
        # 验证计划可行性
        validation = await self._validate_plan(plan)
        
        if not validation.is_valid:
            # 计划不可行，重新规划
            reflection = f"初始计划存在问题：{validation.issues}"
            
            revised_plan = await self.revise_plan(
                original_plan=plan,
                reflection=reflection
            )
            return revised_plan
        
        return plan
    
    async def _validate_plan(self, plan):
        """验证计划可行性"""
        issues = []
        
        # 检查依赖关系
        for step in plan.steps:
            if step.requires and not self._check_dependencies(step.requires, plan):
                issues.append(f"步骤{step.id}的依赖{step.requires}不满足")
        
        # 检查资源可用性
        for step in plan.steps:
            if step.tool and not await self.tool_registry.has_tool(step.tool):
                issues.append(f"步骤{step.id}需要的工具{step.tool}不存在")
        
        return PlanValidation(
            is_valid=len(issues) == 0,
            issues=issues
        )
```

## 4. Chain-of-Thought增强

```python
# 强制Agent进行逐步推理

REASONING_PROMPT_TEMPLATE = """
Please solve this task step-by-step:

Task: {task}

Follow this reasoning process:
1. **Understand**: Restate the task in your own words
2. **Analyze**: Break down the problem into sub-problems
3. **Plan**: Outline your approach
4. **Execute**: Implement the solution
5. **Verify**: Check if the solution meets the requirements

Let's begin:
"""

class ChainOfThoughtReasoning:
    async def reason(self, task: str):
        """强制CoT推理"""
        
        prompt = REASONING_PROMPT_TEMPLATE.format(task=task)
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.7
        )
        
        # 解析CoT结构
        cot = self._parse_chain_of_thought(response.content)
        
        return cot
    
    def _parse_chain_of_thought(self, content: str):
        """解析CoT结构"""
        sections = {
            "understand": "",
            "analyze": "",
            "plan": "",
            "execute": "",
            "verify": ""
        }
        
        # 正则提取各部分
        # ...
        
        return ChainOfThought(**sections)
```

## 5. 与其他模块集成

### 5.1 与Context Graph集成

```python
# 记录推理轨迹

class ReasoningEngine:
    async def reason_with_retry(self, task: str, max_iterations: int):
        for i in range(max_iterations):
            solution = await self.llm.generate(...)
            
            # 记录推理节点
            reasoning_node_id = await self.context_graph.add_node(
                type="reasoning",
                content=solution.content,
                iteration=i + 1
            )
            
            result = await self._execute_solution(solution)
            
            if result.success:
                # 记录成功
                await self.context_graph.add_edge(
                    from_node=reasoning_node_id,
                    to_node="success",
                    label="verified"
                )
                return solution
            else:
                # 记录失败和反思
                await self.context_graph.add_edge(
                    from_node=reasoning_node_id,
                    to_node="failure",
                    label=result.error
                )
```

### 5.2 与Memory集成

```python
# 从历史失败中学习

class ReasoningEngine:
    async def _get_similar_failures(self, task: str):
        """检索相似的历史失败案例"""
        
        similar_cases = await self.memory.retrieve_relevant_memories(
            query=task,
            memory_types=[MemoryType.PATTERN],
            k=5
        )
        
        failures = [
            case for case in similar_cases 
            if "失败" in case.content or "错误" in case.content
        ]
        
        return failures
    
    async def reason_with_history(self, task: str):
        """利用历史经验推理"""
        
        # 检索类似失败
        past_failures = await self._get_similar_failures(task)
        
        if past_failures:
            # 增强Prompt
            lessons = "\n".join(f"- {f.content}" for f in past_failures)
            prompt = f"""
Task: {task}

⚠️ Learn from past failures:
{lessons}

Please avoid these mistakes and provide a better solution.
"""
            return await self.llm.generate(prompt=prompt)
        
        # 无历史，正常推理
        return await self.llm.generate(prompt=task)
```

## 6. 监控指标

```python
class ReasoningMetrics:
    async def collect(self, session_id: str) -> dict:
        return {
            "total_reasoning_attempts": ...,
            "success_on_first_try": ...,
            "avg_iterations_to_success": ...,
            "most_common_failure_types": ...,
            "reflection_effectiveness": ...  # 反思后成功率
        }
```

## 7. 总结

**核心设计**：
1. **External-Loop优先**：真实反馈 > LLM自我评估
2. **与Tool/Planning深度集成**：失败自动重试
3. **Context Graph记录轨迹**：可审计、可学习
4. **Memory驱动改进**：历史失败案例指导未来

**关键原则**：
- 60%宏观不可靠 → 拆分成99.9%的微观
- 失败是常态 → 设计重试和反思机制
- 真实反馈 > 幻觉反馈
