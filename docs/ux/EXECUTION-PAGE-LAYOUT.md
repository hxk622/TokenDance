# TokenDance 三栏布局设计规范 (Three-Column Layout)

**文档版本**: v1.0.0  
**更新日期**: 2026-01-14  
**设计理念**: Vibe-Agentic Workflow - 战略、战术、成果的视觉解耦

---

## 🧭 核心布局原则

### 1. 左右区域职责划分（Zone Responsibility）

**左侧执行区 = AI 执行过程**
- WorkflowGraph: 执行流程的宏观视图
- StreamingInfo: Agent 的思考、工具调用、浏览器操作等执行细节
- **浏览器截图应内联在 StreamingInfo 中**，作为执行上下文的一部分
- 用户在此观察「AI 正在做什么」

**右侧预览区 = 产物预览与编辑 (Artifact Preview & Edit)**
- 仅展示**最终产物**：报告、PPT、代码 Diff、文件等
- 用户可在此**编辑、导出、分享**产出物
- **禁止**在此区域展示执行过程相关内容（如浏览器 PiP、日志等）

```
左侧：执行过程 (Execution)    │    右侧：产物预览 (Artifacts)
──────────────────────────────┼───────────────────────────────
✅ WorkflowGraph              │ ✅ 研究报告
✅ Agent 思考日志             │ ✅ PPT 预览
✅ 工具调用详情               │ ✅ 代码 Diff
✅ 浏览器截图（内联）         │ ✅ 文件列表
✅ Coworker 操作记录          │ ✅ 图表/可视化
──────────────────────────────┼───────────────────────────────
❌ 产物预览                   │ ❌ 执行日志
❌ 编辑功能                   │ ❌ 浏览器 PiP
                              │ ❌ Agent 思考过程
```

### 2. Flatten 原则（内容平铺）

**核心理念**：用户很懒，不会点击 Tab 或展开折叠

**规则**：
- ❌ **禁止隐藏关键内容在 Tab 中** — 用户不会主动切换
- ❌ **禁止使用悬浮 PiP 窗口** — 遮挡内容且需要用户操作
- ✅ **所有执行信息平铺在 StreamingInfo 时间线中**
- ✅ **浏览器截图作为日志卡片内联显示**
- ✅ **多个 Artifact 可以垂直堆叠而非 Tab 切换**（如果空间允许）

**示例 - 浏览器操作内联展示**：
```
[10:21:03] 🌐 正在访问 google.com/search?q=AI+Agent
┌─────────────────────────────┐
│  [浏览器截图实时更新]        │
│  内联在日志流中              │
└─────────────────────────────┘
[10:21:05] ✓ 找到 5 条相关结果
[10:21:06] 🔗 点击第一条链接...
```

---

## 📐 总体布局定义

### 页面结构

```
执行页面 (Execution Page) - Vibe-Agentic Workflow
┌─────────────────────────────────────────────────────────────┐
│                  Header（任务标题 + 状态）h=64px            │
├───────────────────────────┬─────────────────────────────────┤
│  左侧执行区（可调比例）   │   右侧预览区（可调比例）        │
│                           │                                 │
├───────────────────────────┤   ┌─────────────────────────┐   │
│ [上] Workflow Graph       │   │ [Tabs] 产出物切换      │   │
│  - Meego式DAG色球图       │   │  Report | PPT | Files  │   │
│  - 能量连线 + 状态脉冲    │   ├─────────────────────────┤   │
│  - 支持拖拽重组逻辑       │   │                         │   │
│  高度：可调（默认40%）    │   │   主预览区域            │   │
├─────[可拖拽分隔条]────────┤   │   - 浏览器渲染          │   │
│ [下] Streaming Info       │   │   - 代码高亮            │   │
│  - Agent思考过程          │   │   - PPT实时预览         │   │
│  - Tool Calling详情       │   │   - Coworker Diff       │   │
│  - Coworker文件操作树     │   │                         │   │
│  - 可折叠/聚焦模式        │   │                         │   │
│  高度：可调（默认60%）    │   └─────────────────────────┘   │
└───────────────────────────┴─────────────────────────────────┘
         ↑ 可拖拽分隔条                    ↑ 可拖拽分隔条
```

