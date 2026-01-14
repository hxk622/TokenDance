# UI/UX Pro Max Skill 整合方案

> 将 UI/UX Pro Max Skill 的设计智能整合到 TokenDance
> Created: 2026-01-09
> Reference: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

---

## 1. UI/UX Pro Max Skill 概述

### 1.1 核心特性
- **57 UI 样式**：Glassmorphism, Claymorphism, Minimalism, Brutalism, Neumorphism, Bento Grid 等
- **95 色彩方案**：按行业分类（SaaS, E-commerce, Healthcare, Fintech, Beauty）
- **56 字体配对**：Google Fonts 精选组合
- **24 图表类型**：Dashboard 和 Analytics 推荐
- **10 技术栈**：React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, HTML+Tailwind
- **98 UX 准则**：最佳实践、反模式、无障碍规则

### 1.2 工作流程
```bash
# 1. 产品类型分析 → 推荐样式
python3 search.py "SaaS healthcare" --domain product

# 2. 样式详细指南 → 颜色、效果、框架
python3 search.py "minimalism elegant" --domain style

# 3. 字体配对 → Google Fonts 导入
python3 search.py "professional modern" --domain typography

# 4. 色彩方案 → Primary, Secondary, CTA, Background
python3 search.py "saas" --domain color

# 5. 页面结构 → Hero, CTA, Testimonial
python3 search.py "hero-centric" --domain landing

# 6. UX 准则 → 动效、无障碍、Z-index
python3 search.py "animation accessibility" --domain ux

# 7. 技术栈指南 → Vue 特定最佳实践
python3 search.py "responsive" --stack vue
```

---

## 2. 核心设计原则（必须遵守）

### 2.1 图标与视觉元素

| 规则 | ✅ 正确做法 | ❌ 错误做法 |
|------|-----------|-----------|
| **禁用 Emoji 图标** | 使用 SVG 图标（Heroicons, Lucide） | 使用 🎨 🚀 ⚙️ 作为 UI 图标 |
| **稳定悬停状态** | 使用 color/opacity 过渡 | 使用 scale 变换导致布局偏移 |
| **正确品牌 Logo** | 从 Simple Icons 获取官方 SVG | 猜测或使用错误的 logo 路径 |
| **统一图标尺寸** | 固定 viewBox (24x24) + w-6 h-6 | 随机混合不同图标尺寸 |

### 2.2 交互与光标

| 规则 | ✅ 正确做法 | ❌ 错误做法 |
|------|-----------|-----------|
| **光标指针** | 所有可点击/悬停卡片添加 `cursor-pointer` | 交互元素使用默认光标 |
| **悬停反馈** | 提供视觉反馈（颜色、阴影、边框） | 无交互指示 |
| **平滑过渡** | 使用 `transition-colors duration-200` | 瞬间状态变化或过慢 (>500ms) |

### 2.3 明暗模式对比度

| 规则 | ✅ 正确做法 | ❌ 错误做法 |
|------|-----------|-----------|
| **玻璃卡片（浅色模式）** | 使用 `bg-white/80` 或更高透明度 | 使用 `bg-white/10`（过于透明） |
| **文本对比度（浅色）** | 使用 `#0F172A` (slate-900) | 使用 `#94A3B8` (slate-400) 作为正文 |
| **弱化文本（浅色）** | 最低使用 `#475569` (slate-600) | 使用 gray-400 或更浅 |
| **边框可见性** | 浅色模式使用 `border-gray-200` | 使用 `border-white/10`（不可见） |

### 2.4 布局与间距

| 规则 | ✅ 正确做法 | ❌ 错误做法 |
|------|-----------|-----------|
| **浮动导航栏** | 添加 `top-4 left-4 right-4` 间距 | 导航栏贴边 `top-0 left-0 right-0` |
| **内容内边距** | 考虑固定导航栏高度 | 内容被固定元素遮挡 |
| **统一最大宽度** | 使用相同 `max-w-6xl` 或 `max-w-7xl` | 混合不同容器宽度 |

---

## 3. 交付前检查清单

### 3.1 视觉质量
- [ ] 无 Emoji 作为图标（使用 SVG）
- [ ] 所有图标来自统一图标集（Heroicons/Lucide）
- [ ] 品牌 Logo 正确（从 Simple Icons 验证）
- [ ] 悬停状态不导致布局偏移
- [ ] 直接使用主题颜色（bg-primary），不用 var() 包装

### 3.2 交互
- [ ] 所有可点击元素有 `cursor-pointer`
- [ ] 悬停状态提供清晰视觉反馈
- [ ] 过渡流畅（150-300ms）
- [ ] 键盘导航焦点状态可见

### 3.3 明暗模式
- [ ] 浅色模式文本对比度充足（4.5:1 最低）
- [ ] 玻璃/透明元素在浅色模式下可见
- [ ] 两种模式边框均可见
- [ ] 交付前测试两种模式

### 3.4 布局
- [ ] 浮动元素与边缘有适当间距
- [ ] 无内容被固定导航栏遮挡
- [ ] 响应式（320px, 768px, 1024px, 1440px）
- [ ] 移动端无横向滚动

