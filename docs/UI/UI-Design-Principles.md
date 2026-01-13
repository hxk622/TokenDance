# TokenDance UI Design Principles
**从 "被动观察" 到 "主动指挥" - 下一代 AI Agent 平台的交互哲学**

## 一、设计目标：超越 Manus 的三个维度

### 1. 透明度 (Transparency)
**Manus**: 看到 Agent 正在做什么 (Observability)  
**TokenDance**: 理解 Agent **为什么**要这么做 (Explainability)

**实现方式**：
- **Logits Heatmap（决策热力图）**：可视化每个决策点的概率分布
  ```
  [Step 3: 如何获取数据]
  🔥🔥🔥🔥🔥🔥🔥 搜索Google (70%)  ← AI 选择
  🔥🔥 调用API (20%)
  🔥 跳过 (10%)
  ```
- **执行流时间轴**：用户可以拖动时间轴，回放任意时刻的 Agent 状态
- **关键词高亮**：在 Canvas 中高亮显示影响决策的关键信息

### 2. 操作性 (Controllability)
**Manus**: 任务结束后修改结果  
**TokenDance**: 任务进行中**动态干预**

**实现方式**：
- **人机接力（In-line Human Intervention）**：
  - Agent 遇到验证码/登录页时，UI 显示 "🤚 接管" 按钮
  - 用户接管后，Canvas 变为可编辑状态
  - 用户完成后点击 "✅ 继续"，Agent 从中断点恢复（基于 KV-Cache）
  
- **实时 Logits 调整**：
  - 专业用户可以在执行中调整 FSM 状态机参数
  - 例如：屏蔽高风险操作的 token，强制 Agent 选择保守方案

### 3. 沉淀感 (Persistence)
**Manus**: 收集文件和数据  
**TokenDance**: 收集**"智力模块"**

**实现方式**：
- **活的资产（Contextual Hot-link）**：
  - 每个 Artifact 绑定 **KV-Cache Anchor**（生成时的思维快照）
  - 用户点击侧边栏的任意产物，可以：
    - 💡 查看生成时的思考路径
    - 🔄 从这里继续对话（自动加载 Context）
    - 📌 保存为团队技能模板（Expert Agent Snapshot）

---

## 二、核心交互模式

### 2.1 Canvas-based Layout（多窗格协同）
**布局结构**：
```
┌─────────────────────────────────────────────────────┐
│  左侧：对话框 (40%)      │  右侧：Canvas 画布 (60%)  │
│  ─ 用户输入              │  ─ Agent 实时操作预览     │
│  ─ Agent 回复            │  ─ 浏览器/代码编辑器/终端  │
│  ─ 任务状态              │  ─ 执行流可视化           │
├─────────────────────────────────────────────────────┤
│  底部：Artifact 侧边栏（可折叠）                      │
│  📄 竞品分析.md  📊 数据表.csv  💾 KV-Cache Snapshot │
└─────────────────────────────────────────────────────┘
```

**交互原则**：
- **同步滚动**：对话框中的每条消息，Canvas 同步显示对应的执行画面
- **焦点高亮**：当前执行步骤在 Canvas 中高亮显示（类似调试器的断点）
- **Context 提示**：鼠标悬停在 Artifact 上，显示 "生成于第 X 步"

### 2.2 Step-by-step Branching（思维链路的动态树）
**Manus 的问题**：线性展示，失败后只能重试  
**TokenDance 的改进**：平行宇宙可视化

**UI 呈现**（类似 Git 分支图）：
```
[User Input: 分析竞品]
    ├─ 方案A: 深度爬取10个网站 (耗时30min, 精确度95%)
    ├─ 方案B: 快速扫描50个标题 (耗时5min, 精确度70%)  ← 用户选择
    └─ 方案C: 调用 Perplexity API (耗时2min, 依赖外部)
```

**交互流程**：
1. Agent 制定计划时，生成 2-3 个方案（通过不同 temperature/Logits Masking）
2. UI 显示方案对比（耗时、精确度、成本）
3. 用户选择后，Agent 执行对应路径
4. 如果某路径失败，自动切换到备选方案

**技术实现**：
- 后端：多方案生成器（基于不同推理策略）
- 前端：方案对比组件（展示 trade-off）

