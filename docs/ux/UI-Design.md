# TokenDance UI设计文档

> Version: 1.1.0 | MVP阶段 | 整合 AnyGen 参考设计
> Last Updated: 2026-01-09
> 参考来源: [AnyGen UI分析](./AnyGen-UI-Analysis.md)

## 1. 设计原则

### 1.1 核心理念

TokenDance的UI设计融合了Manus、GenSpark和AnyGen的设计精髓：

| 设计维度 | 设计原则 | 来源参考 |
|---------|---------|---------|
| 信息展示 | 渐进式披露，按需展开 | Manus |
| 交互反馈 | 实时流式输出，过程可见 | GenSpark |
| 视觉风格 | 简洁专业，现代感强 | AnyGen |
| 空间布局 | 左侧导航+右侧内容，沉浸式 | AnyGen/Manus |
| 性能优化 | 异步加载，按需渲染 | AnyGen |
| 用户体验 | Guest模式，降低门槛 | AnyGen |

### 1.2 设计关键词

- **清晰**：信息层级分明，操作路径明确
- **高效**：减少认知负担，快速完成任务
- **透明**：Agent思考/执行过程可追溯
- **专业**：符合知识工作者的审美期待
- **现代**：紧跟设计趋势，蓝紫渐变主色调（参考AnyGen）

## 2. 设计规范

### 2.1 色彩系统

**设计参考**：借鉴 AnyGen 的蓝紫渐变色系统，配合 Tailwind 默认色板

#### 深色主题（默认）

```css
/* 背景层级 */
--bg-primary: #0a0a0b;      /* 主背景 */
--bg-secondary: #141415;    /* 卡片/侧边栏背景 */
--bg-tertiary: #1c1c1e;     /* 悬浮/选中状态 */
--bg-elevated: #242426;     /* 弹窗/下拉菜单 */

/* 文字 */
--text-primary: #ffffff;    /* 主要文字 */
--text-secondary: #a1a1aa;  /* 次要文字 */
--text-tertiary: #71717a;   /* 辅助文字 */

/* 强调色 (蓝紫渐变，参考 AnyGen) */
--accent-primary: hsl(262 83% 58%);  /* 主强调色 (#8b5cf6) */
--accent-hover: hsl(262 90% 65%);    /* 悬浮状态 */
--accent-muted: hsl(262 80% 50%);    /* 按下状态 */
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

#### 浅色主题

```css
--bg-primary: #ffffff;
--bg-secondary: #f4f4f5;
--bg-tertiary: #e4e4e7;
--text-primary: #09090b;
--text-secondary: #52525b;
```

### 2.2 排版系统

```css
/* 字体 */
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* 字号 */
--text-xs: 12px;      /* 辅助信息 */
--text-sm: 14px;      /* 正文 */
--text-base: 16px;    /* 标题 */
--text-lg: 18px;      /* 大标题 */
--text-xl: 20px;      /* 页面标题 */
--text-2xl: 24px;     /* 特大标题 */

/* 行高 */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;

/* 字重 */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 2.3 间距系统

```css
/* 基础单位: 4px */
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

### 2.4 圆角系统

```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;
```

### 2.5 阴影系统

```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

## 3. 页面布局

### 3.1 整体布局结构

