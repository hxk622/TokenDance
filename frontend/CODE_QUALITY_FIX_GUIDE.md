# 🎯 TokenDance 前端代码质量修复指南

## 📊 当前状态

**ESLint 检查结果：**
- ❌ 错误：17 个
- ⚠️ 警告：32 个
- 📊 总计：49 个问题

**目标：** 修复所有问题，达到 A 级代码质量

---

## ✅ 已完成的修复

### 1. **安装 DOMPurify** ✅
```bash
pnpm add dompurify
```

### 2. **创建安全渲染工具** ✅
文件：`src/utils/sanitize.ts`
- `sanitizeHtml()` - 清理 HTML
- `renderMarkdown()` - 安全渲染 Markdown
- `escapeHtml()` - 转义纯文本

### 3. **添加全局类型定义** ✅
文件：`src/types/global.d.ts`
- 修复了 `IntersectionObserverInit`
- 修复了 `ScrollBehavior`
- 修复了 `ScrollIntoViewOptions`
- 修复了 `RequestInit`

### 4. **创建 Logo 和 Favicon** ✅
- `public/logo.svg` - 主 Logo
- `public/favicon.svg` - 网站图标
- 已集成到 `index.html`

### 5. **配置 ESLint** ✅
- 创建了 `.eslintrc.cjs`
- 配置了 Vue 3 规则

---

## 🔴 需要手动修复的问题

### 问题 1: 计算属性缺少返回值 (3处)

**文件：** 具体文件未知（ESLint 未显示完整路径）

**错误信息：**
```
18:32  error  Expected to return a value in computed function
29:34  error  Expected to return a value in computed function
40:29  error  Expected to return a value in computed function
```

**修复方法：**
```typescript
// ❌ 错误
const filteredData = computed(() => {
  if (loading.value) {
    // 缺少 return
  }
})

// ✅ 正确
const filteredData = computed(() => {
  if (loading.value) {
    return []
  }
  return data.value
})
```

**查找命令：**
```bash
cd frontend
grep -rn "computed(() =>" src/ | grep -v "return"
```

---

### 问题 2: SVG 属性名无效 (3处)

**文件：** 某个组件（行 129-131）

**错误信息：**
```
129:17  error  Attribute name 0 is not valid
130:17  error  Attribute name 24 is not valid
131:17  error  Attribute name 24\" is not valid
```

**问题：** SVG 属性使用了数字作为属性名

**修复方法：**
```vue
<!-- ❌ 错误 -->
<svg 0="..." 24="..." 24\"="...">

<!-- ✅ 正确 -->
<svg width="24" height="24" viewBox="0 0 24 24">
```

**查找命令：**
```bash
cd frontend
grep -rn '<svg.*[0-9]="' src/
```

---

### 问题 3: 常量条件判断 (3处)

**错误信息：**
```
172:14  error  Unexpected constant condition
85:14   error  Unexpected constant condition
91:12   error  Unexpected constant condition
```

**修复方法：**
```typescript
// ❌ 错误
if (true) {
  // 永远为真
}

while (true) {
  // 无限循环 - 需要添加 break 条件
}

// ✅ 正确
if (someCondition) {
  // 动态条件
}

while (isRunning) {
  // 可以被改变的条件
  if (shouldStop) break
}
```

---

### 问题 4: Props 缺少默认值 (30+处)

**受影响组件：**
- `AnyButton.vue` - icon, iconRight
- `AnyCard.vue` - icon, label, image, title, meta, tag
- `AnyHeader.vue` - title
- `AnyInput.vue` - icon, iconRight, errorMessage, maxlength
- `AnyModal.vue` - title, image, imageAlt
- `AnyNavbar.vue` - icon, logoSrc, sections
- 等 20+ 个组件

**修复方法：**
```typescript
// ❌ 错误
defineProps<{
  title?: string
  icon?: string
}>()

// ✅ 正确
withDefaults(defineProps<{
  title?: string
  icon?: string
}>(), {
  title: '',
  icon: ''
})
```

**批量修复脚本：**
```bash
# 查找所有需要修复的组件
cd frontend
find src/components -name "*.vue" -exec grep -l "defineProps<{" {} \;
```

---

### 问题 5: XSS 安全漏洞 (8处)

**受影响文件：**
- `ChatMessage.vue:63`
- `MessageBubble.vue:95`
- `ResearchCompletionCard.vue:260`
- `StreamingInfo.vue:72, 336`
- `ExecutionPage.vue:590`
- 等

**修复方法：**

**步骤 1：** 在组件中导入安全工具
```typescript
import { renderMarkdown, sanitizeHtml } from '@/utils/sanitize'
```

