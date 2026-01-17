# TokenDance 前端设计规范检查报告

**审查日期**: 2026-01-17  
**审查范围**: 整个前端工程  
**参考规范**: docs/ux/{DESIGN-PRINCIPLES.md, DESIGN-SYSTEM.md, EXECUTION-PAGE-LAYOUT.md}

---

## 执行摘要

对 TokenDance 前端工程的全面审查发现了 **多个关键设计规范违规问题**，主要集中在：

1. ❌ **Emoji 图标滥用** - 17 个文件中发现 Emoji 用作 UI 图标
2. ❌ **"AI 味"文案** - 多处使用"生成"、"AI助手"等违规文案
3. ⚠️ **色彩系统不统一** - 部分组件未使用设计系统变量
4. ✅ **LoginView/RegisterView 已完全符合规范** - 作为标杆示例

---

## 📊 违规统计

| 类别 | 违规数量 | 严重程度 | 优先级 |
|------|---------|---------|--------|
| Emoji 图标 | 17 文件 | 🔴 高 | P0 |
| AI 味文案 | 15+ 处 | 🔴 高 | P0 |
| 色彩系统 | 未统计 | 🟡 中 | P1 |
| 字体规范 | 未统计 | 🟢 低 | P2 |

---

## 🔴 P0 关键问题（必须立即修复）

### 1. Emoji 图标滥用

**违规原则**: DESIGN-PRINCIPLES.md § 2.1 - "禁止使用 Emoji 作为 UI 图标"

**违规文件列表**:

#### 高频违规（核心页面）
- `views/SkillDiscovery.vue` (19-26行)
  ```typescript
  // ❌ 错误
  const categoryIcons: Record<string, string> = {
    research: '🔍',
    writing: '✍️',
    data: '📊',
    visualization: '📈',
    coding: '💻',
    document: '📄',
    other: '📦'
  }
  ```
  **修复建议**: 使用 Lucide Icons 替代
  ```typescript
  // ✅ 正确
  import { Search, PenTool, Database, BarChart, Code, FileText, Package } from 'lucide-vue-next'
  
  const categoryIcons = {
    research: Search,
    writing: PenTool,
    data: Database,
    visualization: BarChart,
    coding: Code,
    document: FileText,
    other: Package
  }
  ```

- `views/PPTEditView.vue` (72, 81行)
  - 使用 Emoji 表示 PPT 状态图标

- `views/PPTGenerateView.vue` (189, 191行)
  - 场景卡片使用 Emoji

#### 其他违规文件
- `components/execution/artifact/ArtifactTabs.vue` (30-32行)
- `components/execution/artifact/LiveDiff.vue` (237行)
- `components/financial/KeyPointsCard.vue` (35行)
- `components/financial/TechnicalAnalysisCard.vue` (4行)
- `components/financial/SentimentDashboard.vue` (31, 136行)
- `components/financial/FinancialAnalysisCard.vue` (4行)
- `components/financial/ComparisonCard.vue` (36行)
- `components/financial/CombinedChart.vue` (36行)
- `components/home/TeamActivity.vue` (33, 61-64行)
- `components/skills/TemplateCard.vue` (32-37行)
- `components/execution/workflow/WorkflowGraph.vue` (274, 277行)
- `views/FinancialAnalysis.vue` (61行)

---

### 2. "AI 味"文案违规

**违规原则**: DESIGN-PRINCIPLES.md § 2.2 - "避免 'AI 助手'、'生成' 等表述"

**违规示例**:

#### 高频违规词汇
```typescript
// ❌ 错误表述
"生成 PPT"
"AI 生成报告" 
"生成内容"
"AI 助手"

// ✅ 正确表述
"撰写 PPT"
"研究报告"
"整理内容"
"执行大脑 Manus"
```

#### 违规文件详情

1. **PPTGenerateView.vue** (3, 10, 165, 238行)
   - 标题: "PPT生成"
   - **修复**: 改为 "PPT 撰写" 或 "演示汇报"

2. **DemoView.vue** (22, 62, 174行)
   - 多处使用"生成"动词