### 2.3 Live Artifacts（中间产物的实时沉淀）
**Artifact 类型**：
- 📄 文档（Markdown/PDF）
- 📊 数据表（CSV/JSON）
- 💻 代码片段（Python/TypeScript）
- 🖼️ 截图（Agent 操作的页面快照）
- 💾 **KV-Cache Snapshot**（思维快照，可复用）

**Artifact 操作**：
```typescript
interface Artifact {
  id: string;
  type: "document" | "code" | "data" | "kv_snapshot";
  content: string;
  metadata: {
    created_at: timestamp;
    parent_step: string;      // 来自哪一步
    kv_anchor: string;        // KV-Cache 锚点 ID
    tokens_used: number;      // 消耗的 token 数
  };
}
```

**右键菜单**：
- 📥 下载
- 🔄 从此处继续对话
- 📌 保存为团队技能
- 🗑️ 删除

---

## 三、杀手级功能清单

### 3.1 Agent 执行流的"录像回放" 🎬
**灵感来源**：Chrome DevTools Performance Recorder

**功能描述**：
- 底部时间轴（类似视频播放器）
- 用户可以拖动到任意时刻，查看：
  - Canvas 状态（当时 Agent 在操作什么）
  - 思考路径（Logits 分布）
  - KV-Cache 变化

**价值**：
- 调试复杂任务时不需要重跑
- 精确定位 "AI 是从哪一步开始走偏的"

### 3.2 Logits Heatmap（决策热力图） 🔥
**功能描述**：
- 在每个决策点，显示 AI 考虑的所有选项及其概率
- 用户可以手动切换到低概率方案（例如 AI 选了 70% 的方案，但用户觉得 20% 的方案更好）

**UI 示例**：
```
[Step 5: 决策 - 如何处理错误]
🔥🔥🔥🔥🔥🔥 重试 (65%)  ← AI 选择
🔥🔥🔥 跳过 (25%)
🔥 终止任务 (10%)

💡 用户操作：点击 "跳过"，手动覆盖 AI 决策
```

### 3.3 Token 预算的可视化仪表盘 💰
**功能描述**：
- 实时显示当前任务的 Token 消耗
- 预估完成所需 Token 和成本
- 支持手动切换模型（GPT-4 ↔ Llama）

**UI 示例**：
```
[当前任务消耗]
GPT-4: ████████░░ 80% (即将自动降级到 Llama)
当月配额: ████████████░░░░ 65%

[预估完成消耗]
继续使用 GPT-4: 预计 $12.5，完成时间 10min
切换到 Llama-8B: 预计 $0.3，完成时间 15min

[操作] 🔄 立即切换到 Llama  |  💎 升级配额
```

### 3.4 人机接管点（Break-point Interaction） 🤚
**触发场景**：
- Agent 遇到验证码
- Agent 需要扫码登录
- Agent 不确定是否继续（置信度 < 50%）

**交互流程**：
```
1. Agent 检测到阻塞 → 发送 "PAUSED" 状态
2. Canvas 显示 "🤚 需要你的帮助" 按钮
3. 用户点击后，Canvas 变为可编辑（鼠标/键盘直接操作）
4. 用户完成后点击 "✅ 继续"
5. Agent 从中断点恢复（基于保存的 KV-Cache）
```

**技术挑战**：
- 如何保存 Canvas 的交互状态（VNC/RDP 协议？）
- 如何让用户操作无缝传递给 Agent

---

## 四、设计哲学对比

| 维度 | Manus | TokenDance |
|------|-------|------------|
| **用户角色** | 观众 | 导演 |
| **交互方式** | 只能看 | 可以接管、分支、回放 |
| **信任来源** | "AI 没出错" | "AI 出错了我能救" |
| **沉淀物** | 文件 | 智力快照 + 可复用技能 |
| **透明度** | 看到 Agent 在做什么 | 理解 Agent 为什么这么做 |
| **操作性** | 任务结束后修改 | 任务进行中干预 |
| **协作模式** | 个人工具 | 团队平台（Workspace 共享） |

---

## 五、实现优先级

### Phase 2A: Canvas 实时交互（MVP）
**目标**：打通 "用户发起任务 → Agent 执行 → Canvas 实时显示 → 生成 Artifact"

