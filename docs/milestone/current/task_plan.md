# Task Plan - 当前开发任务

**创建时间**: 2026-01-14  
**任务名称**: UI-Sprint - 三栏布局执行页面开发  
**预计周期**: 6周 (Week 1-6)

---

## 🎯 本次任务目标

实现 **Vibe-Agentic Workflow** 执行页面的三栏布局，包括：
- 左侧执行区：Workflow Graph (Meego式DAG) + Streaming Info (日志流)
- 右侧预览区：Artifact Tabs + Preview Area
- 完整的拖拽、联动、动画效果

**设计规范**: `docs/ux/Three-Column-Layout.md`

---

---

## 📋 历史里程碑状态

### Backend-Phase4 - 已完成 (2026-01-14)

### 完成项
- [x] 数据库连接池初始化 (PostgreSQL + Redis)
- [x] 应用生命周期管理
- [x] HITL (Human-in-the-Loop) 机制
- [x] Working Memory UI 可视化
- [x] E2E 测试套件
- [x] 文档更新
- [x] Git 提交 (commit: 86d3879)

### 交付物
- `backend/app/core/redis.py` - Redis连接管理
- `backend/app/services/hitl_service.py` - HITL服务
- `backend/app/api/v1/hitl.py` - HITL API
- `backend/test_e2e.py` - E2E测试
- `frontend/src/components/execution/WorkingMemoryPanel.vue` - UI组件
- `PHASE4_COMPLETION_SUMMARY.md` - 完成总结

### 代码量
~1,434行新增/修改

---

---

## 🎨 UI-Sprint - 当前任务 (2026-01-14 开始)

### 总体路线图

**UI-Sprint-Phase1 (Week 1-2)**: 核心框架  
**UI-Sprint-Phase2 (Week 3-4)**: 交互增强  
**UI-Sprint-Phase3 (Week 5-6)**: Vibe体验打磨

---

## 🔨 UI-Sprint-Phase1 - 核心框架 (Week 1-2)

### 目标
完成三栏基础布局 + Workflow Graph骨架 + Scroll-Sync联动。

### 任务清单
- [x] 创建 ExecutionPage.vue 布局容器 (292行) - 已完成
- [x] 实现 ResizableDivider 组件（水平/垂直拖拽）- 已完成
- [x] 实现 WorkflowGraph 组件占位符（Mock节点）- 已完成
- [x] 实现 StreamingInfo 组件占位符（日志流）- 已完成
- [x] 实现 ArtifactTabs 组件占位符 - 已完成
- [x] 实现 PreviewArea 组件占位符 - 已完成
- [x] 完成布局比例 localStorage 持久化 - 已完成
- [x] 实现 Scroll-Sync 基础联动逻辑 - 已完成
- [ ] 集成 Canvas 库（选择 vis-network 或 D3.js）

### 验收标准
- ✅ 用户可拖拽调整左右比例，拖拽后刷新页面比例保持
- ✅ Workflow Graph 可显示至少5个色球节点和连线
- ✅ 点击色球节点时，下部日志区域滚动到对应位置

---

## 👨‍💻 UI-Sprint-Phase2 - 交互增强 (Week 3-4)

### 目标
完善 Artifact Tabs + Coworker 专属视图 + 聚焦模式。

### 任务清单
- [ ] 实现 ArtifactTabs 组件（支持切换、Pin、拖拽排序）
- [ ] 实现 PreviewArea 组件（支持多种预览类型）
- [ ] 实现 Coworker File Tree 视图（类似 VS Code Source Control）
- [ ] 实现 Live Diff 组件（Monaco Editor Diff 模式）
- [ ] 实现聚焦模式（点击节点后上20%/下80%）
- [ ] 实现折叠模式（只显示 mini-graph）
- [ ] 添加“固定视图”按钮（锁定 Scroll-Sync）

### 验收标准
- ✅ 右侧可通过 Tab 切换 Report、PPT、File Diff 等视图
- ✅ Coworker 修改文件时，自动切换到 File Diff Tab 并高亮变更
- ✅ 用户可进入聚焦模式，下部日志只显示当前节点内容

---

## ✨ UI-Sprint-Phase3 - Vibe体验打磨 (Week 5-6)

### 目标
实现毛玻璃特效 + 色球动画 + 智能滚动。

### 任务清单
- [ ] 添加毛玻璃背景（backdrop-filter: blur(20px)）
- [ ] 实现色球呼吸动画（pulse-breath 1.5s 周期）
- [ ] 实现能量连线流光效果（stroke-dasharray + animation）
- [ ] 实现智能滚动策略（检测用户意图，避免强制跳转）
- [ ] 添加过渡动画（布局变化200ms，色球切换300ms）
- [ ] 微交互打磨（Hover态、拖拽反馈、加载动画）

### 验收标准
- ✅ 青色色球有明显的呼吸动画，绿色色球静止锁定
- ✅ 能量连线有从左向右的流光效果
- ✅ 用户手动滚动日志时，自动暂停 Scroll-Sync
- ✅ 整体视觉符合 "Vibe Workflow" 氛围感标准

---

## 📋 当前Sprint待办

### 本周任务 (2026-01-14 ~ 2026-01-20)

#### 1. 三文件工作法实施 🔥
- [ ] 创建task_plan.md (本文件)
- [ ] 创建findings.md (技术决策记录)
- [ ] 创建progress.md (执行日志)
- [ ] 更新AGENT.md (添加工作流规则)

#### 2. 前端集成
- [ ] 在ChatView中添加WorkingMemoryPanel
- [ ] 创建HITLConfirmDialog组件
- [ ] 测试完整的消息流

#### 3. 文档完善
- [ ] 补充API文档
- [ ] 更新README快速开始
- [ ] 编写部署指南

---

## 🎓 开发原则

### Plan Recitation (计划背诵)
- 每次开始新工作前，重读此计划
- 重大决策前，检查是否符合Phase目标
- 防止Context Drift (上下文漂移)

### 2-Action Rule
- 每2次重大操作 (web_search, read_url等) 后
- 必须将发现写入 findings.md
- 避免对话上下文膨胀

### Keep the Failures
- 所有错误必须记录到 progress.md
- 分析失败原因
- 防止重复犯错

---

## 📊 成功标准

### Phase 5 Milestone 1 完成标志
- [ ] 前端完整集成 (Working Memory + HITL)
- [ ] API文档覆盖率 > 80%
- [ ] 所有E2E测试通过
- [ ] 性能基准测试完成

### 交付物要求
- 代码有完整注释
- 关键功能有测试覆盖
- 文档与代码同步更新
- Git提交信息规范

---

## 🔄 计划更新日志

- 2026-01-14: 初始化task_plan.md，记录Phase 4完成状态
- (待续...)

---

**下次更新时机**: Phase 5 Milestone 1 开始时