3. **ExecutionPage.vue** (492行)
   - 状态提示文案

4. **ResearchCompletionCard.vue** (10, 115, 240, 244行)
   - 研究完成提示文案

5. **其他文件**:
   - `PreviewArea.vue` (69, 75行)
   - `ThinkingChain.vue` (128行)
   - `GlobalExecution.vue` (23行)
   - `workflow/StreamingInfo.vue` (25行)

**批量修复建议**:
```bash
# 全局替换
生成 PPT → 撰写 PPT
生成报告 → 研究报告
AI 生成 → 整理 / 撰写 / 研究
AI 助手 → 执行大脑 / Manus / Coworker
```

---

## 🟡 P1 重要问题（应尽快修复）

### 3. 色彩系统不统一

**问题描述**: 部分组件硬编码颜色值，未使用设计系统 CSS 变量

**违规示例**:

```vue
<!-- ❌ 错误：硬编码颜色 -->
<div style="background: #6366f1; color: #ffffff">

<!-- ✅ 正确：使用设计系统变量 -->
<div style="background: var(--accent-primary); color: var(--text-primary)">
```

**待检查文件**:
- 所有 `.vue` 文件的 `<style>` 标签
- 内联样式
- Tailwind 类名（需确保使用主题变量）

**修复方案**:
1. 创建全局 CSS 变量文件 `src/assets/design-system.css`
2. 在 `main.ts` 中导入
3. 逐个组件替换硬编码颜色

---

### 4. 图标库不统一

**问题描述**: 混用多种图标库

**发现的图标库**:
- ✅ Heroicons (正确)
- ✅ Lucide Icons (正确)
- ❌ Emoji (错误)
- ⚠️ 自定义 SVG (需审查)

**规范要求**:
- 主图标库: Lucide Icons (Vue 3)
- 辅助: Heroicons (用于 UI 操作)
- 品牌图标: Simple Icons

**修复任务**:
1. 统一导入 `lucide-vue-next`
2. 替换所有 Emoji 为 Lucide Icons
3. 审查自定义 SVG，确保与设计系统一致

---

## 🟢 P2 优化建议（可后续优化）

### 5. 字体规范

**当前状态**: 部分一致，但未全局统一

