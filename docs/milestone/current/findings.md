# Findings - 技术决策知识库

**创建时间**: 2026-01-14  
**作用**: 记录Phase 1-4的关键技术决策和架构选择

---

## 📐 架构设计决策

### 1. Append-Only Context 模式
**时间**: Phase 1  
**决策**: 采用只追加、不修改的上下文管理方式

**理由**:
- KV-Cache 100%命中率
- 7x性能提升（相比每轮重构context）
- 简化状态管理

**影响**:
- `context_manager.py` 设计遵循此原则
- 所有消息永久保留，不做删除

---

### 2. 三文件Working Memory
**时间**: Phase 2  
**决策**: 采用Manus的三文件工作法

**文件结构**:
- `task_plan.md` - 任务路线图
- `findings.md` - 研究发现 (本文件)
- `progress.md` - 执行日志

**理由**:
- Token节省60-80%
- 长任务成功率提升40%
- 防止Context Drift

**实现**:
- `app/agent/working_memory/three_files.py` (361行)
- 2-Action Rule: 每2次搜索强制写入
- 3-Strike Protocol: 同类错误3次触发恢复

---

### 3. 异步连接池架构
**时间**: Phase 4  
**决策**: PostgreSQL和Redis统一异步连接池管理

**配置**:
```python
# PostgreSQL
pool_size=10
max_overflow=20
pool_pre_ping=True
pool_recycle=3600

# Redis
max_connections=20
socket_keepalive=True
socket_connect_timeout=5
```

**理由**:
- 支持高并发
- 连接复用效率高
- 优雅关闭避免资源泄漏

**文件**: `app/core/database.py`, `app/core/redis.py`

---

## 🛠️ 技术栈选型

### 后端框架
**选择**: FastAPI + SQLAlchemy 2.0 + Alembic

**理由**:
- FastAPI: 异步高性能，自动API文档
- SQLAlchemy 2.0: 异步ORM，类型安全
- Alembic: 数据库迁移管理

**替代方案**: Django (太重), Flask (不支持异步)

---

### 前端框架
**选择**: Vue 3 + TypeScript + Tailwind CSS

**理由**:
- Vue 3: Composition API响应式设计
- TypeScript: 类型安全，IDE支持好
- Tailwind: Utility-first，快速开发

**UI库**: Shadcn/UI (Vue) - 可定制，组件质量高

---

### LLM集成
**选择**: 多模型支持 (Claude + Qwen)

**实现**:
- 抽象基类: `app/agent/llm/base.py`
- Claude: `anthropic.py` - Function Calling
- Qwen: `qwen.py` - 通义千问

**理由**:
- 灵活切换模型
- 降低单一供应商依赖
- Function Calling标准化

---

### 状态管理
**选择**: Redis临时状态 + PostgreSQL持久化

**分工**:
- Redis: HITL请求、缓存、Session状态
- PostgreSQL: 用户数据、消息历史、Artifact

**理由**:
- Redis TTL自动过期
- PostgreSQL ACID保证
- 各司其职，性能最优

---

## 🔧 工具选型

### 包管理器
**选择**: uv (后端) + pnpm (前端)

**理由**:
- uv: Rust实现，速度快，支持清华镜像
- pnpm: 节省磁盘空间，依赖管理严格

---

### 测试框架
**选择**: pytest + pytest-asyncio

**理由**:
- pytest: 生态丰富，插件多
- pytest-asyncio: 完美支持async/await
- Fixture机制强大

---

## 🎨 UI设计原则

### 色彩系统
**主色**: #6366f1 (Indigo)  
**辅助色**: #10b981 (Green), #ef4444 (Red)

**来源**: AnyGen UI分析

**应用**:
- 主要按钮、链接
- 成功/失败状态
- Working Memory Tab激活态

---

### Chain-of-Thought可视化
**设计**: 推理链实时展示

**组件**:
- `ThinkingTrace.vue` - 思考过程
- `ToolCallCard.vue` - 工具调用（蓝色运行/绿色成功/红色失败）
- `ProgressIndicator.vue` - 进度指示