### 3.5 无障碍
- [ ] 所有图片有 alt 文本
- [ ] 表单输入有标签
- [ ] 颜色非唯一指示器
- [ ] 遵守 `prefers-reduced-motion`

---

## 4. 整合到 TokenDance UI 规范

### 4.1 更新色彩系统

**原 TokenDance 色彩（v1.1.0）**：
```css
--accent-primary: hsl(262 83% 58%);  /* #8b5cf6 */
```

**UI/UX Pro Max 建议**：
- 按行业选择色彩方案（SaaS = 蓝色系，Healthcare = 绿色系）
- TokenDance 作为通用 Agent 平台，保持蓝紫色调 ✅
- 新增色彩使用准则：
  ```css
  /* 浅色模式文本对比度 */
  --text-primary-light: #0F172A;   /* slate-900, 对比度 4.5:1+ */
  --text-secondary-light: #475569; /* slate-600, 弱化文本 */
  --text-tertiary-light: #64748B;  /* slate-500, 辅助信息 */
  
  /* 玻璃态组件 */
  --glass-bg-light: rgba(255, 255, 255, 0.8);  /* 浅色模式 */
  --glass-bg-dark: rgba(20, 20, 21, 0.8);      /* 深色模式 */
  ```

### 4.2 更新图标规范

**新增到 UI-Design.md**：
```markdown
## 图标系统

### 图标库选择
- **主图标库**：Lucide Icons (Vue 3 兼容)
- **品牌图标**：Simple Icons (官方 SVG)
- **禁止使用**：Emoji（🎨 🚀 ⚙️）作为 UI 图标

### 图标使用规范
```vue
<!-- ✅ 正确 -->
<Search class="w-6 h-6 text-gray-600" />

<!-- ❌ 错误 -->
<span>🔍</span>
```

### 图标尺寸规范
- **小图标**：w-4 h-4 (16px)
- **标准图标**：w-6 h-6 (24px)
- **大图标**：w-8 h-8 (32px)
- **特大图标**：w-12 h-12 (48px)
```

### 4.3 更新交互规范

**新增到 UI-Design.md § 7. 动效设计**：
```markdown
### 7.3 交互反馈准则（UI/UX Pro Max）

#### 光标状态
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

#### 悬停反馈
```vue
<!-- Card 悬停 -->
<div class="transition-all duration-200 hover:shadow-lg hover:border-accent-primary">
  <!-- 不使用 hover:scale-105 导致布局偏移 -->
</div>

<!-- Button 悬停 -->
<button class="transition-colors duration-200 hover:bg-accent-hover">
  Click Me
</button>
```

#### 过渡时长标准
- **快速**：150ms（按钮、链接）
- **标准**：200ms（卡片、下拉菜单）
- **慢速**：300ms（侧边栏、抽屉）
- **禁止**：>500ms（用户感知延迟）
```

### 4.4 更新布局规范

**新增到 UI-Design.md § 3. 页面布局**：
```markdown
### 3.4 浮动元素规范（UI/UX Pro Max）

#### 浮动导航栏
```vue
<!-- ✅ 正确：与边缘有间距 -->
<nav class="fixed top-4 left-4 right-4 z-50">
  <!-- 导航内容 -->
</nav>

<!-- ❌ 错误：贴边 -->
<nav class="fixed top-0 left-0 right-0 z-50">
  <!-- 导航内容 -->
</nav>
```

#### 内容区域
```vue
<!-- 为固定导航栏预留空间 -->
<main class="pt-24">  <!-- 导航栏高度 + 间距 -->
  <!-- 页面内容 -->
</main>
```

#### 容器宽度统一
```vue
<!-- 使用统一的最大宽度 -->
<div class="max-w-7xl mx-auto px-4">
  <!-- 页面内容 -->
</div>
```
```

### 4.5 新增字体配对参考

**新增到 UI-Design.md § 2.2 排版系统**：
```markdown
### 2.2.5 字体配对（UI/UX Pro Max 推荐）

#### TokenDance 官方配对
```css
/* 标题字体 */
--font-heading: 'Inter', -apple-system, sans-serif;
font-weight: 600-700;

/* 正文字体 */
--font-body: 'Inter', -apple-system, sans-serif;
font-weight: 400-500;

/* 代码字体 */
--font-code: 'JetBrains Mono', 'Fira Code', monospace;
```

#### 备选方案（专业风格）
```css
/* 方案 A: 现代专业 */
--font-heading: 'Poppins', sans-serif;  /* Google Fonts */
--font-body: 'Inter', sans-serif;

/* 方案 B: 优雅简约 */
--font-heading: 'Playfair Display', serif;
--font-body: 'Source Sans Pro', sans-serif;
```

**Google Fonts 导入**：
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```
```

---

## 5. TokenDance 特定规范扩展

### 5.1 Agent 可视化组件

**Agent Canvas（流程编排画布）**：
```vue
<!-- 节点卡片 -->
<div class="
  p-4 rounded-lg border-2
  cursor-pointer
  transition-all duration-200
  hover:shadow-lg hover:border-accent-primary
  bg-white/80 dark:bg-gray-800/80
