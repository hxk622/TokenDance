# TokenDance 前端设计原则

> **整合 Anthropic Frontend Design Skill + UI/UX Pro Max**
> Created: 2026-01-16
> Version: 2.0.0

---

## 核心哲学：避免 AI 味

TokenDance 的 UI 必须：
- **有强烈的审美观点** - 不是中庸的"安全选择"
- **上下文驱动** - 每个页面都应该感觉是为其特定目的定制的
- **令人难忘** - 用户应该记住某个独特的设计元素
- **专业生产级** - 不是原型，而是完成品

---

## 一、设计思维流程

### 1.1 开始任何 UI 工作前的三个问题

| 问题 | 目的 | 示例 |
|------|------|------|
| **这解决什么问题？** | 理解上下文 | "Deep Research 执行页需要让用户感觉可控，而非被动等待" |
| **用户会记住什么？** | 定义差异化 | "三位一体的色球动画" / "能量连线流光效果" |
| **审美基调是什么？** | 承诺风格方向 | "工业实用 + 赛博朋克" / "极简精致 + 日式禅意" |

### 1.2 审美基调选择（11 种风格方向）

> **原则**：选择**极端**，不是中庸。大胆最大主义和精致极简主义都可以——关键是**意图性**。

| 风格 | 特征 | TokenDance 适用场景 |
|------|------|---------------------|
| **极简主义** (Brutally Minimal) | 大量留白、单色调、克制 | Settings 页面、Login |
| **最大主义混沌** (Maximalist Chaos) | 密集信息、重叠元素、视觉张力 | Dashboard 总览 |
| **复古未来** (Retro-Futuristic) | 80s/90s 美学、霓虹色、CRT 效果 | Demo 页面 |
| **有机自然** (Organic/Natural) | 圆角、土色调、柔和阴影 | 用户引导流程 |
| **奢华精致** (Luxury/Refined) | 金色点缀、衬线字体、精细细节 | Premium 功能页 |
| **俏皮玩具** (Playful/Toy-like) | 明亮色彩、圆润形状、弹跳动画 | Onboarding |
| **编辑杂志** (Editorial/Magazine) | 强烈排版、网格系统、对比 | Blog / 文档 |
| **粗野主义** (Brutalist/Raw) | 裸露结构、等宽字体、锐利边缘 | Admin 工具 |
| **装饰艺术** (Art Deco/Geometric) | 对称几何、金属质感、强烈轮廓 | Landing Page Hero |
| **柔和粉彩** (Soft/Pastel) | 低饱和度、柔和渐变、轻盈 | Error 页面 |
| **工业实用** (Industrial/Utilitarian) | 灰度、功能优先、栅格系统 | 执行页（当前） |

**TokenDance 当前选择**：**工业实用 + 赛博朋克元素**（灰度主体 + 霓虹强调色）

---

## 二、五大美学支柱

### 2.1 字体排版（Typography）

#### 禁止使用
❌ Inter（AI 默认）
❌ Roboto（过于通用）
❌ Arial（缺乏个性）
❌ 系统默认字体

#### 推荐配对

| 用途 | Display Font | Body Font | Google Fonts 导入 |
|------|--------------|-----------|-------------------|
| **科技前沿** | Clash Display | Söhne | `@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');` |
| **专业精致** | Cabinet Grotesk | ABC Diatype | - |
| **编辑风格** | Fraunces | Suisse Int'l | `@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;600;900&display=swap');` |
| **现代简约** | Sohne | GT America | - |

**TokenDance 当前**：
- Display: `font-family: 'Space Grotesk', sans-serif;` (H1, H2)
- Body: 系统字体栈 `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`
- Mono: `'SF Mono', Monaco, monospace` (代码块)

#### 排版规范

```css
/* 标题层级 */
h1 { font-size: 2.5rem; font-weight: 700; line-height: 1.2; }
h2 { font-size: 2rem; font-weight: 600; line-height: 1.3; }
h3 { font-size: 1.5rem; font-weight: 600; line-height: 1.4; }

/* 正文 */
body { font-size: 1rem; line-height: 1.6; }
small { font-size: 0.875rem; line-height: 1.5; }

