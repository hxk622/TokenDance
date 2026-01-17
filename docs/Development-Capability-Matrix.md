# TokenDance 能力覆盖矩阵

> **⚠️ 文档已迁移**: 此文件将于 **2026-03-01** 移动到 [`docs/reference/development-capability-matrix.md`](reference/development-capability-matrix.md)
>
> 请更新您的书签。当前内容将保留 6 周以确保向后兼容。

> 基于所有设计文档的完整能力梳理
> 创建时间: 2026-01-13
> 用途: 指导开发优先级，确保无遗漏

## 1. 核心能力分类

### 1.1 Agent引擎核心 (Agent Engine Core)

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **Plan Recitation（目标背诵）** | HLD, Planning | P0 | ⬜ 未实现 | ~150 lines | Phase 3 |
| **Keep the Failures（保留错路）** | HLD, Self-Reflection | P0 | ⬜ 未实现 | ~100 lines | Phase 3 |
| **三文件工作法 (task_plan.md/findings.md/progress.md)** | HLD, FileSystem | P0 | ⬜ 未实现 | ~400 lines | Phase 3 |
| **2-Action Rule（2次行动规则）** | HLD, Context-Management | P0 | 🔄 部分实现 | ~80 lines | Phase 3 |
| **Agent主循环 (Think-Decide-Act)** | Reasoning, Execution | P0 | ✅ 已实现 | ~300 lines | Phase 2 |
| **Function Calling支持** | Tool-Use | P0 | ✅ 已实现 | ~200 lines | Phase 2 |
| **Streaming输出** | - | P1 | ⬜ 未实现 | ~150 lines | Phase 3 |

### 1.2 Context管理 (Context Management)

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **KV-Cache稳定性（固定前缀）** | HLD, Context-Management | P0 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **Append-Only Context（纯追加）** | HLD, KV-Cache-Advanced | P0 | ⬜ 未实现 | ~100 lines | Phase 4 |
| **Structured Tags（结构化标记）** | HLD | P0 | ⬜ 未实现 | ~80 lines | Phase 4 |
| **Tool Definition Masking（工具掩码）** | Tool-Use, KV-Cache | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |
| **文件系统指针（FileSystem Pointer）** | Context-Compression, FileSystem | P0 | ⬜ 未实现 | ~300 lines | Phase 4 |
| **自动压缩与换入换出** | Context-Compression | P1 | ⬜ 未实现 | ~400 lines | Phase 4 |
| **增量摘要（Incremental Summary）** | Context-Management | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |
| **Context Graph记录** | Context-Graph | P1 | ⬜ 未实现 | ~350 lines | Phase 4 |

### 1.3 Planning系统 (Planning System)

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **原子化任务拆分** | Planning | P0 | ⬜ 未实现 | ~200 lines | Phase 3 |
| **Plan Manager（计划管理器）** | Planning | P0 | ⬜ 未实现 | ~250 lines | Phase 3 |
| **非线性图（循环/分支/反馈）** | Planning | P1 | ⬜ 未实现 | ~300 lines | Phase 5 |
| **Plan验证与修订** | Planning, Reasoning | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **依赖关系检测** | Planning | P1 | ⬜ 未实现 | ~150 lines | Phase 4 |

### 1.4 Self-Reflection（自我反思）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **External-Loop（外部信号反馈）** | Self-Reflection, Reasoning | P0 | ⬜ 未实现 | ~200 lines | Phase 3 |
| **Reflexion（内部循环）** | Self-Reflection, Reasoning | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |
| **Actor-Critic（双模型）** | Self-Reflection | P2 | ⬜ 未实现 | ~300 lines | Phase 5 |
| **失败模式分析** | Self-Reflection, Monitor-Evaluation | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **自动重试与修复** | Tool-Use, Reasoning | P1 | ⬜ 未实现 | ~150 lines | Phase 3 |