```
┌──────────────────────────────────────────────────────────────┐
│                         Header (可选)                        │
├────────────┬─────────────────────────────────────────────────┤
│            │                                                 │
│            │                                                 │
│  Sidebar   │              Main Content                       │
│  (260px)   │              (flex: 1)                          │
│            │                                                 │
│            │                                                 │
│            ├─────────────────────────────────────────────────┤
│            │              Input Area                         │
├────────────┴─────────────────────────────────────────────────┤
│                        Footer (可选)                         │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 侧边栏 (Sidebar)

**尺寸**：宽度 260px，可折叠至 60px

**结构**：
```
┌─────────────────────┐
│ Logo / TokenDance   │
├─────────────────────┤
│ [+ 新对话] 按钮      │
├─────────────────────┤
│ 今天                 │
│   ├─ 会话标题1       │
│   └─ 会话标题2       │
│ 昨天                 │
│   └─ 会话标题3       │
│ 更早                 │
│   └─ ...            │
├─────────────────────┤
│ ─────────────────── │
│ 工作空间             │
│ 设置                 │
│ 用户头像 / 名称      │
└─────────────────────┘
```

**交互**：
- 会话hover显示删除/重命名操作
- 支持拖拽排序（可选）
- 会话自动按时间分组

### 3.3 主对话区 (Main Content)

**结构**：
```
┌─────────────────────────────────────────────────────┐
│                    消息列表区                        │
│                    (可滚动)                          │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 👤 用户消息                                      │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 🤖 Agent消息                                     │ │
│ │   ┌─ 思考过程 (可折叠) ─────────────────────┐   │ │
│ │   │ 分析用户需求...                         │   │ │
│ │   └────────────────────────────────────────┘   │ │
│ │                                                 │ │
│ │   ┌─ 工具调用 ─────────────────────────────┐   │ │
│ │   │ 🔍 web_search("AI Agent")              │   │ │
│ │   │ ✅ 返回 5 条结果                        │   │ │
│ │   └────────────────────────────────────────┘   │ │
│ │                                                 │ │
│ │   正文回复内容...                               │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
├─────────────────────────────────────────────────────┤
│                    输入区域                          │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 📎 输入框...                            [发送] │ │
│ └─────────────────────────────────────────────────┘ │
│            快捷操作: [深度研究] [生成PPT]            │
└─────────────────────────────────────────────────────┘
```

## 4. 核心组件设计

### 4.1 消息气泡 (Message Bubble)

#### 用户消息
```vue
<template>
  <div class="flex justify-end mb-4">
    <div class="max-w-[80%] bg-accent-primary text-white 
                rounded-2xl rounded-br-md px-4 py-3">
      {{ message.content }}
    </div>
  </div>
</template>
```

#### Agent消息
```vue
<template>
  <div class="flex mb-4">
    <div class="w-8 h-8 rounded-full bg-bg-tertiary flex-shrink-0 mr-3">
      <Logo />
    </div>
    <div class="flex-1 max-w-[85%]">
      <!-- 思考过程 (可折叠) -->
      <ThinkingBlock v-if="message.thinking" :content="message.thinking" />
      
      <!-- 工具调用 -->
      <ToolCallBlock v-for="tool in message.toolCalls" :key="tool.id" :tool="tool" />
      
      <!-- 正文 -->
      <div class="prose prose-invert">
        <MarkdownRenderer :content="message.content" />
      </div>
      
      <!-- 引用来源 -->
      <CitationList v-if="message.citations" :citations="message.citations" />
    </div>
  </div>
</template>
```

### 4.2 思考过程块 (ThinkingBlock)

**设计要点**：
- 默认折叠，显示"正在思考..."
- 可展开查看详细思考过程
- 流式输出时有打字机效果

```vue
<template>
  <div class="mb-3 rounded-lg bg-bg-tertiary/50 overflow-hidden">
    <button @click="expanded = !expanded" 
            class="w-full px-4 py-2 flex items-center justify-between 
                   text-text-secondary text-sm hover:bg-bg-tertiary">
      <span class="flex items-center gap-2">
        <BrainIcon class="w-4 h-4" />
        {{ loading ? '正在思考...' : '思考过程' }}
      </span>
      <ChevronIcon :class="{ 'rotate-180': expanded }" />
    </button>
    <div v-show="expanded" class="px-4 py-3 text-sm text-text-tertiary 
                                  border-t border-border-default">
      {{ content }}
    </div>
  </div>
</template>
```

### 4.3 工具调用块 (ToolCallBlock)

**状态**：pending → running → success/error

```vue
<template>
  <div class="mb-3 rounded-lg border border-border-default overflow-hidden">
    <div class="px-4 py-2 flex items-center justify-between bg-bg-secondary">
      <span class="flex items-center gap-2 text-sm">
        <ToolIcon :name="tool.name" class="w-4 h-4" />
        <span class="font-mono">{{ tool.name }}</span>
        <span class="text-text-tertiary">({{ tool.args }})</span>
      </span>
      <StatusBadge :status="tool.status" />
    </div>
    
    <!-- 展开查看结果 -->
    <div v-if="expanded" class="px-4 py-3 bg-bg-primary 
                                border-t border-border-default">
      <pre class="text-xs text-text-secondary overflow-x-auto">
        {{ tool.result }}
      </pre>
    </div>
  </div>
