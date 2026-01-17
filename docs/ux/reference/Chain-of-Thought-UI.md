# TokenDance 推理链可视化 UI设计

> Version: 1.0.0 | MVP阶段
> Last Updated: 2026-01-08

## 1. 概念定义

### 1.1 什么是推理链可视化？

**推理链可视化（Chain-of-Thought Visualization）** 或称 **执行追踪（Execution Tracing）**，是AI Agent产品的标准UI范式，用于实时展示Agent的思考、决策和执行过程。

在Manus、ChatGPT o1、OpenManus等自主Agent产品中，这已成为核心交互模式。

### 1.2 三种核心名称

| 名称 | 英文 | 侧重点 |
|-----|------|--------|
| **思维链/推理链** | Chain of Thought (CoT) | AI内部思考过程的可视化 |
| **步骤流/任务拆解** | Step-by-Step Task Breakdown | 执行步骤的清晰展示 |
| **Agent可观测性** | Agent Observability UI | 工具调用和资源访问追踪 |

## 2. 为什么需要这种UI？

### 2.1 核心价值

| 价值维度 | 用户痛点 | 解决方案 |
|---------|---------|---------|
| **缓解等待焦虑** | Agent处理复杂任务需要几十秒甚至数分钟 | 实时"心跳"显示，让用户知道Agent在工作 |
| **建立信任** | 用户怀疑AI直接给出的结果 | 展示推理链，可验证是否搜索了正确的信息 |
| **逻辑验证** | 担心Agent遗漏关键步骤 | 检查每个决策点，确认没有逻辑跳跃 |
| **可调试性** | 开发者难以定位问题 | 完整的执行轨迹，快速发现错误节点 |

### 2.2 TokenDance的应用场景

#### Deep Research（深度研究）
```
用户看到：
1. 🤔 正在分析研究主题...
2. 🔍 搜索"AI Agent市场规模 2024"... (3个结果)
3. 📄 读取 gartner.com/research/... 
4. 🔍 搜索"AI Agent主要玩家"... (5个结果)
5. 📊 正在聚合信息...
6. ✅ 生成报告完成

价值：用户清楚看到Agent查了哪些来源，建立信任
```

#### AI PPT生成
```
用户看到：
1. 📝 生成大纲... (完成)
2. 🎨 第1页：封面 - 生成中...
3. ✅ 第1页：封面 - 完成
4. 🎨 第2页：市场概述 - 生成中...
5. ⚠️  第2页：内容过长，正在精简...
6. ✅ 第2页：市场概述 - 完成

价值：明确进度，减少焦虑
```

## 3. UI组成要素

### 3.1 状态标签（Status Badge）

```vue
<template>
  <div class="flex items-center gap-2 text-sm">
    <StatusIcon :type="status" class="w-4 h-4" />
    <span>{{ statusText }}</span>
  </div>
</template>

<script setup>
const statusTypes = {
  thinking: { icon: '🤔', text: '思考中', color: 'text-blue-400' },
  searching: { icon: '🔍', text: '搜索中', color: 'text-purple-400' },
  analyzing: { icon: '📊', text: '分析中', color: 'text-yellow-400' },
  generating: { icon: '✍️', text: '生成中', color: 'text-green-400' },
  verifying: { icon: '✔️', text: '验证中', color: 'text-teal-400' },
  completed: { icon: '✅', text: '完成', color: 'text-green-500' },
  failed: { icon: '❌', text: '失败', color: 'text-red-500' }
}
</script>
```

### 3.2 动作实体（Action Entity）

**明确展示Agent的具体操作**

```vue
<template>
  <div class="mb-2 pl-6 border-l-2 border-accent-primary">
    <!-- 工具调用 -->
    <div class="text-sm text-text-secondary mb-1">
      <span class="font-mono">web_search</span>
      <span class="text-text-tertiary mx-2">→</span>
      <span>"AI Agent市场规模"</span>
    </div>
    
    <!-- 访问的资源 -->
    <div v-if="resources.length" class="space-y-1">
      <div v-for="url in resources" :key="url" 
           class="text-xs text-text-tertiary truncate">
        📄 {{ url }}
      </div>
    </div>
    
    <!-- 执行的代码 -->
    <div v-if="code" class="mt-2">
      <CodeBlock :code="code" language="python" />
    </div>
  </div>
</template>
```