">
  <!-- ✅ 使用 SVG 图标，不用 Emoji -->
  <BrainIcon class="w-6 h-6 text-accent-primary" />
  <span class="text-sm font-medium">Reasoning Node</span>
</div>
```

**Memory Timeline（记忆时间线）**：
```vue
<!-- 时间线节点 -->
<div class="
  flex items-center gap-3
  cursor-pointer
  transition-colors duration-200
  hover:bg-gray-100 dark:hover:bg-gray-800
  p-3 rounded-lg
">
  <!-- ✅ 图标统一尺寸 w-5 h-5 -->
  <ClockIcon class="w-5 h-5 text-gray-500" />
  <span class="text-sm text-gray-700 dark:text-gray-300">2 hours ago</span>
</div>
```

### 5.2 上下文可视化

**Token 使用统计**：
```vue
<!-- 进度条 -->
<div class="relative h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
  <!-- ✅ 平滑过渡，不突变 -->
  <div 
    class="absolute inset-y-0 left-0 bg-accent-primary transition-all duration-300"
    :style="{ width: `${tokenUsage}%` }"
  />
</div>
```

### 5.3 Sandbox/Browser 监控

**日志流**：
```vue
<!-- 日志卡片 -->
<div class="
  font-mono text-xs
  p-3 rounded-lg
  border border-gray-200 dark:border-gray-700
  bg-gray-50 dark:bg-gray-900
  hover:bg-gray-100 dark:hover:bg-gray-800
  transition-colors duration-200
">
  <!-- ✅ 代码字体 + 对比度充足 -->
  <span class="text-gray-900 dark:text-gray-100">$ npm install</span>
</div>
```

---

## 6. 实施计划

### Phase 1: 基础规范更新（Week 1）
- [x] 分析 UI/UX Pro Max Skill
- [ ] 更新 UI-Design.md（图标、交互、布局规范）
- [ ] 创建组件开发检查清单
- [ ] 更新色彩系统（浅色模式对比度）

### Phase 2: 组件库实现（Week 2-3）
- [ ] 基础组件遵守新规范（Button, Card, Input）
- [ ] Agent Canvas 组件（悬停反馈、无布局偏移）
- [ ] Memory Timeline 组件（统一图标、过渡流畅）
- [ ] Context Viewer 组件（对比度充足）

### Phase 3: 样式审查（Week 4）
- [ ] 检查所有组件（无 Emoji 图标）
- [ ] 测试明暗模式（对比度 4.5:1+）
- [ ] 响应式测试（320px - 1440px）
- [ ] 无障碍测试（键盘导航、屏幕阅读器）

---

## 7. 关键收益

### 7.1 专业性提升
- **统一视觉语言**：SVG 图标 + 统一尺寸 + 品牌一致性
- **流畅交互**：200ms 过渡 + 悬停反馈 + 光标指针
- **可访问性**：4.5:1 对比度 + 键盘导航 + 语义化 HTML

### 7.2 开发效率
- **检查清单驱动**：交付前 25 项检查点
- **明确规范**：禁止 Emoji、统一图标库、固定过渡时长
- **减少返工**：一次性做对，避免后期修改

### 7.3 用户体验
- **视觉一致性**：所有页面遵循相同设计语言
- **交互流畅**：无布局偏移、平滑过渡、即时反馈
- **跨平台兼容**：响应式布局 + 无障碍支持

---

## 8. 对比总结

| 维度 | TokenDance v1.1.0 | + UI/UX Pro Max |
|------|-------------------|----------------|
| **图标系统** | 未明确规范 | ✅ Lucide Icons，禁用 Emoji |
| **悬停反馈** | 基础定义 | ✅ 200ms 过渡，无布局偏移 |
| **对比度** | 基础色彩 | ✅ 4.5:1 最低，浅色模式优化 |
| **布局规范** | 基础结构 | ✅ 浮动元素间距，统一容器宽度 |
| **检查清单** | 无 | ✅ 25 项交付前检查 |
| **字体配对** | 单一 Inter | ✅ 多种备选方案 + Google Fonts |
| **技术栈指南** | 无 | ✅ Vue 特定最佳实践 |

---

## 9. 下一步行动

### 9.1 立即行动
1. ✅ 分析 UI/UX Pro Max Skill
2. 更新 `docs/design/UI-Design.md` 整合新规范
3. 创建 `docs/design/UI-Component-Checklist.md` 交付检查清单
4. 更新项目根目录 `CLAUDE.md` 添加 UI/UX 规范引用

### 9.2 后续工作
1. 实现组件库时遵守新规范
2. Code Review 使用检查清单
3. CI/CD 集成无障碍测试
4. 定期审查设计一致性

---

**文档版本**：v1.0
**最后更新**：2026-01-09
**参考来源**：[UI/UX Pro Max Skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
**TokenDance Team**
