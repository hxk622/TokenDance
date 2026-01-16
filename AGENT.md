# TokenDance Agent Instructions

## 项目概述

### 产品愿景：Vibe-Agentic Workflow

TokenDance 不是另一个 Agent 工具，而是一个**人机共生的终极创作场**。我们通过 **Vibe-Agentic Workflow** 将顶级 Agent 的原子能力进行重组和升华：

**三位一体架构 (The Trinity)**:

1. **Manus （执行大脑）**
   - 全自动任务链 + 计划背诵 + 沙箱执行
   - 负责高难度的外部决策、跨平台调度、从 0 到 1 的全自动交付

2. **Coworker （执行双手）**
   - 本地文件深度操控 + 外科手术式修改
   - 继承 Claude Code 的基因，深度解析本地文件系统

3. **Vibe Workflow （生命气息）**
   - 情感价值 + 直觉交互 + 氛围感体验
   - 将复杂的 Agent 智力转化为丝滑的创作愉悦感

**使命**: 让"Claude Code"这种硬核能力真正服务于全世界（**For the rest of the world**）

MVP功能：AI Deep Research（Manus 主导 + Coworker 辅助）、AI PPT Generation（Manus 主导 + Vibe 增强）

> 详见 [VisionAndMission.md](./docs/product/VisionAndMission.md)

### 垂直场景战略

#### 金融投研场景

**一句话定位**:
> "TokenDance 金融版：不是替你炒股，而是让投研效率提升 10 倍的协作工作台"

**核心原则**:
1. **不做报告生成器** - BettaFish 已经能做，我们要做差异化
2. **发挥 Vibe Workflow 优势** - 让投研过程可视化、可干预、有氛围感
3. **强调人机协作** - 不是 AI 替代分析师，而是 AI 增强分析师
4. **合规第一** - 只做"工具"，不做"投顾"

**与竞品差异**:
- BettaFish: 报告导向（提问 → 等报告）
- TokenDance: 协作导向（Vibe 投研工作台 - 和 AI 一起研究，实时干预）

**禁止事项**:
- ❌ 预测具体股价
- ❌ 给出明确买卖建议
- ❌ 承诺收益率
- ❌ 涉及内幕信息

> 详见 `backend/app/skills/builtin/deep_research/resources/financial_research_template.md`

## 核心架构原则
- **Plan Recitation**: TODO列表追加到Context末尾，防止Lost-in-the-Middle
- **Dual Context Streams**: 摘要入Context（Working Memory），全量存文件系统（File System）
- **原子化拆分**: 把60%成功率的大任务切成100个99.9%成功率的小任务
- **Keep the Failures**: 保留失败记录供学习，记录到Context Graph
- **Skill三级加载**: L1元数据（始终加载），L2指令（触发时加载），L3资源（按需加载）

## 开发规则

### Agent 行为准则：独立思考与质疑

**原则**: Agent 不是纯执行工具，而是具有独立判断力的协作者。

#### 必须做到：

1. **风险识别** - 对用户需求进行独立分析
   - 指出潜在技术风险（性能、安全、兼容性）
   - 识别产品逻辑漏洞（用户体验、边界情况）
   - 评估实现复杂度与价值比

2. **优化建议** - 提供更好的替代方案
   - 当发现更优解时，主动提出并说明理由
   - 对比多种方案的优缺点
   - 推荐最佳实践而非简单实现

3. **补充细节** - 完善用户未考虑到的方面
   - 响应式设计（移动端适配）
   - 无障碍支持（a11y）
   - 错误处理与降级策略
   - 性能优化考虑

4. **质疑不合理需求** - 当发现明显问题时直言
   - 不盲目服从明显错误的设计，不要太听话
   - 用专业判断指出反模式 (anti-pattern)
   - 提供数据或案例支持你的观点

5. **主动提问与反向启发** - 深化思考的深度和广度
   - 在接受任务时，主动提出关键疑问
   - 暴露可能的假设和前提条件
   - 探索边界情况和未考虑的场景
   - 挑战设计背后的深层逻辑
   - **约定**: 用户重视这些问题，Agent 应大胆抛出

#### 输出格式：

当发现问题时，使用以下结构：

```markdown
## ✅ 设计亮点（值得保留）
- ...

## ⚠️ 关键问题与优化建议
### 问题N：...
**当前方案**：...
**问题**：...
**建议**：...
✅ **解决方案**：...
```

#### 例外情况：

- 用户明确说明"我知道问题，但就这么做"
- 用户是MVP快速验证，可接受技术债
- 用户已经经过充分调研和设计

**核心价值观**: “我们不是在制造锤子，我们是在构建一个激发灵感的工坊” —— 这意味着每个决策都应该经得起推敲。

