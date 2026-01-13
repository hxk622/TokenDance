# AnyGen UI 分析与设计参考

## 概述
本文档基于 AnyGen (www.anygen.io) 的 UI 源码分析，提取关键设计模式和交互理念，为 TokenDance 的 UI 设计提供参考。

**分析基准**：AnyGen 官网下载版本 (2026-01-09)
**URL**: http://localhost:8765 (本地服务器)

---

## 1. 技术栈分析

### 1.1 前端架构
```json
{
  "framework": "React 18.3.1",
  "buildSystem": "Modern.js (Garfish 微前端)",
  "uiLibrary": "@universe-design (自研), Mantine",
  "stateManagement": "React Context/Hooks",
  "routing": "Modern.js Routes",
  "styling": "CSS Modules + Tailwind-like utilities",
  "editor": "TipTap Editor (富文本), CodeMirror (代码)",
  "rendering": "SSR + CSR Hybrid"
}
```

### 1.2 核心依赖
- **React 18.3.1** (vendor-96, vendor-97)
- **@universe-design**: 自研 UI 组件库（30+ 异步模块）
- **Mantine**: 补充 UI 组件（模态框、通知、表单）
- **TipTap**: 富文本编辑器（文档/PPT）
- **CodeMirror**: 代码编辑器
- **Icon Libraries**: 图标库（独立加载）

### 1.3 微前端架构
```javascript
// Garfish Module Info
{
  "app:@ccm-axon/web": {
    "buildVersion": "1.0.0.4405",
    "globalName": "__VMOK_@ccm-axon/web:1.0.0.4405__",
    "modules": [...],
    "publicPath": "//sf16-scmcdn.larksuitecdn.com/obj/lark-static-sg/ccm/axon-web/",
    "remotesInfo": {
      "un_publish:@ccm-vmok/slide": {
        "moduleSource": "static-module",
        "matchedVersion": "https://...axon-slides/module/ee/slide/web/1.0.0.22/vmok/vmok-manifest.json"
      }
    }
  }
}
```
**关键特性**：
- 主应用 + Slide 模块分离
- CDN 部署，按需加载
- Shared dependencies (React, React-DOM)

---

## 2. 页面结构与路由

### 2.1 主要路由
```
/__common/
  ├── $ (首页/Landing Page)
  ├── __axon/
  │   ├── home/page (工作台首页)
  │   ├── file/(fileId$)/page (文件详情)
  │   ├── library/page (资源库)
  │   ├── designer/page (设计器)
  │   ├── developer/page (开发者工具)
  │   ├── layout (公共布局)
  │   ├── page/(page_id)/page (页面编辑)
  │   ├── quant/(page_id)/page (量化分析)
  │   └── share/(token$)/page (分享页面)
  └── template/
      ├── install/(templateId)/page (模板安装)
      └── preview/(templateId)/page (模板预览)
```

### 2.2 布局组件
```javascript
// Layout 组件加载的资源
{
  "chunkIds": ["52739", "28762", ..., "85440"],
  "assets": [
    "static/js/async/utils-*.js",      // 工具函数
    "static/js/async/universe-design-*.js",  // UI 组件
    "static/js/async/mantine.js",      // Mantine UI
    "static/js/async/business-*.js",   // 业务组件
    "static/js/vendor-*.js"            // 第三方库
  ]
}
```

---

## 3. UI 设计模式

### 3.1 设计系统
**@universe-design 组件库**（30个模块）：
- `universe-design-0`: 基础组件（Button, Input, Tooltip）
- `universe-design-18~29`: 高级组件（Table, Modal, Drawer, Popover）
- 组件按需异步加载，优化首屏性能

**颜色系统**（推测）：
- 主色调：现代蓝紫色渐变
- 中性色：灰度系统
- 语义色：成功/警告/错误

### 3.2 响应式设计
- **断点系统**（推测基于 Mantine）：
  ```
  xs: 576px
  sm: 768px
  md: 992px
  lg: 1200px
  xl: 1400px
  ```

### 3.3 交互模式
1. **异步加载**：所有页面组件按需加载
2. **渐进式渲染**：核心 UI 先显示，业务逻辑后加载
3. **骨架屏**：加载状态占位
4. **错误边界**：组件级错误隔离

---

## 4. 核心功能模块

### 4.1 文件管理 (file/(fileId$)/page)
**加载资源**：
- `mantine.js`: 模态框、通知
- `icon-libraries.js`: 图标库
- `business-*.js`: 业务组件（28个模块）
- `shared-ui.js`, `shared.js`: 共享 UI 和逻辑

**推测功能**：
- 文件预览（文档、PPT、代码）
- 文件编辑（TipTap + CodeMirror）
- 协作功能（评论、版本历史）
- 导出/分享

### 4.2 工作台首页 (home/page)
**特殊资源**：
- `editor-kit-*.js` (5个模块): 编辑器工具包
- `docx-kit.js`: DOCX 导入/导出
- `tiptap-editor.js`: 富文本编辑器
- 72个异步业务组件

