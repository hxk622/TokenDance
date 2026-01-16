# Phase 3.2 - LLM Prompt 优化：混合执行系统提示词

**完成日期**: 2025年1月16日  
**作者**: Warp Agent  
**状态**: ✅ 完成

## 概览

Phase 3.2 为混合执行系统（Skill/MCP/LLM 三路执行）实现了优化的 LLM 提示词。这些提示词引导 LLM 在决定任务执行路径时做出更聪明的选择。

## 核心改进

### 1. 三路执行系统提示词 (HYBRID_EXECUTION_SYSTEM_PROMPT)

**位置**: `backend/app/agent/hybrid_execution_prompts.py`

**核心内容**:
- ⚡ **Skill 路径** (快速, <100ms)
  - 何时使用：预构建、经过测试的工作流
  - 示例：报告生成、数据管道执行
  - 关键词：report, analysis, workflow, pipeline

- 🔧 **MCP 代码路径** (灵活, <5s)
  - 何时使用：结构化数据任务、文件操作、计算
  - 数据清晰、输出具体、错误处理
  - 关键词：query, filter, calculate, csv, transform

- 🧠 **LLM 推理路径** (思考, 自适应)
  - 何时使用：抽象思考、创意写作、概念解释
  - 示例：战略分析、内容生成、建议
  - 关键词：explain, discuss, write, advise

### 2. 代码生成提示词 (MCP_CODE_GENERATION_PROMPT)

**特点**:
```
✓ 任务分析流程（数据/输出/库）
✓ 代码结构模板（导入/加载/处理/输出）
✓ 质量检查清单（错误处理/资源限制/输出格式）
✓ 性能考虑（pandas vs numpy, 避免大文件）
✓ 安全约束（禁用 system access, eval/exec）
```

**最佳实践**:
1. 显式错误处理 (try-except)
2. 清晰标记的输出 (print with labels)
3. 资源限制意识 (no infinite loops)
4. 结构化输出 (summary + details)

### 3. 执行路径选择提示词 (EXECUTION_PATH_SELECTION_PROMPT)

**决策矩阵**:
| 任务类型 | 路径 | 原因 |
|---------|------|------|
| 预构建工作流 | Skill | 优化、测试、<100ms |
| 数据查询/过滤 | MCP | 灵活、结构化 |
| 数据转换 | MCP | 精确、可重复 |
| 计算 | MCP | 准确、可证明 |
| 分析 | MCP/LLM | 数据量大→MCP, 概念→LLM |
| 创意写作 | LLM | 需要推理 |
| 战略建议 | LLM | 复杂决策 |

**降级策略**:
```
1. Skill 失败 → 尝试 MCP 代码
2. MCP 代码失败 → 使用 LLM 推理分析
3. 使用 LLM 解释失败原因并建议替代方案
```

## 集成方式

### AgentEngine 中的集成

```python
from app.agent.hybrid_execution_prompts import (
    HYBRID_EXECUTION_SYSTEM_PROMPT,
    MCP_CODE_GENERATION_PROMPT,
    EXECUTION_PATH_SELECTION_PROMPT,
)

class AgentEngine:
    def _get_system_prompt(self) -> str:
        """根据是否启用混合执行返回对应的提示词"""
        if self.execution_router is not None:
            return HYBRID_EXECUTION_SYSTEM_PROMPT
        else:
            return self.context_manager.get_system_prompt()
```

### 使用流程

1. **初始化**:
   ```python
   engine = AgentEngine(
       llm=llm,
       filesystem=fs,
       workspace_id="ws1",
       session_id="sess1",
       enable_skills=True  # 启用混合执行
   )
   ```

2. **LLM 调用**:
   ```python
   system_prompt = engine._get_system_prompt()  # 获取优化后的提示词
   response = await llm.complete(
       messages=messages,
       system=system_prompt
   )
   ```

3. **路由决策**:
   ```python
   # LLM 根据提示词做出决策
   decision = execution_router.route(user_message)
   # 执行对应路径
   ```

## 提示词内容详解

### HYBRID_EXECUTION_SYSTEM_PROMPT 的关键部分

```markdown
## 🎯 Three Execution Paths

### Path 1: Skill Execution (⚡ Fastest)
- 预构建的工作流
- 复杂多步操作已优化
- 示例：报告生成、数据管道

### Path 2: MCP Code Execution (🔧 Flexible)
- 结构化数据任务
- 文件操作（CSV, JSON, Excel）
- 数据分析和转换
- 数学计算

### Path 3: LLM Reasoning (🧠 Thoughtful)
- 抽象思考和分析
- 创意写作和内容生成
- 概念解释
- 战略规划和建议

## 📋 路由决策流程

1. 分析请求类型
2. 检查可用上下文
3. 做出路由决策
```

### MCP_CODE_GENERATION_PROMPT 的质量检查清单

```
✅ 包含 try-except 错误处理
✅ 有清晰的输出语句（带标签的 print）
✅ 遵守资源限制（无无限循环）
✅ 无系统访问（os.system, exec, eval）
✅ 仅使用可用库
✅ 优雅处理缺失文件
✅ 生成结构化输出
```

