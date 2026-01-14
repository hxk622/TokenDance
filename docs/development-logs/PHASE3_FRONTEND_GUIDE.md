# Phase 3: 前端 Chat UI 开发指南 🎨

## 📊 当前进度

✅ Phase 1: Agent 核心引擎 (已完成)
✅ Phase 2: API 层 + SSE 流式输出 (已完成)
🔄 Phase 3: 前端 Chat UI (待开发)

---

## 🎯 Phase 3 目标

创建一个完整的 Chat UI，实时显示 Agent 的思考过程和工具调用。

---

## 📁 需要创建的组件

### 1. **ChatView.vue** (主页面)

位置: `frontend/src/views/ChatView.vue`

功能：
- 整合所有子组件
- 管理 Session 状态
- 处理 SSE 事件流

结构：
```vue
<template>
  <div class="chat-view">
    <!-- Header: 显示 Agent 信息 -->
    <header>...</header>
    
    <!-- Messages: 消息列表 -->
    <MessageList :messages="messages" />
    
    <!-- Thinking: 当前思考过程 -->
    <ThinkingTrace v-if="currentThinking" />
    
    <!-- Input: 输入框 -->
    <InputBox @send="handleSend" />
  </div>
</template>
```

### 2. **MessageList.vue** (消息列表)

位置: `frontend/src/components/MessageList.vue`

功能：
- 显示所有消息（用户+助手）
- 自动滚动到底部
- 支持展开/折叠历史消息

结构：
```vue
<template>
  <div class="message-list">
    <MessageBubble
      v-for="msg in messages"
      :key="msg.id"
      :message="msg"
    />
  </div>
</template>
```

关键点：
- 用户消息靠右，助手消息靠左
- 支持 Markdown 渲染
- 自动滚动到最新消息

### 3. **MessageBubble.vue** (单条消息)

位置: `frontend/src/components/MessageBubble.vue`

功能：
- 渲染单条消息
- 支持多种消息类型（user, assistant, error）
- 显示时间戳

结构：
```vue
<template>
  <div :class="['message-bubble', message.role]">
    <!-- User Message -->
    <div v-if="message.role === 'user'" class="user-message">
      {{ message.content }}
    </div>
    
    <!-- Assistant Message -->
    <div v-else-if="message.role === 'assistant'" class="assistant-message">
      <!-- Reasoning (可折叠) -->
      <ThinkingCollapsible v-if="message.reasoning" />
      
      <!-- Tool Calls (可折叠) -->
      <ToolCallList v-if="message.toolCalls" />
      
      <!-- Answer -->
      <div class="answer" v-html="renderMarkdown(message.content)" />
    </div>
  </div>
</template>
```

### 4. **InputBox.vue** (输入框)

位置: `frontend/src/components/InputBox.vue`

功能：
- 多行文本输入
- Enter 发送，Shift+Enter 换行
- 显示加载状态
- 停止生成按钮

结构：
```vue
<template>
  <div class="input-box">
    <textarea
      v-model="content"
      @keydown.enter="handleEnter"
      :disabled="isLoading"
      placeholder="Type your message..."
    />
    
    <div class="actions">
      <button v-if="!isLoading" @click="send">
        Send
      </button>
      <button v-else @click="stop">
        Stop
      </button>
    </div>
  </div>
</template>
```

关键点：
- 自动 resize textarea
- 禁用状态管理
- 焦点管理

### 5. **ThinkingTrace.vue** (思考过程)

位置: `frontend/src/components/ThinkingTrace.vue`

功能：
- 实时显示 Agent 推理过程
- 显示当前迭代次数
- 可折叠/展开

结构：
```vue
<template>
  <div class="thinking-trace">
    <div class="header">
      <span>🤔 Agent is thinking...</span>
      <span class="iteration">Iteration {{ iteration }}</span>
    </div>
    
    <div class="content">
      <p>{{ thinking }}</p>
    </div>
    
    <!-- Tool Calls (if any) -->
    <ToolCallList :tool-calls="toolCalls" />
  </div>
</template>
```

样式：
- 半透明背景
- 打字机效果（可选）
- 动画过渡

### 6. **ToolCallCard.vue** (工具调用卡片)

位置: `frontend/src/components/ToolCallCard.vue`

功能：
- 显示工具名称和参数
- 显示执行状态（running, success, error）
- 显示结果