</template>
```

### 4.4 输入框组件 (ChatInput)

**功能**：
- 自动高度调整（最大4行）
- 支持拖拽上传文件
- 快捷键发送 (Cmd/Ctrl + Enter)
- 快捷操作按钮

```vue
<template>
  <div class="border border-border-default rounded-xl bg-bg-secondary 
              focus-within:border-accent-primary transition-colors">
    <!-- 文件预览区 -->
    <div v-if="files.length" class="px-4 pt-3 flex gap-2 flex-wrap">
      <FileChip v-for="file in files" :key="file.id" :file="file" 
                @remove="removeFile(file.id)" />
    </div>
    
    <!-- 输入区 -->
    <div class="flex items-end gap-2 p-3">
      <button class="p-2 text-text-secondary hover:text-text-primary">
        <PaperclipIcon class="w-5 h-5" />
      </button>
      
      <textarea 
        v-model="input"
        @keydown.enter.meta="send"
        placeholder="输入消息..."
        class="flex-1 bg-transparent resize-none outline-none 
               text-text-primary placeholder:text-text-tertiary"
        rows="1"
      />
      
      <button 
        @click="send"
        :disabled="!input.trim()"
        class="p-2 rounded-lg bg-accent-primary text-white 
               hover:bg-accent-hover disabled:opacity-50">
        <SendIcon class="w-5 h-5" />
      </button>
    </div>
    
    <!-- 快捷操作 -->
    <div class="px-4 pb-3 flex gap-2">
      <QuickAction icon="SearchIcon" label="深度研究" @click="setMode('research')" />
      <QuickAction icon="PresentationIcon" label="生成PPT" @click="setMode('ppt')" />
    </div>
  </div>
</template>
```

### 4.5 确认弹窗 (ConfirmDialog) - HITL

**用途**：高风险操作前的人工确认

```vue
<template>
  <Dialog :open="open" @close="$emit('cancel')">
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center">
      <div class="bg-bg-elevated rounded-xl p-6 max-w-md w-full mx-4 
                  shadow-xl border border-border-default">
        <!-- 标题 -->
        <div class="flex items-center gap-3 mb-4">
          <div class="p-2 rounded-full" :class="iconBgClass">
            <component :is="icon" class="w-5 h-5" />
          </div>
          <h3 class="text-lg font-semibold text-text-primary">{{ title }}</h3>
        </div>
        
        <!-- 内容 -->
        <p class="text-text-secondary mb-4">{{ description }}</p>
        
        <!-- 详情（如代码预览） -->
        <div v-if="details" class="mb-4 p-3 rounded-lg bg-bg-primary 
                                   border border-border-default max-h-48 overflow-auto">
          <pre class="text-xs font-mono text-text-secondary">{{ details }}</pre>
        </div>
        
        <!-- 操作按钮 -->
        <div class="flex justify-end gap-3">
          <button @click="$emit('cancel')" 
                  class="px-4 py-2 rounded-lg text-text-secondary 
                         hover:bg-bg-tertiary">
            取消
          </button>
          <button @click="$emit('confirm')" 
                  class="px-4 py-2 rounded-lg bg-accent-primary text-white 
                         hover:bg-accent-hover">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Dialog>
</template>
```

### 4.6 进度指示器 (ProgressIndicator)

**用于**：Deep Research、PPT生成等长任务

```vue
<template>
  <div class="rounded-lg border border-border-default bg-bg-secondary p-4">
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm font-medium text-text-primary">{{ title }}</span>
      <span class="text-xs text-text-tertiary">{{ current }}/{{ total }}</span>
    </div>
    
    <!-- 进度条 -->
    <div class="h-2 bg-bg-tertiary rounded-full overflow-hidden mb-3">
      <div class="h-full bg-accent-primary transition-all duration-300"
           :style="{ width: `${progress}%` }" />
    </div>
    
    <!-- 步骤列表 -->
    <div class="space-y-2">
      <div v-for="step in steps" :key="step.id" 
           class="flex items-center gap-2 text-sm">
        <CheckIcon v-if="step.status === 'done'" class="w-4 h-4 text-success" />
        <LoaderIcon v-else-if="step.status === 'running'" class="w-4 h-4 text-accent-primary animate-spin" />
        <CircleIcon v-else class="w-4 h-4 text-text-tertiary" />
        <span :class="step.status === 'done' ? 'text-text-secondary' : 'text-text-primary'">
          {{ step.label }}
        </span>
      </div>
    </div>
  </div>
