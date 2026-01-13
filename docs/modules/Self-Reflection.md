# Self-Reflection设计文档

## 1. 核心理念

**将反思从简单的Prompt技巧转变为结构化、可编程的循环**

```
传统做法: "请反思你的回答是否正确"
    ↓
LLM自说自话，缺乏真实反馈

TokenDance做法: 
1. 执行动作 → 获取真实结果
2. 检测失败 → 结构化分析原因
3. 生成反思 → 修正策略
4. 重新执行 → 验证改进
```

## 2. 三大工业落地模式

### 模式A: Reflexion（内部循环模式）

**原理**：Agent在同一Context中自我迭代

**适用场景**：
- 推理任务（数学、逻辑）
- 文本生成（反复润色）
- 规划任务（优化方案）

**实现**：
```python
# packages/core/reflection/reflexion.py

class ReflexionLoop:
    """Reflexion模式：Context内迭代"""
    
    async def execute(
        self, 
        task: str,
        max_iterations: int = 3
    ):
        context = []
        
        for i in range(max_iterations):
            # 尝试执行
            response = await self.llm.generate(
                system=SYSTEM_PROMPT,
                messages=context + [{"role": "user", "content": task}]
            )
            
            # 自我评估
            self_eval = await self._self_evaluate(response, task)
            
            if self_eval.is_satisfactory:
                return response
            
            # 生成反思
            reflection = await self._generate_reflection(
                task=task,
                attempt=response,
                evaluation=self_eval
            )
            
            # 将尝试和反思添加到Context
            context.append({
                "role": "assistant",
                "content": response.content
            })
            context.append({
                "role": "system",
                "content": f"""
## Reflection on Attempt {i+1}

**What went wrong**: {reflection.issues}
**Why it happened**: {reflection.root_causes}
**How to improve**: {reflection.suggestions}

Please revise your approach based on this reflection.
"""
            })
        
        return response
    
    async def _self_evaluate(self, response, task):
        """自我评估（可能不准确）"""
        
        eval_prompt = f"""
Task: {task}

Your response: {response.content}

Evaluate your response:
1. Does it fully address the task?
2. Is the logic sound?
3. Are there any obvious errors?

Return JSON:
{{
  "is_satisfactory": true/false,
  "issues": ["issue1", "issue2", ...],
  "confidence": 0.0-1.0
}}
"""
        
        result = await self.llm.generate(
            prompt=eval_prompt,
            temperature=0.3,
            response_format="json"
        )
        
        return SelfEvaluation(**json.loads(result.content))
    
    async def _generate_reflection(self, task, attempt, evaluation):
        """生成结构化反思"""
        
        reflection_prompt = f"""
You attempted this task but it has issues.

Task: {task}
Your attempt: {attempt.content}
Issues found: {evaluation.issues}

Reflect deeply:
1. What specific parts went wrong?
2. Why did you make those mistakes?
3. What should you do differently?

Return JSON:
{{
  "issues": ["specific issue 1", ...],
  "root_causes": ["why it happened", ...],
  "suggestions": ["concrete improvement", ...]
}}
"""
        
        result = await self.llm.generate(
            prompt=reflection_prompt,
            temperature=0.5,
            response_format="json"
        )
        
        return Reflection(**json.loads(result.content))
```

**优点**：
- Context连贯，Agent能看到完整演化历史
- 适合纯推理任务

**缺点**：
- Context膨胀，Token成本高
- 自我评估不可靠（幻觉问题）

---

### 模式B: Actor-Critic（批判者-执行者模式）

**原理**：两个独立Agent，职责分离

**适用场景**：
- 代码生成（Actor写，Critic审查）
- 内容创作（Actor创作，Critic编辑）
- 方案设计（Actor提案，Critic评审）

