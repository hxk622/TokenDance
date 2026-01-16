# Task Plan - 当前开发任务

**创建时间**: 2026-01-15  
**任务名称**: MVP Sprint - Deep Research + PPT + 文件索引  
**预计周期**: 4周 (Week 1-4)
**开发模式**: Option A (功能) + Option B (基础设施) 并行

---

## 🎯 本次任务目标

实现 **MVP 核心功能**，包括：
- Deep Research 工作流 (Manus 主导)
- PPT Generation 工作流
- 本地文件索引系统 (Coworker 基因)
- E2E 测试 + 性能基准

**设计规范**: `docs/product/VisionAndMission.md`

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
- [x] 集成 D3.js 库并实现 DAG 渲染 - 已完成

### 验收标准
- ✅ 用户可拖拽调整左右比例，拖拽后刷新页面比例保持
- ✅ Workflow Graph 可显示至少5个色球节点和连线
- ✅ 点击色球节点时，下部日志区域滚动到对应位置

---

## 👨‍💻 UI-Sprint-Phase2 - 交互增强 (Week 3-4) ✅ 已完成

### 目标
完善 Artifact Tabs + Coworker 专属视图 + 聚焦模式。

### 任务清单
- [x] 实现 ArtifactTabs 组件（支持切换、Pin、拖拽排序）- 已完成
- [x] 实现 PreviewArea 组件（支持多种预览类型）- 已完成
- [x] 实现 Coworker File Tree 视图（类似 VS Code Source Control）- 已完成
- [x] 实现 Live Diff 组件（Monaco Editor Diff 模式）- 已完成
- [x] 实现聚焦模式（点击节点后上20%/下80%）- 已完成
- [x] 实现折叠模式（只显示 mini-graph）- 已完成
- [x] 添加"固定视图"按钮（锁定 Scroll-Sync）- 已完成

### 验收标准
- ✅ 右侧可通过 Tab 切换 Report、PPT、File Diff 等视图
- ✅ Coworker 修改文件时，自动切换到 File Diff Tab 并高亮变更
- ✅ 用户可进入聚焦模式，下部日志只显示当前节点内容

**完成时间**: 2026-01-15
**Commit**: 2147df9

---

## ✨ UI-Sprint-Phase3 - Vibe体验打磨 (Week 5-6) ✅ 已完成

### 目标
实现毛玻璃特效 + 色球动画 + 智能滚动。

### 任务清单
- [x] 添加毛玻璃背景（backdrop-filter: blur(20px)）- 已完成
- [x] 实现色球呼吸动画（pulse-breath 1.5s 周期）- 已完成
- [x] 实现能量连线流光效果（stroke-dasharray + animation）- 已完成
- [x] 实现智能滚动策略（检测用户意图，避免强制跳转）- 已完成
- [x] 添加过渡动画（布局变化200ms，色球切换300ms）- 已完成
- [x] 微交互打磨（Hover态、拖拽反馈、加载动画）- 已完成

### 验收标准
- ✅ 青色色球有明显的呼吸动画，绿色色球静止锁定
- ✅ 能量连线有从左向右的流光效果
- ✅ 用户手动滚动日志时，自动暂停 Scroll-Sync
- ✅ 整体视觉符合 "Vibe Workflow" 氛围感标准

**完成时间**: 2026-01-15
**Commit**: 6db26ed

---
## 📋 MVP Sprint - Week 1-2 任务

### Deep Research 工作流 (Option A)

#### 1. DeepResearchAgent 实现 ✅
文件: `backend/app/agent/agents/deep_research.py`
- [x] 继承 ResearchAgent，扩展多轮搜索能力
- [x] 实现 QueryExpansion (查询扩展)
- [x] 实现 SourceCredibility (来源可信度评估)
- [x] 实现 InformationSynthesis (信息综合)

#### 2. 研究报告生成 ✅
文件: `backend/app/agent/tools/builtin/report_generator.py`
- [x] Markdown 报告模板
- [x] 引用管理 (自动生成参考文献)
- [x] 摘要生成 (Executive Summary)
- [x] 关键发现提取

#### 3. 时光长廊 (Timeline) ✅
文件: `backend/app/services/research_timeline.py`
- [x] 截图存储 (MinIO/本地)
- [x] 时间戳索引
- [x] 页面元数据记录
- [ ] 前端 Timeline 组件集成

