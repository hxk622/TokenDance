# AnyGen UX 最佳实践

**版本**: v1.0.0
**更新日期**: 2025-01-21
**来源**: AnyGen (www.anygen.io) UI/UX 分析

---

## 1. 核心设计哲学

### 1.1 用户是主角（User as Director）

**原则**：强调用户主动性，AI 是工具而非主导者。

| ❌ 避免 | ✅ 采用 |
|---------|---------|
| "我来帮你生成..." | "开始生成" |
| "AI 助手建议..." | "建议方案" |
| "让我帮你分析" | "分析报告" |
| "请稍等，AI 正在处理" | 直接展示进度 |

**文案规则**：
```
- 避免第一人称（"我"、"让我"）
- 避免"帮你"类表述
- 使用动作导向语言（"撰写"、"分析"、"研究"）
- 状态展示用客观描述，非拟人化
```

---

### 1.2 透明可控（Transparency + Control）

**进度展示**：
```
✅ 实时展示 AI 具体在做什么
✅ 显示阶段进度（1/4、2/4...）
✅ 允许用户随时干预/调整
✅ 错误时提供清晰的诊断信息

❌ 只显示"处理中..."
❌ 无法中断的长时间等待
❌ 隐藏执行细节
```

**干预点设计**：
```vue
<!-- 好的设计：提供干预按钮 -->
<div class="intervention-panel">
  <span class="status">正在搜索相关资料...</span>
  <button class="btn-secondary">调整方向</button>
  <button class="btn-ghost">跳过此步</button>
</div>
```

---

## 2. 视觉设计规范

### 2.1 配色系统

**主色调**：克制的灰度系统 + 功能性强调色

```css
/* 背景层次 */
--bg-primary: #fafafa;      /* 主背景 */
--bg-secondary: #f5f5f5;    /* 卡片背景 */
--bg-tertiary: #eeeeee;     /* 输入框背景 */

/* 文字层次 */
--text-primary: #1a1a1a;    /* 主文字 */
--text-secondary: #666666;  /* 次要文字 */
--text-muted: #999999;      /* 弱化文字 */
--text-placeholder: #c4c4c4; /* placeholder */

/* 功能色 */
--accent-primary: #0066ff;  /* 主强调 */
--accent-success: #00c853;  /* 成功 */
--accent-warning: #ff9500;  /* 警告 */
--accent-error: #ff3b30;    /* 错误 */
```

**禁止**：
```css
/* ❌ 避免 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); /* 紫色渐变 */
background: linear-gradient(to right, #ff416c, #ff4b2b); /* 彩虹渐变 */
```

### 2.2 图标规范

**统一使用 Lucide Icons**，禁止 Emoji：

```vue
<!-- ✅ 正确 -->
<MagnifyingGlassIcon class="w-4 h-4" />
<DocumentTextIcon class="w-4 h-4" />

<!-- ❌ 错误 -->
<span>🔍</span>
<span>📄</span>
```

**图标尺寸规范**：
```
- 按钮内图标: 16px (w-4 h-4)
- 列表项图标: 20px (w-5 h-5)
- 卡片标题图标: 24px (w-6 h-6)
- 空状态图标: 48px (w-12 h-12)
```

### 2.3 圆角规范

```css
--radius-sm: 4px;    /* 小元素 (tag, badge) */
--radius-md: 8px;    /* 中等元素 (button, input) */
--radius-lg: 12px;   /* 大元素 (card, modal) */
--radius-xl: 16px;   /* 特大元素 (dialog, panel) */
--radius-full: 9999px; /* 圆形 (avatar, chip) */
```

---

## 3. 交互模式

### 3.1 加载与等待

**原则**：永远让用户知道发生了什么

```vue
<!-- ✅ 好的加载状态 -->
<div class="loading-state">
  <div class="phase-indicator">阶段 2/4: 信息提取</div>
  <div class="progress-bar" :style="{ width: '45%' }"></div>
  <div class="current-action">正在阅读 arxiv.org 论文...</div>
</div>

<!-- ❌ 差的加载状态 -->
<div class="loading">
  <Spinner />
  <span>请稍候...</span>
</div>
```

**骨架屏规范**：
```vue
<!-- 内容加载时使用骨架屏 -->
<template v-if="loading">
  <div class="skeleton-card">
    <div class="skeleton-line w-3/4 h-4 mb-2"></div>
    <div class="skeleton-line w-1/2 h-3"></div>
  </div>
</template>
```

### 3.2 表单交互

**输入框**：
```vue
<input
  class="input-field"
  placeholder="描述你的研究主题..."
  :class="{ 'input-focus': isFocused, 'input-error': hasError }"
/>

<style>
.input-field {
  border: 1px solid var(--any-border);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  transition: border-color 150ms ease;
}
.input-field:focus {
  border-color: var(--accent-primary);
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1);
}
</style>
```