**实现**：
```python
# packages/core/reflection/actor_critic.py

class ActorCriticSystem:
    """Actor-Critic模式"""
    
    def __init__(
        self, 
        actor_llm,      # 执行者，可用大模型
        critic_llm      # 批判者，可用小模型降低成本
    ):
        self.actor = actor_llm
        self.critic = critic_llm
    
    async def execute(
        self, 
        task: str,
        max_iterations: int = 3
    ):
        for i in range(max_iterations):
            # Actor执行
            action = await self.actor.generate(
                system="You are an AI agent. Complete the task to the best of your ability.",
                messages=[{"role": "user", "content": task}]
            )
            
            # Critic评估
            evaluation = await self._critic_evaluate(task, action)
            
            if evaluation.approved:
                # 通过审查
                await self._record_success(task, action, evaluation)
                return action
            
            # 未通过：Critic提供反馈
            feedback = evaluation.feedback
            
            # 将反馈传给Actor
            task = self._augment_task_with_feedback(task, action, feedback)
        
        # 最后一次尝试
        return action
    
    async def _critic_evaluate(self, task, action):
        """Critic评估Actor的输出"""
        
        critic_prompt = f"""
You are a critic reviewing an agent's work.

Task: {task}
Agent's output: {action.content}

Evaluate:
1. Correctness: Does it solve the task correctly?
2. Completeness: Does it address all requirements?
3. Quality: Is the quality acceptable?

Return JSON:
{{
  "approved": true/false,
  "score": 0-100,
  "feedback": {{
    "strengths": ["...", ...],
    "weaknesses": ["...", ...],
    "suggestions": ["concrete improvement", ...]
  }}
}}
"""
        
        result = await self.critic.generate(
            prompt=critic_prompt,
            temperature=0.3,
            response_format="json"
        )
        
        return CriticEvaluation(**json.loads(result.content))
    
    def _augment_task_with_feedback(self, original_task, failed_attempt, feedback):
        """将反馈融入新的任务描述"""
        
        return f"""
{original_task}

⚠️ Previous attempt had issues:
{failed_attempt.content}

Critic feedback:
**Weaknesses**: {', '.join(feedback.weaknesses)}
**Suggestions**: {chr(10).join(f'- {s}' for s in feedback.suggestions)}

Please address these issues in your revised solution.
"""
```

**成本优化**：
```python
# Critic可以用小模型
actor = Claude("claude-3-5-sonnet")     # $3/M tokens
critic = Claude("claude-3-haiku")       # $0.25/M tokens

# 或者用不同厂商
actor = Claude("claude-3-5-sonnet")
critic = Gemini("gemini-1.5-flash")     # $0.075/M tokens
```

**优点**：
- 职责分离，Critic可用小模型降低成本
- 评估相对客观（不同模型视角）

**缺点**：
- 两个模型，延迟增加
- Critic仍可能有幻觉

---

### 模式C: External-Loop（外部信号反馈模式）⭐推荐

**原理**：依赖外部真实反馈（测试、用户、工具）

**适用场景**：
- 代码生成（单测验证）
- 工具调用（真实执行结果）
- 数据处理（Schema验证）

**实现**：
```python
# packages/core/reflection/external_loop.py

class ExternalLoop:
    """External-Loop模式：真实反馈驱动"""
    
    def __init__(self, llm, sandbox, tool_executor):
        self.llm = llm
        self.sandbox = sandbox
        self.tool_executor = tool_executor
    
    async def execute_code_with_tests(
        self, 
        task: str,
        test_cases: List[TestCase],
        max_iterations: int = 3
    ):
        """代码生成 + 测试驱动反思"""
        
        context = []
        
        for i in range(max_iterations):
            # 生成代码
            code_response = await self.llm.generate(
                system="You are a Python expert. Write clean, tested code.",
                messages=context + [{"role": "user", "content": task}]
            )
            
            code = self._extract_code(code_response.content)
            
            # 外部验证：运行测试
            test_result = await self.sandbox.run_tests(code, test_cases)
            
            if test_result.all_passed:
                # 测试通过！
                await self._record_success(task, code, test_result)
                return code
            
            # 测试失败：将真实错误反馈给Agent
            context.append({
                "role": "assistant",
                "content": code_response.content
            })
            context.append({
                "role": "tool",
                "name": "test_runner",
                "content": f"""
## Test Results (Attempt {i+1})

❌ {test_result.failed_count} / {len(test_cases)} tests failed

**Failed Tests:**
{self._format_test_failures(test_result.failures)}

**Error Messages:**
{chr(10).join(f'- {f.error}' for f in test_result.failures)}

Please fix the code to pass all tests.
"""
            })
        
        return code
    
    async def execute_tool_with_retry(
        self,
        tool_name: str,
        args: dict,
        max_retries: int = 2
    ):
        """工具调用 + 真实错误反馈"""
        
        context = []
        
        for attempt in range(max_retries + 1):
            try:
                # 执行工具
                result = await self.tool_executor.execute(tool_name, **args)
                
                # 成功
                await self._record_tool_success(tool_name, args, result)
                return result
                
            except ToolExecutionError as e:
                if attempt == max_retries:
                    raise
                
                # 失败：分析错误并修正参数
                error_analysis = await self._analyze_tool_error(
                    tool_name, args, str(e)
                )
                
                # 让LLM修正参数
                fixed_args = await self.llm.generate(
                    prompt=f"""
Tool call failed:
- Tool: {tool_name}
- Args: {args}
- Error: {str(e)}

Error analysis: {error_analysis}

Return corrected args as JSON.
""",
                    response_format="json"
                )
                
                args = json.loads(fixed_args.content)
                
                # 记录到Context Graph
                await self.context_graph.record_tool_failure(
                    tool_name=tool_name,
                    original_args=args,
                    error=str(e),
                    fixed_args=args,
                    attempt=attempt + 1
                )
    
    def _format_test_failures(self, failures):
        """格式化测试失败信息"""
        return "\n".join(
            f"""
Test: {f.test_name}
Input: {f.input}
Expected: {f.expected}
Actual: {f.actual}
"""
            for f in failures
        )
```