### 本地文件索引 (Option B)

#### 4. 文件系统服务 ✅
文件: `backend/app/services/file_indexer.py`
- [x] 目录遍历 (支持 .gitignore)
- [ ] 文件监听 (watchdog) - 待集成
- [x] 增量索引策略
- [x] 语言检测

#### 5. 代码分析 ✅
文件: `backend/app/services/code_analyzer.py`
- [x] AST 解析 (Python ast 模块)
- [x] 依赖关系提取
- [x] 符号提取 (函数/类/变量)
- [x] 代码结构图生成

#### 6. 向量化索引 ✅
文件: `backend/app/services/vector_indexer.py`
- [x] 文件内容向量化 (OpenAI Embeddings / 本地模型)
- [x] pgvector 存储
- [x] 语义搜索 API

#### 7. API 端点 ✅
文件: `backend/app/api/v1/research.py` + `backend/app/api/v1/files.py`
- [x] Deep Research API (启动/状态/报告/时间线)
- [x] Files API (索引/搜索/目录树/符号分析)
- [x] 路由注册到 api.py

---

## 📋 MVP Sprint - Week 3-4 任务

### PPT Generation (Option A)

#### 7. PPT Agent
文件: `backend/app/agent/agents/ppt_agent.py`
- [ ] 大纲生成 (从研究报告/笔记)
- [ ] 内容填充 (每页要点)
- [ ] 视觉建议 (图表/图片)

#### 8. 渲染引擎
文件: `backend/app/services/ppt_renderer.py`
- [ ] Slidev 模板集成
- [ ] Marp 备选方案
- [ ] 图表渲染 (Mermaid/Chart.js)
- [ ] 导出 (PDF/PPTX via puppeteer)

### 测试与性能 (Option B)

#### 9. E2E 测试
文件: `backend/tests/e2e/`
- [ ] Deep Research 完整流程测试
- [ ] PPT Generation 测试
- [ ] HITL 交互测试
- [ ] 错误恢复测试

#### 10. 性能基准
文件: `backend/tests/benchmark/`
- [ ] Token 消耗统计
- [ ] 响应时间测量
- [ ] 并发任务测试 (5 tasks)
- [ ] 内存/CPU 监控

---

## 📦 新增交付物 (2026-01-15)

### HITL 前端集成
- `frontend/src/api/hitl.ts` - HITL API 客户端
- `frontend/src/components/execution/HITLConfirmDialog.vue` - 确认弹窗
- ChatView 集成轮询 + 浮动徽章

### Vibe 设计系统
- `frontend/src/styles/vibe.css` - 全局 Vibe 样式
- `frontend/src/components/common/RippleButton.vue` - 波纹按钮

### 文档
- `docs/api/README.md` - API 文档
- `docs/deployment/README.md` - 部署指南

---

## 🌟 MVP 扩展功能 (2026-01-15 新增)

### 1. AI 图像生成 (Nano Banana 集成) ✅ 已完成
文件: `backend/app/skills/builtin/image_generation/SKILL.md`
- [x] 创建 image_generation Skill 定义
- [x] 创建马年祝福图模板 (`resources/chinese_new_year_2026.md`)
- [x] 实现 generate_image 工具 (Gemini API 调用)
- [x] 实现 edit_image 工具
- [x] 前端图像预览组件 (ArtifactTabs + PreviewArea)
- [x] 添加 GEMINI_API_KEY 环境变量配置

### 2. 舆情分析场景模板 ✅ 已创建
文件: `backend/app/skills/builtin/deep_research/resources/sentiment_analysis_template.md`
- [x] 创建舆情分析场景模板
- [x] 定义情感分析框架
- [x] 定义舆情报告输出模板
- [ ] 集成到 Deep Research Skill 工作流

### 3. 科学计算技能 (100+ Skills) ✅ 已存在
目录: `backend/app/skills/scientific/`
- [x] bioinformatics - 生物信息学
- [x] chemistry - 化学
- [x] clinical - 临床
- [x] data-science - 数据科学
- [x] database - 数据库
- [x] lab-automation - 实验室自动化
- [x] physics - 物理
- [x] research-tools - 研究工具
- [x] visualization - 可视化 (matplotlib, seaborn, plotly, networkx)
- [x] writing - 写作

