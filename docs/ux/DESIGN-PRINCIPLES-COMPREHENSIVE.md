# TokenDance UX 设计原则 - 完整指南

**文档版本**: v1.0.0  
**整合时间**: 2026-01-15  
**范围**: 集成 docs/ux 下所有文档的核心设计理念

---

## 📚 文档导航

| 文档 | 侧重点 | 核心内容 |
|-----|-------|---------|
| **UI-Design-Principles.md** | 🎯 产品理念 | Transparency / Controllability / Persistence - 三维度设计哲学 |
| **Three-Column-Layout.md** | 📐 执行页布局 | 左侧执行区 (40%-65%) / 右侧预览区 (35%-60%) - 可调比例布局 |
| **Chain-of-Thought-UI.md** | 🔗 推理过程可视化 | 思维链展示、工具调用追踪、进度反馈 - 建立用户信任 |
| **UI-Design.md** | 🎨 组件与规范 | 色彩系统、排版、间距、圆角、阴影 - 基础设计系统 |
| **UI-Component-Checklist.md** | ✅ 质量保证 | 25 项交付检查清单 - 确保专业标准 |
| **UI-UX-Pro-Max-Integration.md** | 🚀 最佳实践 | Lucide Icons、200ms 过渡、4.5:1 对比度 - 专业化标准 |
| **AnyGen-UI-Analysis.md** | 📊 竞品参考 | 微前端架构、异步加载、Feature Flags - 架构灵感 |

---

## 🎯 三大核心原则

### 1. Transparency（透明度）
**核心理念**：用户能理解 Agent **为什么**做这个决策

**实现方式**：
- 推理链可视化（Chain-of-Thought）
- 决策热力图（Logits Heatmap）
- 执行流时间轴（可回放）
- 关键决策点高亮

**设计表现**：
```
✅ Agent思考过程实时展示
✅ 工具调用详细日志
✅ 搜索/分析结果来源标注
✅ 错误时显示诊断信息
❌ 隐藏内部推理细节
❌ 直接返回结果（不展示过程）
```

---

### 2. Controllability（可控性）
**核心理念**：用户能在任何时刻干预和调整

**实现方式**：
- 人机接管点（中断/恢复）
- 动态方案选择（平行宇宙分支）
- 实时 Logits 调整（覆盖 AI 决策）
- 随时停止/回滚

**设计表现**：
```
✅ Agent遇到障碍时显示\"🤚 接管\"按钮
✅ 多个方案对比（耗时/精确度权衡）
✅ 用户操作无缝衔接（从中断点恢复）
✅ 失败时提供替代路径
❌ 执行锁定（无法中断）
❌ 只有一个执行方案
```

---

### 3. Persistence（沉淀感）
**核心理念**：成功经验能被团队复用

**实现方式**：
- KV-Cache Snapshot（思维快照）
- 活的资产（Contextual Hot-link）
- Expert Agent 技能导出
- Workspace 团队共享

**设计表现**：
```
✅ 完整任务记录（生成于第 X 步）
✅ 关键产出物可标记为\"技能\"
✅ 失败的分支也被保留（作为学习资源）
✅ 团队成员可一键复用成功方案
❌ 完成后直接删除
❌ 只保留最终结果
```

---

## 🏗️ 布局与空间

### 三栏布局规范（执行页）

**整体结构**：
```
Header (固定高度 64px)
├─ 左侧执行区 (可调 30%-65%)
│  ├─ 上: Workflow Graph (40-50%)
│  │   └─ DAG色球图 + 能量连线 + 状态脉冲
│  └─ 下: Streaming Info (50-60%)
│      └─ Agent思考 + Tool Calling + Coworker日志
└─ 右侧预览区 (可调 35%-70%)
   ├─ Tabs: Report | PPT | Files | Diff
   └─ 预览: 浏览器 | 代码 | 演示文稿 | 文件树
```

**尺寸规范**：
- 最小视口：1280px
- 推荐视口：1440px+
- 最小左侧：300px（DAG不拥挤）
- 最小右侧：400px（预览可用）
- 拖拽柄：8px，热区 ±4px（总 16px）