/* 行间距黄金比例 */
p { margin-bottom: 1.5em; }
```

---

### 2.2 色彩与主题（Color & Theme）

#### 核心原则
**主导色 + 锐利强调色** > 平庸的均匀调色板

#### 禁止的 AI 陈词滥调
❌ 紫色渐变 + 白色背景
❌ 蓝紫粉三色过渡
❌ 所有颜色平均分配

#### TokenDance 色彩系统

```css
:root {
  /* 主色调：灰度工业 */
  --bg-primary: #fafafa;
  --bg-secondary: #f1f5f9;
  --text-primary: #111827;
  --text-secondary: #6b7280;
  
  /* 强调色：赛博朋克霓虹 */
  --accent-cyan: #00D9FF;     /* Manus 节点 */
  --accent-green: #00FF88;    /* Coworker 节点 */
  --accent-amber: #FFB800;    /* 警告/HITL */
  --accent-red: #FF3B30;      /* 错误 */
  
  /* 功能色 */
  --status-active: #00D9FF;
  --status-success: #00FF88;
  --status-pending: #FFB800;
  --status-error: #FF3B30;
  --status-inactive: #8E8E93;
}
```

#### 对比度标准
- **正文**: 4.5:1 最低（WCAG AA）
- **大文本**: 3:1 最低
- **浅色模式文本**: `#111827` (gray-900)
- **弱化文本**: `#6b7280` (gray-500)

#### 色彩使用示例

```vue
<!-- ✅ 正确：主导色 + 强调 -->
<div class="bg-white border-gray-100">
  <h2 class="text-gray-900">标题</h2>
  <p class="text-gray-600">正文</p>
  <button class="bg-cyan-500 text-black">CTA</button>
</div>

<!-- ❌ 错误：颜色过于分散 -->
<div class="bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400">
  ...
</div>
```

---

### 2.3 动效（Motion）

#### 核心原则
**一个精心编排的页面加载** > 分散的微交互

#### 过渡时间标准

| 元素类型 | 时长 | 缓动函数 |
|---------|------|----------|
| **卡片 hover** | 200ms | `ease-out` |
| **节点动画** | 300ms | `cubic-bezier(0.34, 1.56, 0.64, 1)` |
| **页面过渡** | 400ms | `ease-in-out` |
| **Modal 出现** | 150ms | `ease-out` |

#### 高影响力动画示例

```css
/* 页面加载：交错显示 */
.card:nth-child(1) { animation: fadeInUp 600ms ease-out 100ms backwards; }
.card:nth-child(2) { animation: fadeInUp 600ms ease-out 200ms backwards; }
.card:nth-child(3) { animation: fadeInUp 600ms ease-out 300ms backwards; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 能量连线流光 */
.edge-active {
  stroke-dasharray: 10 5;
  animation: flow-energy 1s linear infinite;
}

@keyframes flow-energy {
  from { stroke-dashoffset: 0; }
  to { stroke-dashoffset: -30; }
}
```

#### 禁止导致布局偏移

```css
/* ❌ 错误：scale 导致布局偏移 */
.card:hover {
  transform: scale(1.05);
}

/* ✅ 正确：使用 shadow + opacity */
.card {
  transition: box-shadow 200ms ease-out;
}
.card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}
```

---

### 2.4 空间构成（Spatial Composition）

#### 核心技巧
- **不对称** - 打破左右对称
- **重叠** - Z-index 层次
- **对角线流动** - 45° 倾斜元素
- **打破网格** - 部分元素溢出容器
- **负空间** - 慷慨留白 OR 受控密度

#### TokenDance 示例

```vue
<!-- 首页 Hero：不对称布局 -->
<section class="grid grid-cols-1 lg:grid-cols-12 gap-8">
  <div class="lg:col-span-7">
    <!-- 文案：占 7 列 -->
  </div>
  <div class="lg:col-span-5">
    <!-- Trinity 可视化：占 5 列 -->
  </div>
</section>

<!-- 执行页：重叠的 Browser PiP -->
<div class="fixed bottom-4 right-4 z-50">
  <BrowserPip /> <!-- 浮在其他元素之上 -->
</div>
```

---

### 2.5 背景与视觉细节（Backgrounds & Details）

#### 创造氛围，而非纯色