结构：
```vue
<template>
  <div :class="['tool-call-card', status]">
    <div class="header">
      <span class="icon">🔧</span>
      <span class="tool-name">{{ toolName }}</span>
      <span class="status">{{ statusText }}</span>
    </div>
    
    <div class="parameters">
      <pre>{{ JSON.stringify(parameters, null, 2) }}</pre>
    </div>
    
    <div v-if="result" class="result">
      <strong>Result:</strong>
      <div>{{ result }}</div>
    </div>
  </div>
</template>
```

状态颜色：
- running: 蓝色 + 加载动画
- success: 绿色
- error: 红色

---

## 🔌 SSE 集成 (核心)

### 创建 `useAgentStream` Composable

位置: `frontend/src/composables/useAgentStream.ts`

```typescript
import { ref } from 'vue'

export function useAgentStream(sessionId: string, callbacks: {
  onStart?: () => void
  onReasoning?: (data: any) => void
  onToolCall?: (data: any) => void
  onToolResult?: (data: any) => void
  onAnswer?: (data: any) => void
  onError?: (data: any) => void
  onDone?: () => void
}) {
  const eventSource = ref<EventSource | null>(null)
  
  const sendMessage = async (content: string) => {
    // 关闭之前的连接
    if (eventSource.value) {
      eventSource.value.close()
    }
    
    // 创建 EventSource
    const url = `${API_BASE}/api/v1/sessions/${sessionId}/messages`
    
    eventSource.value = new EventSource(url)
    
    // 注册事件监听器
    eventSource.value.addEventListener('start', (e) => {
      const data = JSON.parse(e.data)
      callbacks.onStart?.()
    })
    
    eventSource.value.addEventListener('reasoning', (e) => {
      const data = JSON.parse(e.data)
      callbacks.onReasoning?.(data)
    })
    
    eventSource.value.addEventListener('tool_call', (e) => {
      const data = JSON.parse(e.data)
      callbacks.onToolCall?.(data)
    })
    
    eventSource.value.addEventListener('tool_result', (e) => {
      const data = JSON.parse(e.data)
      callbacks.onToolResult?.(data)
    })
    
    eventSource.value.addEventListener('answer', (e) => {
      const data = JSON.parse(e.data)
      callbacks.onAnswer?.(data)
    })
    
    eventSource.value.addEventListener('error', (e) => {
      const data = JSON.parse(e.data)
      callbacks.onError?.(data)
    })
    
    eventSource.value.addEventListener('done', (e) => {
      const data = JSON.parse(e.data)
      callbacks.onDone?.()
      eventSource.value?.close()
    })
    
    // 错误处理
    eventSource.value.onerror = (error) => {
      console.error('EventSource error:', error)
      callbacks.onError?.({ message: 'Connection error' })
      eventSource.value?.close()
    }
  }
  
  const stopGeneration = () => {
    eventSource.value?.close()
    eventSource.value = null
  }
  
  return {
    sendMessage,
    stopGeneration
  }
}
```

---

## 🎨 UI 设计要点

### 颜色方案

```css
/* User Message */
.user-message {
  background: #3b82f6; /* Blue */
  color: white;
}

/* Assistant Message */
.assistant-message {
  background: white;
  border: 1px solid #e5e7eb;
}

/* Thinking Trace */
.thinking-trace {
  background: #f3f4f6;
  border-left: 4px solid #fbbf24; /* Amber */
}

/* Tool Call - Running */
.tool-call-card.running {
  border-left: 4px solid #3b82f6; /* Blue */
}

/* Tool Call - Success */
.tool-call-card.success {
  border-left: 4px solid #10b981; /* Green */
}

/* Tool Call - Error */
.tool-call-card.error {
  border-left: 4px solid #ef4444; /* Red */
}
```

### 动画

```css
/* 打字机效果 */
@keyframes typing {
  from { width: 0 }
  to { width: 100% }
}

/* 加载动画 */
@keyframes pulse {
  0%, 100% { opacity: 1 }
  50% { opacity: 0.5 }
}

/* 工具调用旋转 */
@keyframes spin {
  from { transform: rotate(0deg) }
  to { transform: rotate(360deg) }
}
```

---

## 📦 需要的依赖

```json
{
  "dependencies": {
    "marked": "^11.0.0",           // Markdown 渲染
    "highlight.js": "^11.9.0",      // 代码高亮
    "date-fns": "^3.0.0"            // 时间格式化
  }
}
```