**响应式适配**：
```typescript
const layoutRatio = {
  'deep-research': { left: 35, right: 65 },    // 预览主导
  'ppt-generation': { left: 30, right: 70 },
  'code-refactor': { left: 60, right: 40 },    // 执行主导
  'file-operations': { left: 65, right: 35 },
  'default': { left: 45, right: 55 }
}
```

---

## 🎨 视觉设计

### 色彩系统

**深色主题（默认）**：
```css
/* 背景层级 */
--bg-primary: #0a0a0b;
--bg-secondary: #141415;
--bg-tertiary: #1c1c1e;
--bg-elevated: #242426;

/* 强调色（蓝紫渐变） */
--accent-primary: hsl(262 83% 58%);  /* #8b5cf6 */
--accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);

/* 功能色 */
--success: #22c55e;
--warning: #f59e0b;
--error: #ef4444;
```

**浅色主题**：
```css
--bg-primary: #ffffff;
--bg-secondary: #f4f4f5;
--text-primary: #09090b;
```

### 色球状态色（Workflow Graph）

```css
/* 青色脉冲 - Agent正在计算 */
--color-node-active: #00D9FF;

/* 绿色锁定 - 节点已完成 */
--color-node-success: #00FF88;

/* 琥珀暂停 - 等待人工介入 */
--color-node-pending: #FFB800;

/* 红色冲突 - 执行失败 */
--color-node-error: #FF3B30;

/* 灰色待执行 */
--color-node-inactive: #8E8E93;
```

### 排版系统

```css
/* 字体：统一使用 Inter + JetBrains Mono */
--font-sans: 'Inter', -apple-system, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* 字号层级 */
--text-xs: 12px;      /* 辅助信息 */
--text-sm: 14px;      /* 正文 */
--text-base: 16px;    /* 标题 */
--text-lg: 18px;      /* 大标题 */
--text-xl: 20px;      /* 页面标题 */
--text-2xl: 24px;     /* 特大标题 */

/* 字重 */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 间距系统

```css
/* 基础单位：4px */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
```

### 圆角与阴影

```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;

--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
```

---

## ⚡ 动画标准

### 过渡时长

```css
--transition-fast: 150ms;      /* 按钮、链接 */
--transition-standard: 200ms;  /* 卡片、下拉菜单 */
--transition-slow: 300ms;      /* 侧边栏、抽屉 */
```

**禁止**：>500ms（用户感知延迟）

### 核心动画

**色球呼吸动画**：
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

**能量连线流光**：
```css
@keyframes flow-energy {
  0% { stroke-dashoffset: 100; }
  100% { stroke-dashoffset: 0; }
}

.edge-active {
  animation: flow-energy 2s linear infinite;
}
```

---

## 🚫 禁止事项（严格遵守）

### 1. UI 语言
```
❌ \"我能帮你...\" / \"让我帮你...\" / \"AI 助手\"
✅ \"你的智能工作台\" / \"和 Agent 一起完成\"

❌ 功能导向：\"深度研究\" / \"生成PPT\"
✅ 任务导向：\"市场调研\" / \"演示汇报\"
```

### 2. 图标系统
```
❌ Emoji 作为 UI 图标（🎨 🚀 ⚙️）
✅ Lucide Icons / Heroicons SVG

❌ 混合不同图标库
✅ 统一来源（w-6 h-6 = 24px 标准尺寸）
```

### 3. 交互反馈
```
❌ 悬停导致布局偏移（hover:scale-105）
✅ 颜色/阴影/边框变化（无布局影响）

❌ 过慢动画 (>500ms)
✅ 150-300ms 标准过渡

❌ 无 cursor-pointer
✅ 所有可点击元素有光标指示
```

### 4. 明暗模式
```
❌ 浅色模式文本对比度 <4.5:1
✅ 使用 #0F172A 或更深的颜色