**优点**：
- **真实反馈**：不是LLM自说自话，而是真实执行结果
- **可靠性高**：测试通过 = 真通过，不是幻觉
- **成本低**：不需要额外LLM评估

**缺点**：
- 需要可执行的验证环境
- 不适用于纯创意任务

---

## 3. TokenDance的Reflection架构

### 3.1 统一接口

```python
# packages/core/reflection/manager.py

from enum import Enum

class ReflectionMode(str, Enum):
    REFLEXION = "reflexion"
    ACTOR_CRITIC = "actor_critic"
    EXTERNAL_LOOP = "external_loop"

class ReflectionManager:
    """反思管理器：统一三种模式"""
    
    def __init__(self, llm, sandbox, tools, context_graph):
        self.llm = llm
        self.sandbox = sandbox
        self.tools = tools
        self.context_graph = context_graph
        
        # 三种模式
        self.reflexion = ReflexionLoop(llm)
        self.actor_critic = ActorCriticSystem(
            actor_llm=llm,
            critic_llm=llm  # 可配置为小模型
        )
        self.external_loop = ExternalLoop(llm, sandbox, tools)
    
    async def execute_with_reflection(
        self,
        task: str,
        mode: ReflectionMode,
        **kwargs
    ):
        """根据模式选择执行"""
        
        if mode == ReflectionMode.REFLEXION:
            return await self.reflexion.execute(task, **kwargs)
        elif mode == ReflectionMode.ACTOR_CRITIC:
            return await self.actor_critic.execute(task, **kwargs)
        else:  # EXTERNAL_LOOP
            return await self.external_loop.execute_code_with_tests(task, **kwargs)
```

### 3.2 自动模式选择

```python
class AdaptiveReflection:
    """根据任务类型自动选择反思模式"""
    
    async def execute(self, task: str):
        # 分析任务类型
        task_type = await self._classify_task(task)
        
        if task_type == "code_generation":
            # 代码生成：External-Loop（测试驱动）
            return await self.reflection.execute_with_reflection(
                task,
                mode=ReflectionMode.EXTERNAL_LOOP,
                test_cases=await self._generate_test_cases(task)
            )
        
        elif task_type == "creative_writing":
            # 创意写作：Actor-Critic（Critic审查）
            return await self.reflection.execute_with_reflection(
                task,
                mode=ReflectionMode.ACTOR_CRITIC
            )
        
        elif task_type == "reasoning":
            # 推理任务：Reflexion（自我迭代）
            return await self.reflection.execute_with_reflection(
                task,
                mode=ReflectionMode.REFLEXION
            )
        
        else:
            # 默认：External-Loop
            return await self.reflection.execute_with_reflection(
                task,
                mode=ReflectionMode.EXTERNAL_LOOP
            )
```

## 4. 避免反思陷阱

### 4.1 Token成本控制

```python
# 问题：反思循环导致Token爆炸

# ❌ 错误做法
for i in range(10):  # 可能10次全部用完
    response = await llm.generate(...)
    reflection = await llm.generate(...)  # 每次都调用LLM

# ✅ 正确做法
MAX_REFLECTION_ITERATIONS = 3  # 限制次数
REFLECTION_TOKEN_BUDGET = 10000  # Token预算

for i in range(MAX_REFLECTION_ITERATIONS):
    if current_tokens > REFLECTION_TOKEN_BUDGET:
        break  # 超预算，停止反思
    
    response = await llm.generate(...)
    
    # 优先使用外部验证
    if has_external_validator:
        is_correct = await external_validate(response)
        if is_correct:
            break  # 外部验证通过，无需LLM反思
```