</template>
```

### 4.7 引用卡片 (CitationCard)

**用于**：Deep Research结果的来源标注

```vue
<template>
  <div class="inline-flex items-center gap-1 px-2 py-1 rounded-md 
              bg-bg-tertiary hover:bg-bg-elevated cursor-pointer 
              text-xs text-text-secondary transition-colors"
       @click="showDetail = !showDetail">
    <span class="text-accent-primary font-medium">[{{ index }}]</span>
    <span class="truncate max-w-[150px]">{{ citation.title }}</span>
  </div>
  
  <!-- 详情弹出 -->
  <Popover v-if="showDetail" :anchor="$el">
    <div class="p-3 max-w-sm">
      <a :href="citation.url" target="_blank" 
         class="text-accent-primary hover:underline font-medium">
        {{ citation.title }}
      </a>
      <p class="text-xs text-text-tertiary mt-1">{{ citation.domain }}</p>
      <p class="text-sm text-text-secondary mt-2">{{ citation.snippet }}</p>
    </div>
  </Popover>
</template>
```

## 5. 页面设计

### 5.1 首页/新对话页

**场景**：用户首次进入或点击"新对话"

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│                  🚀 TokenDance                      │
│                                                     │
│              我能帮你完成各种任务                    │
│                                                     │
│     ┌────────────────────────────────────────┐     │
│     │ 输入你想完成的任务...                   │     │
│     └────────────────────────────────────────┘     │
│                                                     │
│        [🔍 深度研究]  [📊 生成PPT]  [💻 执行代码]   │
│                                                     │
│     ────────── 试试这些 ──────────                  │
│                                                     │
│     "帮我调研2024年AI Agent市场趋势"               │
│     "把这份报告做成10页PPT"                        │
│     "分析这份CSV数据并生成图表"                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 5.2 Deep Research结果页

**场景**：研究完成后的报告展示

```
┌─────────────────────────────────────────────────────┐
│  📋 AI Agent市场调研报告                     [导出] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  目录                                               │
│  ├─ 1. 市场概述                                    │
│  ├─ 2. 主要玩家分析                                │
│  ├─ 3. 技术趋势                                    │
│  └─ 4. 结论与展望                                  │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  ## 1. 市场概述                                     │
│                                                     │
│  2024年全球AI Agent市场规模预计达到XXX亿美元[1]，  │
│  较去年增长XX%[2]。主要驱动因素包括...             │
│                                                     │
│  ## 2. 主要玩家分析                                │
│                                                     │
│  | 公司 | 产品 | 特点 |                            │
│  | Anthropic | Claude | ... |                      │
│  | OpenAI | ChatGPT | ... |                        │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│  📚 参考来源                                        │
│  [1] Gartner报告 - gartner.com/...                 │
│  [2] IDC研究 - idc.com/...                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 5.3 PPT预览页

**场景**：PPT生成后的预览与编辑

```
┌─────────────────────────────────────────────────────┐
│  📊 AI发展趋势.pptx           [编辑] [导出PPTX/PDF] │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────┐ ┌─────────────────────────────────────┐   │
│  │  1  │ │                                     │   │
│  │ ◉   │ │         AI 发展趋势                 │   │
│  └─────┘ │              2024                   │   │
│  ┌─────┐ │                                     │   │
│  │  2  │ │      Your Name | Company            │   │
│  │ ○   │ │                                     │   │
│  └─────┘ └─────────────────────────────────────┘   │
│  ┌─────┐                                           │
│  │  3  │       [← 上一页]  1/10  [下一页 →]        │
│  │ ○   │                                           │
│  └─────┘  ──────────────────────────────────────   │
│  ┌─────┐                                           │
│  │  4  │  💡 不满意这一页？                        │
│  │ ○   │  [重新生成] [编辑内容]                    │
│  └─────┘                                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 6. 响应式设计

### 6.1 断点定义

```css
/* Tailwind默认断点 */
sm: 640px   /* 手机横屏 */
md: 768px   /* 平板竖屏 */
lg: 1024px  /* 平板横屏/小笔记本 */
xl: 1280px  /* 桌面 */
2xl: 1536px /* 大屏桌面 */
```

### 6.2 响应式策略

| 屏幕尺寸 | 侧边栏 | 布局调整 |
|---------|--------|---------|
| < 768px | 抽屉模式 | 全屏对话 |
| 768px - 1024px | 可折叠 | 双栏布局 |
| > 1024px | 常驻显示 | 标准布局 |

## 7. 动效设计

### 7.1 基础动效

```css
/* 过渡曲线 */
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);

