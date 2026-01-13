# TokenDance 设计文档总览

> 通用AI Agent平台 - MVP阶段
> Last Updated: 2026-01-09

## 📚 文档导航

### 产品文档
- **[产品需求文档 (PRD)](./product/PRD.md)**
  - 产品定位与愿景
  - 目标用户与用户旅程
  - MVP功能范围（AI Deep Research + AI PPT）
  - 渐进式披露与Human-in-the-Loop设计
  - 成功指标与里程碑

### UI 设计文档
- **[UI 设计原则](./UI/UI-Design-Principles.md)** ⭐ 核心
  - 设计哲学：从 "被动观察" 到 "主动指挥"
  - 透明度、操作性、沉淀感三大维度
  - Canvas 实时交互、思维链路动态树
  - 杀手级功能：录像回放、Logits 热力图、人机接管点

- **[UI 设计文档](./UI/UI-Design.md)** ⭐ 更新 v1.1.0
  - 设计原则与视觉规范（整合 AnyGen 参考设计）
  - 色彩系统（蓝紫渐变主色调）、排版系统、间距系统
  - 核心组件设计（ChatMessage、ConfirmDialog等）
  - 页面布局与响应式设计
  - 技术实现（Shadcn/UI Vue + Tailwind）
  - 性能优化策略（代码分割、异步加载）
  - Feature Flags 系统、Guest 模式设计

- **[AnyGen UI 分析](./UI/AnyGen-UI-Analysis.md)** 🆕
  - 技术栈分析（React + Modern.js 微前端）
  - 页面结构与路由系统
  - UI 设计模式（@universe-design 组件库）
  - 性能优化策略（代码分割、CDN 部署）
  - 用户体验特性（Feature Flags、Guest 模式）
  - TokenDance 设计借鉴与创新点

- **[UI/UX Pro Max 整合](./UI/UI-UX-Pro-Max-Integration.md)** 🆕
  - 核心设计原则（图标、交互、对比度、布局）
  - 交付前检查清单（25 项必查）
  - 整合到 TokenDance UI 规范
  - Agent 特定组件规范
  - 实施计划与关键收益

- **[UI 组件检查清单](./UI/UI-Component-Checklist.md)** ✅
  - 25 项交付前必查（视觉质量、交互、无障碍）
  - 常见错误参考与正确做法
  - TokenDance 特定组件检查
  - 工具推荐与使用流程

- **[思维链 UI 设计](./UI/Chain-of-Thought-UI.md)**
  - Chain-of-Thought 可视化设计

### 技术架构文档
- **[高层设计 (HLD)](./architecture/HLD.md)**
  - 系统整体架构
  - 核心架构原则（Plan Recitation、Keep the Failures等）
  - 技术选型与决策
  - 数据流设计
  - 部署架构与安全设计

- **[低层设计 (LLD)](./architecture/LLD.md)**
  - 项目目录结构
  - 数据库Schema设计
  - RESTful API设计
  - 核心类设计（Agent Engine、Context Manager等）
  - 前端类型定义

### 专项设计文档

**基础设施层**:
- **[FileSystem 模块](./modules/FileSystem.md)** 🆕 ⭐
  - 文件系统优先架构（Source of Truth）
  - workspace/ 目录设计（tasks/, context/, drafts/）
  - Markdown 为 DSL（YAML Frontmatter + Body）
  - 文件监听与数据库同步
  - 与 Context/Memory/Agent 深度集成
  - 透明、可干预、零学习成本

- **[Context管理机制](./modules/Context-Management.md)**
  - 滑动窗口 + 增量摘要
  - 分层存储（Hot/Warm/Cold）
  - Dual Context Streams（Working Memory + File System）⭐
  - KV Cache友好设计
  - 与文件系统深度集成

- **[Memory系统设计](./modules/Memory.md)**
  - 三层记忆架构（Episodic/Semantic/Procedural）
  - 自动提取、合并、压缩
  - 向量检索 + 时间衰减 + 重要性加权
  - 与 Context 管理和文件系统深度集成⭐

- **[Skill系统设计](./modules/Skill-Design.md)**
  - 三级懒加载机制（L1/L2/L3）
  - SKILL.md规范与格式
  - Skill系统组件（Registry、Matcher、Loader）
  - MVP Skill列表
  - Skill开发指南

**核心能力层**:
- **[Reasoning设计](./modules/Reasoning.md)**
  - Self-Reflection三大模式（Reflexion/Actor-Critic/External-Loop）
  - External-Loop优先策略
  - Chain-of-Thought增强
  - 与Tool-Use/Planning集成

- **[Planning设计](./modules/Planning.md)**
  - 原子化拆分原则（60% → 99.9%）
  - 非线性图：悔（Loop）、判（Branching）、改（Feedback）
  - Plan Recitation机制
  - 与Reasoning/Execution集成

