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
- **自动提交**: 每完成一个功能模块或组件后，立即执行 `git add .` + `git commit` + `git push`，保留开发成果
- **提交信息格式**: 
  ```
  feat: <简短描述功能>
  
  <详细说明>
  
  Co-Authored-By: Warp <agent@warp.dev>
  ```
- **提交粒度**: 每完成一个独立组件、修复一个bug、或完成一个TODO项时提交

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
# 安装依赖（假设使用pnpm monorepo）
pnpm install

# 启动前端开发服务器
pnpm --filter web dev

# 启动后端服务器
pnpm --filter api dev

# 运行测试
pnpm test

# 代码检查
pnpm lint
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
