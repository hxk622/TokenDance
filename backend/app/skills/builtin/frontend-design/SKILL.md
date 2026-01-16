---
name: frontend-design
description: 创建独特、生产级前端界面，避免 AI 味。用于构建 Web 组件、页面或应用，生成精致、有创意的代码。
author: Anthropic (adapted for TokenDance)
version: 1.0.0
license: MIT
tags: [frontend, design, ui, aesthetics, production]
---

# Frontend Design Skill

这个 skill 指导创建独特、生产级的前端界面，避免千篇一律的"AI 生成感"。实现精致、具有卓越审美细节和创意选择的真实可运行代码。

用户提供前端需求：组件、页面、应用或界面。可能包含目的、受众或技术约束的上下文。

## 设计思维

**编码前，理解上下文并承诺一个大胆的审美方向：**

- **目的**：这个界面解决什么问题？谁在使用？
- **基调**：选择极端风格 
  - 极简主义 (brutally minimal)
  - 最大主义混沌 (maximalist chaos)
  - 复古未来 (retro-futuristic)
  - 有机自然 (organic/natural)
  - 奢华精致 (luxury/refined)
  - 俏皮玩具 (playful/toy-like)
  - 编辑杂志 (editorial/magazine)
  - 粗野主义 (brutalist/raw)
  - 装饰艺术 (art deco/geometric)
  - 柔和粉彩 (soft/pastel)
  - 工业实用 (industrial/utilitarian)
  
  这些只是灵感，设计一个真正符合审美方向的独特风格。

- **约束**：技术要求（框架、性能、无障碍）
- **差异化**：什么让这个界面**难以忘怀**？用户会记住的一件事是什么？

**关键**：选择明确的概念方向并精准执行。大胆的最大主义和精致的极简主义都可以——关键是**意图性**，而非强度。

然后实现可运行的代码（HTML/CSS/JS, React, Vue 等）：
- 生产级且功能完整
- 视觉震撼且令人难忘
- 具有清晰审美观点的连贯性
- 在每个细节上精雕细琢

## 前端美学指南

### 核心原则

#### 1. 字体排版 (Typography)
- **选择美丽、独特、有趣的字体**
- **禁止**：Arial, Inter, Roboto, 系统默认字体
- **推荐**：配对一个独特的展示字体 + 精致的正文字体
- **示例**：
  - Display: Clash Display, Cabinet Grotesk, Sohne, Fraunces
  - Body: Söhne, ABC Diatype, Suisse Int'l, GT America

#### 2. 色彩与主题 (Color & Theme)
- **承诺一个连贯的审美**
- 使用 CSS 变量保持一致性
- **主导色 + 锐利的强调色** > 平庸的均匀调色板
- **禁止**：紫色渐变 + 白色背景（AI 陈词滥调）
- **推荐**：
  - 大胆对比：深色背景 + 霓虹强调
  - 极简精致：灰度系统 + 单一强调色
  - 温暖有机：土色调 + 天然质感

#### 3. 动效 (Motion)
- **用于效果和微交互的动画**
- HTML 优先使用 CSS-only 方案
- React 可用时使用 Framer Motion
- **重点关注高影响力时刻**：
  - 一个精心编排的页面加载（带交错显示 `animation-delay`）
  - > 分散的微交互
- 使用滚动触发和令人惊喜的悬停状态

#### 4. 空间构成 (Spatial Composition)
- **意外的布局**
- 不对称
- 重叠
- 对角线流动
- 打破网格的元素
- 慷慨的负空间 **或** 受控的密度

#### 5. 背景与视觉细节 (Backgrounds & Visual Details)
**创造氛围和深度，而非默认纯色**

添加符合整体美学的上下文效果和纹理：
- 渐变网格 (gradient meshes)
- 噪点纹理 (noise textures)
- 几何图案 (geometric patterns)
- 分层透明度 (layered transparencies)
- 戏剧性阴影 (dramatic shadows)
- 装饰边框 (decorative borders)
- 自定义光标 (custom cursors)
- 颗粒叠加 (grain overlays)

## 绝对禁止的 AI 味

**永远不要使用**这些通用 AI 生成美学：

❌ **字体**：Inter, Roboto, Arial, 系统字体
❌ **配色**：紫色渐变 + 白色背景
❌ **布局**：可预测的组件模式
❌ **设计**：缺乏上下文特色的千篇一律

## 创意解读原则

- **创造性解读，做出意外选择**，感觉是真正为上下文设计的
- **没有设计应该相同**
- 在浅色/深色主题、不同字体、不同美学之间变化
- **永远不要**在多次生成中收敛到常见选择（例如 Space Grotesk）

## 实现复杂度匹配

**重要**：实现复杂度要匹配审美愿景

- **最大主义设计** → 需要精细代码 + 广泛动画 + 效果
- **极简/精致设计** → 需要克制、精确、细心关注间距/排版/微妙细节
- **优雅来自于很好地执行愿景**

## TokenDance 特定指导

在 TokenDance 项目中使用时：

1. **遵守 WARP.md 规范** - 避免 AI 味是核心原则
2. **参考 UI-UX-Pro-Max-Integration.md** - 57 UI 样式 + 95 色彩方案
3. **使用 Heroicons/Lucide** - 禁用 Emoji
4. **对比度标准**: 4.5:1 最低
5. **过渡时间**: 200ms (卡片) / 300ms (节点)
6. **灰度为主**: #fafafa / #f1f5f9 背景

## 记住

Claude 能够创造非凡的创意作品。**不要退缩，展示当跳出思维定式并全力投入独特愿景时真正能够创造的东西。**
