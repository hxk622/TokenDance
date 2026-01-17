# TokenDance 设计系统

**版本**: v2.0.0
**更新日期**: 2026-01-17
**整合来源**: UI-Design.md, UI-UX-Pro-Max-Integration.md, Frontend-Design-Principles.md

---

## 1. 色彩系统

### 1.1 深色主题（默认）

```css
/* 背景层级 */
--bg-primary: #0a0a0b;      /* 主背景 */
--bg-secondary: #141415;    /* 卡片/侧边栏背景 */
--bg-tertiary: #1c1c1e;     /* 悬浮/选中状态 */
--bg-elevated: #242426;     /* 弹窗/下拉菜单 */

/* 文字 */
--text-primary: #ffffff;
--text-secondary: #a1a1aa;
--text-tertiary: #71717a;

/* 强调色（蓝紫渐变） */
--accent-primary: hsl(262 83% 58%);  /* #8b5cf6 */
--accent-hover: hsl(262 90% 65%);
--accent-muted: hsl(262 80% 50%);
--accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);

/* 功能色 */
--success: #22c55e;
--warning: #f59e0b;
--error: #ef4444;
--info: #3b82f6;

/* 边框 */
--border-default: #27272a;
--border-hover: #3f3f46;
```

### 1.2 浅色主题

```css
--bg-primary: #ffffff;
--bg-secondary: #f4f4f5;
--bg-tertiary: #e4e4e7;

--text-primary: #0F172A;     /* slate-900, 对比度 15.8:1 */
--text-secondary: #475569;   /* slate-600, 对比度 7.1:1 */
--text-tertiary: #64748B;    /* slate-500 */

/* 玻璃态组件 */
--glass-bg-light: rgba(255, 255, 255, 0.8);  /* 浅色模式 */
--glass-bg-dark: rgba(20, 20, 21, 0.8);      /* 深色模式 */
```

### 1.3 色球状态色（Workflow Graph 专用）

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

/* 灰色待执行 */
--color-node-inactive: #8E8E93;
--color-node-inactive-glow: rgba(142, 142, 147, 0.2);
```

### 1.4 对比度标准

- **正文**: 4.5:1 最低（WCAG AA）
- **大文本**: 3:1 最低
- **浅色模式文本**: 必须使用 `#0F172A` (gray-900) 或更深
- **弱化文本**: 最低 `#475569` (slate-600)

---

## 2. 排版系统

### 2.1 字体栈

```css
/* 正文字体 */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

/* 代码字体 */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* 标题字体（可选升级） */
--font-display: 'Space Grotesk', sans-serif;
```

### 2.2 字号层级

```css
--text-xs: 12px;      /* 辅助信息 */
--text-sm: 14px;      /* 正文 */
--text-base: 16px;    /* 标题 */
--text-lg: 18px;      /* 大标题 */
--text-xl: 20px;      /* 页面标题 */
--text-2xl: 24px;     /* 特大标题 */
```

### 2.3 字重

```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 2.4 行高

```css
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

---

## 3. 间距系统

基础单位：**4px**

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
```

---

## 4. 圆角与阴影

### 4.1 圆角

```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;
```

### 4.2 阴影

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

---

## 5. 动画标准

### 5.1 过渡时长

```css
--transition-fast: 150ms;      /* 按钮、链接 */
--transition-standard: 200ms;  /* 卡片、下拉菜单 */
--transition-slow: 300ms;      /* 侧边栏、抽屉 */
```

**禁止**: >500ms（用户感知延迟）

### 5.2 缓动函数

```css
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);  /* 轻微回弹 */
```

### 5.3 核心动画

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
  stroke-dasharray: 10 5;
  animation: flow-energy 1s linear infinite;
}
```

---

## 6. 图标规范

### 6.1 图标库

- **主图标库**: Lucide Icons (Vue 3)
- **品牌图标**: Simple Icons (官方 SVG)
- **禁止使用**: Emoji 作为 UI 图标（🎨 🚀 ⚙️）

### 6.2 图标尺寸

```vue
<!-- 小图标 16px -->
<SearchIcon class="w-4 h-4" />

<!-- 标准图标 24px -->
<BellIcon class="w-6 h-6" />

<!-- 大图标 32px -->
<UserIcon class="w-8 h-8" />

<!-- 特大图标 48px -->
<LogoIcon class="w-12 h-12" />
```

### 6.3 图标使用

```vue
<!-- ✅ 正确 -->
<Search class="w-6 h-6 text-gray-600" />

<!-- ❌ 错误 -->
<span>🔍</span>
```

### 6.4 图标可访问性

```vue
<button aria-label="Search">
  <SearchIcon class="w-5 h-5" />
</button>
```

---

## 7. 交互反馈

### 7.1 光标状态

```css
/* 所有交互元素 */
.interactive {
  cursor: pointer;
}

/* 禁用状态 */
.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
```

### 7.2 悬停反馈（禁止布局偏移）

```vue
<!-- ✅ 正确：颜色/阴影变化 -->
<div class="transition-all duration-200 hover:shadow-lg hover:border-accent-primary">
  Card
</div>

<!-- ❌ 错误：scale 导致布局偏移 -->
<div class="hover:scale-105">
  Card
</div>
```

### 7.3 焦点状态（键盘导航）

```vue
<button class="focus:outline-none focus:ring-2 focus:ring-accent-primary">
  Submit
</button>
```

---

## 8. 响应式断点

```css
sm: 640px   /* 手机横屏 */
md: 768px   /* 平板竖屏 */
lg: 1024px  /* 平板横屏/小笔记本 */
xl: 1280px  /* 桌面 */
2xl: 1536px /* 大屏桌面 */
```

### 响应式策略

| 屏幕尺寸 | 侧边栏 | 布局调整 |
|---------|--------|----------|
| < 768px | 抽屉模式 | 全屏对话 |
| 768px - 1024px | 可折叠 | 双栏布局 |
| > 1024px | 常驻显示 | 标准布局 |

---

## 9. 组件库

### 9.1 基础组件（Shadcn/UI Vue）

- Button, Input, Textarea
- Dialog, Popover, Tooltip
- Dropdown, Select
- Card, Badge
- ScrollArea, Separator
- Tabs, Accordion, Collapsible

### 9.2 业务组件（自研）

- AgentCanvas (流程编排画布)
- MemoryTimeline (记忆时间线)
- SkillPicker (技能选择器)
- ToolConfig (工具配置器)
- ExecutionLog (执行日志查看器)
- ContextViewer (上下文查看器)

### 9.3 编辑器

- **富文本**: TipTap
- **代码编辑**: Monaco Editor
- **Markdown**: vue-markdown-render + highlight.js

---

**维护者**: TokenDance Team