**工作量评估**:
| 功能 | 工作量 | 优先级 |
|------|--------|--------|
| Nano Banana API 集成 | 2-3天 | P0.5 |
| 马年祝福图模板 | 已完成 | P0.5 |
| 舆情分析模板 | 已完成 | P1 |
| 科学计算技能 | 已存在 | P1 |

---

## 📝 开发原则

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

### Deep Research MVP
- [ ] 用户输入主题，自动搜索 5+ 来源
- [ ] 生成结构化 Markdown 报告 (带引用)
- [ ] 时光长廊显示关键页面截图
- [ ] 支持 HITL 确认关键发现

### PPT Generation MVP
- [ ] 从研究报告一键生成 PPT
- [ ] 10-15 页幻灯片
- [ ] 支持导出 PDF
- [ ] 基础图表支持

### 文件索引 MVP
- [ ] 拖入文件夹自动索引
- [ ] 语义搜索 ("找到处理用户认证的代码")
- [ ] 文件树可视化
- [ ] 增量更新 (< 1s)

### 交付物要求
- 代码有完整注释
- 关键功能有测试覆盖
- 文档与代码同步更新
- Git提交信息规范

---

## 📅 里程碑

- **Week 1 End**: Deep Research 基础流程 + 文件遍历
- **Week 2 End**: 研究报告生成 + 向量化索引
- **Week 3 End**: PPT 大纲生成 + E2E 测试框架
- **Week 4 End**: PPT 导出 + 性能基准报告

---

## 🔄 计划更新日志

- 2026-01-14: 初始化task_plan.md，记录Phase 4完成状态
- 2026-01-15: UI-Sprint Phase 1-3 全部完成
- 2026-01-15: HITL 前端集成完成
- 2026-01-15: API 文档 + 部署指南完成
- 2026-01-15: 切换到 MVP Sprint (Deep Research + PPT + 文件索引)
- 2026-01-15: **MVP 扩展功能讨论与初步实施**
  - 新增 AI 图像生成 Skill (Nano Banana)
  - 新增马年祝福图模板
  - 新增舆情分析场景模板 (作为 Deep Research 扩展)
  - 确认科学计算 100+ Skills 已存在

---

## 🔧 改进任务 - 信任等级机制 + Skill 冷启动优化 (2026-01-15)

### 1. 信任等级机制 (Trust Level) ✅ 已完成

**目标**: 优化 HITL 确认体验，减少不必要的打断

**实现内容**:
- `backend/app/agent/tools/risk.py` - 风险等级枚举和操作分类
- `backend/app/agent/tools/base.py` - BaseTool 扩展风险评估方法
- `backend/app/models/trust_config.py` - TrustConfig 和 TrustAuditLog 模型
- `backend/app/services/trust_service.py` - 信任决策服务
- `backend/app/agent/base.py` - Agent 集成信任评估
- `backend/app/api/v1/trust.py` - Trust API 端点
- `frontend/src/api/trust.ts` - 前端 API 客户端
- `frontend/src/components/execution/HITLConfirmDialog.vue` - 增强确认弹窗
- `frontend/src/components/settings/TrustSettings.vue` - 信任设置页面

**风险等级**: NONE → LOW → MEDIUM → HIGH → CRITICAL

### 2. Skill 冷启动优化 - 场景预设和模板系统 ✅ 已完成

**目标**: 帮助新用户快速上手，降低使用门槛

**实现内容**:
- `backend/app/skills/types.py` - 新增 SkillTemplate, ScenePreset, TemplateCategory 类型
- `backend/app/skills/template_registry.py` - 模板注册和管理服务
- `backend/app/skills/builtin/deep_research/templates.yaml` - 5 个研究模板
- `backend/app/skills/builtin/ppt/templates.yaml` - 5 个 PPT 模板
- `backend/app/skills/presets/scenes.yaml` - 8 个场景预设
- `backend/app/api/v1/skills.py` - Skill 发现 API
- `frontend/src/api/skills.ts` - 前端 API 客户端
- `frontend/src/views/SkillDiscovery.vue` - Skill 发现页面
- `frontend/src/components/skills/TemplateCard.vue` - 模板卡片组件
- `frontend/src/components/skills/TemplateModal.vue` - 模板详情弹窗
- `frontend/src/router/index.ts` - 添加 /discover 路由