---

## 🎨 尺寸规范

### 1. 视口与容器

| 元素 | 尺寸 | 说明 |
|------|------|------|
| 最小视口宽度 | 1280px | 低于此宽度显示横向滚动条 |
| 推荐视口宽度 | 1440px+ | 最佳体验宽度 |
| Header 高度 | 64px | 固定高度，包含任务标题、状态指示器 |
| 主内容区高度 | calc(100vh - 64px) | 自适应视口高度 |
| 内边距 | 16px | 所有区域统一内边距 |

### 2. 左右比例（水平分隔）

**任务类型自适应比例**：

```typescript
const layoutRatio = {
  'deep-research': { left: 35, right: 65 },    // 预览主导
  'ppt-generation': { left: 30, right: 70 },   // 预览主导
  'code-refactor': { left: 60, right: 40 },    // 执行主导（Coworker）
  'file-operations': { left: 65, right: 35 },  // 执行主导（Coworker）
  'default': { left: 45, right: 55 },          // 默认均衡
}
```

**用户可拖拽调整**：
- 最小左侧宽度：300px（防止Workflow Graph过于拥挤）
- 最小右侧宽度：400px（保证预览区可用性）
- 拖拽柄宽度：8px，可交互区域±4px（总计16px热区）

### 3. 上下比例（垂直分隔 - 左侧执行区内部）

**默认布局**：
- Workflow Graph（上）：40%
- Streaming Info（下）：60%

**动态调整规则**：

```typescript
interface VerticalLayoutRule {
  condition: string;
  ratio: { top: number; bottom: number };
}

const verticalRules: VerticalLayoutRule[] = [
  // DAG节点过多时，扩大上部空间
  { condition: 'dagNodes > 15', ratio: { top: 50, bottom: 50 } },
  
  // 聚焦模式：突出下部日志
  { condition: 'focusMode === true', ratio: { top: 20, bottom: 80 } },
  
  // 折叠模式：只显示当前节点mini-graph
  { condition: 'collapsed === true', ratio: { top: 15, bottom: 85 } },
]
```

**用户可拖拽调整**：
- 最小上部高度：120px（至少显示3个色球节点）
- 最小下部高度：200px（至少显示10行日志）
- 拖拽柄高度：8px，可交互区域±4px

---

## 🎨 色彩系统

### 1. 色球状态色（Workflow Graph）

```css
/* 青色脉冲 - Agent正在计算 */
--color-node-active: #00D9FF;
--color-node-active-glow: rgba(0, 217, 255, 0.5);

/* 绿色锁定 - 节点已完成 */
--color-node-success: #00FF88;
--color-node-success-glow: rgba(0, 255, 136, 0.3);

/* 琥珀暂停 - 等待人工介入 */
--color-node-pending: #FFB800;
--color-node-pending-glow: rgba(255, 184, 0, 0.4);

/* 红色冲突 - 执行失败 */
--color-node-error: #FF3B30;
--color-node-error-glow: rgba(255, 59, 48, 0.5);

/* 灰色待执行 - 预演节点 */
--color-node-inactive: #8E8E93;
--color-node-inactive-glow: rgba(142, 142, 147, 0.2);
```

### 2. 能量连线色

```css
/* Context传递连线 */
--color-edge-default: rgba(255, 255, 255, 0.3);
--color-edge-active: rgba(0, 217, 255, 0.8);   /* 数据流动中 */
--color-edge-error: rgba(255, 59, 48, 0.6);    /* 逻辑冲突 */
```

### 3. 背景与分隔