```css
/* 渐变网格（首页背景） */
.bg-vibe {
  background: 
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.08), transparent),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(139, 92, 246, 0.05), transparent);
}

/* 噪点纹理 */
.bg-pattern {
  background-image: 
    linear-gradient(to right, #000 1px, transparent 1px),
    linear-gradient(to bottom, #000 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.02;
}

/* 玻璃态毛玻璃 */
.glass {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

---

## 三、绝对禁止的 AI 味

### 3.1 视觉陈词滥调

| 类别 | ❌ 禁止 | ✅ 替代 |
|------|---------|---------|
| **字体** | Inter, Roboto, Arial | Space Grotesk, Cabinet Grotesk |
| **配色** | 紫色渐变 + 白背景 | 灰度 + 霓虹强调 |
| **图标** | Emoji (🎨 🚀 ⚙️) | Heroicons / Lucide SVG |
| **布局** | 卡片 + 卡片 + 卡片 | 不对称、重叠、打破网格 |
| **动画** | 所有元素 scale(1.05) | 精心编排的交错显示 |

### 3.2 文案陈词滥调

| ❌ AI 味 | ✅ 人性化 |
|---------|-----------|
| "我能帮你..." | "你的智能工作台" |
| "让 AI 帮你..." | "和 Agent 一起完成任务" |
| "AI 助手" | "执行大脑 Manus" |
| "生成" / "创建" | "撰写" / "研究" / "整理" |

---

## 四、TokenDance 特定规范

### 4.1 三栏布局原则

参考 `Three-Column-Layout.md`：

| 区域 | 宽度 | 用途 | 交互 |
|------|------|------|------|
| **左栏** | 45% | 工作流图 + 日志 | 垂直 divider 拖拽 |
| **中栏** | - | 垂直分隔条 | 拖拽调整左右比例 |
| **右栏** | 55% | 成果预览 | Tab 切换 |

### 4.2 去 AI 味检查清单

**视觉**
- [ ] 无 Emoji 图标
- [ ] 图标来自 Heroicons/Lucide
- [ ] 字体非 Inter/Roboto
- [ ] 配色非紫色渐变

**交互**
- [ ] 所有可点击元素有 `cursor-pointer`
- [ ] hover 不导致布局偏移
- [ ] 过渡时间 150-300ms
- [ ] 关键动画有交错 `animation-delay`

**文案**
- [ ] 无"AI 助手"类表述
- [ ] 强调用户主动性（"接管" / "干预"）
- [ ] 任务导向（"撰写报告" vs "生成报告"）

### 4.3 Footer Slogan 规范

```vue
<footer>
  <p>随时接管 · 实时干预 · 沉淀复用</p>
</footer>
```

**原则**：
- **接管** - Controllability
- **干预** - Transparency  
- **复用** - Persistence

---

## 五、实现复杂度匹配

### 5.1 最大主义设计 → 复杂实现

**特征**：密集信息、多层次、丰富动画
**示例**：Dashboard 总览页

```vue
<template>
  <!-- 多层背景 -->
  <div class="relative">
    <div class="absolute inset-0 bg-gradient-mesh"></div>
    <div class="absolute inset-0 bg-noise-texture"></div>
    
    <!-- 动态元素 -->
    <div class="orb-container">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>
    
    <!-- 内容 -->
    <main class="relative z-10">
      <!-- 交错显示的卡片 -->
      <div v-for="(card, i) in cards" 
           :style="{ animationDelay: `${i * 100}ms` }"
           class="card fade-in">
        ...
      </div>
    </main>
  </div>
</template>

<style>
/* 多个 @keyframes */
@keyframes orb-float { ... }
@keyframes fade-in { ... }
@keyframes pulse { ... }
</style>
```

### 5.2 极简设计 → 精确实现

**特征**：大量留白、单色调、克制
**示例**：Settings 页面

```vue
<template>
  <div class="max-w-2xl mx-auto py-24">
    <!-- 精确的间距 -->
    <h1 class="mb-12">Settings</h1>
    
    <!-- 细微的边框 -->
    <div class="space-y-8">
      <div class="border-b border-gray-100 pb-8">
        <label class="text-sm text-gray-600 mb-2">Account</label>
        <input class="w-full border-none bg-transparent text-lg" />
      </div>
    </div>
  </div>
</template>

<style>
/* 克制的 hover */
input:focus {
  outline: none;
  border-bottom: 1px solid #111827;
}
</style>
```

---

## 六、参考资源

| 资源 | 用途 | 链接 |
|------|------|------|
| **Anthropic Frontend Design** | 避免 AI 味的核心原则 | `backend/app/skills/builtin/frontend-design/SKILL.md` |
| **UI/UX Pro Max Integration** | 57 UI 样式 + 95 色彩方案 | `docs/ux/UI-UX-Pro-Max-Integration.md` |
| **Three Column Layout** | TokenDance 执行页布局 | `docs/ux/Three-Column-Layout.md` |
| **WARP.md** | 项目规范（去 AI 味是核心） | `WARP.md` |

---

## 记住

> Claude 能够创造非凡的创意作品。**不要退缩，展示当跳出思维定式并全力投入独特愿景时真正能够创造的东西。**

**优雅来自于很好地执行愿景。**