### 3.3 可折叠结构（Collapsible Structure）

**默认收起详细日志，点击展开查看"思维细节"**

```vue
<template>
  <div class="rounded-lg bg-bg-tertiary/30 overflow-hidden">
    <!-- 折叠头部 -->
    <button @click="expanded = !expanded"
            class="w-full px-4 py-2 flex items-center justify-between
                   text-sm hover:bg-bg-tertiary/50 transition-colors">
      <div class="flex items-center gap-2">
        <ChevronRightIcon 
          class="w-4 h-4 transition-transform"
          :class="{ 'rotate-90': expanded }" 
        />
        <span class="font-medium">{{ title }}</span>
        <StatusBadge :status="status" />
      </div>
      <span class="text-xs text-text-tertiary">
        {{ duration }}
      </span>
    </button>
    
    <!-- 展开内容 -->
    <div v-show="expanded" 
         class="px-4 py-3 border-t border-border-default
                text-sm text-text-secondary space-y-2">
      <slot />
    </div>
  </div>
</template>
```

### 3.4 进度反馈（Progress Indicator）

**明确告知任务完成进度**

```vue
<template>
  <div class="space-y-2">
    <!-- 进度条 -->
    <div class="flex items-center justify-between text-sm mb-1">
      <span class="font-medium">生成PPT</span>
      <span class="text-text-tertiary">{{ current }}/{{ total }}</span>
    </div>
    
    <div class="h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
      <div class="h-full bg-accent-primary transition-all duration-300"
           :style="{ width: `${progress}%` }" />
    </div>
    
    <!-- 步骤列表 -->
    <div class="mt-3 space-y-1.5">
      <div v-for="(step, index) in steps" :key="index"
           class="flex items-center gap-2 text-sm">
        <StepIcon :status="step.status" />
        <span :class="getStepTextClass(step.status)">
          {{ step.label }}
        </span>
        <span v-if="step.status === 'running'" 
              class="text-xs text-text-tertiary">
          {{ step.elapsed }}s
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
const getStepTextClass = (status) => {
  return {
    'pending': 'text-text-tertiary',
    'running': 'text-text-primary',
    'completed': 'text-text-secondary line-through',
    'failed': 'text-error'
  }[status]
}
</script>
```

## 4. 完整组件示例

### 4.1 ExecutionTraceBlock（执行追踪块）

```vue
<template>
  <div class="space-y-3">
    <!-- 主标题 -->
    <div class="flex items-center gap-2">
      <SpinnerIcon v-if="isRunning" class="w-4 h-4 animate-spin text-accent-primary" />
      <CheckCircleIcon v-else-if="isCompleted" class="w-4 h-4 text-success" />
      <span class="font-medium">{{ title }}</span>
    </div>
    
    <!-- 步骤列表 -->
    <div class="space-y-2">
      <ExecutionStep
        v-for="step in steps"
        :key="step.id"
        :step="step"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  title: String,
  steps: Array,
  status: String
})

const isRunning = computed(() => props.status === 'running')
const isCompleted = computed(() => props.status === 'completed')
</script>
```

### 4.2 ExecutionStep（单个执行步骤）