**推测布局**：
```
┌──────────────────────────────────────────┐
│ Header (导航 + 用户菜单)                   │
├──────────────────────────────────────────┤
│ ┌────────┬──────────────────────────────┐ │
│ │ Sidebar│  Main Content Area           │ │
│ │  ├ Home│    ├ Recent Files            │ │
│ │  ├ Lib │    ├ Templates               │ │
│ │  ├ Team│    └ Recommended             │ │
│ │  └ ...│                               │ │
│ └────────┴──────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### 4.3 分享页面 (share/(token$)/page)
**特殊资源**：
- `mermaid~*.js` (3个模块): 图表渲染
- `codemirror-*.js` (5个模块): 代码展示
- 只读模式，无编辑功能

---

## 5. 性能优化策略

### 5.1 代码分割
- **Vendor 分割**：175个 vendor 模块（平均 50KB）
- **Async 分割**：230+ 异步业务模块
- **Route-based splitting**：每个路由独立打包

### 5.2 资源加载
```javascript
// 首屏加载（__common/$）
{
  "chunkIds": ["52739", ..., "69201"],  // 207个 chunk
  "referenceCssAssets": [
    "static/css/async/universe-design-0.css",
    "static/css/vendor-14.css",
    // ... 18个 CSS 文件
  ]
}
```
**策略**：
- 共享 vendor 预加载
- 路由组件懒加载
- CSS 按需加载

### 5.3 CDN 部署
```
publicPath: "//sf16-scmcdn.larksuitecdn.com/obj/lark-static-sg/ccm/axon-web/"
```
- 全球 CDN 加速
- 版本化文件名（缓存优化）
- 静态资源与动态 API 分离

---

## 6. 用户体验特性

### 6.1 用户系统
```javascript
window.User = {
  "userInfo": {
    "id": "7593242028104847070",
    "name": "Guest User 63935",
    "email": "",
    "locales": ["en_us", "ja_jp", "zh_cn"]
  },
  "clientFeatures": {
    "mino.lark.axon.async_message_enabled": true,
    "mino.lark.axon.notebook_enabled": true,
    "mino.superagent_canvas": true,
    "mino.page.export_word_enable": true,
    // ... 200+ feature flags
  }
}
```
**关键点**：
- Guest 模式支持（无需注册试用）
- 多语言支持（3种语言）
- Feature flags 动态控制功能开关

### 6.2 分析与监控
```javascript
// Google Tag Manager
GTM-M3DH5C54

// Meta Pixel
3396133396871780

// Region Data
{"__REGION__": "sg"}
```
**监控点**：
- 页面访问统计
- 用户行为追踪
- 区域化服务（新加坡节点）

---

## 7. 对比与启示

### 7.1 AnyGen vs TokenDance 定位
| 维度 | AnyGen | TokenDance (目标) |
|------|--------|-------------------|
| 核心功能 | AI 文档/PPT 生成 | AI Agent 平台 (PPT + Deep Research + ...) |
| 编辑器 | TipTap (文档导向) | TipTap + Code (多模态) |
| 协作 | 实时协作 (推测) | Agent 协作 + 人机协作 |
| 架构 | 微前端 (Garfish) | 单体应用 (初期) |
| UI 库 | @universe-design (自研) | Shadcn/UI (开源) |

### 7.2 值得借鉴的设计
1. **异步加载策略**
   - 首屏只加载核心 UI（~500KB）
   - 业务模块按路由懒加载
   - 共享依赖预加载

2. **组件库设计**
   - 基础组件 + 业务组件分离
   - 按需加载（30个 universe-design 模块）
   - CSS 独立打包

3. **编辑器集成**
   - TipTap 富文本 + CodeMirror 代码
   - Editor Kit 模块化（5个子模块）
   - DOCX 导入/导出支持

4. **Feature Flags**
   - 200+ 功能开关
   - 灰度发布支持
   - A/B 测试能力

5. **Guest 模式**
   - 无需注册即可试用
   - 降低用户门槛
   - 转化率优化

---

## 8. TokenDance UI 设计建议

### 8.1 技术栈选型（已定）
```json
{
  "framework": "Vue 3 + TypeScript",
  "uiLibrary": "Shadcn/UI (Vue) + Tailwind CSS",
  "stateManagement": "Pinia",
  "editor": "TipTap (富文本) + Monaco Editor (代码)",
  "buildTool": "Vite",
  "routing": "Vue Router"
}
```

### 8.2 页面结构建议
```
/
├── / (Landing Page)
├── /home (工作台首页)
│   ├── Recent Tasks
│   ├── Agent Templates
│   └── Quick Actions
├── /agent/:id (Agent 详情/编辑)
│   ├── Canvas (流程编排)
│   ├── Memory (记忆管理)
│   ├── Tools (工具配置)
│   └── Logs (执行日志)
├── /library (资源库)
│   ├── Skills (技能库)
│   ├── Templates (模板库)
│   └── Memories (记忆库)
└── /share/:token (分享页面)
```

### 8.3 布局设计
```vue
<!-- 主布局 -->
<template>
  <div class="app-layout">
    <!-- Header -->
    <header class="border-b">
      <nav>
        <Logo />
        <MainNav />
        <UserMenu />
      </nav>
    </header>
    
    <!-- Main -->
    <div class="flex h-[calc(100vh-64px)]">
      <!-- Sidebar (可折叠) -->
      <aside class="w-64 border-r" v-if="showSidebar">
        <Sidebar />
      </aside>
      
      <!-- Content -->
      <main class="flex-1 overflow-auto">
        <RouterView />
      </main>
    </div>
  </div>