### 1.5 Tool System（工具系统）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **ShellTool（终端工具）** 🚨 | HLD, Manus | P0 | ⬜ 缺失 | ~200 lines | Phase 3 |
| **WebSearchTool** | Tool-Use | P0 | ✅ 已实现 | ~216 lines | Phase 3 |
| **ReadUrlTool** | Tool-Use | P0 | ✅ 已实现 | ~276 lines | Phase 3 |
| **FileOpsTool（文件操作）** | Tool-Use, FileSystem | P0 | ⬜ 未实现 | ~300 lines | Phase 3 |
| **CodeExecuteTool（代码执行）** | Tool-Use, Sandbox | P1 | ⬜ 未实现 | ~250 lines | Phase 5 |
| **CreateArtifactTool（产物生成）** | Tool-Use | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **ToolRegistry（工具注册表）** | Tool-Use | P0 | ⬜ 未实现 | ~200 lines | Phase 3 |
| **强类型约束（Pydantic）** | Tool-Use | P0 | ⬜ 未实现 | ~100 lines | Phase 3 |
| **自我修复循环** | Tool-Use, Reasoning | P1 | ⬜ 未实现 | ~150 lines | Phase 4 |
| **层级化工具选择** | Tool-Use | P1 | ⬜ 未实现 | ~180 lines | Phase 4 |
| **MCP协议支持** | Tool-Use, MCP-Design | P2 | ⬜ 未实现 | ~500 lines | Phase 5 |

### 1.6 Skill System（技能系统）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **三级懒加载（L1/L2/L3）** | Skill-Design, HLD | P1 | ⬜ 未实现 | ~400 lines | Phase 4 |
| **Skill注册表** | Skill-Design | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **Skill匹配器（意图识别）** | Skill-Design | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |
| **SKILL.md解析器** | Skill-Design | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **Skill动态加载** | Skill-Design | P1 | ⬜ 未实现 | ~150 lines | Phase 4 |
| **预置Skill：Deep Research** | Skill-Design, GenSpark | P1 | 🔄 工具已实现，Skill未封装 | ~300 lines | Phase 4 |
| **预置Skill：PPT生成** | Skill-Design | P2 | ⬜ 未实现 | ~500 lines | Phase 5 |

### 1.7 Memory System（记忆系统）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **Working Memory（工作记忆）** | Memory, Context-Management | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **Episodic Memory（情景记忆）** | Memory | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |
| **Semantic Memory（语义记忆）** | Memory | P1 | ⬜ 未实现 | ~300 lines | Phase 4 |
| **Procedural Memory（程序性记忆）** | Memory | P2 | ⬜ 未实现 | ~250 lines | Phase 5 |
| **Vector检索（pgvector）** | Memory | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **时间衰减与压缩** | Memory | P2 | ⬜ 未实现 | ~150 lines | Phase 5 |
| **memory.md/learnings.md文件** | Memory, FileSystem | P1 | ⬜ 未实现 | ~150 lines | Phase 4 |

### 1.8 FileSystem（文件系统）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **AgentFileSystem基础API** | FileSystem | P0 | ⬜ 未实现 | ~300 lines | Phase 3 |
| **YAML Frontmatter + Markdown** | FileSystem | P0 | ⬜ 未实现 | ~150 lines | Phase 3 |
| **文件监听（watchdog）** | FileSystem | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **双写策略（File→DB同步）** | FileSystem, Memory | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |
| **多租户隔离目录** | FileSystem, Multi-Tenancy | P0 | ⬜ 未实现 | ~150 lines | Phase 3 |
| **Workspace目录规划** | FileSystem | P0 | ⬜ 未实现 | ~100 lines | Phase 3 |

### 1.9 Sandbox（沙箱）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **Docker隔离容器** | Sandbox | P1 | ⬜ 未实现 | ~400 lines | Phase 5 |
| **资源限制（CPU/内存/网络）** | Sandbox | P1 | ⬜ 未实现 | ~200 lines | Phase 5 |
| **代码执行（Python/Node/Shell）** | Sandbox | P1 | ⬜ 未实现 | ~300 lines | Phase 5 |
| **安全策略（黑名单）** | Sandbox | P1 | ⬜ 未实现 | ~150 lines | Phase 5 |
| **容器生命周期管理** | Sandbox | P1 | ⬜ 未实现 | ~200 lines | Phase 5 |

### 1.10 Browser Use（浏览器自动化）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **Playwright集成** | Browser-Use | P1 | 🔄 ReadUrl已用httpx实现 | ~300 lines | Phase 4 |
| **网页导航与提取** | Browser-Use | P1 | 🔄 ReadUrl已实现基础版 | ~200 lines | Phase 4 |
| **表单填写** | Browser-Use | P2 | ⬜ 未实现 | ~200 lines | Phase 5 |
| **截图功能** | Browser-Use | P2 | ⬜ 未实现 | ~100 lines | Phase 5 |
| **域名白名单** | Browser-Use | P1 | ⬜ 未实现 | ~50 lines | Phase 4 |