**设计系统要求**:
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-display: 'Space Grotesk', sans-serif; /* 标题 */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace; /* 代码 */
```

**检查项**:
- [ ] 所有标题使用 Space Grotesk
- [ ] 正文使用 Inter
- [ ] 代码块使用 JetBrains Mono

---

### 6. 动画时长规范

**设计系统要求**:
```css
--transition-fast: 150ms;      /* 按钮、链接 */
--transition-standard: 200ms;  /* 卡片、下拉菜单 */
--transition-slow: 300ms;      /* 侧边栏、抽屉 */
```

**常见违规**:
- 使用 `500ms` 以上的过渡（用户感知延迟）
- 使用 `ease` 而非 `cubic-bezier(0.4, 0, 0.2, 1)`

---

### 7. 响应式断点

**检查项**:
- [ ] 所有组件在 `< 768px` 下可用
- [ ] 三栏布局在 `< 1280px` 下降级为两栏
- [ ] 执行页面在小屏幕下使用 Modal 显示 Workflow Graph

---

## ✅ 符合规范的优秀示例

### LoginView.vue & RegisterView.vue

这两个文件完全符合设计规范，可作为其他组件的参考标准：

**亮点**:
1. ✅ **色彩系统**: 完整使用 CSS 变量
   ```css
   --bg-primary: #0a0a0b;
   --accent-primary: hsl(262 83% 58%);
   --color-node-active: #00D9FF;
   ```

2. ✅ **图标规范**: 使用 SVG 而非 Emoji
   ```vue
   <svg class="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="..." />
   </svg>
   ```

3. ✅ **字体系统**: 正确使用 Inter + Space Grotesk
   ```css
   font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
   ```

4. ✅ **动画标准**: 符合时长和缓动函数规范
   ```css
   --transition-fast: 150ms;
   --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
   ```

5. ✅ **状态色**: 使用执行页面规范的色球颜色
   ```css
   --color-node-active: #00D9FF;    /* 青色 */
   --color-node-success: #00FF88;   /* 绿色 */
   --color-node-pending: #FFB800;   /* 琥珀 */
   ```

---

## 📋 修复优先级路线图

### Phase 1: P0 关键修复（本周）

**任务 1.1: Emoji 图标替换**
- [ ] 安装 `lucide-vue-next`
- [ ] 创建图标映射表
- [ ] 批量替换核心页面 Emoji
  - SkillDiscovery.vue
  - PPTEditView.vue
  - PPTGenerateView.vue
  - ArtifactTabs.vue

**任务 1.2: 文案优化**
- [ ] 全局搜索替换"生成" → "撰写/研究/整理"
- [ ] 移除所有"AI 助手"表述
- [ ] 更新 PPT 相关文案

**验收标准**:
- grep 搜索 Emoji 无结果
- grep 搜索"生成"仅保留技术术语（如"生成器"类型定义）

---

### Phase 2: P1 重要优化（下周）

**任务 2.1: 色彩系统统一**
- [ ] 创建 `design-system.css`
- [ ] 审计所有硬编码颜色
- [ ] 逐个组件替换为 CSS 变量

**任务 2.2: 图标库统一**
- [ ] 移除所有 Emoji 依赖
- [ ] 统一使用 Lucide Icons
- [ ] 清理未使用的图标导入

---

### Phase 3: P2 持续优化（两周内）

**任务 3.1: 字体规范**
- [ ] 确保 Inter 和 Space Grotesk 已加载
- [ ] 全局应用字体系统
- [ ] 优化字重层级

**任务 3.2: 动画优化**
- [ ] 审计所有 `transition` 时长
- [ ] 统一使用设计系统缓动函数
- [ ] 移除 >500ms 的过渡

**任务 3.3: 响应式完善**
- [ ] 测试所有页面在断点处的表现
- [ ] 修复布局问题
- [ ] 优化移动端体验

---

## 🛠️ 技术实施方案

### 方案 1: Emoji 图标批量替换脚本

```typescript
// scripts/replace-emoji-icons.ts
import { Search, PenTool, Database, BarChart, Code, FileText, Package } from 'lucide-vue-next'

export const iconMapping = {
  '🔍': Search,
  '✍️': PenTool,
  '📊': Database,
  '📈': BarChart,
  '💻': Code,
  '📄': FileText,
  '📦': Package,
  // ... 添加更多映射
}

// 使用示例
<component :is="iconMapping['🔍']" class="w-5 h-5" />
```

### 方案 2: 全局设计系统变量

```css
/* src/assets/design-system.css */
:root {
  /* 直接从 DESIGN-SYSTEM.md 导入 */
  --bg-primary: #0a0a0b;
  --bg-secondary: #141415;
  --bg-tertiary: #1c1c1e;
  --bg-elevated: #242426;
  
  --text-primary: #ffffff;
  --text-secondary: #a1a1aa;
  --text-tertiary: #71717a;
  
  --accent-primary: hsl(262 83% 58%);
  --accent-hover: hsl(262 90% 65%);
  
  /* 状态色 */
  --color-node-active: #00D9FF;
  --color-node-success: #00FF88;
  --color-node-pending: #FFB800;
  --color-node-error: #FF3B30;
  
  /* 间距 */
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  
  /* 动画 */
  --transition-fast: 150ms;
  --transition-standard: 200ms;
  --transition-slow: 300ms;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
}
```

### 方案 3: 文案批量替换

```bash
#!/bin/bash
# scripts/fix-ai-wording.sh

# 在所有 .vue 文件中替换
find frontend/src -name "*.vue" -type f -exec sed -i '' 's/生成 PPT/撰写 PPT/g' {} +
find frontend/src -name "*.vue" -type f -exec sed -i '' 's/生成报告/研究报告/g' {} +
find frontend/src -name "*.vue" -type f -exec sed -i '' 's/AI 助手/执行大脑/g' {} +
find frontend/src -name "*.vue" -type f -exec sed -i '' 's/AI生成/整理/g' {} +