- **[Tool-Use设计](./modules/Tool-Use.md)**
  - 三步走闭环（Definition → Reasoning → Execution）
  - 稳定性四大策略（Guardrails、Self-Heal、MCP、层级选择）
  - Tool-Making未来趋势
  - 与文件系统集成

- **[MCP 模块设计](./modules/MCP-Design.md)** 🆕
  - MCP ≈ AI 的 USB-C 接口（标准化外部系统连接）
  - 双层支持：预置 MCP (Google Drive, GitHub, Slack) + 自定义 MCP
  - MCP Manager 核心架构（Registry, Auth, Client）
  - MCP.md 规范与目录结构
  - 与 Agent 集成（Tool-Use 层、Context Manager）
  - 安全设计（权限隔离、HITL、加密存储）
  - Context Graph 深度集成（MCP 调用可追溯）

**执行层**:
- **[Sandbox设计](./modules/Sandbox.md)**
  - Docker隔离执行环境
  - 安全策略、资源限制
  - 测试驱动执行
  - 与文件系统集成

- **[Browser-Use设计](./modules/Browser-Use.md)**
  - Playwright浏览器自动化
  - 网页抓取、截图、表单填写
  - Deep Research核心工具
  - 安全限制、域名白名单

- **[Execution设计](./modules/Execution.md)**
  - 统一执行引擎
  - 集成Sandbox/Browser/FileSystem
  - 为Planning/Reflection提供执行支持
  - 记录执行轨迹到Context Graph

**监控审计层**:
- **[Self-Reflection设计](./modules/Self-Reflection.md)**
  - 三大工业落地模式（Reflexion/Actor-Critic/External-Loop）
  - External-Loop优先策略（真实反馈 > LLM幻觉）
  - 避免反思陷阱（Token成本、延迟、过度修正）
  - 与Memory/Context Graph深度集成

- **[Monitor & Evaluation设计](./modules/Monitor-Evaluation.md)**
  - 三层监控体系（实时/会话/系统）
  - 质量/性能/成本指标收集
  - 异常检测与告警
  - A/B测试框架

- **[Context Graph设计](./modules/Context-Graph.md)**
  - 决策轨迹记录（而非静态知识）
  - 审计追踪：解释"发生了什么"和"为什么"
  - 失败分析：识别常见错误模式
  - 模式涌现：自动发现最佳实践

## 🎯 项目概述

TokenDance是一个融合了Manus、GenSpark、AnyGen最佳实践的通用AI Agent平台。

**核心理念**: 将Agent的思考过程透明化，让AI协作像与人协作一样自然高效。

### 核心特性

| 特性 | 说明 | 来源灵感 |
|-----|------|---------|
| **Skill三级懒加载** | L1元数据始终在线，L2指令按需加载，L3资源动态获取 | 创新设计 |
| **Plan Recitation** | 目标背诵，防止Lost-in-the-Middle | Manus |
| **Keep the Failures** | 保留错误记录，形成先验避坑能力 | Manus |
| **Dual Context Streams** | Working Memory + File System双重分身 | Manus |
| **Read-then-Summarize** | 网页先摘要再入context，避免爆炸 | GenSpark |
| **Citations** | 引用回溯，每个结论可追溯来源 | GenSpark |
| **双系统验证** | A模型执行，B模型验证，防幻觉 | AnyGen |
| **Human-in-the-Loop** | 高风险操作人工确认 | AnyGen |
| **File System First** | 文件系统 = Source of Truth，透明可干预 | Manus ⭐ |
| **KV-Cache 优化** | Append-Only + 结构化标记，命中率 > 90% | Manus 🆕 |

### MVP功能

#### 1. AI Deep Research（深度研究）
- 多源并行搜索
- 智能信息聚合与去重
- 引用回溯系统
- 结构化报告生成

#### 2. AI PPT（智能演示文稿）
- 主题/大纲智能生成
- 多套模板风格
- 实时预览与编辑
- 单页重新生成
- 导出PPTX/PDF

## 🏗️ 技术栈

- **[Context管理机制](./modules/Context-Management.md)** ⭐ 更新 v2.0.0
  - 滑动窗口 + 增量摘要
  - Dual Context Streams（Working Memory + File System）
  - **KV-Cache 优化策略** 🆕：Append-Only + Structured Tags + Tool Masking
  - 性能提升：7x faster
  - KV-Cache 命中率 > 90%

- **[Tool-Use设计](./modules/Tool-Use.md)** ⭐ 更新 v2.0.0
  - 三步走闭环（Definition → Reasoning → Execution）
  - 四大稳定性策略（Guardrails、Self-Heal、MCP、层级选择）
  - **工具定义一次性加载** 🆕：所有工具在初始化时加载
  - **工具掩码技术** 🆕：通过 Attention Mask 控制可见性

### 前端
- **框架**: Vue 3 + TypeScript
- **UI组件**: Shadcn/UI Vue + Tailwind CSS
- **状态管理**: Pinia
- **构建工具**: Vite

