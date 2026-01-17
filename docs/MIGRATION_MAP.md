# 文档迁移映射表

> TokenDance 文档重组 - 文件移动追踪
>
> **创建日期**: 2026-01-17
> **状态**: 🚧 进行中

## 📋 迁移概览

- **总文件数**: 87 个 Markdown 文件
- **需要移动**: ~40 个文件
- **需要合并**: 5 个文件（3 个 AGENTS.md + 2 个 Multi-Tenancy）
- **需要删除**: 1 个文件（test_report.md）
- **需要创建**: ~15 个新文件

---

## 🔄 Week 2: 核心合并（优先级最高）

### 1. AGENTS.md 合并（3 个文件 → 3 个新文件）

| 原文件 | 新位置 | 状态 | 说明 |
|--------|--------|------|------|
| `/AGENTS.md` | `docs/guides/developer/agent-development.md` | ⏳ 待处理 | 合并核心 Agent 行为准则 |
| `/backend/AGENTS.md` | `backend/DEVELOPMENT.md` | ⏳ 待处理 | 提取后端特定内容 |
| `/frontend/AGENTS.md` | `frontend/DEVELOPMENT.md` | ⏳ 待处理 | 提取前端特定内容 |

**合并策略**:
- 核心 Agent 准则 → `docs/guides/developer/agent-development.md`
- 后端开发命令 → `backend/DEVELOPMENT.md`
- 前端开发命令 → `frontend/DEVELOPMENT.md`

### 2. Multi-Tenancy 版本合并（2 个文件 → 1 个文件 + 1 个归档）

| 原文件 | 新位置 | 状态 | 说明 |
|--------|--------|------|------|
| `docs/architecture/Multi-Tenancy-v2.md` | `docs/architecture/multi-tenancy.md` | ⏳ 待处理 | 使用 v2 作为基础 |
| `docs/architecture/Multi-Tenancy.md` | `docs/archive/deprecated/multi-tenancy-v1.md` | ⏳ 待处理 | 归档 v1 版本 |

### 3. README.md 重写/创建

| 文件 | 操作 | 状态 | 说明 |
|------|------|------|------|
| `backend/README.md` | 重写 | ⏳ 待处理 | 当前仅 2 行，需要充实内容 |
| `frontend/README.md` | 创建 | ⏳ 待处理 | 当前不存在 |

### 4. 根目录清理（7 个文件 → 3-4 个文件）

| 原文件 | 新位置 | 状态 | 说明 |
|--------|--------|------|------|
| `/README.md` | 保持不变 | ✅ 保留 | 主项目概览 |
| `/AGENTS.md` | `docs/guides/developer/agent-development.md` | ⏳ 待处理 | 见上方合并策略 |
| `/QUICKSTART.md` | `docs/getting-started/quickstart.md` | ⏳ 待处理 | 移动到入门指南 |
| `/E2E_TEST_GUIDE.md` | `docs/guides/developer/testing-guide.md` | ⏳ 待处理 | 移动到开发者指南 |
| `/AGENT_ROBUSTNESS_ASSESSMENT.md` | `docs/reference/agent-robustness-assessment.md` | ⏳ 待处理 | 移动到参考资料 |
| `/test_report.md` | 删除 | ⏳ 待处理 | 临时文件，直接删除 |
| `CONTRIBUTING.md` | 创建 | ⏳ 待处理 | 新建贡献指南 |
| `CHANGELOG.md` | 创建 | ⏳ 待处理 | 新建版本历史 |

---

## 📝 Week 3: 系统化重命名（统一为 kebab-case）

### 架构文档

| 原文件 | 新文件名 | 状态 | 说明 |
|--------|----------|------|------|
| `docs/architecture/HLD.md` | `docs/architecture/hld.md` | ⏳ 待处理 | 高层设计 |
| `docs/architecture/LLD.md` | `docs/architecture/lld.md` | ⏳ 待处理 | 低层设计 |
| `docs/architecture/Agent-Engine-LLD.md` | `docs/architecture/agent-engine-lld.md` | ⏳ 待处理 | Agent 引擎设计 |
| `docs/architecture/Agent-Runtime-Design.md` | `docs/architecture/agent-runtime-design.md` | ⏳ 待处理 | Agent 运行时设计 |
| `docs/architecture/MCP-Integration.md` | `docs/architecture/mcp-integration.md` | ⏳ 待处理 | MCP 集成 |
| `docs/architecture/Working-Memory-Design.md` | `docs/architecture/working-memory-design.md` | ⏳ 待处理 | Working Memory 设计 |