安装：
```bash
cd frontend
npm install marked highlight.js date-fns
```

---

## 🔧 API 客户端

创建 `frontend/src/api/agent.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const agentApi = {
  // 发送消息（非流式）
  async sendMessage(sessionId: string, content: string) {
    const response = await fetch(
      `${API_BASE}/api/v1/sessions/${sessionId}/messages`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, stream: false })
      }
    )
    return response.json()
  },
  
  // 获取消息历史
  async getMessages(sessionId: string) {
    const response = await fetch(
      `${API_BASE}/api/v1/sessions/${sessionId}/messages`
    )
    return response.json()
  },
  
  // 获取 Working Memory
  async getWorkingMemory(sessionId: string) {
    const response = await fetch(
      `${API_BASE}/api/v1/sessions/${sessionId}/working-memory`
    )
    return response.json()
  }
}
```

---

## 🧪 测试

### 手动测试流程

1. **启动后端**:
```bash
cd backend
uv run uvicorn app.main:app --reload
```

2. **启动前端**:
```bash
cd frontend
npm run dev
```

3. **测试场景**:
   - [ ] 发送简单消息（2+2=?）
   - [ ] 发送需要搜索的消息
   - [ ] 发送多步骤任务
   - [ ] 测试停止生成
   - [ ] 测试错误处理

---

## 📋 开发检查清单

### 组件开发
- [ ] ChatView.vue - 主页面
- [ ] MessageList.vue - 消息列表
- [ ] MessageBubble.vue - 单条消息
- [ ] InputBox.vue - 输入框
- [ ] ThinkingTrace.vue - 思考过程
- [ ] ToolCallCard.vue - 工具调用卡片

### 功能实现
- [ ] SSE 流式接收
- [ ] 消息历史加载
- [ ] 自动滚动到底部
- [ ] Markdown 渲染
- [ ] 代码高亮
- [ ] 停止生成功能
- [ ] 错误提示
- [ ] 加载状态

### 样式优化
- [ ] 响应式布局
- [ ] 暗色模式支持
- [ ] 动画过渡
- [ ] 移动端适配

---

## 🚀 快速开始

### Option 1: 从头开始

按照上面的组件列表逐个创建。

### Option 2: 参考现有组件

查看 `frontend/src/components/` 中是否有可复用的组件。

### Option 3: 使用 UI 库

可以考虑集成：
- Shadcn/UI (Vue)
- Element Plus
- Naive UI

---

## 💡 实现建议

### 1. 先实现基础功能

最小可用版本：
- ChatView（无样式）
- MessageList（纯文本）
- InputBox（基础输入）
- SSE 接收

### 2. 再添加增强功能

- Thinking Trace 展示
- Tool Calls 可视化
- Markdown 渲染
- 动画效果

### 3. 最后优化体验

- 响应式设计
- 加载状态
- 错误处理
- 性能优化

---

## 📚 参考资料

- [EventSource API (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- [Vue 3 Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Marked.js (Markdown)](https://marked.js.org/)
- [Highlight.js (代码高亮)](https://highlightjs.org/)

---

## 🎁 示例代码片段

### SSE 连接示例

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/sessions/test-123/messages?content=Hello'
)

eventSource.addEventListener('reasoning', (e) => {
  const data = JSON.parse(e.data)
  console.log('Reasoning:', data.content)
})

eventSource.addEventListener('answer', (e) => {
  const data = JSON.parse(e.data)
  console.log('Answer:', data.content)
})

eventSource.addEventListener('done', () => {
  console.log('Done!')
  eventSource.close()
})
```

### Markdown 渲染示例

```vue
<script setup>
import { marked } from 'marked'
import hljs from 'highlight.js'

// 配置 marked
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value
    }
    return hljs.highlightAuto(code).value
  }
})

const renderMarkdown = (content) => {
  return marked.parse(content)
}
</script>

<template>
  <div v-html="renderMarkdown(message.content)" />
</template>
```

---

## ⏭️ 下一步

完成 Phase 3 后，可以继续：

- **Phase 4**: Working Memory 可视化
- **Phase 5**: Deep Research Skill
- **Phase 6**: PPT Generation

---

**开发愉快！** 🎉

如有问题，参考：
- `backend/AGENT_ENGINE_README.md`
- `DEVELOPMENT_SUMMARY.md`
- API 文档: http://localhost:8000/api/v1/docs