# 验证
echo "检查剩余违规文案："
grep -r "生成" frontend/src --include="*.vue" | grep -v "生成器" | grep -v "生成时间"
```

---

## 📈 进度跟踪

| 阶段 | 任务 | 状态 | 完成度 | 负责人 | 截止日期 |
|------|------|------|--------|--------|---------|
| P0 | Emoji 图标替换 | 🔴 未开始 | 0% | - | 本周五 |
| P0 | AI 味文案修复 | 🔴 未开始 | 0% | - | 本周五 |
| P1 | 色彩系统统一 | 🔴 未开始 | 0% | - | 下周五 |
| P1 | 图标库统一 | 🔴 未开始 | 0% | - | 下周五 |
| P2 | 字体规范 | 🔴 未开始 | 0% | - | 两周内 |
| P2 | 动画优化 | 🔴 未开始 | 0% | - | 两周内 |

---

## 🎯 验收标准

### 自动化检查清单

```bash
#!/bin/bash
# scripts/design-audit.sh

echo "=== TokenDance 设计规范自动检查 ==="

# 1. 检查 Emoji
echo "1. 检查 Emoji 图标..."
EMOJI_COUNT=$(grep -r -P "[\x{1F300}-\x{1F9FF}]" frontend/src --include="*.vue" | wc -l)
if [ $EMOJI_COUNT -gt 0 ]; then
  echo "   ❌ 发现 $EMOJI_COUNT 处 Emoji 使用"
else
  echo "   ✅ 无 Emoji 违规"
fi

# 2. 检查 AI 味文案
echo "2. 检查 AI 味文案..."
AI_WORDING=$(grep -r "AI 助手\|生成 \|让 AI" frontend/src --include="*.vue" | wc -l)
if [ $AI_WORDING -gt 0 ]; then
  echo "   ❌ 发现 $AI_WORDING 处 AI 味文案"
else
  echo "   ✅ 无 AI 味违规"
fi

# 3. 检查硬编码颜色（简化版）
echo "3. 检查硬编码颜色..."
HARDCODED_COLORS=$(grep -r "#[0-9a-fA-F]\{6\}" frontend/src --include="*.vue" | grep -v "var(--" | wc -l)
echo "   ⚠️  发现 $HARDCODED_COLORS 处可能的硬编码颜色（需人工审查）"

echo ""
echo "=== 检查完成 ==="
```

### 人工审查清单

- [ ] 首页无 Emoji，使用 Lucide Icons
- [ ] 所有文案符合"用户导向"原则
- [ ] 色彩系统统一使用 CSS 变量
- [ ] 动画时长符合 150-300ms 标准
- [ ] 响应式布局在所有断点下正常工作
- [ ] 字体系统全局应用 Inter + Space Grotesk

---

## 📝 附录

### A. 设计规范文档索引

- **核心原则**: `/docs/ux/DESIGN-PRINCIPLES.md`
- **设计系统**: `/docs/ux/DESIGN-SYSTEM.md`
- **执行页布局**: `/docs/ux/EXECUTION-PAGE-LAYOUT.md`

### B. 参考标杆文件

- ✅ `frontend/src/views/LoginView.vue`
- ✅ `frontend/src/views/RegisterView.vue`

### C. 快速修复模板

```vue
<!-- 图标修复模板 -->
<script setup>
import { Search, PenTool, Code } from 'lucide-vue-next'
</script>

<template>
  <!-- ❌ 错误 -->
  <span>🔍</span>
  
  <!-- ✅ 正确 -->
  <Search class="w-5 h-5 text-gray-600" />
</template>

<!-- 文案修复模板 -->
<template>
  <!-- ❌ 错误 -->
  <h1>AI 生成 PPT</h1>
  
  <!-- ✅ 正确 -->
  <h1>演示汇报</h1>
</template>
```

---

**报告生成时间**: 2026-01-17 17:45:00  
**下次审查时间**: P0 修复完成后