### 4.2 延迟控制

```python
# 问题：多次迭代导致延迟过高

# 用户体验阈值
MAX_REFLECTION_TIME_SECONDS = 30

start_time = time.time()

for i in range(max_iterations):
    if time.time() - start_time > MAX_REFLECTION_TIME_SECONDS:
        # 超时，返回当前最佳结果
        return current_best_response
    
    response = await llm.generate(...)
```

### 4.3 过度修正（Over-correction）

```python
# 问题：反复修改导致结果越来越差

class ReflectionState:
    """跟踪反思历史，避免过度修正"""
    
    def __init__(self):
        self.history = []
        self.best_response = None
        self.best_score = 0
    
    def add_attempt(self, response, score):
        self.history.append((response, score))
        
        if score > self.best_score:
            self.best_response = response
            self.best_score = score
    
    def should_stop_reflection(self):
        """检测是否应该停止反思"""
        
        if len(self.history) < 2:
            return False
        
        # 如果最近3次得分都在下降，停止
        recent_scores = [s for _, s in self.history[-3:]]
        if len(recent_scores) >= 3 and all(
            recent_scores[i] > recent_scores[i+1] 
            for i in range(len(recent_scores)-1)
        ):
            return True
        
        return False
```

## 5. 与其他模块集成

### 5.1 与Context Graph集成

```python
# 记录反思轨迹

async def execute_with_reflection(task, mode):
    for i in range(max_iterations):
        # 执行
        response = await llm.generate(...)
        
        # 记录尝试
        attempt_node = await context_graph.add_node(
            type="reflection_attempt",
            iteration=i + 1,
            content=response.content
        )
        
        # 验证
        validation = await validate(response)
        
        if validation.success:
            # 成功
            await context_graph.add_edge(
                from_node=attempt_node,
                to_node="success",
                label="validated"
            )
            return response
        else:
            # 失败：记录反思
            reflection_node = await context_graph.add_node(
                type="reflection",
                issues=validation.issues,
                suggestions=validation.suggestions
            )
            
            await context_graph.add_edge(
                from_node=attempt_node,
                to_node=reflection_node,
                label="reflected"
            )
```

### 5.2 与Memory集成

```python
# 从历史反思中学习

async def execute_with_historical_lessons(task):
    # 检索类似任务的历史反思
    past_reflections = await memory.retrieve_relevant_memories(
        query=task,
        memory_types=[MemoryType.PATTERN],
        filters={"has_reflection": True}
    )
    
    if past_reflections:
        # 提取历史教训
        lessons = "\n".join(
            f"- {r.content}" for r in past_reflections
        )
        
        # 增强初始Prompt
        task_with_lessons = f"""
{task}

⚠️ Learn from past mistakes:
{lessons}
"""
        return await llm.generate(prompt=task_with_lessons)
    
    return await llm.generate(prompt=task)
```

## 6. 监控指标

```python
class ReflectionMetrics:
    async def collect(self, session_id: str) -> dict:
        return {
            # 效果指标
            "reflection_enabled_tasks": ...,
            "success_rate_with_reflection": ...,
            "success_rate_without_reflection": ...,
            "improvement_rate": ...,  # 反思后改进率
            
            # 成本指标
            "avg_iterations_per_task": ...,
            "avg_tokens_per_reflection": ...,
            "avg_latency_per_iteration_ms": ...,
            
            # 模式分布
            "mode_usage": {
                "reflexion": 0.2,
                "actor_critic": 0.3,
                "external_loop": 0.5
            },
            
            # 质量指标
            "over_correction_rate": ...,  # 过度修正比例
            "reflection_effectiveness": ...  # 反思有效性
        }
```

## 7. 总结

**TokenDance的Self-Reflection策略**：
1. **External-Loop优先**：优先使用真实反馈（测试、工具结果）
2. **Actor-Critic次之**：需要主观评估时，用小模型Critic降低成本
3. **Reflexion保底**：无外部验证时，自我反思兜底

**关键原则**：
- 真实反馈 > LLM幻觉评估
- 限制迭代次数（≤3次）
- 跟踪最佳结果，避免过度修正
- 所有反思轨迹记录到Context Graph

**成本控制**：
- Token预算限制
- 延迟阈值控制
- Critic使用小模型

**长期积累**：
- 反思结果存入Memory
- 历史教训指导未来
- 从失败中学习