**步骤 2：** 创建安全的计算属性
```typescript
const safeContent = computed(() => {
  return renderMarkdown(props.content)
})
```

**步骤 3：** 使用安全的内容
```vue
<!-- ❌ 不安全 -->
<div v-html="content"></div>

<!-- ✅ 安全 -->
<div v-html="safeContent"></div>
```

---

## 🛠️ 快速修复命令

### 1. 查找所有 v-html 使用
```bash
cd frontend
grep -rn "v-html" src/
```

### 2. 查找所有计算属性
```bash
cd frontend
grep -rn "computed(() =>" src/
```

### 3. 查找所有 Props 定义
```bash
cd frontend
grep -rn "defineProps<{" src/
```

### 4. 运行 ESLint 自动修复
```bash
cd frontend
npm run lint
```

### 5. 运行类型检查
```bash
cd frontend
npm run type-check
```

---

## 📋 修复优先级

### 🔴 高优先级（立即修复）
1. ✅ XSS 安全漏洞 - 已提供工具，需要应用到组件
2. ❌ SVG 属性错误 - 导致构建失败
3. ❌ 计算属性返回值 - 导致运行时错误

### 🟡 中优先级（本周内）
4. ❌ 常量条件判断 - 代码质量问题
5. ❌ Props 默认值 - 类型安全问题

### 🟢 低优先级（逐步改进）
6. ✅ 类型定义 - 已修复
7. ⚠️ ESLint 警告 - 不影响功能

---

## 🎯 达到 A 级的步骤

### 第一步：修复所有错误（17个）
```bash
# 1. 修复 SVG 属性错误（3个）
# 2. 修复计算属性返回值（3个）
# 3. 修复常量条件判断（3个）
# 4. 修复类型定义（已完成）
# 5. 修复 XSS 漏洞（8个）
```

### 第二步：修复所有警告（32个）
```bash
# 主要是 Props 默认值问题
# 使用 withDefaults 批量修复
```

### 第三步：验证
```bash
npm run lint        # 应该 0 errors, 0 warnings
npm run type-check  # 应该通过
npm run build       # 应该成功
```

---

## 📝 修复模板

### 模板 1: 修复 Props 默认值
```typescript
// 在组件的 <script setup> 中
withDefaults(defineProps<{
  title?: string
  icon?: string
  disabled?: boolean
}>(), {
  title: '',
  icon: '',
  disabled: false
})
```

### 模板 2: 修复 v-html XSS
```vue
<script setup lang="ts">
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/sanitize'

const props = defineProps<{
  content: string
}>()

const safeContent = computed(() => renderMarkdown(props.content))
</script>

<template>
  <div v-html="safeContent"></div>
</template>
```

### 模板 3: 修复计算属性
```typescript
const filteredItems = computed(() => {
  if (!items.value) {
    return [] // 确保总是返回值
  }
  return items.value.filter(item => item.active)
})
```

---

## 🚀 自动化修复脚本

创建一个修复脚本 `scripts/fix-code-quality.sh`：

```bash
#!/bin/bash

echo "🔧 开始修复代码质量问题..."

# 1. 运行 ESLint 自动修复
echo "📝 运行 ESLint 自动修复..."
cd frontend
npm run lint

# 2. 运行类型检查
echo "🔍 运行类型检查..."
npm run type-check

# 3. 运行构建测试
echo "🏗️ 测试构建..."
npm run build

echo "✅ 修复完成！"
```

---

## 📊 预期结果

修复所有问题后：
- ✅ ESLint: 0 errors, 0 warnings
- ✅ TypeScript: 0 errors
- ✅ Build: Success
- ✅ 代码质量评级: **A** (优秀)

---

## 💡 最佳实践建议

### 1. 使用 Git Pre-commit Hook
已配置 husky，每次提交前自动检查

### 2. 使用 VS Code 扩展
- ESLint
- Volar (Vue 3)
- Prettier

### 3. 定期运行质量检查
```bash
npm run check  # 运行所有检查
```

### 4. 代码审查清单
- [ ] 所有 Props 有默认值
- [ ] 所有计算属性有返回值
- [ ] 所有 v-html 使用了安全工具
- [ ] 没有常量条件判断
- [ ] 类型定义完整

---

## 📞 需要帮助？

如果在修复过程中遇到问题：
1. 查看具体的错误信息
2. 参考本文档的修复模板
3. 运行 `npm run lint` 查看详细错误

---

**最后更新：** 2026-01-18
**状态：** 进行中
**目标：** A 级代码质量