**按钮状态**：
```css
.btn-primary {
  background: var(--accent-primary);
  transition: all 150ms ease;
}
.btn-primary:hover {
  filter: brightness(1.1);
}
.btn-primary:active {
  transform: scale(0.98);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

### 3.3 反馈机制

**即时反馈**：
```typescript
// 操作后立即反馈
async function handleSubmit() {
  // 1. 立即禁用按钮，显示加载状态
  isSubmitting.value = true
  
  // 2. 乐观更新 UI
  items.value.push(newItem)
  
  try {
    await api.submit(newItem)
    // 3. 成功：显示轻量 toast
    toast.success('已保存')
  } catch (error) {
    // 4. 失败：回滚 + 显示错误
    items.value.pop()
    toast.error('保存失败，请重试')
  } finally {
    isSubmitting.value = false
  }
}
```

---

## 4. 研究进度展示规范

### 4.1 阶段指示器

```vue
<template>
  <div class="phase-indicator">
    <div 
      v-for="(phase, index) in phases" 
      :key="phase.id"
      :class="[
        'phase-item',
        { 'phase-active': currentPhase === index },
        { 'phase-done': currentPhase > index }
      ]"
    >
      <div class="phase-dot"></div>
      <span class="phase-label">{{ phase.name }}</span>
    </div>
  </div>
</template>

<style>
.phase-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
}
.phase-active {
  color: var(--accent-primary);
}
.phase-active .phase-dot {
  background: var(--accent-primary);
  animation: pulse 1.5s infinite;
}
.phase-done {
  color: var(--accent-success);
}
</style>
```

### 4.2 来源可信度展示

```vue
<template>
  <div class="source-card">
    <div class="source-header">
      <img :src="faviconUrl" class="source-favicon" />
      <span class="source-domain">{{ domain }}</span>
      <CredibilityBadge :level="credibility" />
    </div>
    <p class="source-title">{{ title }}</p>
    <div class="source-status">
      <StatusDot :status="status" />
      <span>{{ statusText }}</span>
    </div>
  </div>
</template>
```

**可信度等级**：
```typescript
const credibilityConfig = {
  authoritative: { 
    label: '权威', 
    color: '#00c853',
    description: '学术期刊、官方文档'
  },
  reliable: { 
    label: '可靠', 
    color: '#0066ff',
    description: '知名媒体、专业博客'
  },
  moderate: { 
    label: '一般', 
    color: '#ff9500',
    description: '普通网站'
  },
  questionable: { 
    label: '存疑', 
    color: '#ff3b30',
    description: '未知来源'
  }
}
```

### 4.3 搜索关键词展示

```vue
<template>
  <div class="query-list">
    <div 
      v-for="query in queries" 
      :key="query.id"
      class="query-item"
    >
      <StatusIcon :status="query.status" />
      <span class="query-text">{{ query.text }}</span>
      <span v-if="query.resultCount" class="query-result">
        {{ query.resultCount }} 结果
      </span>
    </div>
  </div>
</template>

<style>
.query-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}
.query-text {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
}
.query-result {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
```

---

## 5. 动画规范

### 5.1 时长标准

```css
--duration-fast: 100ms;    /* 微交互 (hover, active) */
--duration-normal: 150ms;  /* 常规过渡 (展开, 切换) */
--duration-slow: 300ms;    /* 复杂动画 (模态框, 页面切换) */
```

### 5.2 缓动函数

```css
--ease-out: cubic-bezier(0, 0, 0.2, 1);      /* 减速 - 进入动画 */
--ease-in: cubic-bezier(0.4, 0, 1, 1);       /* 加速 - 退出动画 */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1); /* 标准过渡 */
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性 - 强调 */
```

### 5.3 常用动画

```css
/* 脉冲呼吸 - 进行中状态 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 淡入 - 元素出现 */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 交错出现 - 列表项 */
.list-item {
  animation: fadeIn 200ms var(--ease-out);
  animation-fill-mode: both;
}
.list-item:nth-child(1) { animation-delay: 0ms; }
.list-item:nth-child(2) { animation-delay: 50ms; }
.list-item:nth-child(3) { animation-delay: 100ms; }
```

---

## 6. 响应式设计

### 6.1 断点

```css
/* Mobile first */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

### 6.2 移动端适配

```css
/* 触摸目标最小尺寸 */
.touchable {
  min-height: 44px;
  min-width: 44px;
}

/* 移动端输入框 */
@media (max-width: 640px) {
  .input-field {
    font-size: 16px; /* 防止 iOS 自动缩放 */
  }
}
```

---

## 7. 无障碍（a11y）

### 7.1 键盘导航

```vue
<button
  @keydown.enter="handleClick"
  @keydown.space="handleClick"
  :tabindex="0"
  role="button"
>
  操作按钮
</button>
```

### 7.2 ARIA 标签

```vue
<div
  role="progressbar"
  :aria-valuenow="progress"
  aria-valuemin="0"
  aria-valuemax="100"
  :aria-label="`研究进度 ${progress}%`"
>
  <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
</div>
```

---

## 8. 检查清单

### 新组件开发前

- [ ] 确认配色使用 CSS 变量
- [ ] 确认图标使用 Lucide
- [ ] 确认文案避免 AI 味
- [ ] 确认有加载/错误/空状态
- [ ] 确认动画时长符合规范
- [ ] 确认触摸目标 ≥44px

### 提交前

- [ ] 在 light/dark 模式下测试
- [ ] 在移动端测试
- [ ] 检查键盘导航
- [ ] 运行 `pnpm lint`

---

**文档维护者**: TokenDance Team
**参考来源**: AnyGen (www.anygen.io)