### 1.11 Monitor & Evaluation（监控与评估）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **质量指标收集** | Monitor-Evaluation | P1 | ⬜ 未实现 | ~300 lines | Phase 4 |
| **性能指标收集** | Monitor-Evaluation | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |
| **成本指标收集** | Monitor-Evaluation | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **实时监控Dashboard** | Monitor-Evaluation | P2 | ⬜ 未实现 | ~400 lines | Phase 5 |
| **失败模式分析** | Monitor-Evaluation | P2 | ⬜ 未实现 | ~250 lines | Phase 5 |

### 1.12 MCP（Model Context Protocol）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **MCP Manager核心** | MCP-Design | P2 | ⬜ 未实现 | ~300 lines | Phase 5 |
| **MCP Client** | MCP-Design | P2 | ⬜ 未实现 | ~250 lines | Phase 5 |
| **MCP Registry** | MCP-Design | P2 | ⬜ 未实现 | ~200 lines | Phase 5 |
| **预置MCP：Google Drive** | MCP-Design | P2 | ⬜ 未实现 | ~400 lines | Phase 5 |
| **预置MCP：GitHub** | MCP-Design | P2 | ⬜ 未实现 | ~400 lines | Phase 5 |
| **OAuth管理** | MCP-Design | P2 | ⬜ 未实现 | ~200 lines | Phase 5 |

### 1.13 Multi-Tenancy（多租户）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **三层租户模型（Org/Team/Workspace）** | Multi-Tenancy, HLD | P0 | ⬜ 未实现 | ~400 lines | Phase 3 |
| **物理隔离（FileSystem）** | Multi-Tenancy, FileSystem | P0 | ⬜ 未实现 | ~150 lines | Phase 3 |
| **逻辑隔离（PostgreSQL RLS）** | Multi-Tenancy | P0 | ⬜ 未实现 | ~200 lines | Phase 3 |
| **KV-Cache隔离** | Multi-Tenancy, KV-Cache | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **资源配额管理** | Multi-Tenancy | P1 | ⬜ 未实现 | ~250 lines | Phase 4 |

### 1.14 UI/Frontend（前端界面）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **Chat界面（消息流）** | UI-Design, Chain-of-Thought-UI | P0 | ⬜ 未实现 | ~400 lines | Phase 3 |
| **推理链可视化（CoT UI）** | Chain-of-Thought-UI | P0 | ⬜ 未实现 | ~500 lines | Phase 3 |
| **Sidebar（会话列表）** | UI-Design | P0 | ⬜ 未实现 | ~300 lines | Phase 3 |
| **Working Memory标签页** | UI-Design, FileSystem, HLD | P0 | ⬜ 未实现 | ~300 lines | Phase 3 |
| **Artifact预览（PPT/文档）** | UI-Design | P1 | ⬜ 未实现 | ~400 lines | Phase 4 |
| **Citation引用卡片** | UI-Design, AnyGen-UI | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **进度指示器** | Chain-of-Thought-UI | P0 | ⬜ 未实现 | ~200 lines | Phase 3 |
| **工具调用块** | Chain-of-Thought-UI | P0 | ⬜ 未实现 | ~250 lines | Phase 3 |
| **Guest模式** | AnyGen-UI | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **深色主题** | UI-Design | P0 | ⬜ 未实现 | ~100 lines | Phase 3 |

### 1.15 HITL（Human-in-the-Loop）

| 能力 | 来源文档 | 优先级 | 当前状态 | 预计代码量 | 目标阶段 |
|------|---------|--------|---------|-----------|---------|
| **HITL基础框架** | AnyGen, HLD | P0 | 🔄 部分实现 | ~200 lines | Phase 3 |
| **确认对话框（高风险操作）** | HITL | P0 | ⬜ 未实现 | ~150 lines | Phase 3 |
| **渐进式引导** | HITL, AnyGen | P1 | ⬜ 未实现 | ~200 lines | Phase 4 |
| **用户介入信号** | HITL | P1 | ⬜ 未实现 | ~100 lines | Phase 4 |

## 2. 原则性能力 (Architectural Principles)

这些是架构原则，不是独立功能，但需要在实现中贯彻：