**理由**:
- 透明度提升用户信任
- Debug时快速定位问题
- 符合Progressive Disclosure原则

---

## 🚀 性能优化策略

### 1. SSE流式输出
**决策**: 使用Server-Sent Events

**理由**:
- 单向数据流，简单高效
- 自动断线重连
- 浏览器原生支持

**实现**: `app/api/v1/messages.py` + `useAgentStream.ts`

---

### 2. 连接池调优
**策略**: 根据负载动态调整

**当前配置**: 适合中小规模部署  
**优化方向**: 监控连接使用率，按需扩容

---

### 3. Token优化
**核心**: 三文件工作法 + Append-Only Context

**预期效果**:
- Token消耗: -70%
- 首字延迟: 7x提升
- 长任务成功率: +40%

---

## 🔒 安全设计

### 1. HITL确认机制
**时间**: Phase 4  
**决策**: 高风险操作人工确认

**实现**:
- HITLService: Redis状态管理
- 5分钟TTL超时保护
- 支持并发多个确认请求

**覆盖场景**:
- 文件删除
- 危险命令执行
- 敏感操作

---

### 2. 数据库RLS
**决策**: Row-Level Security行级安全

**实现**: PostgreSQL RLS策略 (设计中)

**理由**:
- 多租户数据隔离
- 数据库层面权限控制
- 防止越权访问

---

## 📦 部署架构 (规划中)

### 容器化
**选择**: Docker + Docker Compose

**服务拆分**:
- backend: FastAPI应用
- frontend: Nginx静态文件
- postgres: 数据库
- redis: 缓存

---

### 生产环境 (待实施)
**目标**: Kubernetes + CI/CD

**监控**: Prometheus + Grafana  
**日志**: ELK Stack  
**追踪**: Jaeger (OpenTelemetry)

---

## 🎓 经验教训

### 1. Alembic迁移管理
**教训**: 必须在env.py中导入所有模型

**解决**: 显式导入User, Workspace, Session等所有模型

---

### 2. Redis异步客户端
**教训**: 需要使用`redis.asyncio`而非同步版本

**解决**: `from redis.asyncio import Redis`

---

### 3. Vue组件自动刷新
**教训**: setInterval需要在组件卸载时清理

**解决**: 使用onUnmounted hook

---

---

## 🎭 产品理念升级

### Vibe Workflow (氛围感工作流)
**时间**: 2026-01-14  
**决策**: 将"Vibe Workflow"沉淀为产品核心理念

**定义**:  
以情绪价值和认知流(Flow)为核心的设计范式。工具不仅解决功能需求，更要创造顺滑、优雅且充满激励感的使用环境。

**三大支柱**:
1. **直觉重于指令** - 最好的操作是不需要思考的
2. **情感共鸣与审美张力** - 美学本身就是生产力
3. **极低摩擦力的流** - 消除Context Switching

**价值对比**:
- 目标: 享受过程 > 完成任务
- 反馈: 情感激励与节奏感 > 二元反馈
- 用户状态: 主动沉浸 > 被动疲劳
- 产品门槛: 直觉探索 > 学习手册

**宣言**:
> "我们不只是在制造锤子，我们是在构建一个激发灵感的工坊。我们相信，当工具的'Vibe'对了，创造力就会自然涌现。"

**影响**:
- 指导所有UI/UX设计决策
- 强调动效、反馈、流畅度
- 区别于传统工具型产品

**实现要点**:
- SSE流式输出让对话感觉流畅
- Chain-of-Thought可视化提供透明感
- Working Memory面板让用户看到Agent的思考
- HITL确认带来控制感和安全感

---

## 🔄 更新日志

- 2026-01-14 08:00: 初始化findings.md，回顾Phase 1-4关键决策
- 2026-01-14 16:20: 记录Vibe Workflow产品理念升级
- (待续...)

---

**下次更新时机**: 
- 做出新的技术决策时
- 执行2-Action Rule时（每2次重大搜索/调研后）
