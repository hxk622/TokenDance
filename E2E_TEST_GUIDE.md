# E2E 测试指南

## 当前状态

✅ **Phase 1-3 已完成** - 代码已推送到 GitHub
- Phase 1: Agent Engine (100%)
- Phase 2: API + SSE Streaming (100%)
- Phase 3: Chat UI (100%)

✅ **前端 TypeScript 编译通过**
- 所有组件类型正确
- 无编译错误

## 测试环境要求

### 后端要求
- Python 3.11+
- Poetry (依赖管理)
- Anthropic API Key (必需)

### 前端要求
- Node.js 16+
- npm/pnpm

## 快速开始

### 1. 安装后端依赖

如果没有安装 Poetry:
```bash
# macOS
brew install poetry

# 或使用 pip
pip3 install poetry
```

安装依赖:
```bash
cd backend
poetry install
```

### 2. 配置环境变量

编辑 `backend/.env`:
```bash
# 必需
ANTHROPIC_API_KEY=sk-ant-xxxxx  # 你的 API Key

# 可选（使用默认值）
ENVIRONMENT=development
DEBUG=true
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. 启动后端服务

```bash
cd backend
poetry run python -m app.main
```

服务将在 `http://localhost:8000` 启动

访问 API 文档: http://localhost:8000/api/v1/docs

### 4. 启动前端服务

```bash
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 启动

## 测试场景

### 场景 1: 后端 API 测试

```bash
cd backend
poetry run pytest test_api_integration.py -v
```

**预期结果**: 11 个测试全部通过

### 场景 2: Agent Engine 单元测试

```bash
cd backend
poetry run pytest test_agent_engine_complete.py -v
```

**预期结果**: 7 个测试全部通过

### 场景 3: 前端 TypeScript 编译

```bash
cd frontend
npx vue-tsc --noEmit
```

**预期结果**: 无错误（已验证 ✅）

### 场景 4: 完整 E2E 流程（手动）

1. 启动后端和前端服务
2. 打开浏览器访问 http://localhost:5173
3. 在输入框输入消息，例如: "Python 中如何读取文件？"
4. 观察：
   - ✅ 用户消息立即显示
   - ✅ "Agent 思考中..." 提示出现
   - ✅ 实时推理文本更新
   - ✅ 工具调用卡片显示（如果触发）
   - ✅ 最终答案以 Markdown 格式渲染
   - ✅ 代码块语法高亮

## 已知限制

### 当前 MVP 范围
1. **Session 管理**: 前端硬编码 sessionId，需要实现完整的 Session CRUD
2. **数据库**: 当前使用内存存储，未连接 PostgreSQL
3. **Redis**: 未启用缓存层
4. **Working Memory**: UI 组件已创建但未集成到 ChatView
5. **用户认证**: 未实现

### 测试依赖
- 后端测试需要 Anthropic API Key（会消耗 tokens）
- 部分测试可能需要外网访问

## 下一步计划

### Phase 4: Working Memory 可视化
- [ ] 创建 WorkingMemory 组件（显示 3 文件）
- [ ] 集成到 ChatView 侧边栏
- [ ] 实时刷新机制

### Phase 5: Session 管理
- [ ] Session 列表 UI
- [ ] 创建/删除/选择 Session
- [ ] Session 持久化（PostgreSQL）

### Phase 6: Deep Research Skill
- [ ] 实现 Search 工具
- [ ] 实现 Read URL 工具
- [ ] Multi-step 研究流程

### Phase 7: PPT Generation
- [ ] Outline 生成
- [ ] Slide 内容填充
- [ ] 导出 PPTX

## 故障排查

### 问题 1: 后端无法启动
**症状**: `ModuleNotFoundError: No module named 'fastapi'`
**解决**: 确认 Poetry 依赖已安装
```bash
cd backend
poetry install
```

### 问题 2: 前端编译错误
**症状**: TypeScript 类型错误
**解决**: 已修复（commit 5920053），确保代码是最新的
```bash
git pull origin master
```

### 问题 3: CORS 错误
**症状**: 浏览器控制台显示 CORS policy 错误
**解决**: 检查 `backend/.env` 中的 `BACKEND_CORS_ORIGINS`
```bash
BACKEND_CORS_ORIGINS=http://localhost:5173
```

### 问题 4: API Key 错误
**症状**: `401 Unauthorized` from Anthropic
**解决**: 
1. 检查 `backend/.env` 中的 `ANTHROPIC_API_KEY`
2. 确认 API Key 有效且有余额

## 性能基准（预估）

| 指标 | 目标值 | 备注 |
|------|--------|------|
| 首字延迟 | <500ms | SSE 流式输出 |
| Token 效率 | 70% 节省 | vs 传统 Agent |
| Context 利用率 | >90% | KV-Cache 命中 |
| 成功率 | >85% | 复杂任务 |

## 贡献者

- **后端**: Agent Engine + API Layer
- **前端**: Chat UI + SSE Integration
- **文档**: 完整技术文档

**Co-Authored-By**: Warp AI Agent <agent@warp.dev>

---

最后更新: 2026-01-14
提交: `5920053`