| 原则 | 来源文档 | 如何贯彻 | 涉及模块 |
|------|---------|---------|---------|
| **KV-Cache稳定性** | HLD | 固定System Prompt，工具定义一次加载 | Agent Engine, Tool System, Context |
| **Append-Only Growth** | HLD | Context只追加不修改，保证KV-Cache命中 | Context Manager |
| **Dual Context Streams** | HLD, FileSystem | Working Memory + File System双轨记忆 | Context, FileSystem, Memory |
| **Action Space Pruning** | HLD, Tool-Use | Skill级别工具子集，不暴露所有工具 | Skill System, Tool Registry |
| **Plan Recitation** | HLD, Planning | TODO列表追加到Context末尾 | Planning, Context |
| **Keep the Failures** | HLD, Self-Reflection | 失败记录保留，Agent避坑学习 | Reasoning, Context |

## 3. 优先级分布统计

### 3.1 按优先级统计

| 优先级 | 能力数量 | 已完成 | 部分完成 | 未实现 | 占比 |
|--------|---------|--------|---------|--------|------|
| **P0（核心必须）** | 32 | 4 | 3 | 25 | 39% |
| **P1（重要）** | 42 | 0 | 0 | 42 | 51% |
| **P2（可选）** | 8 | 0 | 0 | 8 | 10% |
| **总计** | 82 | 4 | 3 | 75 | 100% |

### 3.2 当前完成度

- ✅ **已完成**: 4个能力 (5%)
  - Agent主循环 (Think-Decide-Act)
  - Function Calling支持
  - WebSearchTool
  - ReadUrlTool

- 🔄 **部分完成**: 3个能力 (4%)
  - 2-Action Rule（部分实现）
  - HITL基础框架（部分实现）
  - Deep Research Skill（工具已实现，Skill未封装）

- ⬜ **未实现**: 75个能力 (91%)

## 4. 关键缺失能力（Must-Have for MVP）

根据分析，以下能力是MVP必需但当前缺失的：

### 4.1 P0缺失（立即补充）

1. **ShellTool（终端工具）** 🚨
   - 来源：Manus核心能力，HLD
   - 作用：解锁系统生态（grep, git, tree, rg等），覆盖80%工具需求
   - 代码量：~200 lines
   - 时间：30-40分钟

2. **三文件工作法** (task_plan.md/findings.md/progress.md)
   - 来源：Manus核心架构，HLD
   - 作用：Token消耗降低60-80%，长任务成功率提升40%
   - 代码量：~400 lines
   - 时间：2-3小时

3. **FileOpsTool（文件操作工具）**
   - 来源：Tool-Use, FileSystem
   - 作用：Agent读写文件，实现三文件工作法
   - 代码量：~300 lines
   - 时间：1.5-2小时

4. **AgentFileSystem基础API**
   - 来源：FileSystem模块
   - 作用：文件系统抽象层，支持多租户隔离
   - 代码量：~300 lines
   - 时间：1.5-2小时

5. **多租户基础架构** (Org/Team/Workspace)
   - 来源：Multi-Tenancy, HLD
   - 作用：企业级产品的基础，数据隔离
   - 代码量：~750 lines（包含DB schema）
   - 时间：4-5小时

6. **Plan Manager（计划管理器）**
   - 来源：Planning模块
   - 作用：原子化任务拆分，Plan验证
   - 代码量：~250 lines
   - 时间：1.5-2小时

7. **前端Chat界面基础**
   - 来源：UI-Design
   - 作用：用户交互入口
   - 代码量：~700 lines（Chat + Sidebar）
   - 时间：4-5小时

8. **推理链可视化UI**
   - 来源：Chain-of-Thought-UI
   - 作用：建立信任，缓解等待焦虑
   - 代码量：~500 lines
   - 时间：3-4小时

### 4.2 P1重要（尽快补充）

9. **Skill系统三级懒加载**
   - 来源：Skill-Design
   - 作用：Token节省90%+，能力可插拔
   - 代码量：~1050 lines（含Matcher、Loader）
   - 时间：6-8小时

10. **Context压缩与文件系统指针**
    - 来源：Context-Compression
    - 作用：防止Context爆炸，可恢复
    - 代码量：~700 lines
    - 时间：4-5小时

## 5. 开发工作量预估

### 5.1 按阶段统计（所有能力）