---

### Git提交规范
- **自动提交**: 每完成一个功能模块或组件后，立即执行 `git add .` + `git commit` + `git push`，保留开发成果
- **提交信息格式**: 
  ```
  feat: <简短描述功能>
  
  <详细说明>
  
  Co-Authored-By: Warp <agent@warp.dev>
  ```
- **提交粒度**: 每完成一个独立组件、修复一个bug、或完成一个TODO项时提交

### 三文件工作法 (Manus)

**核心理念**: 文件系统指针 > 内联文本，节省Context 60-80%

#### 文件位置
```
docs/milestone/
├── current/              # 当前任务
│   ├── task_plan.md    # 任务计划
│   ├── findings.md     # 技术决策
│   └── progress.md     # 执行日志
└── archive/             # 历史归档
```

#### 1. task_plan.md (路线图)
**作用**: 任务拆解。在开始任何工作前，AI必须先写好Phase 1, Phase 2...的计划。

**关键点**: 
- 利用SessionStart和PreToolUse钟子
- 让AI在做重大决策前必须"重读"这个计划
- 防止跑偏 (Context Drift)

**Plan Recitation**: 每次开始新工作前，重读task_plan.md

#### 2. findings.md (知识库)
**作用**: 存储研究发现和技术决策。

**关键点**: 
- 推行 "2-Action Rule"
- 每进行两次重大操作 (web_search/read_url等)
- AI必须将发现存入此文件，而不是塞进对话上下文
- 这极大地节省了Token

**2-Action Rule**:
- 每2次`web_search`或`read_url`后
- 必须将发现写入findings.md
- 对话只记录"已写入findings.md"

注意: `grep`、`read_files`等小操作不算在"2次"内

#### 3. progress.md (Session日志)
**作用**: 记录执行过程和测试结果。

**关键点**: 
- 强制记录 **所有错误**
- 这是为了防止AI在同一个坑里反复摔倒
- Manus所谓的不重复失败原则

**Keep the Failures**: 所有错误必须记录到progress.md

#### 为什么能节省Context？

**传统方式**:
```
User: 搜索FastAPI最佳实践
Assistant: [返回3000 tokens的搜索结果]
User: 搜索Vue3组件设计
Assistant: [又返回2500 tokens]
```
→ 对话历史不断膨胀，每次LLM调用都要处理所有历史

**三文件方式**:
```
User: 搜索FastAPI最佳实践
Assistant: [执行搜索，写入findings.md]
         → 对话只记录: "已将FastAPI最佳实践写入findings.md"

User: 现在开始写代码
Assistant: [read_files findings.md]
         → 只在需要时加载
```

**节省原理**:
1. **延迟加载** - 只在需要时读取文件
2. **摘要替代** - 对话历史只记录"已写入"
3. **结构化存储** - 文件系统是无限的，Context是有限的
4. **选择性加载** - 可以只读task_plan.md而不读findings.md

#### Session生命周期

**开始**:
1. 读取task_plan.md
2. 检查当前任务目标
3. 开始工作

**执行中**:
1. 每2次重大操作后写入findings.md
2. 每个Session结束后更新progress.md
3. 遇到错误立即记录到progress.md

**结束**:
1. 更新task_plan.md的完成状态
2. 归档到`docs/milestone/archive/`（如需）
3. Git提交

## 技术栈
- **Frontend**: Vue 3 + TypeScript + Shadcn/UI (Vue) + Tailwind + Pinia
- **Backend**: FastAPI + Celery
- **Database**: 
  - PostgreSQL + pgvector (主存储 + 向量检索)
  - Neo4j (图数据库 - Context Graph、Memory Relations)
  - Redis (缓存) + MinIO (对象存储)
- **Sandbox**: Docker
- **Browser**: Playwright
- **LLM**: Claude API (优先), Gemini API (备选)

## 项目结构
```
TokenDance/
├── apps/
│   ├── web/          # Vue 3前端
│   └── api/          # FastAPI后端
├── packages/
│   ├── core/         # 核心Agent逻辑
│   │   ├── context/  # Context管理 & 双重分身
│   │   ├── memory/   # 三层记忆系统
│   │   ├── reasoning/# 推理引擎 (External-Loop)
│   │   ├── planning/ # 规划引擎 (原子化拆分)
│   │   ├── tools/    # 工具注册表
│   │   ├── skills/   # Skill管理器
│   │   └── context_graph/ # 决策轨迹记录
│   ├── sandbox/      # Docker沙箱
│   └── ui/           # 共享UI组件
└── docs/             # 设计文档
```

## 文档目录规范

### 标准目录结构