```css
/* 主背景 - 深色毛玻璃 */
--bg-primary: rgba(18, 18, 18, 0.95);
--bg-secondary: rgba(28, 28, 30, 0.9);

/* 分隔线 */
--divider-color: rgba(255, 255, 255, 0.1);
--divider-hover: rgba(0, 217, 255, 0.5);  /* 拖拽柄hover态 */

/* 毛玻璃效果 */
backdrop-filter: blur(20px) saturate(180%);
```

---

## ⚡ 动画标准

### 1. 过渡动画

```css
/* 布局变化 - 拖拽分隔条 */
--transition-layout: all 200ms cubic-bezier(0.4, 0, 0.2, 1);

/* 色球状态切换 */
--transition-node: all 300ms cubic-bezier(0.34, 1.56, 0.64, 1);  /* 轻微回弹 */

/* Tab切换 */
--transition-tab: opacity 150ms ease-in-out;

/* Hover微交互 */
--transition-hover: all 120ms ease-out;
```

### 2. 色球呼吸动画

```css
@keyframes pulse-breath {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
    box-shadow: 0 0 20px var(--color-node-active-glow);
  }
  50% {
    transform: scale(1.1);
    opacity: 0.9;
    box-shadow: 0 0 40px var(--color-node-active-glow);
  }
}

.node-active {
  animation: pulse-breath 1.5s ease-in-out infinite;
}
```

### 3. 能量连线流光效果

```css
@keyframes flow-energy {
  0% {
    stroke-dashoffset: 100;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

.edge-active {
  stroke-dasharray: 10 5;
  animation: flow-energy 1s linear infinite;
}
```

### 4. 滚动联动动画

```typescript
// 智能滚动策略
interface ScrollSyncOptions {
  mode: 'instant' | 'smooth' | 'manual';  
  duration: number;  // smooth模式持续时间（默认300ms）
  lockWhileReading: boolean;  // 用户阅读时锁定
  highlightOnly: boolean;  // 只高亮不滚动
}

const scrollConfig: ScrollSyncOptions = {
  mode: 'smooth',
  duration: 300,
  lockWhileReading: true,
  highlightOnly: false,
}
```

---

## 🖱️ 交互规范

### 1. 拖拽分隔条 (Resizable Divider)

**视觉状态**：
```css
/* 默认态 */
.divider {
  width: 8px;  /* 垂直分隔 */
  height: 8px; /* 水平分隔 */
  background: var(--divider-color);
  cursor: col-resize; /* 或 row-resize */
}

/* Hover态 */
.divider:hover {
  background: var(--divider-hover);
  transition: var(--transition-hover);
}

/* 拖拽中 */
.divider.dragging {
  background: var(--color-node-active);
  z-index: 1000;
}
```

**交互逻辑**：
1. 双击分隔条 → 恢复默认比例
2. 拖拽时显示实时比例提示（如"45% / 55%"）
3. 拖拽结束后保存到localStorage

### 2. Workflow Graph 交互

**色球（Node）**：
```typescript
interface NodeInteraction {
  // 单击：聚焦该节点，下部日志滚动到对应位置
  onClick: (nodeId: string) => void;
  
  // 双击：进入聚焦模式（上20% / 下80%）
  onDoubleClick: (nodeId: string) => void;
  
  // Hover：显示节点详情Tooltip（执行时长、状态、输出摘要）
  onHover: (nodeId: string) => void;
  
  // 右键：打开上下文菜单（重新执行、查看日志、复制输出）
  onContextMenu: (nodeId: string) => void;
}
```

**连线（Edge）**：
```typescript
interface EdgeInteraction {
  // 单击：显示Logits解码弹窗
  onClick: (edgeId: string) => void;
  
  // 拖拽：重新连接节点（重组逻辑）
  onDrag: (fromNodeId: string, toNodeId: string) => void;
  
  // 双击：断开连线（阻止数据传递）
  onDoubleClick: (edgeId: string) => void;
}
```

### 3. Streaming Info 区域