### 产品文档

| 原文件 | 新文件名 | 状态 | 说明 |
|--------|----------|------|------|
| `docs/product/PRD.md` | `docs/product/prd.md` | ⏳ 待处理 | 产品需求文档 |
| `docs/product/VisionAndMission.md` | `docs/product/vision-and-mission.md` | ⏳ 待处理 | 愿景与使命 |
| `docs/product/Financial-Product-Plan.md` | `docs/product/financial-product-plan.md` | ⏳ 待处理 | 金融产品计划 |
| `docs/product/Financial-UI-Enhancement.md` | `docs/product/financial-ui-enhancement.md` | ⏳ 待处理 | 金融 UI 增强 |

### 模块文档

| 原文件 | 新文件名 | 状态 | 说明 |
|--------|----------|------|------|
| `docs/modules/Context-Ment.md` | `docs/modules/context-management.md` | ⏳ 待处理 | Context 管理 |
| `docs/modules/Memory.md` | `docs/modules/memory.md` | ⏳ 待处理 | Memory 系统 |
| `docs/modules/Reasoning.md` | `docs/modules/reasoning.md` | ⏳ 待处理 | Reasoning 设计 |
| `docs/modules/Planning.md` | `docs/modules/planning.md` | ⏳ 待处理 | Planning 设计 |
| `docs/modules/Execution.md` | `docs/modules/execution.md` | ⏳ 待处理 | Execution 设计 |
| `docs/modules/Tool-Use.md` | `docs/modules/tool-use.md` | ⏳ 待处理 | Tool-Use 设计 |
| `docs/modules/Sandbox.md` | `docs/modules/sandbox.md` | ⏳ 待处理 | Sandbox 设计 |
| `docs/modules/Browser-Use.md` | `docs/modules/browser-use.md` | ⏳ 待处理 | Browser-Use 设计 |
| `docs/modules/FileSystem.md` | `docs/modules/filesystem.md` | ⏳ 待处理 | FileSystem 模块 |
| `docs/modules/MCP-Design.md` | `docs/modules/mcp-design.md` | ⏳ 待处理 | MCP 设计 |
| `docs/modules/Skill-Design.md` | `docs/modules/skill-design.md` | ⏳ 待处理 | Skill 设计 |
| `docs/modules/Self-Reflection.md` | `docs/modules/self-reflection.md` | ⏳ 待处理 | Self-Reflection 设计 |
| `docs/modules/Monitor-Evaluation.md` | `docs/modules/monitor-evaluation.md` | ⏳ 待处理 | Monitor & Evaluation |
| `docs/modules/Context-Graph.md` | `docs/modules/context-graph.md` | ⏳ 待处理 | Context Graph 设计 |

### UX 文档

| 原文件 | 新文件名 | 状态 | 说明 |
|--------|----------|------|------|
| `docs/ux/DESIGN-PRINCIPLES.md` | `docs/ux/design-principles.md` | ⏳ 待处理 | 设计原则 |
| `docs/ux/DESIGN-SYSTEM.md` | `docs/ux/design-system.md` | ⏳ 待处理 | 设计系统 |
| `docs/ux/COMPONENT-CHECKLIST.md` | `docs/ux/component-checklist.md` | ⏳ 待处理 | 组件检查清单 |
| `docs/ux/EXECUTION-PAGE-LAYOUT.md` | `docs/ux/execution-page-layout.md` | ⏳ 待处理 | 执行页面布局 |

### 其他文档

| 原文件 | 新文件名 | 状态 | 说明 |
|--------|----------|------|------|
| `docs/NEO4J_INTEGRATION.md` | `docs/reference/neo4j-integration.md` | ⏳ 待处理 | Neo4j 集成 |
| `docs/Development-Capability-Matrix.md` | `docs/reference/development-capability-matrix.md` | ⏳ 待处理 | 开发能力矩阵 |
| `docs/Development-Roadmap-v2.md` | `docs/reference/development-roadmap-v2.md` | ⏳ 待处理 | 开发路线图 v2 |

---

## 📂 Week 4: 内容重组（移动到新目录）

### 移动到 getting-started/

