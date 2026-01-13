# UI 组件交付检查清单

> TokenDance UI 组件开发规范 - 交付前必查
> Based on UI/UX Pro Max Best Practices
> Version: 1.0 | Last Updated: 2026-01-09

---

## 使用说明

**目标**：确保每个 UI 组件交付前符合专业标准，避免返工

**使用时机**：
- ✅ 组件开发完成后
- ✅ Code Review 前
- ✅ 提交 Pull Request 前
- ✅ 发布到生产环境前

**检查方式**：
```bash
# 每个组件对应一个检查清单
# 组件开发者自查 → Team Lead 复查 → QA 测试
```

---

## 1. 视觉质量 (5 项)

### 1.1 图标系统
- [ ] **无 Emoji 图标**
  ```vue
  <!-- ❌ 禁止 -->
  <span class="icon">🎨</span>
  <div>🚀 Launch</div>
  
  <!-- ✅ 正确 -->
  <PaletteIcon class="w-6 h-6" />
  <RocketIcon class="w-5 h-5" />
  ```

### 1.2 图标一致性
- [ ] **所有图标来自统一图标集**
  - 主图标库：Lucide Icons (Vue 3)
  - 品牌图标：Simple Icons (官方 SVG)
  ```vue
  <!-- ✅ 正确 -->
  import { Search, Bell, User } from 'lucide-vue-next'
  ```