**Scroll-Sync 逻辑**：
```typescript
interface ScrollSyncBehavior {
  // 首次点击节点 → smooth滚动
  firstClick: 'smooth-scroll';
  
  // 5秒内连续点击 → 只高亮不滚动
  rapidClick: 'highlight-only';
  
  // 用户手动滚动时 → 暂停Scroll-Sync
  userScroll: 'pause-sync';
  
  // 用户点击"固定视图"按钮 → 完全锁定
  locked: 'no-sync';
}
```

**Context-Focus（上下文聚焦）**：
```typescript
// 用户点击"聚焦模式"按钮
function enableFocusMode(nodeId: string) {
  // 1. 上部Workflow Graph只显示当前节点的mini-graph
  workflowGraph.showMiniGraph(nodeId);
  
  // 2. 下部日志过滤，只显示该节点的详细推理流
  streamingInfo.filterByNode(nodeId);
  
  // 3. 调整布局比例为 20% / 80%
  layout.setVerticalRatio(20, 80);
}
```

### 4. 右侧预览区 (Artifact Tabs)

**Tab切换逻辑**：
```typescript
interface ArtifactTab {
  id: string;
  type: 'report' | 'ppt' | 'code' | 'browser' | 'file-diff';
  title: string;
  icon: string;
  isPinned: boolean;  // 是否固定
  autoFocus: boolean; // 是否自动聚焦
}

// 自动焦点切换规则
const autoFocusRules = {
  'manus-report-generated': { focusTab: 'report' },
  'coworker-file-modified': { focusTab: 'file-diff' },
  'ppt-slide-created': { focusTab: 'ppt' },
}
```

**多窗口预览**：
- 支持Pin多个Tab（如同时查看Report和PPT）
- 拖拽Tab标签可调整顺序
- 右键Tab可关闭或移动到新窗口

---

## 🔄 响应式策略

### 断点定义

```css
/* Extra Large Desktop */
@media (min-width: 1920px) {
  /* 左侧执行区可扩展到800px */
}

/* Large Desktop (标准) */
@media (min-width: 1440px) and (max-width: 1919px) {
  /* 默认布局 */
}

/* Medium Desktop (临界点) */
@media (min-width: 1280px) and (max-width: 1439px) {
  /* 减少内边距到12px，最小化Tabs高度 */
}

/* Small Desktop (降级模式) */
@media (max-width: 1279px) {
  /* 三栏变两栏：隐藏Workflow Graph，只保留Streaming Info + Preview */
  /* 用户可通过按钮切换显示Workflow Graph（全屏Modal） */
}
```

### 移动端适配（未来Phase）

- 三栏完全折叠为单栏
- 通过底部Tab Bar切换视图（Strategy / Execution / Preview）
- Workflow Graph以卡片式展示，而非Canvas

---

## 🧩 组件定义

### 1. 布局组件层级

```typescript
<ExecutionPage>
  <Header />
  
  <MainContent>
    {/* 左侧执行区 */}
    <LeftPanel width={leftWidth}>
      <WorkflowGraph height={topHeight} />
      <VerticalDivider onDrag={handleVerticalDrag} />
      <StreamingInfo height={bottomHeight} />
    </LeftPanel>
    
    <HorizontalDivider onDrag={handleHorizontalDrag} />
    
    {/* 右侧预览区 */}
    <RightPanel width={rightWidth}>
      <ArtifactTabs tabs={artifacts} />
      <PreviewArea content={currentArtifact} />
    </RightPanel>
  </MainContent>
</ExecutionPage>
```

### 2. WorkflowGraph 组件

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import * as d3 from 'd3'  // 或使用vis-network

interface Node {
  id: string
  type: 'manus' | 'coworker'
  status: 'active' | 'success' | 'pending' | 'error' | 'inactive'
  label: string
  metadata: {
    startTime: number
    duration: number
    output: string
  }
}

interface Edge {
  id: string
  from: string
  to: string
  type: 'context' | 'result'
  logits?: string  // Logits解码结果
}