| 原文件 | 新位置 | 状态 | 说明 |
|--------|--------|------|------|
| `/QUICKSTART.md` | `docs/getting-started/quickstart.md` | ⏳ 待处理 | 快速开始 |

### 移动到 guides/developer/

| 原文件 | 新位置 | 状态 | 说明 |
|--------|--------|------|------|
| `/E2E_TEST_GUIDE.md` | `docs/guides/developer/testing-guide.md` | ⏳ 待处理 | 测试指南 |
| `/AGENTS.md` | `docs/guides/developer/agent-development.md` | ⏳ 待处理 | Agent 开发（合并后） |

### 移动到 reference/

| 原文件 | 新位置 | 状态 | 说明 |
|--------|--------|------|------|
| `/AGENT_ROBUSTNESS_ASSESSMENT.md` | `docs/reference/agent-robustness-assessment.md` | ⏳ 待处理 | Agent 鲁棒性评估 |
| `docs/NEO4J_INTEGRATION.md` | `docs/reference/neo4j-integration.md` | ⏳ 待处理 | Neo4j 集成 |
| `docs/Development-Capability-Matrix.md` | `docs/reference/development-capability-matrix.md` | ⏳ 待处理 | 开发能力矩阵 |
| `docs/Development-Roadmap-v2.md` | `docs/reference/development-roadmap-v2.md` | ⏳ 待处理 | 开发路线图 v2 |

### 移动到 archive/

| 原文件 | 新位置 | 状态 | 说明 |
|--------|--------|------|------|
| `docs/development-logs/*` | `docs/archive/development-logs/*` | ⏳ 待处理 | 所有开发日志 |
| `docs/architecture/Multi-Tenancy.md` | `docs/archive/deprecated/multi-tenancy-v1.md` | ⏳ 待处理 | 旧版多租户设计 |

---

## 🆕 Week 6: 新建文档

### 根目录

| 文件 | 状态 | 说明 |
|------|------|------|
| `CONTRIBUTING.md` | ⏳ 待创建 | 贡献指南 |
| `CHANGELOG.md` | ⏳ 待创建 | 版本历史 |

### 入门指南

| 文件 | 状态 | 说明 |
|------|------|------|
| `docs/getting-started/installation.md` | ⏳ 待创建 | 安装指南 |
| `docs/getting-started/configuration.md` | ⏳ 待创建 | 配置说明 |
| `docs/getting-started/troubleshooting.md` | ⏳ 待创建 | 常见问题排查 |

### 用户指南

| 文件 | 状态 | 说明 |
|------|------|------|
| `docs/guides/user/chat-interface.md` | ⏳ 待创建 | 聊天界面使用 |
| `docs/guides/user/working-memory.md` | ⏳ 待创建 | Working Memory 使用 |
| `docs/guides/user/skills-usage.md` | ⏳ 待创建 | Skill 使用指南 |

### 开发者指南

| 文件 | 状态 | 说明 |
|------|------|------|
| `docs/guides/developer/git-workflow.md` | ⏳ 待创建 | Git 工作流程 |
| `docs/guides/developer/code-quality.md` | ⏳ 待创建 | 代码质量标准 |
| `backend/DEVELOPMENT.md` | ⏳ 待创建 | 后端开发指南 |
| `frontend/DEVELOPMENT.md` | ⏳ 待创建 | 前端开发指南 |

---

## 🗑️ 删除文件

| 文件 | 状态 | 说明 |
|------|------|------|
| `/test_report.md` | ⏳ 待删除 | 临时测试报告 |

---

## 📊 进度统计

### 总体进度

- ✅ 已完成: 0 个文件
- ⏳ 进行中: 0 个文件
- 📋 待处理: ~87 个文件

### 按周统计

| 周次 | 任务 | 状态 |
|------|------|------|
| Week 1 | 准备阶段 | 🚧 进行中 |
| Week 2 | 核心合并 | ⏳ 待开始 |
| Week 3 | 系统化重命名 | ⏳ 待开始 |
| Week 4 | 内容重组 | ⏳ 待开始 |
| Week 5 | 链接更新与验证 | ⏳ 待开始 |
| Week 6 | 填补文档空白 | ⏳ 待开始 |

---

## 🔗 相关资源

- [文档重组计划](./docs-reorganization-plan.md)（如果存在）
- [主文档索引](./README.md)

---

**最后更新**: 2026-01-17
**维护者**: TokenDance Team