### 1.3 品牌 Logo
- [ ] **品牌 Logo 正确无误**
  - 从 [Simple Icons](https://simpleicons.org/) 获取官方 SVG
  - 验证颜色和比例正确
  ```vue
  <!-- ✅ 正确 -->
  <svg role="img" viewBox="0 0 24 24">
    <path d="M23.546..." fill="#5865F2"/> <!-- Discord 官方色 -->
  </svg>
  ```

### 1.4 悬停稳定性
- [ ] **悬停状态不导致布局偏移**
  ```vue
  <!-- ❌ 禁止：导致布局偏移 -->
  <div class="hover:scale-105">Card</div>
  
  <!-- ✅ 正确：不影响布局 -->
  <div class="transition-colors hover:bg-gray-100">Card</div>
  <div class="transition-shadow hover:shadow-lg">Card</div>
  ```

### 1.5 主题颜色使用
- [ ] **直接使用主题颜色，不用 var() 包装**
  ```vue
  <!-- ❌ 避免 -->
  <div :style="{ backgroundColor: 'var(--accent-primary)' }">
  
  <!-- ✅ 正确 -->
  <div class="bg-accent-primary">
  ```

---

## 2. 交互反馈 (4 项)

### 2.1 光标状态
- [ ] **所有可点击元素有 cursor-pointer**
  ```vue
  <!-- ✅ 正确 -->
  <button class="cursor-pointer">Click</button>
  <div @click="handleClick" class="cursor-pointer">Card</div>
  <a href="#" class="cursor-pointer">Link</a>
  ```

### 2.2 悬停反馈
- [ ] **悬停状态提供清晰视觉反馈**
  ```vue
  <!-- ✅ 正确：至少一种反馈 -->
  <button class="hover:bg-accent-hover">Color</button>
  <div class="hover:shadow-lg">Shadow</div>
  <a class="hover:border-accent-primary">Border</a>
  ```

### 2.3 过渡流畅
- [ ] **过渡时长符合标准（150-300ms）**
  ```vue
  <!-- ✅ 正确 -->
  <button class="transition-colors duration-200">Fast</button>
  <div class="transition-all duration-200">Standard</div>
  <aside class="transition-transform duration-300">Slow</aside>
  
  <!-- ❌ 禁止 -->
  <div class="transition-all duration-1000">Too Slow</div>
  ```

### 2.4 键盘导航
- [ ] **焦点状态可见（键盘导航）**
  ```vue
  <!-- ✅ 正确 -->
  <button class="focus:outline-none focus:ring-2 focus:ring-accent-primary">
    Submit
  </button>
  ```

---

## 3. 明暗模式 (4 项)

### 3.1 文本对比度
- [ ] **浅色模式文本对比度充足（4.5:1 最低）**
  ```css
  /* ✅ 正确 */
  --text-primary-light: #0F172A;   /* slate-900, 对比度 15.8:1 */
  --text-secondary-light: #475569; /* slate-600, 对比度 7.1:1 */
  
  /* ❌ 禁止 */
  --text-primary-light: #94A3B8;   /* slate-400, 对比度 3.2:1 */
  ```

### 3.2 玻璃态组件
- [ ] **玻璃/透明元素在浅色模式下可见**
  ```vue
  <!-- ✅ 正确：浅色模式足够不透明 -->
  <div class="bg-white/80 dark:bg-gray-800/80">
    Glass Card
  </div>
  
  <!-- ❌ 禁止：浅色模式过于透明 -->
  <div class="bg-white/10 dark:bg-gray-800/80">
    Invisible Card
  </div>
  ```

### 3.3 边框可见性
- [ ] **两种模式边框均可见**
  ```vue
  <!-- ✅ 正确 -->
  <div class="border border-gray-200 dark:border-gray-700">
    Card
  </div>
  
  <!-- ❌ 禁止：浅色模式不可见 -->
  <div class="border border-white/10 dark:border-gray-700">
    Card
  </div>
  ```

### 3.4 模式测试
- [ ] **交付前测试两种模式**
  - 浅色模式所有元素可见
  - 深色模式所有元素可见
  - 切换无闪烁或布局跳动

---

## 4. 布局规范 (4 项)

### 4.1 浮动元素间距
- [ ] **浮动元素与边缘有适当间距**
  ```vue
  <!-- ✅ 正确：浮动导航栏 -->
  <nav class="fixed top-4 left-4 right-4 z-50">
    <!-- 导航内容 -->
  </nav>
  
  <!-- ❌ 禁止：贴边 -->
  <nav class="fixed top-0 left-0 right-0 z-50">
    <!-- 导航内容 -->
  </nav>
  ```

### 4.2 固定元素遮挡
- [ ] **无内容被固定导航栏遮挡**
  ```vue
  <!-- ✅ 正确：预留导航栏高度 -->
  <nav class="fixed top-4 left-4 right-4 h-16"></nav>
  <main class="pt-24">  <!-- 16 + 4*2 + padding -->
    Content
  </main>
  ```

### 4.3 响应式断点
- [ ] **响应式测试通过（320px, 768px, 1024px, 1440px）**
  - 320px：iPhone SE
  - 768px：iPad 竖屏
  - 1024px：iPad 横屏
  - 1440px：桌面

### 4.4 横向滚动
- [ ] **移动端无横向滚动**
  ```vue
  <!-- ✅ 正确：响应式容器 -->
  <div class="max-w-full overflow-hidden px-4">
    Content
  </div>
  ```

---

## 5. 无障碍 (4 项)

### 5.1 图片替代文本
- [ ] **所有图片有 alt 文本**
  ```vue
  <!-- ✅ 正确 -->
  <img src="logo.png" alt="TokenDance Logo" />
  
  <!-- ❌ 禁止 -->
  <img src="logo.png" />
  ```

### 5.2 表单标签
- [ ] **表单输入有标签**
  ```vue
  <!-- ✅ 正确 -->
  <label for="email">Email</label>
  <input id="email" type="email" />
  
  <!-- ❌ 禁止 -->
  <input type="email" placeholder="Email" />
  ```

### 5.3 颜色指示器
- [ ] **颜色非唯一指示器**
  ```vue
  <!-- ✅ 正确：颜色 + 图标 + 文字 -->
  <div class="text-red-600">
    <XCircleIcon class="w-5 h-5" />
    <span>Error: Invalid input</span>
  </div>
  
  <!-- ❌ 禁止：仅颜色 -->
  <div class="text-red-600">Invalid</div>
  ```

### 5.4 动效控制
- [ ] **遵守 prefers-reduced-motion**
  ```css
  /* ✅ 正确 */
  .animated {
    transition: all 200ms;
  }
  
  @media (prefers-reduced-motion: reduce) {
    .animated {
      transition: none;
    }
  }
  ```

---

## 6. 图标规范 (3 项)

### 6.1 图标尺寸
- [ ] **图标尺寸符合规范**
  ```vue
  <!-- ✅ 正确 -->
  <SearchIcon class="w-4 h-4" />  <!-- 小图标 16px -->
  <BellIcon class="w-6 h-6" />    <!-- 标准图标 24px -->
  <UserIcon class="w-8 h-8" />    <!-- 大图标 32px -->
  <LogoIcon class="w-12 h-12" />  <!-- 特大图标 48px -->
  ```

### 6.2 图标颜色
- [ ] **图标颜色语义正确**
  ```vue
  <!-- ✅ 正确 -->
  <CheckIcon class="w-5 h-5 text-green-600" />  <!-- 成功 -->
  <XIcon class="w-5 h-5 text-red-600" />        <!-- 错误 -->
  <AlertIcon class="w-5 h-5 text-yellow-600" /> <!-- 警告 -->
  ```

### 6.3 图标可访问性
- [ ] **图标有语义化说明**
  ```vue
  <!-- ✅ 正确 -->
  <button aria-label="Search">
    <SearchIcon class="w-5 h-5" />
  </button>
  ```

---

## 7. 性能优化 (2 项)

### 7.1 图片优化
- [ ] **图片懒加载（非首屏）**
  ```vue
  <!-- ✅ 正确 -->
  <img src="hero.jpg" loading="eager" />  <!-- 首屏 -->
  <img src="feature.jpg" loading="lazy" /> <!-- 非首屏 -->
  ```

### 7.2 防抖节流
- [ ] **输入框/滚动事件防抖节流**
  ```vue
  <script setup>
  import { useDebounceFn } from '@vueuse/core'
  
  const handleSearch = useDebounceFn((value) => {
    // 搜索逻辑
  }, 300)
  </script>
  ```

---

## 8. TokenDance 特定 (3 项)

### 8.1 Agent 节点
- [ ] **Agent Canvas 节点符合规范**
  - 使用 SVG 图标（BrainIcon, ToolIcon）
  - 悬停反馈清晰
  - 无布局偏移

### 8.2 记忆时间线
- [ ] **Memory Timeline 节点符合规范**
  - 图标统一尺寸 w-5 h-5
  - 时间戳格式一致
  - 过渡流畅 200ms

### 8.3 上下文可视化
- [ ] **Context Viewer 符合规范**
  - Token 使用进度条平滑过渡
  - 代码字体使用 font-mono
  - 对比度充足（4.5:1+）

---

## 检查清单总结

**25 项必查**：

| 类别 | 项数 | 重点 |
|------|------|------|
| 视觉质量 | 5 | 无 Emoji、统一图标、Logo 正确 |
| 交互反馈 | 4 | cursor-pointer、200ms 过渡 |
| 明暗模式 | 4 | 对比度 4.5:1+、边框可见 |
| 布局规范 | 4 | 浮动间距、响应式、无遮挡 |
| 无障碍 | 4 | alt 文本、标签、颜色+文字 |
| 图标规范 | 3 | 尺寸统一、颜色语义、aria-label |
| 性能优化 | 2 | 懒加载、防抖节流 |
| TokenDance | 3 | Agent 节点、Memory 时间线 |

---

## 使用流程

### Step 1: 自查（开发者）
```bash
# 组件开发完成后
1. 打开本检查清单
2. 逐项检查所有 25 项
3. 所有 [ ] 变为 [x] 后提交代码
```

### Step 2: 复查（Team Lead）
```bash
# Code Review 时
1. 验证开发者已完成自查
2. 重点检查视觉质量和交互反馈
3. 明暗模式切换测试
```

### Step 3: 测试（QA）
```bash
# 提交测试时
1. 响应式测试（4 个断点）
2. 无障碍测试（键盘导航、屏幕阅读器）
3. 性能测试（Lighthouse）
```

---

## 常见错误参考

### ❌ 错误示例 1：使用 Emoji
```vue
<button>
  🚀 Launch  <!-- ❌ 禁止 -->
</button>
```

### ✅ 正确做法
```vue
<button class="flex items-center gap-2">
  <RocketIcon class="w-5 h-5" />
  <span>Launch</span>
</button>
```

---

### ❌ 错误示例 2：悬停导致布局偏移
```vue
<div class="hover:scale-105">  <!-- ❌ 布局偏移 -->
  Card
</div>
```

### ✅ 正确做法
```vue
<div class="transition-shadow hover:shadow-lg">
  Card
</div>
```

---

### ❌ 错误示例 3：浅色模式对比度不足
```css
/* ❌ 对比度 3.2:1 */
.text-light {
  color: #94A3B8;  /* slate-400 */
}
```

### ✅ 正确做法
```css
/* ✅ 对比度 7.1:1 */
.text-light {
  color: #475569;  /* slate-600 */
}
```

---

## 工具推荐

### 对比度检查
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Chrome DevTools: Lighthouse (Accessibility)

### 图标库
- [Lucide Icons](https://lucide.dev/)
- [Simple Icons](https://simpleicons.org/)

### 响应式测试
- Chrome DevTools: Device Toolbar
- [Responsively App](https://responsively.app/)

### 无障碍测试
- [axe DevTools](https://www.deque.com/axe/devtools/)
- Chrome DevTools: Lighthouse

---

**版本**：v1.0
**最后更新**：2026-01-09
**参考来源**：UI/UX Pro Max Skill
**维护者**：TokenDance Team