```vue
<template>
  <div class="rounded-lg bg-bg-secondary/50">
    <!-- 步骤头部（始终可见） -->
    <div class="px-4 py-3">
      <div class="flex items-start gap-3">
        <!-- 状态图标 -->
        <div class="flex-shrink-0 mt-0.5">
          <LoaderIcon v-if="step.status === 'running'" 
                      class="w-4 h-4 animate-spin text-accent-primary" />
          <CheckIcon v-else-if="step.status === 'completed'" 
                     class="w-4 h-4 text-success" />
          <XIcon v-else-if="step.status === 'failed'" 
                 class="w-4 h-4 text-error" />
          <CircleIcon v-else 
                      class="w-4 h-4 text-text-tertiary" />
        </div>
        
        <!-- 步骤内容 -->
        <div class="flex-1 min-w-0">
          <!-- 标题 -->
          <div class="flex items-center gap-2 mb-1">
            <span class="font-medium text-sm">{{ step.title }}</span>
            <span v-if="step.duration" 
                  class="text-xs text-text-tertiary">
              {{ step.duration }}ms
            </span>
          </div>
          
          <!-- 简要描述 -->
          <div class="text-sm text-text-secondary">
            {{ step.description }}
          </div>
          
          <!-- 工具调用（如果有） -->
          <div v-if="step.toolCall" 
               class="mt-2 px-3 py-2 rounded bg-bg-tertiary/50">
            <div class="flex items-center gap-2 text-xs font-mono">
              <span class="text-accent-primary">{{ step.toolCall.name }}</span>
              <span class="text-text-tertiary">(</span>
              <span>{{ formatParams(step.toolCall.params) }}</span>
              <span class="text-text-tertiary">)</span>
            </div>
          </div>
          
          <!-- 访问的资源 -->
          <div v-if="step.resources?.length" class="mt-2 space-y-1">
            <div v-for="url in step.resources" :key="url"
                 class="text-xs text-text-tertiary truncate">
              <LinkIcon class="inline w-3 h-3 mr-1" />
              {{ url }}
            </div>
          </div>
        </div>
        
        <!-- 展开/折叠按钮 -->
        <button v-if="step.details"
                @click="toggleDetails"
                class="flex-shrink-0 p-1 hover:bg-bg-tertiary rounded">
          <ChevronDownIcon 
            class="w-4 h-4 transition-transform"
            :class="{ 'rotate-180': showDetails }" 
          />
        </button>
      </div>
    </div>
    
    <!-- 详细信息（可折叠） -->
    <div v-if="showDetails && step.details" 
         class="px-4 pb-3 border-t border-border-default">
      <div class="pt-3 text-sm text-text-secondary whitespace-pre-wrap">
        {{ step.details }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  step: Object
})

const showDetails = ref(false)

const toggleDetails = () => {
  showDetails.value = !showDetails.value
}

const formatParams = (params) => {
  return Object.entries(params)
    .map(([k, v]) => `${k}="${v}"`)
    .join(', ')
}
</script>
```

## 5. 实战示例

### 5.1 Deep Research完整流程展示

```vue
<template>
  <div class="space-y-4">
    <!-- 执行追踪容器 -->
    <ExecutionTraceBlock
      title="深度研究：AI Agent市场"
      :steps="researchSteps"
      :status="overallStatus"
    />
  </div>
</template>

<script setup>
const researchSteps = ref([
  {
    id: '1',
    title: '分析研究主题',
    description: '识别关键词，拆解搜索维度',
    status: 'completed',
    duration: 1200,
    details: '将主题拆解为：市场规模、主要玩家、技术趋势、挑战'
  },
  {
    id: '2',
    title: '多源搜索',
    description: '并行搜索4个维度',
    status: 'completed',
    duration: 3500,
    toolCall: {
      name: 'web_search',
      params: { query: 'AI Agent市场规模 2024', num_results: 5 }
    },
    resources: [
      'https://gartner.com/research/ai-agent-market',
      'https://idc.com/reports/ai-2024',
      'https://techcrunch.com/ai-agent-growth'
    ]
  },
  {
    id: '3',
    title: '内容提取与摘要',
    description: '从3个高质量来源提取信息',
    status: 'running',
    toolCall: {
      name: 'read_url',
      params: { url: 'gartner.com/...', mode: 'markdown' }
    }
  },
  {
    id: '4',
    title: '信息聚合',
    description: '去重、交叉验证、评估可信度',
    status: 'pending'
  },
  {
    id: '5',
    title: '生成结构化报告',
    description: '整合结论，标注引用来源',
    status: 'pending'
  }
])
</script>
```

## 6. 技术实现

### 6.1 协议层面：AG-UI / MCP

**使用标准协议推送执行事件**