❌ 玻璃态过于透明（bg-white/10）
✅ 浅色模式 bg-white/80+

❌ 浮动导航贴边
✅ top-4 left-4 right-4 间距
```

---

## ✅ 交付检查清单

### 视觉质量（5 项）
- [ ] 无 Emoji 图标
- [ ] 所有图标来自统一图标集
- [ ] 品牌 Logo 正确
- [ ] 悬停稳定性（无布局偏移）
- [ ] 直接使用主题颜色（不用 var() 包装）

### 交互反馈（4 项）
- [ ] cursor-pointer 光标
- [ ] 悬停状态视觉反馈
- [ ] 过渡流畅（150-300ms）
- [ ] 焦点状态可见（键盘导航）

### 明暗模式（4 项）
- [ ] 浅色模式对比度充足（4.5:1+）
- [ ] 玻璃态组件可见
- [ ] 两种模式边框可见
- [ ] 交付前两种模式都测试

### 布局规范（4 项）
- [ ] 浮动元素有适当间距
- [ ] 无内容被固定导航遮挡
- [ ] 响应式测试（320/768/1024/1440px）
- [ ] 移动端无横向滚动

### 无障碍（4 项）
- [ ] 所有图片有 alt 文本
- [ ] 表单输入有标签
- [ ] 颜色非唯一指示器
- [ ] 遵守 prefers-reduced-motion

### 图标规范（3 项）
- [ ] 图标尺寸统一（w-6 h-6）
- [ ] 图标颜色语义正确
- [ ] 图标有 aria-label

### TokenDance 特定（3 项）
- [ ] Agent 节点符合规范
- [ ] Memory Timeline 一致性
- [ ] Context Viewer 对比度充足

---

## 🎬 执行流可视化标准

### 状态标签
```vue
<!-- 思考中 -->
<span class=\"text-blue-400\">🤔 思考中</span>

<!-- 搜索中 -->
<span class=\"text-purple-400\">🔍 搜索中</span>

<!-- 完成 -->
<span class=\"text-green-500\">✅ 完成</span>

<!-- 失败 -->
<span class=\"text-red-500\">❌ 失败</span>
```

### 可折叠结构
```
[▶] Agent思考过程  (点击展开)
[▼] 工具调用详情
    → web_search(\"AI Agent\")
    → 返回 5 条结果
[▶] 生成报告 (折叠)
```

### 进度反馈
```
[====████░░░░░░░░░░] 40% (6/15 页完成)
```

---

## 🔧 首页设计规范

### 设计特点
- **Logo**：简洁黑色标志 + \"TokenDance\" 文字
- **背景**：灰色为主（#fafafa），细微网格纹理
- **CTA**：黑色按钮，悬停时加深
- **工作流卡片**：白色背景 + 图标 + 文案，悬停加阴影
- **Footer Slogan**：\"随时接管 · 实时干预 · 沉淀复用\"

### 禁止
```
❌ 彩虹渐变背景
❌ 大面积毛玻璃
❌ Emoji 图标
❌ AI 助手开场白
✅ 克制的灰度系统
✅ 专业 SVG 图标
✅ 任务导向文案
```

---

## 📊 参考标杆

### 设计参考
- **Linear** - 简洁专业、高效
- **Notion** - 灰度系统、功能直接
- **Vercel** - 克制动效、强调内容

### 微观参考
- **AnyGen** - 蓝紫渐变色系、异步加载、微前端架构
- **Manus** - 三栏布局、执行可视化、信息结构

---

## 🚀 实施清单

### 立即行动
- [ ] 所有新组件遵守检查清单（25 项）
- [ ] 代码审查时检查图标/过渡/对比度
- [ ] 部署前测试明暗模式 + 响应式

### 长期维护
- [ ] 定期审查设计一致性
- [ ] 收集用户反馈改进交互
- [ ] 更新文档保持与代码同步

---

**版本**：v1.0.0  
**最后更新**：2026-01-15  
**维护者**：TokenDance Team  
**覆盖范围**：整合 docs/ux 下 7 个核心文档