```
docs/
├── product/              # 产品文档
│   ├── VisionAndMission.md  (必读)
│   └── PRD.md
├── architecture/         # 架构设计
│   ├── HLD.md
│   └── LLD.md
├── ux/                   # UI/UX设计（合并了UI和design）
│   ├── Three-Column-Layout.md  (必读)
│   ├── UI-Design.md
│   └── Chain-of-Thought-UI.md
├── modules/              # 模块设计
│   ├── Context-Management.md
│   ├── Memory.md
│   └── ...
└── milestone/            # 项目里程碑
    ├── current/          # 当前开发任务（三文件工作法）
    │   ├── task_plan.md
    │   ├── findings.md
    │   └── progress.md
    └── archive/          # 历史里程碑归档
```

### 重要规范

1. **目录命名统一使用小写** - `ux` 而非 `UX` 或 `UI`
2. **禁止目录歧义** - 不允许同时存在 `UI/` 和 `design/`，一律合并到 `ux/`
3. **Milestone命名规范** - 历史里程碑归档时必须加上前缀（如 `Backend-Phase1-Completion.md`）
4. **当前开发任务** - 始终使用 `docs/milestone/current/` 三文件，不创建新的Phase文件

### Milestone命名约定

**历史里程碑（已归档）**:
- `Backend-Phase1-Completion.md` - 后端基础架构
- `Backend-Phase2-Final.md` - 数据库集成
- `Backend-Phase3-Complete.md` - Agent引擎
- `Backend-Phase4-UI-Integration.md` - 前后端集成

**当前任务（正在进行）**:
- 使用 `current/task_plan.md` 记录当前任务的Sprint计划
- Sprint内部可以有子阶段（如UI-Sprint-Phase1/2/3）
- 不在milestone目录根部创建新的Phase文件

---

## 文档索引

**产品与架构**:
- `docs/product/VisionAndMission.md` - 产品愿景与使命（必读！）
- `docs/product/PRD.md` - 产品需求文档
- `docs/architecture/HLD.md` - 高层设计
- `docs/architecture/LLD.md` - 低层设计 (API + DB Schema)

**UX设计**:
- `docs/ux/Three-Column-Layout.md` - 三栏布局规范（必读！）
- `docs/ux/UI-Design.md` - UI设计规范
- `docs/ux/UI-UX-Pro-Max-Integration.md` - UI/UX Pro Max 规范整合（必读！）
- `docs/ux/Chain-of-Thought-UI.md` - 执行追踪UI

**核心模块**:
- `docs/modules/Context-Management.md` - Context管理
- `docs/modules/Memory.md` - 三层记忆
- `docs/modules/Skill-Design.md` - Skill三级懒加载
- `docs/modules/Reasoning.md` - Self-Reflection
- `docs/modules/Planning.md` - 原子化拆分
- `docs/modules/Tool-Use.md` - 工具使用闭环
- `docs/modules/Context-Graph.md` - 决策轨迹记录

## 测试文件规范

### 测试文件位置
- **后端测试**: 所有测试文件必须放在 `backend/tests/` 目录下
- **前端测试**: 所有测试文件必须放在 `frontend/tests/` 目录下（如有）
- **禁止**: 不允许在模块根目录（如 `backend/`）直接放置测试文件

### 测试文件命名
- 文件名必须以 `test_` 前缀开头，如 `test_agent_engine.py`
- 测试类名以 `Test` 开头，如 `TestAgentEngine`
- 测试方法名以 `test_` 开头，如 `test_run_task`

### 测试目录结构
```
backend/tests/
├── __init__.py
├── test_agent_engine.py
├── test_api_integration.py
└── ...
```

---

## 常用命令
```bash
# 前端 - 安装依赖
pnpm install

# 前端 - 启动开发服务器
cd frontend && pnpm dev

# 后端 - 安装依赖 (使用 uv)
cd backend && uv sync --all-extras

# 后端 - 启动开发服务器
cd backend && uv run uvicorn app.main:app --reload

# 后端 - 运行测试
cd backend && uv run pytest tests/

# 后端 - 代码检查
cd backend && uv run ruff check . && uv run mypy .
```

## 设计哲学

### Vibe-Agentic Workflow 三大支柱

1. **直觉重于指令 (Intuition over Instruction)**
   - 拖拽文件即可启动工作流
   - 意图卡片选择而非复杂 Prompt
   - 一键直达，减少认知负荷

2. **情感共鸣与审美张力 (Emotional Resonance & Aesthetic Logic)**
   - 毛玻璃特效 + 丝滑动画反馈
   - 实时进度美学，而非生硬的进度条
   - 界面根据用户状态动态反馈