```python
# 后端：发送执行事件到前端

from fastapi import WebSocket

class ExecutionEventStream:
    async def send_thinking_event(self, ws: WebSocket, content: str):
        await ws.send_json({
            "type": "execution.thinking",
            "data": {
                "content": content,
                "timestamp": now()
            }
        })
    
    async def send_tool_call_event(self, ws: WebSocket, tool_call: dict):
        await ws.send_json({
            "type": "execution.tool_call",
            "data": {
                "id": tool_call["id"],
                "name": tool_call["name"],
                "params": tool_call["params"],
                "status": "running"
            }
        })
    
    async def send_tool_result_event(self, ws: WebSocket, result: dict):
        await ws.send_json({
            "type": "execution.tool_result",
            "data": {
                "id": result["id"],
                "status": result["status"],
                "summary": result["summary"],
                "duration": result["duration"]
            }
        })
    
    async def send_step_complete_event(self, ws: WebSocket, step: dict):
        await ws.send_json({
            "type": "execution.step_complete",
            "data": step
        })
```

### 6.2 前端：实时接收与渲染

```typescript
// composables/useExecutionTrace.ts

export function useExecutionTrace(sessionId: string) {
  const steps = ref<ExecutionStep[]>([])
  const ws = ref<WebSocket | null>(null)
  
  const connect = () => {
    ws.value = new WebSocket(`ws://api/v1/ws?session=${sessionId}`)
    
    ws.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      
      switch (message.type) {
        case 'execution.thinking':
          addThinkingStep(message.data)
          break
        
        case 'execution.tool_call':
          addToolCallStep(message.data)
          break
        
        case 'execution.tool_result':
          updateToolCallResult(message.data)
          break
        
        case 'execution.step_complete':
          completeStep(message.data)
          break
      }
    }
  }
  
  const addThinkingStep = (data: any) => {
    steps.value.push({
      id: generateId(),
      type: 'thinking',
      title: '正在思考...',
      description: data.content,
      status: 'running',
      timestamp: data.timestamp
    })
  }
  
  const addToolCallStep = (data: any) => {
    steps.value.push({
      id: data.id,
      type: 'tool_call',
      title: `调用工具: ${data.name}`,
      description: formatParams(data.params),
      status: 'running',
      toolCall: data
    })
  }
  
  return { steps, connect }
}
```

## 7. 最佳实践

### 7.1 信息密度控制

```
✅ 好的实践：
- 思考中：分析用户需求...
- 搜索中：查询"AI Agent市场"（5个结果）
- 读取中：gartner.com/...

❌ 坏的实践：
- 步骤1
- 步骤2
- 步骤3
```

### 7.2 性能优化

- **虚拟滚动**：超过50个步骤时启用虚拟列表
- **懒加载详情**：折叠内容按需加载
- **节流更新**：高频事件合并（如思考内容流式更新）

### 7.3 错误处理展示

```vue
<div v-if="step.status === 'failed'" class="mt-2 p-3 rounded bg-error/10">
  <div class="flex items-start gap-2">
    <AlertTriangleIcon class="w-4 h-4 text-error flex-shrink-0 mt-0.5" />
    <div>
      <div class="text-sm font-medium text-error">执行失败</div>
      <div class="text-xs text-error/80 mt-1">{{ step.error }}</div>
      <button v-if="step.canRetry" 
              class="mt-2 text-xs text-accent-primary hover:underline">
        重试
      </button>
    </div>
  </div>
</div>
```

## 8. 参考资源

### 开源组件库
- **AI SDK Core Components**：Vercel提供的ChainOfThought组件
- **LangChain UI**：官方UI组件库
- **OpenManus UI**：开源Agent UI参考

### 协议标准
- **AG-UI Protocol**：Agent UI标准协议
- **MCP (Model Context Protocol)**：Anthropic推出的上下文协议

## 9. 附录

### A. 状态类型完整列表

| 状态 | 图标 | 颜色 | 说明 |
|-----|------|------|------|
| pending | ○ | gray | 待执行 |
| thinking | 🤔 | blue | 思考推理中 |
| planning | 📋 | indigo | 制定计划中 |
| searching | 🔍 | purple | 网页搜索中 |
| reading | 📄 | cyan | 读取内容中 |
| analyzing | 📊 | yellow | 分析数据中 |
| generating | ✍️ | green | 生成内容中 |
| executing | ⚡ | orange | 执行代码中 |
| verifying | ✔️ | teal | 验证结果中 |
| completed | ✅ | green | 已完成 |
| failed | ❌ | red | 失败 |

### B. 相关文档

- [UI设计文档](./UI-Design.md)
- [PRD文档](../product/PRD.md)
- [HLD文档](../architecture/HLD.md)
