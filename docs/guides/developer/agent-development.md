# Agent 开发指南

> TokenDance Agent 开发核心准则与最佳实践

**最后更新**: 2026-01-17

---

## 📋 概述

TokenDance 是 Agent Runtime，不是通用智能体。本文档定义了 Agent 的核心行为准则、开发技能和工作流程。

**核心架构**: 详见 [`docs/architecture/Agent-Runtime-Design.md`](../../architecture/Agent-Runtime-Design.md)

---

## 🎯 三文件工作法 (Three-File Workflow)

对于复杂任务，使用 `docs/milestone/current/` 中的三个文件：

| 文件 | 用途 | 更新时机 |
|------|------|----------|
| `task_plan.md` | 任务分解与阶段规划 | 开始任务时创建，每个阶段前重读 |
| `findings.md` | 研究结果与技术决策 | 每 2 次主要操作后写入 |
| `progress.md` | 执行日志与错误追踪 | 所有错误立即记录 |

**关键规则**:
- 每 2 次主要操作（web_search/read_url）→ 写入 `findings.md`
- 所有错误 → 记录到 `progress.md`
- 开始新工作前 → 重读 `task_plan.md`

---

## 🧠 Agent 行为准则

### DO (应该做的)

- ✅ **主动识别风险**: 性能、安全、用户体验
- ✅ **提出更好方案**: 附带推理过程
- ✅ **质疑不合理需求**: 礼貌但坚定
- ✅ **考虑边界情况**: 边缘场景、无障碍、错误处理

### DON'T (不应该做的)

- ❌ **盲目执行**: 明显错误的设计
- ❌ **跳过错误处理**: 任何情况下
- ❌ **忽略移动端**: 响应式设计必须考虑

### 问题报告格式

```markdown
## ⚠️ Issue: [标题]
**Current**: 当前状态描述
**Problem**: 问题分析
**Suggestion**: 建议方案（附理由）
```

---

## 🛠️ 开发技能 (Development Skills)

### 1. 🔍 系统化调试 (Systematic Debugging)

**铁律**: 不找到根因不提 Fix

**四阶段流程**:
1. **Root Cause** - 读错误、复现、查 git diff、追踪数据流
2. **Pattern** - 找工作的例子，对比差异
3. **Hypothesis** - 单一假设，最小改动验证
4. **Implementation** - 先写失败测试，再修复

**3 次失败后**: 停下来质疑架构，不要继续猜

---

### 2. ✅ TDD (测试驱动开发)

**铁律**: 没有失败的测试，不写实现代码

**红绿重构循环**:
1. **RED** - 写失败测试，运行确认失败
2. **GREEN** - 写最小实现，运行确认通过
3. **REFACTOR** - 重构，保持绿色

**禁止**: 先写代码后补测试、测试立即通过、"就这一次跳过"

---

### 3. 🎯 完成前验证 (Verification Before Completion)

**铁律**: 证据先于断言

**流程**:
1. 识别验证命令（什么证明完成？）
2. 运行完整命令（不是"应该行"）
3. 读完整输出 + 检查 exit code
4. 确认后才能宣称完成

**禁止词汇**: "should", "probably", "seems to", "应该没问题了"

---

### 4. 🎨 UI/UX 交付前检查清单

提交前必查:
- [ ] 无 emoji 图标（使用 Lucide Icons）
- [ ] 所有可点击元素有 `cursor-pointer`
- [ ] 浅色模式对比度 ≥ 4.5:1
- [ ] 过渡动画 200-300ms
- [ ] 响应式测试: 375px / 768px / 1024px

---

## 🎨 UI/UX 约束

### 禁止 (DO NOT)

- ❌ AI 助手话术: "我能帮你...", "让我帮你..."
- ❌ Emoji 作为图标 - 使用 Lucide Icons
- ❌ 彩虹渐变、重度玻璃态
- ❌ 通用提示词: "帮我...", "生成..."

### 要求 (DO)

- ✅ 用户主导语言（User-as-director）
- ✅ 克制的灰色调色板（#fafafa, #f1f5f9, #111827）
- ✅ 过渡动画: 200-300ms ease
- ✅ 参考: Linear, Notion, Vercel

**详细规范**: [`docs/ux/design-principles.md`](../../ux/design-principles.md)

---

## 💰 金融场景约束

如果开发金融功能，严格遵守:

- ❌ 不预测股价
- ❌ 不提供买卖建议
- ❌ 不承诺收益
- ❌ 不使用内幕信息

---

## 📝 文档维护原则

**核心原则**: 文档要压缩和变更，不要只追加内容

### DO

- ✅ 更新时审视现有内容是否需要合并/删除
- ✅ 相似内容合并到一处，避免重复
- ✅ 过时内容及时删除或标记 deprecated
- ✅ 保持文档结构清晰，层级不超过 3 级
- ✅ 每个文档控制在合理长度（建议 < 500 行）

### DON'T

- ❌ 只追加不删除，导致文档膨胀
- ❌ 同一信息在多处重复
- ❌ 保留过时/冲突的内容
- ❌ 无限嵌套的目录结构

### 变更检查清单

1. 是否有可以合并的相似章节？
2. 是否有过时需要删除的内容？
3. 新增内容是否与现有内容冲突？
4. 文档长度是否仍在合理范围？

---

## 🔗 Git & PR 指南

### Commit 格式

```
feat: <简短描述>

<详细说明>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### 规则

- Commit after completing each component/bug fix/TODO item
- Always include co-author line
- Run lint and tests before committing

---

## 📚 必读文档

| 文档 | 内容 |
|------|------|
| [`docs/product/vision-and-mission.md`](../../product/vision-and-mission.md) | 产品愿景 |
| [`docs/architecture/Agent-Runtime-Design.md`](../../architecture/Agent-Runtime-Design.md) | Agent Runtime 5 大定律 |
| [`docs/ux/design-principles.md`](../../ux/design-principles.md) | UI 设计原则 |
| [`docs/ux/execution-page-layout.md`](../../ux/execution-page-layout.md) | 三栏布局规范 |

---

## 💡 重要提醒

- Context Graph 记录所有决策轨迹
- 大结果 → 文件系统，context 只保留摘要
- Context > 50K tokens → 自动摘要
- Plans/TODOs 始终追加到 context 末尾
- **规则同步**: 所有项目规则变动必须更新到本文档，确保其他 Coding Agent 可理解本项目
- **文档维护**: 更新文档时要压缩和变更，不要只追加内容，防止文档爆炸和内容混乱

---

## 🔗 相关资源

- [后端开发指南](../../../backend/DEVELOPMENT.md)
- [前端开发指南](../../../frontend/DEVELOPMENT.md)
- [测试指南](./testing-guide.md)
- [架构文档](../../architecture/)