**设计规范修正**:
- 将 Emoji 图标替换为 Heroicons 图标名称引用
- 将功能导向描述改为用户任务导向描述
- 遵循 agent.md 中的 UI 设计原则

---

**当前状态**: MVP Sprint Week 2 完成，金融场景规划启动 (2026-01-16)

---

## 🏦 金融场景开发计划 (2026-01-16 新增)

### 目标
实现面向金融投研用户的完整工作流，差异化定位为 **"和 AI 一起研究"的协作工作台**。

### 背景
- **竞品分析**: MindSpider (数据终端)、OpenBB (开源平台)、BettaFish (自动报告)、Daily Stock Analysis (订阅推送)
- **核心差异**: Vibe Workflow + 透明可干预 + 完整工作流
- **详细方案**: `docs/product/Financial-Product-Plan.md`

### 里程碑

#### Phase 1: 基础架构 (Week 1-2, 约 10-13 天)
- [ ] 任务 1.1: FinancialResearchAgent 核心 (3-4 天)
  - 继承 DeepResearchAgent
  - 金融专属状态机：scoping → collecting → analyzing → valuating → sentiment → reporting
  - 集成 financial_research_template.md
  - 数据源智能路由

- [ ] 任务 1.2: 金融数据工具集 (5-6 天)
  - GetStockQuoteTool - 实时行情
  - GetFinancialStatementsTool - 财务报表
  - GetFinancialRatiosTool - 财务指标计算
  - GetAnalystRatingsTool - 机构评级
  - GetMarketSentimentTool - 市场情绪
  - CalculateValuationTool - 估值计算

- [ ] 任务 1.3: OpenBB SDK 集成 (2-3 天)
  - OpenBBProvider 服务
  - 多数据源降级策略
  - 错误处理与缓存

#### Phase 2: 分析引擎 (Week 3-4, 约 10-13 天)
- [ ] 任务 2.1: 财务分析模块 (3-4 天)
  - 盈利能力/成长能力/偿债能力/现金流分析
  - 财务健康度评分

- [ ] 任务 2.2: 估值分析模块 (3-4 天)
  - 相对估值 (PE/PB/PS)
  - 行业对比 + 历史估值
  - DCF 简化模型

- [ ] 任务 2.3: 情绪分析模块 (4-5 天, P2 可延后)
  - 社交媒体抓取
  - NLP 情感分类
  - 情绪指数计算

#### Phase 3: Vibe UI (Week 5-6, 约 10-13 天)
- [ ] 任务 3.1: 股票分析报告页面 (5-6 天)
  - 三栏布局 (左导航 + 中报告 + 右实时流)
  - MetricCard/ValuationTable/SentimentRadar 组件

- [ ] 任务 3.2: 实时数据流右侧栏 (3-4 天)
  - K 线图 (Lightweight Charts)
  - 价格跳动动画
  - 最新消息流

- [ ] 任务 3.3: AI 研究助手交互 (2-3 天)
  - 卡片式对话框
  - 预设问题 + 追问功能

#### Phase 4: 测试优化 (Week 7-8, 约 5-7 天)
- [ ] 任务 4.1: E2E 测试 (3-4 天)
- [ ] 任务 4.2: 性能优化 (2-3 天)

### 技术栈扩展
```python
# 后端新增
openbb>=4.0.0           # OpenBB Platform SDK
yfinance>=0.2.0         # Yahoo Finance
pandas-ta>=0.3.0        # 技术指标
transformers>=4.30.0    # NLP 情绪分析
numpy-financial>=1.0.0  # 财务计算
```

```json
// 前端新增
{
  "lightweight-charts": "^4.0.0",  // K线图
  "chart.js": "^4.0.0"             // 通用图表
}
```

### 成功标准
- [ ] 输入股票代码 → 60s 内生成完整报告
- [ ] 报告包含 5 个章节（指标/财务/估值/情绪/风险）
- [ ] 实时数据流延迟 < 1s
- [ ] Vibe 氛围感评分 > 4.5/5
- [ ] 完整的免责声明 + 合规审查

---