3. **极低摩擦力的“流” (Frictionless Flow)**
   - 异步（Manus）与同步（Coworker）的节奏管理
   - 消除 Context Switching
   - 无缝衔接，智能预判

### 技术原则

4. **长期主义**: 打好技术地基，模块间自洽不矛盾
5. **Progressive Disclosure**: 渐进式披露复杂性
6. **Human in the Loop**: 关键决策人工介入
7. **Workspace概念**: 每个Session有独立工作空间（沙箱隔离）
8. **Controlled Randomness**: 温度参数根据任务类型调整
9. **Action Space Pruning**: 最小工具集 > 100个垂直API

## UI 设计原则：避免 AI 味道

**核心原则**: TokenDance 是"可指挥的智能工作台"，不是另一个 ChatGPT 克隆

### 禁止事项

1. **禁止 AI 助手式开场白**
   - ❌ "我能帮你..." / "让我帮你..." / "AI 助手"
   - ✅ 直接展示用户能做什么 → "你的智能工作台"

2. **禁止 Emoji 图标**
   - ❌ 🔍🚀📊💻 等 emoji 作为主要图标
   - ✅ 使用专业的 SVG 图标系统（Heroicons/Lucide）

3. **禁止功能导向的描述**
   - ❌ "深度研究" / "生成PPT" / "执行代码"
   - ✅ 用户任务导向 → "市场调研" / "演示汇报" / "开发调试"

4. **禁止通用示例 Prompt**
   - ❌ "帮我..." / "请..." / "生成..."
   - ✅ 具体场景 → "竞品分析·行业报告·数据洞察"

5. **禁止过度的毛玻璃和渐变**
   - ❌ 彩虹渐变背景、大面积半透明
   - ✅ 克制的灰度系统、细微的网格纹理

### 设计语言

**视觉风格**：
- 灰度为主（#fafafa / #f1f5f9 背景）
- 黑色强调（#111827 / #1f2937）
- 色彩克制（仅在状态和强调时使用）
- 细边框（1px gray-100/200）
- 圆角适中（8px / 12px / 16px）

**交互反馈**：
- hover: 边框加深、subtle shadow
- active: 轻微缩放（scale-[0.98]）
- 过渡: 200-300ms ease

**文案原则**：
- 用户是"导演"而非"观众"
- 强调"和 Agent 一起"而非"让 Agent 帮你"
- 突出"接管""干预""复用"等控制感词汇

**参考标杆**：
- Linear（简洁、专业、高效）
- Notion（灰度系统、功能直接）
- Vercel（克制的动效、强调内容）

**Footer Slogan**：
```
随时接管 · 实时干预 · 沉淀复用
```

这三个词直接体现 UI-Design-Principles.md 的核心：
- Controllability (可控性)
- Transparency (透明度)
- Persistence (沉淀感)

## Agent 协作规范：知识沉淀与持续改进

### Plans 使用规范

Agent 支持创建和编辑 Plans（实施计划），用于：
- 复杂任务的分阶段规划
- 技术方案设计与评审
- 多步骤实现的追踪

**沉淀原则**: 重要的讨论结论、技术决策、设计共识应当被持久化：
1. **Plans** - 用于实施计划和技术方案
2. **Rules (WARP.md)** - 用于项目规范和开发约定
3. **三文件工作法** - 用于日常开发的 findings/progress

### Rules 动态更新

当讨论中产生以下内容时，应主动提议更新 WARP.md：
- 新的技术约定或编码规范
- 项目结构变更
- 工具链更新
- 设计规范调整
- 重要的架构决策

**参考项目**: [K-Dense-AI/claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) - 展示了如何将领域知识组织为可复用的 Skills

---

## UI/UX 设计规范（Pro Max 整合版）

**权威参考**: `docs/ux/UI-UX-Pro-Max-Integration.md` （必读！）

该文档整合了 [UI/UX Pro Max Skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) 的专业规范，包含：
- 57 UI 样式 + 95 色彩方案 + 56 字体配对
- 图标系统：Lucide Icons（禁用 Emoji）
- 交互规范：200ms 过渡、cursor-pointer、无布局偏移
- 对比度标准：4.5:1 最低（浅色模式优化）
- 交付检查清单：25 项质量检查点

**开发时必须遵守**: UI-UX-Pro-Max-Integration.md 中的所有规范

---

## 重要提醒
- 所有模块都向Context Graph记录决策轨迹
- 大文件/工具结果存文件系统，Message中只放摘要
- Context超过50K tokens触发自动摘要
- Plan和TODO列表始终追加在Context末尾（Plan Recitation）
- Memory提取在Session结束或摘要生成时触发