</template>
```

### 8.4 组件库规划
**基础组件**（Shadcn/UI）：
- Button, Input, Select, Checkbox, Radio
- Card, Dialog, Sheet, Popover, Tooltip
- Table, Tabs, Accordion, Collapsible

**业务组件**（自研）：
- AgentCanvas (流程编排画布)
- MemoryTimeline (记忆时间线)
- SkillPicker (技能选择器)
- ToolConfig (工具配置器)
- ExecutionLog (执行日志查看器)
- ContextViewer (上下文查看器)

### 8.5 性能优化
1. **路由懒加载**
   ```typescript
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
   ```

2. **组件异步加载**
   ```vue
   <script setup>
   const AgentCanvas = defineAsyncComponent(() => 
     import('@/components/AgentCanvas.vue')
   )
   </script>
   ```

3. **虚拟滚动**（大列表）
   ```vue
   <VirtualList
     :items="logs"
     :item-height="48"
   />
   ```

### 8.6 主题设计
**配色方案**（参考 AnyGen 的现代感）：
```css
:root {
  /* Primary (蓝紫渐变) */
  --primary: 262 83% 58%;
  --primary-foreground: 210 40% 98%;
  
  /* Background */
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  
  /* Muted */
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  
  /* Border */
  --border: 214.3 31.8% 91.4%;
  
  /* Accent */
  --accent: 262 83% 58%;
}
```

### 8.7 交互模式
1. **即时反馈**
   - 加载骨架屏
   - 乐观更新
   - 错误提示

2. **渐进式展示**
   - 首屏快速渲染
   - 次要功能延迟加载
   - 空状态友好提示

3. **键盘快捷键**
   - `Cmd+K`: 命令面板
   - `Cmd+S`: 保存
   - `Cmd+/`: 快捷键帮助

---

## 9. 实施路线图

### Phase 1: 基础框架（Week 1-2）
- [x] 技术栈选型（Vue 3 + Shadcn/UI）
- [ ] 项目初始化（Vite + TypeScript）
- [ ] 路由配置
- [ ] 主布局开发
- [ ] Shadcn/UI 组件集成

### Phase 2: 核心页面（Week 3-4）
- [ ] Landing Page（营销页面）
- [ ] Home 页面（工作台）
- [ ] Agent Canvas（流程编排）
- [ ] Library 页面（资源库）

### Phase 3: 业务组件（Week 5-6）
- [ ] MemoryTimeline
- [ ] SkillPicker
- [ ] ToolConfig
- [ ] ExecutionLog
- [ ] ContextViewer

### Phase 4: 优化与完善（Week 7-8）
- [ ] 性能优化（代码分割、懒加载）
- [ ] 主题系统（明暗模式）
- [ ] 国际化（i18n）
- [ ] 单元测试（Vitest）

---

## 10. 关键差异点

### 10.1 TokenDance 独特设计
1. **Agent Canvas**
   - 流程编排画布（类似 Manus）
   - 节点类型：Reasoning, Planning, Tool-Use, Reflection
   - 实时执行可视化

2. **Memory Graph 可视化**
   - Neo4j 图谱展示
   - 记忆关联分析
   - 时间线回溯

3. **Context Management 面板**
   - 滑动窗口可视化
   - 增量摘要展示
   - Token 使用统计

4. **Sandbox/Browser 监控**
   - 实时日志流
   - 资源占用监控
   - 安全策略配置

### 10.2 不借鉴的部分
- **微前端架构**：初期单体应用更合适
- **自研 UI 库**：使用成熟的 Shadcn/UI
- **SSR**：初期纯 CSR，后期按需引入

---

## 11. 总结

### 11.1 核心借鉴
1. **异步加载策略**：首屏快速渲染，业务模块懒加载
2. **组件库设计**：基础组件 + 业务组件分离
3. **Feature Flags**：灰度发布和 A/B 测试
4. **Guest 模式**：降低试用门槛
5. **编辑器集成**：TipTap + Code Editor 双引擎

### 11.2 创新点
1. **Agent Canvas**：可视化流程编排
2. **Memory Graph**：图谱化记忆管理
3. **Context 可视化**：上下文管理面板
4. **Execution 监控**：实时日志和性能分析

### 11.3 下一步行动
1. 使用本分析更新 `docs/design/UI-Design.md`
2. 创建 `docs/components/` 目录，详细设计业务组件
3. 搭建 Vite + Vue 3 + Shadcn/UI 项目脚手架
4. 实现 Landing Page 和 Layout 原型

---

**文档版本**：v1.0
**最后更新**：2026-01-09
**作者**：TokenDance Team
**参考来源**：AnyGen (www.anygen.io) UI 源码分析