const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])

// Canvas渲染逻辑
function renderGraph() {
  // 使用D3.js或vis-network绘制DAG
}
</script>
```

### 3. StreamingInfo 组件

```vue
<script setup lang="ts">
interface LogEntry {
  id: string
  nodeId: string
  timestamp: number
  type: 'thinking' | 'tool-call' | 'result' | 'error'
  content: string
}

// Coworker专属：文件操作树
interface FileOperation {
  path: string
  action: 'read' | 'modified' | 'created' | 'deleted'
  diff?: string  // Git-style diff
}
</script>

<template>
  <div class="streaming-info">
    <!-- 模式切换 -->
    <div class="mode-tabs">
      <button :class="{ active: mode === 'all' }">全部</button>
      <button :class="{ active: mode === 'coworker' }">Coworker</button>
    </div>
    
    <!-- Coworker模式：文件树 + Diff -->
    <div v-if="mode === 'coworker'" class="coworker-view">
      <FileTree :operations="fileOperations" />
      <LiveDiff :diff="currentDiff" />
    </div>
    
    <!-- 标准模式：日志流 -->
    <div v-else class="log-stream">
      <LogEntry 
        v-for="log in logs" 
        :key="log.id"
        :entry="log"
        @click="handleLogClick"
      />
    </div>
  </div>
</template>
```

### 4. ArtifactTabs 组件

```vue
<script setup lang="ts">
const tabs = ref<ArtifactTab[]>([
  { id: '1', type: 'report', title: '研究报告', icon: '📄', isPinned: false },
  { id: '2', type: 'ppt', title: 'PPT', icon: '📊', isPinned: false },
])

function handleTabSwitch(tabId: string) {
  // 切换Tab，加载对应预览内容
}

function handleTabPin(tabId: string) {
  // 固定Tab，防止被自动切换覆盖
}
</script>

<template>
  <div class="artifact-tabs">
    <div 
      v-for="tab in tabs" 
      :key="tab.id"
      :class="['tab', { active: currentTab === tab.id, pinned: tab.isPinned }]"
      @click="handleTabSwitch(tab.id)"
      @contextmenu.prevent="handleTabPin(tab.id)"
    >
      <span class="icon">{{ tab.icon }}</span>
      <span class="title">{{ tab.title }}</span>
      <button v-if="tab.isPinned" class="pin-icon">📌</button>
    </div>
  </div>
