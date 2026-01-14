# TokenDance Agent Instructions

## 项目概述
TokenDance是一个通用AI Agent平台，结合Manus、GenSpark、AnyGen的优势，MVP功能包括AI Deep Research和AI PPT Generation。

## 核心架构原则
- **Plan Recitation**: TODO列表追加到Context末尾，防止Lost-in-the-Middle
- **Dual Context Streams**: 摘要入Context（Working Memory），全量存文件系统（File System）
- **原子化拆分**: 把60%成功率的大任务切成100个99.9%成功率的小任务
- **Keep the Failures**: 保留失败记录供学习，记录到Context Graph
- **Skill三级加载**: L1元数据（始终加载），L2指令（触发时加载），L3资源（按需加载）

## 开发规则

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

## 文档索引
完整设计文档位于 `docs/` 目录，需要时按需读取：

**产品与架构**:
- `docs/product/PRD.md` - 产品需求文档
- `docs/architecture/HLD.md` - 高层设计
- `docs/architecture/LLD.md` - 低层设计 (API + DB Schema)

**UI设计**:
- `docs/design/UI-Design.md` - UI设计规范
- `docs/design/Chain-of-Thought-UI.md` - 执行追踪UI

**核心模块**:
- `docs/modules/Context-Management.md` - Context管理（摘要压缩、增量更新）
- `docs/modules/Memory.md` - 三层记忆（Episodic/Semantic/Procedural）
- `docs/modules/Skill-Design.md` - Skill三级懒加载
- `docs/modules/Reasoning.md` - Self-Reflection三模式
- `docs/modules/Planning.md` - 原子化拆分、非线性图
- `docs/modules/Tool-Use.md` - 三步走闭环、稳定性四策略
- `docs/modules/Context-Graph.md` - 决策轨迹记录、审计追踪

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
cd backend && uv run pytest

# 后端 - 代码检查
cd backend && uv run ruff check . && uv run mypy .
```

## 设计哲学
1. **长期主义**: 打好技术地基，模块间自洽不矛盾
2. **Progressive Disclosure**: 渐进式披露复杂性
3. **Human in the Loop**: 关键决策人工介入
4. **Workspace概念**: 每个Session有独立工作空间
5. **Controlled Randomness**: 温度参数根据任务类型调整
6. **Action Space Pruning**: 最小工具集 > 100个垂直API

## 重要提醒
- 所有模块都向Context Graph记录决策轨迹
- 大文件/工具结果存文件系统，Message中只放摘要
- Context超过50K tokens触发自动摘要
- Plan和TODO列表始终追加在Context末尾（Plan Recitation）
- Memory提取在Session结束或摘要生成时触发