**核心功能**：
1. ✅ WebSocket 实时推送 Agent 状态
2. ✅ Canvas 画布显示 Agent 操作（简化版：文本模拟）
3. ✅ Artifact 侧边栏实时更新
4. ✅ 人机接管点（手动暂停/恢复）

**技术栈**：
- 后端：FastAPI WebSocket + 简化版 Agent 状态机
- 前端：Vue 3 + Canvas 组件（暂不集成真实浏览器，先用文本模拟）

### Phase 2B: 可解释性增强
**核心功能**：
1. Logits Heatmap 组件
2. 执行流时间轴（录像回放）
3. 决策点的 "为什么" 解释

### Phase 2C: 协作与沉淀
**核心功能**：
1. KV-Cache Snapshot 绑定到 Artifact
2. Expert Agent 技能导出/导入
3. Workspace 团队共享
4. Token 预算治理仪表盘

---

## 六、关键技术决策

### 6.1 Canvas 如何渲染真实浏览器？
**方案对比**：

| 方案 | 优点 | 缺点 | 采用 |
|------|------|------|------|
| **VNC/RDP 截图流** | 真实浏览器画面 | 延迟高，带宽消耗大 | ❌ |
| **Playwright 截图 + 增量传输** | 清晰，可交互 | 需要复杂的状态同步 | ✅ Phase 2B |
| **HTML/CSS 重放** | 轻量，可编辑 | 无法完美还原 JS 交互 | ✅ Phase 2A（MVP）|

**Phase 2A 采用方案**：HTML 文本模拟
```typescript
// Agent 推送的 Canvas 状态
{
  "type": "browser",
  "content": {
    "url": "https://google.com",
    "html": "<simplified HTML>",
    "highlights": ["搜索框", "第一条结果"]
  }
}
```

### 6.2 KV-Cache Snapshot 如何存储？
**方案**：
- **格式**：Protocol Buffers（二进制，高效压缩）
- **存储**：S3/MinIO（对象存储）
- **索引**：PostgreSQL（metadata：artifact_id → kv_snapshot_url）

**存储结构**：
```python
class KVCacheSnapshot:
    id: str
    workspace_id: str
    created_at: datetime
    size_bytes: int
    s3_url: str  # s3://tokendance/kv-cache/{snapshot_id}.pb
    metadata: {
        "step_id": "step_5",
        "model": "claude-3-5-sonnet",
        "context_length": 12000
    }
```

---

## 七、用户故事（User Stories）

### Story 1: 数据分析师使用 TokenDance
**场景**：分析竞品的定价策略

1. **发起任务**：在对话框输入 "帮我分析 5 个竞品的定价"
2. **观察执行**：
   - Canvas 显示 Agent 正在打开竞品网站
   - 侧边栏实时出现提取的价格表
3. **人工干预**：Agent 访问某个网站需要登录，用户点击 "🤚 接管"，手动登录
4. **继续执行**：用户点击 "✅ 继续"，Agent 恢复执行
5. **获取结果**：生成 Markdown 报告 + CSV 数据表
6. **保存技能**：用户将此次任务保存为 "竞品定价分析模板"，团队成员可一键复用

### Story 2: 开发者调试 AI 代码
**场景**：AI 生成的 Python 代码有 Bug

1. **回放执行**：拖动时间轴到 "生成代码" 的步骤
2. **查看决策**：Logits Heatmap 显示 AI 当时考虑了 3 种实现方式
3. **切换方案**：手动选择概率较低的方案 B（更保守的实现）
4. **重新执行**：Agent 基于新方案重新生成代码
5. **保存快照**：将成功的方案 B 保存为 KV-Cache Snapshot，下次直接加载

---

## 八、设计原则总结

### 核心原则：**"可控的透明度"**
1. **永远让用户知道 AI 在做什么**（Transparency）
2. **永远让用户能够干预 AI 的决策**（Controllability）
3. **永远让成功的经验可以复用**（Persistence）

### 交互信条：
- ❌ 不要让用户 "等着 AI 完成"
- ✅ 让用户 "和 AI 一起完成"

- ❌ 不要让失败的任务白白浪费
- ✅ 让失败的尝试变成可调试的录像

- ❌ 不要让专家经验只存在个人脑海
- ✅ 让专家经验沉淀为团队资产

---

**结论**：TokenDance 不是 "更快的 Manus"，而是 **"可指挥的智能工作台"**。