</template>
```

---

## 🎯 实施路线图

### Phase 1: 核心框架（Week 1-2）

**目标**：完成三栏基础布局 + Workflow Graph骨架

**任务清单**：
- [ ] 实现`<ExecutionPage>`布局容器
- [ ] 实现水平/垂直可拖拽分隔条（`<ResizableDivider>`）
- [ ] 集成Canvas库（选择D3.js或vis-network）
- [ ] 实现Workflow Graph的基础渲染（色球 + 连线）
- [ ] 实现Scroll-Sync基础联动逻辑
- [ ] 完成布局比例的localStorage持久化

**验收标准**：
- ✅ 用户可拖拽调整左右比例，拖拽后刷新页面比例保持
- ✅ Workflow Graph可显示至少5个色球节点和连线
- ✅ 点击色球节点时，下部日志区域滚动到对应位置

---

### Phase 2: 交互增强（Week 3-4）

**目标**：完善Artifact Tabs + Coworker专属视图

**任务清单**：
- [ ] 实现`<ArtifactTabs>`组件（支持切换、Pin、拖拽排序）
- [ ] 实现Coworker File Tree视图（类似VS Code Source Control）
- [ ] 实现Live Diff组件（Monaco Editor Diff模式）
- [ ] 实现聚焦模式（点击节点后上20%/下80%）
- [ ] 实现折叠模式（只显示mini-graph）
- [ ] 添加"固定视图"按钮（锁定Scroll-Sync）

**验收标准**：
- ✅ 右侧可通过Tab切换Report、PPT、File Diff等视图
- ✅ Coworker修改文件时，自动切换到File Diff Tab并高亮变更
- ✅ 用户可进入聚焦模式，下部日志只显示当前节点内容

---

### Phase 3: Vibe体验打磨（Week 5-6）

**目标**：实现毛玻璃特效 + 色球动画 + 智能滚动

**任务清单**：
- [ ] 添加毛玻璃背景（backdrop-filter: blur(20px)）
- [ ] 实现色球呼吸动画（pulse-breath 1.5s周期）
- [ ] 实现能量连线流光效果（stroke-dasharray + animation）
- [ ] 实现智能滚动策略（检测用户意图，避免强制跳转）
- [ ] 添加过渡动画（布局变化200ms，色球切换300ms）
- [ ] 微交互打磨（Hover态、拖拽反馈、加载动画）

**验收标准**：
- ✅ 青色色球有明显的呼吸动画，绿色色球静止锁定
- ✅ 能量连线有从左向右的流光效果
- ✅ 用户手动滚动日志时，自动暂停Scroll-Sync
- ✅ 整体视觉符合"Vibe Workflow"氛围感标准

---

## 📚 技术栈建议

### 前端库选择

| 需求 | 推荐方案 | 备选方案 |
|------|----------|----------|
| 布局拖拽 | `react-resizable-panels` | 自研（基于`onMouseMove`） |
| Workflow Graph | `vis-network` (DAG专用) | `D3.js` (更灵活但复杂) |
| 代码高亮 | `Monaco Editor` | `Prism.js` |
| Diff视图 | `Monaco Editor (Diff Mode)` | `react-diff-viewer` |
| Canvas动画 | `Framer Motion` + Canvas | 原生Canvas API |

### 性能优化

```typescript
// 1. Workflow Graph虚拟化渲染（节点>50时）
import { useVirtualizer } from '@tanstack/react-virtual'

// 2. 日志流虚拟滚动（日志>1000条时）
import { FixedSizeList } from 'react-window'

// 3. Canvas离屏渲染（避免主线程阻塞）
const offscreenCanvas = document.createElement('canvas')
const offscreenCtx = offscreenCanvas.getContext('2d')
```

---

## 🧪 测试用例

### 布局测试

```typescript
describe('Three-Column Layout', () => {
  it('should adjust left/right ratio by dragging divider', () => {
    // 1. 初始比例为45% / 55%
    // 2. 拖拽水平分隔条向右移动100px
    // 3. 验证左侧宽度增加，右侧宽度减少
  })
  
  it('should persist layout ratio to localStorage', () => {
    // 1. 拖拽分隔条
    // 2. 刷新页面
    // 3. 验证比例保持
  })
  
  it('should prevent divider from being dragged beyond min/max width', () => {
    // 1. 尝试将左侧拖拽到<300px
    // 2. 验证被限制在300px
  })
})
```

### 交互测试

```typescript
describe('Workflow Graph Interaction', () => {
  it('should scroll to corresponding log when clicking node', () => {
    // 1. 点击Workflow Graph中的Node-3
    // 2. 验证下部Streaming Info滚动到Node-3的日志起始位置
  })
  
  it('should enter focus mode on double-click node', () => {
    // 1. 双击Node-2
    // 2. 验证上部Graph缩小到20%，下部Info扩大到80%
    // 3. 验证下部日志只显示Node-2相关内容
  })
})
```

---

## 📖 参考资料

- [Manus 执行页面设计](https://manus.im)
- [Meego DAG可视化](https://www.meego.com)
- [VS Code Source Control UI](https://code.visualstudio.com)
- [Linear 的三栏布局最佳实践](https://linear.app)
- [Figma 的Canvas交互设计](https://figma.com)

---

**文档维护者**: TokenDance 核心团队  
**最后更新**: 2026-01-14  
**版本历史**:
- v1.0.0 (2026-01-14): 初始版本，定义三栏布局完整规范