| 阶段 | P0能力 | P1能力 | P2能力 | 总代码量 | 预计工时 |
|------|--------|--------|--------|---------|---------|
| **Phase 3（当前）** | 12个 | 2个 | 0个 | ~5,150 lines | 25-30小时 |
| **Phase 4** | 2个 | 25个 | 1个 | ~9,380 lines | 45-55小时 |
| **Phase 5** | 0个 | 4个 | 7个 | ~5,450 lines | 25-30小时 |
| **总计** | 14个 | 31个 | 8个 | ~19,980 lines | 95-115小时 |

注：P0已完成4个（Phase 1-2），P0总共32个，剩余18个待开发。

### 5.2 MVP最小可用版本（推荐范围）

**MVP定义**：能够完成Deep Research任务，具备基础HITL和UI，支持单租户

**必需能力**：
- Agent Engine: Plan Recitation + Keep Failures + 三文件工作法
- Tools: ShellTool + FileOpsTool + Web Search + Read URL
- FileSystem: 基础API + Workspace目录
- Planning: Plan Manager + 原子化拆解
- UI: Chat界面 + 推理链可视化 + Working Memory标签页
- Multi-Tenancy: 基础架构（单Org场景）

**MVP工作量**：
- 代码量：~5,500 lines
- 时间：30-35小时（约4-5个工作日）
- 优先级：全部P0

## 6. 开发建议

### 6.1 立即行动（Phase 3补全）

1. **ShellTool** (30min) - 解锁系统生态
2. **AgentFileSystem基础** (2h) - 文件操作基础
3. **FileOpsTool** (2h) - Agent读写文件
4. **三文件工作法** (3h) - Token优化核心
5. **Plan Manager** (2h) - 任务拆解
6. **多租户基础** (5h) - 企业级基础
7. **Chat UI + 推理链可视化** (8h) - 用户界面

**Phase 3补全总计**: ~22小时（3个工作日）

### 6.2 快速推进（Phase 4核心）

- Skill三级懒加载系统 (8h)
- Context压缩与文件系统指针 (5h)
- Memory系统基础 (8h)
- Context Graph记录 (4h)

**Phase 4核心总计**: ~25小时（3-4个工作日）

### 6.3 完善补充（Phase 5）

- Sandbox Docker隔离 (8h)
- MCP协议支持 (10h)
- 监控与评估Dashboard (8h)
- 高级UI功能（Artifact预览等）(6h)

**Phase 5总计**: ~32小时（4-5个工作日）

## 7. 总结

### 7.1 关键发现

1. **ShellTool是严重遗漏** 🚨
   - Manus核心能力，Development-Roadmap-v2中未包含
   - 必须立即补充，是MVP的P0能力

2. **三文件工作法是MVP核心** ⭐⭐⭐
   - Token节省60-80%，长任务成功率提升40%
   - 必须在Phase 3立即实现

3. **前端UI工作量被低估**
   - 推理链可视化、Working Memory标签页是MVP必需
   - 预计需要8-10小时开发

4. **Skill系统是差异化优势**
   - 三级懒加载是TokenDance特色
   - 应在Phase 4优先实现

5. **Context管理是性能关键**
   - KV-Cache优化、文件系统指针直接影响成本
   - 需要在Phase 4系统性实现

### 7.2 修订后的MVP范围

**MVP核心能力（30-35小时）**：
1. ShellTool + FileOpsTool + Web Search + Read URL
2. AgentFileSystem基础 + 三文件工作法
3. Plan Manager + 原子化拆解
4. Plan Recitation + Keep Failures
5. Chat UI + 推理链可视化 + Working Memory标签页
6. 多租户基础架构
7. HITL完善（确认对话框）

完成以上后，TokenDance即可达到**可演示的MVP状态**，能够：
- ✅ 完成Deep Research任务
- ✅ 展示推理过程和文件操作
- ✅ Token消耗优化60%+
- ✅ 支持企业级多租户
- ✅ 具备基础HITL能力

### 7.3 开发时间线

- **Phase 3补全**: 3个工作日 (2026-01-14 ~ 2026-01-16)
- **Phase 4核心**: 3-4个工作日 (2026-01-17 ~ 2026-01-21)
- **MVP达成**: 2026-01-21
- **Phase 5完善**: 2026-01-22 ~ 2026-01-28

**目标**: 2026-01-21达到MVP，2026-01-28完成Phase 5核心功能。