### 后端
- **框架**: FastAPI（Python）
- **任务队列**: Celery + Redis
- **数据库**: PostgreSQL + pgvector
- **缓存**: Redis
- **对象存储**: MinIO
- **沙箱**: Docker

### LLM & 外部服务
- **主模型**: Claude API
- **备选**: Gemini API
- **搜索**: Tavily API / SerpAPI

## 📐 架构亮点

### 1. Token效率优化

```
传统Agent: 每次任务携带全量指令 → 10K+ tokens
TokenDance: Skill三级懒加载 → 2K tokens (节皁80%)
```

### 2. KV-Cache 优化 🆕

```
传统Agent: 每轮重构 context → 35,000 tokens 计算 → 慢
TokenDance: Append-Only + Stable Prefix → 5,000 tokens 计算 → 7x faster

System Prompt + 工具定义（固定）→ KV-Cache 100% 命中 → 首字延迟 <500ms
结构化标记：<|SYSTEM|> <|REASONING|> <|TOOL_CALL|> <|TOOL_RESULT|>
```

### 3. Skill可插拔

```
新增Skill:
1. 创建 skills/my_skill/SKILL.md
2. 重启服务
3. 自动热加载，无需修改代码
```

### 4. 工具精简化

```
5个高泛化工具 > 100个垂直API
Agent可在沙箱中自建工具
```

## 📅 开发计划

### Phase 1 (Week 1-2): 基础框架
- [x] 项目目录结构
- [ ] 数据库Schema实现
- [ ] FastAPI基础框架
- [ ] Vue3前端基础布局

### Phase 2 (Week 3-4): Agent引擎核心
- [ ] Context Manager
- [ ] Skill三级加载系统
- [ ] 基础工具实现
- [ ] Plan Manager

### Phase 3 (Week 5-6): Deep Research Skill
- [ ] 搜索工具集成
- [ ] Read-then-Summarize
- [ ] 引用回溯系统

### Phase 4 (Week 7-8): AI PPT Skill
- [ ] PPT模板系统
- [ ] 内容生成pipeline
- [ ] 导出PPTX/PDF

### Phase 5 (Week 9-10): 打磨发布
- [ ] 双系统验证
- [ ] Memory持久化
- [ ] UI优化与测试

## 🔗 相关资源

### 参考产品
- [Manus](https://manus.im) - 沙箱执行 + 计划管理
- [GenSpark](https://genspark.ai) - 深度研究 + 引用回溯
- [AnyGen](https://anygen.io) - 渐进式引导 + HITL + UI/UX 最佳实践 ⭐
- [Perplexity](https://perplexity.ai) - 搜索引擎

### 技术文档
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Shadcn/UI Vue](https://www.shadcn-vue.com/)
- [Claude API Reference](https://docs.anthropic.com/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

## 📝 文档贡献

如需更新文档，请遵循以下规范：

### 目录结构规范

```
docs/
├── README.md                 # 文档导航入口
├── product/                  # 产品文档
│   └── PRD.md               # 产品需求文档
├── architecture/            # 架构设计文档
│   ├── HLD.md              # 高层设计
│   ├── LLD.md              # 低层设计
│   └── Multi-Tenancy.md    # 多租户设计
├── UI/                      # UI/UX 设计文档（统一存放）
│   ├── UI-Design-Principles.md  # 设计原则与哲学
│   ├── UI-Design.md             # 视觉规范与组件
│   ├── UI-Component-Checklist.md
│   └── ...                      # 其他 UI 相关文档
├── modules/                 # 模块设计文档
│   ├── Context-Management.md
│   ├── Memory.md
│   ├── Planning.md
│   └── ...                  # 各功能模块设计
└── [其他专项文档]           # 如 NEO4J_INTEGRATION.md
```

### 目录职责说明

| 目录 | 职责 | 文档类型 |
|-----|------|----------|
| `product/` | 产品定义 | PRD、用户故事、竞品分析 |
| `architecture/` | 系统架构 | HLD、LLD、架构决策记录 |
| `UI/` | **所有 UI/UX 相关** | 设计原则、视觉规范、组件设计、交互设计 |
| `modules/` | 功能模块 | 各子系统详细设计 |

### 其他规范

1. **命名规范**: 使用英文，kebab-case（如 `UI-Design-Principles.md`）
2. **版本管理**: 更新文档时同步更新版本号和日期
3. **交叉引用**: 确保文档间的链接正确
4. **UI 文档归属**: 所有 UI/UX 相关文档统一放入 `UI/` 目录

## 📄 License

MIT License

## 👥 团队

- Product: [Product Team]
- Design: [Design Team]
- Engineering: [Engineering Team]

---

**问题反馈**: 请在项目Issue中提出
**文档更新**: 2026-01-09 - 新增 FileSystem 模块设计、增加 KV-Cache 优化策略（HLD v1.1.0, Context-Management v2.0.0, Tool-Use v2.0.0）
