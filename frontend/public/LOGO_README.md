# TokenDance Logo & Brand Assets

## 📁 文件说明

### Logo 文件
- `logo.svg` - 主 Logo（200x200px，带动画效果）
- `favicon.svg` - 网站图标（32x32px，简化版）

### 使用场景

#### 1. 网站 Favicon
已在 `index.html` 中配置：
```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
```

#### 2. 在 Vue 组件中使用 Logo
```vue
<template>
  <img src="/logo.svg" alt="TokenDance Logo" class="logo" />
</template>
```

#### 3. 作为背景图
```css
.header {
  background-image: url('/logo.svg');
  background-size: contain;
  background-repeat: no-repeat;
}
```

## 🎨 品牌颜色

### 主色调
```css
--primary-gradient: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
--primary-purple: #6366F1;
--primary-violet: #8B5CF6;
```

### 辅助色
```css
--accent-cyan: #06B6D4;
--background-dark: #1A1A1E;
```

## 🎯 设计理念

### Logo 元素
1. **T 和 D 字母** - 代表 TokenDance
2. **流动的曲线** - 象征 Token 的流动和 Dance 的动感
3. **粒子动画** - 代表 AI 的智能和活力
4. **渐变色彩** - 体现科技感和未来感

### 设计特点
- ✨ **动态感** - 粒子动画营造流动氛围
- 🎨 **现代感** - 渐变色彩和简洁线条
- 🔮 **科技感** - 发光效果和流畅曲线
- 🌈 **品牌感** - 独特的紫蓝渐变配色

## 📐 使用规范

### Logo 尺寸建议
- **网站头部**: 40-60px 高度
- **移动端**: 32-40px 高度
- **社交媒体**: 200x200px 或 512x512px

### 最小尺寸
- 不小于 24x24px（保证可识别性）

### 留白空间
- Logo 周围至少保留 Logo 高度 20% 的留白

### 禁止事项
- ❌ 不要改变 Logo 的颜色比例
- ❌ 不要拉伸或压缩 Logo
- ❌ 不要在低对比度背景上使用
- ❌ 不要添加阴影或其他效果

## 🔄 生成其他格式

### 转换为 PNG（如需要）
```bash
# 使用 Inkscape 或在线工具转换
# 推荐尺寸: 512x512, 256x256, 128x128, 64x64, 32x32
```

### 生成 ICO 文件
```bash
# 使用在线工具将 favicon.svg 转换为 favicon.ico
# 推荐: https://realfavicongenerator.net/
```

## 🎨 Logo 变体

### 深色背景（当前版本）
- 适用于深色主题
- 使用亮色渐变

### 浅色背景（如需要）
- 可以调整颜色为深色
- 或添加深色描边

## 📱 响应式使用

```vue
<template>
  <!-- 桌面端显示完整 Logo -->
  <img
    src="/logo.svg"
    alt="TokenDance"
    class="hidden md:block h-12"
  />

  <!-- 移动端显示简化版 -->
  <img
    src="/favicon.svg"
    alt="TD"
    class="md:hidden h-8"
  />
</template>
```

## 🌟 特色功能

### SVG 动画
Logo 包含内置的 CSS 动画：
- 粒子上下浮动
- 透明度渐变
- 自动循环播放

### 可定制性
SVG 格式支持：
- 修改颜色
- 调整大小
- 添加/移除动画
- 导出为其他格式

## 📞 联系方式

如需定制 Logo 或其他品牌设计，请联系设计团队。

---

**Created with ❤️ for TokenDance**
