# Planning设计文档

## 1. 核心原则

**原子化拆分原则**：
- 大模型在"宏观逻辑"上60%成功率，在"微观动作"上99.9%成功率
- 工程核心：把1个60%成功率的大任务切碎成100个99.9%成功率的小任务

## 2. 非线性图：悔、判、改

```python
# 三种能力

1. 悔 (Loop/Retry)：循环重试
   - 工具调用失败自动重试
   - 计划执行卡住时回退

2. 判 (Branching)：条件分支
   - if test_passed: deploy() else: fix_bugs()
   - 根据环境动态选择路径

3. 改 (Feedback)：反馈修正
   - 用户介入纠正
   - 外部信号触发Plan修订
```

## 3. Plan Recitation

```python
# 原理：TODO列表追加到Context末尾，防止Lost-in-the-Middle

class PlanningManager:
    async def update_context_with_plan(self, context: dict):
        """将当前计划追加到Context末尾"""
        plan = await self.fs.read("task/plan.md")
        todos = await self.get_active_todos()
        
        context["system_suffix"] = f"""
# CURRENT PLAN
{plan}

# ACTIVE TODOs
{chr(10).join(f"- [ ] {t.title}" for t in todos)}
"""
        return context
```

## 4. 原子化任务拆分

```python
class AtomicPlanner:
    async def decompose(self, task: str) -> List[Step]:
        """将大任务拆分为原子步骤"""
        
        prompt = f"""
将以下任务拆分为原子步骤，每步应：
1. 单一职责
2. 可独立验证
3. 失败时可重试

任务：{task}

返回JSON：
[
  {{"id": 1, "action": "...", "tool": "...", "depends_on": []}},
  {{"id": 2, "action": "...", "tool": "...", "depends_on": [1]}}
]
"""
        
        steps = await self.llm.generate(prompt=prompt, response_format="json")
        return [Step(**s) for s in json.loads(steps.content)]
```

## 5. 与其他模块集成

- **与Reasoning集成**：Plan验证失败触发Re-planning
- **与Execution集成**：Step执行由Sandbox保障安全
- **与Context管理集成**：Plan Recitation依赖Context追加机制
- **与Context Graph集成**：记录Plan演化轨迹

## 6. 总结

**核心价值**：
- 原子化拆分：大任务 → 小任务
- 非线性图：支持循环、分支、反馈
- Plan Recitation：防止遗忘

**设计原则**：
- 流程控制权归代码
- 内容生成权归模型
- 每步独立可验证