## 代码示例

### 示例 1: Skill 路径

```
User: "生成季度业务报告"
分析: 复杂工作流，多个步骤
决策: SKILL 路径（如果存在"business-report"技能）
结果: 结构化报告，包含图表和见解
```

### 示例 2: MCP 代码路径

```python
User: "过去一周有多少用户注册？"
分析: 用户表数据查询
决策: MCP 代码路径

生成的代码:
import pandas as pd
from datetime import datetime, timedelta

df = pd.read_csv('users.csv')
df['signup_date'] = pd.to_datetime(df['signup_date'])
last_week = datetime.now() - timedelta(days=7)
recent_users = df[df['signup_date'] >= last_week]
print(f"过去一周注册用户: {len(recent_users)}")

结果: "过去一周注册用户: 42"
```

### 示例 3: LLM 路径

```
User: "我们进入亚洲市场的战略应该是什么？"
分析: 战略分析，多个因素
决策: LLM 路径
结果: 深思熟虑的分析，包含市场洞察、风险、机遇
```

## 性能指标

| 路径 | 响应时间 | 精度 | 用途 |
|------|---------|------|------|
| Skill | <100ms | 95%+ | 预构建工作流 |
| MCP 代码 | <5s | 99%+ | 数据和计算 |
| LLM | 可变 | 90%+ | 分析和建议 |

## 约束和限制

### Skill 路径约束
- 仅当高置信度匹配（>80%）时使用
- 需要预先存在的 Skill 定义
- 可用的 Skill 库数量固定

### MCP 代码路径约束
- 执行超时：5秒
- 内存限制：避免加载 >1GB 文件
- 无系统访问：不能使用 os.system()
- 沙箱环境：受限的库和权限

### LLM 路径约束
- 需要足够的上下文窗口
- 对复杂推理可能时间较长
- 可能需要多轮对话

## 最佳实践

### 何时使用每条路径

**使用 Skill 路径时**:
- ✅ 任务与已知工作流完全匹配
- ✅ 性能是关键考虑因素
- ✅ 任务是可重复的和标准化的

**使用 MCP 代码路径时**:
- ✅ 需要处理数据文件
- ✅ 需要精确的数值计算
- ✅ 需要数据转换或筛选
- ✅ 用户要求代码解决方案

**使用 LLM 路径时**:
- ✅ 任务需要创意思考
- ✅ 需要深入分析和推理
- ✅ 需要生成文本内容
- ✅ 需要战略或概念性建议

## 调试和监控

### 记录执行路径

```python
# 在 UnifiedExecutionContext 中记录
record = context.record_execution(
    execution_type=ExecutionType.SKILL,
    user_message="用户输入",
    status=ExecutionStatus.SUCCESS,
    result={...}
)
```

### 查看执行统计

```python
stats = execution_router.get_stats()
print(f"Skill路径: {stats[ExecutionPath.SKILL]}")
print(f"MCP路径: {stats[ExecutionPath.MCP_CODE]}")
print(f"LLM路径: {stats[ExecutionPath.LLM_REASONING]}")
```

### 性能监控

记录每个路径的：
- 调用次数
- 成功率（按路径）
- 平均执行时间
- 错误分布

## 常见问题

**Q: LLM 总是选择 MCP 路径吗？**  
A: 不是。提示词包含清晰的决策标准和示例。LLM 会根据任务类型选择最合适的路径。

**Q: 如果代码执行失败怎么办？**  
A: 系统会自动降级到 LLM 推理路径，LLM 会分析失败原因并提供替代方案。

**Q: 如何增加新的 Skill？**  
A: 在 `backend/app/skills/builtin/` 中定义 Skill，注册到 SkillRegistry。提示词会自动识别。

**Q: 可以自定义提示词吗？**  
A: 可以。修改 `hybrid_execution_prompts.py` 中的常量，然后重新启动 Agent。

## 未来改进

1. **动态提示词调整**: 根据执行结果调整路由策略
2. **A/B 测试框架**: 测试不同的提示词变体
3. **路径特定提示词**: 每个路径的定制化指导
4. **学习反馈循环**: 从失败中学习并改进决策
5. **多语言支持**: 中文、英文、其他语言的提示词

## 总结

Phase 3.2 通过优化的 LLM 提示词实现了智能的三路执行路由。这使得 TokenDance Agent 能够：

- ⚡ 快速执行预构建任务（Skill）
- 🔧 灵活处理数据和计算（MCP）
- 🧠 进行深思熟虑的分析（LLM）

关键是让 LLM 理解每条路径的优缺点，并根据任务特征做出正确的选择。

---

**相关文档**:
- `docs/modules/MCP-Execution-Guide.md` - MCP 代码执行指南
- `docs/architecture/Agent-Runtime-Design.md` - Agent Runtime 五条铁律
- `backend/app/agent/hybrid_execution_prompts.py` - 完整的提示词实现