/* 过渡时长 */
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
```

### 7.2 关键动效

| 场景 | 动效 | 时长 |
|-----|-----|-----|
| 消息出现 | fadeInUp | 200ms |
| 思考块展开 | slideDown | 200ms |
| 按钮hover | scale(1.02) | 150ms |
| 弹窗出现 | fadeIn + scaleUp | 200ms |
| 流式文字 | 逐字显示 | 自然速度 |

## 8. 无障碍设计

### 8.1 键盘导航

- 所有交互元素可Tab聚焦
- Enter/Space触发操作
- Esc关闭弹窗/取消操作
- 方向键在列表中导航

### 8.2 ARIA标签

```vue
<button 
  aria-label="发送消息"
  :aria-disabled="!canSend"
>
  <SendIcon />
</button>
```

### 8.3 对比度

- 文字对比度 ≥ 4.5:1 (WCAG AA)
- 大文字对比度 ≥ 3:1

## 9. 技术实现

### 9.1 组件库

**基础组件**：使用 **Shadcn/UI Vue** + **Tailwind CSS**

核心组件：
- Button, Input, Textarea
- Dialog, Popover, Tooltip
- Dropdown, Select
- Card, Badge
- ScrollArea, Separator
- Tabs, Accordion, Collapsible

**参考 AnyGen 的模块化设计**：
- 基础 UI 组件（Shadcn/UI）：30+ 组件
- 业务组件（自研）：Agent Canvas, Memory Timeline, Skill Picker 等
- 按需异步加载，优化首屏性能

### 9.2 图标库

使用 **Lucide Icons**

```vue
import { Search, Send, Paperclip, ChevronDown } from 'lucide-vue-next'
```

### 9.3 编辑器集成

**参考 AnyGen 的双引擎设计**：

1. **富文本编辑器**：TipTap (文档/PPT)
   - 模块化架构（5个 editor-kit 子模块）
   - DOCX 导入/导出支持

2. **代码编辑器**：Monaco Editor (VS Code 内核)
   - 语法高亮
   - 智能补全
   - 多语言支持

3. **Markdown渲染**：vue-markdown-render + highlight.js

## 10. 附录

### A. 组件清单

| 组件 | 用途 | 优先级 |
|-----|-----|-------|
| ChatMessage | 消息展示 | P0 |
| ChatInput | 消息输入 | P0 |
| ThinkingBlock | 思考过程 | P0 |
| ToolCallBlock | 工具调用 | P0 |
| ConfirmDialog | HITL确认 | P0 |
| ProgressIndicator | 进度展示 | P1 |
| CitationCard | 引用展示 | P1 |
| FileChip | 文件标签 | P1 |
| QuickAction | 快捷操作 | P2 |

### B. 性能优化策略（参考 AnyGen）

#### 代码分割
- **路由级分割**：每个页面独立打包
- **组件级分割**：大型组件异步加载
- **Vendor 分割**：第三方库独立打包

#### 资源加载
```typescript
// 路由懒加载
const routes = [
  {
    path: '/home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/agent/:id',
    component: () => import('@/views/Agent.vue')
  }
]

// 组件异步加载
const AgentCanvas = defineAsyncComponent(() => 
  import('@/components/AgentCanvas.vue')
)
```

#### 首屏优化
- 核心 UI 优先加载（~500KB）
- 业务模块按需加载
- CSS 按路由分割
- 预加载关键资源

#### 渲染优化
- 虚拟滚动（大列表）
- 骨架屏（加载状态）
- 图片懒加载
- 防抖/节流（输入框、滚动）

### C. Feature Flags 系统（参考 AnyGen）

**用途**：灰度发布、A/B 测试、功能开关

```typescript
interface FeatureFlags {
  'agent.canvas.enabled': boolean;
  'memory.graph.enabled': boolean;
  'deep.research.enabled': boolean;
  'ppt.generation.enabled': boolean;
  'guest.mode.enabled': boolean;
}

// 使用示例
const featureFlags = useFeatureFlags();

if (featureFlags['agent.canvas.enabled']) {
  // 显示 Agent Canvas
}
```

### D. Guest 模式（参考 AnyGen）

**目标**：降低试用门槛，提升转化率

**特性**：
- 无需注册即可试用
- 限制使用次数/功能
- 引导注册转化

```typescript
interface User {
  id: string;
  name: string;
  email?: string;  // Guest 用户为空
  type: 'guest' | 'registered';
  trialLimit: number;
}
```

### E. 相关文档

- [PRD文档](../product/PRD.md)
- [技术架构HLD](../architecture/HLD.md)
- [AnyGen UI分析](./AnyGen-UI-Analysis.md)
- [NEO4J集成指南](../../NEO4J_INTEGRATION.md)
