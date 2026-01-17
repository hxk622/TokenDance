<template>
  <div class="research-assistant" :class="{ 'is-expanded': isExpanded }">
    <!-- Header -->
    <div class="assistant-header" @click="toggleExpand">
      <div class="header-left">
        <div class="assistant-avatar">🧠</div>
        <div class="header-text">
          <h4 class="assistant-name">研究助手</h4>
          <p class="assistant-status">{{ statusText }}</p>
        </div>
      </div>
      <button class="toggle-button">
        <span class="toggle-icon">{{ isExpanded ? '−' : '+' }}</span>
      </button>
    </div>

    <!-- Content (collapsible) -->
    <div v-show="isExpanded" class="assistant-content">
      <!-- Quick Questions -->
      <div v-if="!hasConversation" class="quick-questions">
        <p class="questions-label">快速提问</p>
        <div class="questions-list">
          <button
            v-for="(question, idx) in quickQuestions"
            :key="idx"
            class="question-chip"
            @click="askQuestion(question)"
          >
            {{ question }}
          </button>
        </div>
      </div>

      <!-- Conversation -->
      <div v-else class="conversation" ref="conversationRef">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message"
          :class="msg.role"
        >
          <div class="message-avatar">
            {{ msg.role === 'user' ? '👤' : '🧠' }}
          </div>
          <div class="message-content">
            <p class="message-text" v-html="formatMessage(msg.content)"></p>
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading" class="message assistant loading">
          <div class="message-avatar">🧠</div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Follow-up Questions -->
      <div v-if="hasConversation && suggestedQuestions.length > 0" class="follow-up-questions">
        <p class="questions-label">继续追问</p>
        <div class="questions-list">
          <button
            v-for="(question, idx) in suggestedQuestions"
            :key="idx"
            class="question-chip small"
            @click="askQuestion(question)"
          >
            {{ question }}
          </button>
        </div>
      </div>

      <!-- Input Area -->
      <div class="input-area">
        <input
          v-model="inputText"
          type="text"
          class="input-field"
          placeholder="输入您的问题..."
          @keyup.enter="sendMessage"
          :disabled="isLoading"
        />
        <button
          class="send-button"
          :disabled="!inputText.trim() || isLoading"
          @click="sendMessage"
        >
          发送
        </button>
      </div>

      <!-- Actions -->
      <div class="assistant-actions">
        <button class="action-link" @click="clearConversation">
          清空对话
        </button>
        <button class="action-link" @click="exportConversation">
          导出记录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const props = defineProps<{
  symbol?: string
  stockName?: string
  stockInfo?: any
  analysisResults?: any
}>()

const emit = defineEmits<{
  (e: 'ask', question: string): void
}>()

// State
const isExpanded = ref(true)
const isLoading = ref(false)
const inputText = ref('')
const messages = ref<Message[]>([])
const conversationRef = ref<HTMLElement | null>(null)

// Computed
const hasConversation = computed(() => messages.value.length > 0)

const statusText = computed(() => {
  if (isLoading.value) return '思考中...'
  if (!props.symbol) return '选择股票开始分析'
  return `分析 ${props.stockName || props.symbol}`
})

// Quick questions based on current stock
const quickQuestions = computed(() => {
  if (!props.symbol) {
    return [
      '推荐几只白酒龙头股',
      '当前市场热点是什么',
      '如何进行股票估值分析',
    ]
  }
  
  const name = props.stockName || props.symbol
  return [
    `${name}的主营业务是什么`,
    `${name}的财务状况如何`,
    `${name}当前估值合理吗`,
    `${name}有哪些风险点`,
    `${name}的竞争对手有哪些`,
    `${name}未来增长前景如何`,
  ]
})

// Suggested follow-up questions
const suggestedQuestions = computed(() => {
  if (messages.value.length === 0) return []
  
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage.role !== 'assistant') return []
  
  // Generate context-aware follow-up questions
  const name = props.stockName || props.symbol || '该股票'
  return [
    '能详细解释一下吗',
    `和同行业相比如何`,
    '有什么投资建议',
  ]
})

// Methods
function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

async function askQuestion(question: string) {
  inputText.value = question
  await sendMessage()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return
  
  // Add user message
  messages.value.push({
    role: 'user',
    content: text,
    timestamp: new Date(),
  })
  
  inputText.value = ''
  isLoading.value = true
  
  // Scroll to bottom
  await nextTick()
  scrollToBottom()
  
  // Emit event for parent to handle
  emit('ask', text)
  
  // Simulate AI response (in production, this would call the backend)
  await simulateResponse(text)
  
  isLoading.value = false
  await nextTick()
  scrollToBottom()
}

async function simulateResponse(question: string) {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000))
  
  // Generate a contextual response
  let response = ''
  const name = props.stockName || props.symbol || '该股票'
  
  if (question.includes('主营业务')) {
    response = `根据公开资料，${name}主要从事相关业务。建议您查看公司最新年报获取详细信息。\n\n**注意：** 以上信息仅供参考，不构成投资建议。`
  } else if (question.includes('财务状况')) {
    response = `从财务分析来看，${name}的整体财务状况需要综合多个指标评估。\n\n主要关注点：\n- 盈利能力：ROE、净利率\n- 偿债能力：资产负债率\n- 成长能力：营收增速\n\n建议结合左侧的财务分析卡片查看详细数据。`
  } else if (question.includes('估值')) {
    response = `估值分析需要综合多个因素考虑：\n\n1. **相对估值**：PE、PB、PS 与历史和行业对比\n2. **绝对估值**：DCF 模型估算内在价值\n3. **市场情绪**：当前市场对该股票的预期\n\n请参考左侧估值分析卡片获取详细数据。\n\n**免责声明：** 估值仅供参考，不代表实际价格预测。`
  } else if (question.includes('风险')) {
    response = `投资${name}需关注以下风险：\n\n1. **行业风险**：行业周期性、政策变化\n2. **经营风险**：竞争加剧、成本上升\n3. **财务风险**：债务水平、现金流\n4. **市场风险**：估值波动、流动性\n\n**重要提示：** 投资有风险，入市需谨慎。`
  } else if (question.includes('竞争')) {
    response = `${name}的竞争格局分析需要考虑：\n\n- 行业集中度\n- 主要竞争对手\n- 核心竞争优势\n- 市场份额变化趋势\n\n建议使用行业对比功能深入分析。`
  } else {
    response = `感谢您的提问。关于"${question}"，这是一个很好的问题。\n\n作为研究助手，我可以帮您：\n- 解读财务数据\n- 分析估值水平\n- 评估市场情绪\n- 识别潜在风险\n\n请告诉我您想深入了解的方面。`
  }
  
  messages.value.push({
    role: 'assistant',
    content: response,
    timestamp: new Date(),
  })
}

function scrollToBottom() {
  if (conversationRef.value) {
    conversationRef.value.scrollTop = conversationRef.value.scrollHeight
  }
}

function clearConversation() {
  messages.value = []
}

function exportConversation() {
  const text = messages.value
    .map(m => `[${m.role === 'user' ? '用户' : '助手'}] ${m.content}`)
    .join('\n\n')
  
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `research-${props.symbol || 'conversation'}-${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

function formatMessage(content: string): string {
  // Convert markdown-like formatting to HTML
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Watch for symbol changes to reset conversation
watch(() => props.symbol, () => {
  messages.value = []
})
</script>

<style scoped>
.research-assistant {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  transition: all 300ms ease;
}

/* Header */
.assistant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  cursor: pointer;
  transition: background 200ms ease;
}

.assistant-header:hover {
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.assistant-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.assistant-name {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.assistant-status {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0.125rem 0 0 0;
}

.toggle-button {
  width: 28px;
  height: 28px;
  border: none;
  background: #ffffff;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toggle-icon {
  font-size: 1.25rem;
  font-weight: 300;
  color: #6b7280;
}

/* Content */
.assistant-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 500px;
}

/* Quick Questions */
.quick-questions,
.follow-up-questions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.questions-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  margin: 0;
}

.questions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.question-chip {
  padding: 0.5rem 0.875rem;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  font-size: 0.8125rem;
  color: #374151;
  cursor: pointer;
  transition: all 200ms ease;
}

.question-chip:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.question-chip.small {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

/* Conversation */
.conversation {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-right: 0.5rem;
  max-height: 300px;
}

.message {
  display: flex;
  gap: 0.75rem;
  animation: fadeIn 300ms ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
}

.message-content {
  max-width: 80%;
}

.message-text {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}

.message.user .message-text {
  background: #111827;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: #f3f4f6;
  color: #374151;
  border-bottom-left-radius: 4px;
}

.message-time {
  display: block;
  font-size: 0.625rem;
  color: #9ca3af;
  margin-top: 0.25rem;
  text-align: right;
}

.message.user .message-time {
  text-align: right;
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 0.75rem 1rem;
  background: #f3f4f6;
  border-radius: 12px;
  border-bottom-left-radius: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #9ca3af;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input Area */
.input-area {
  display: flex;
  gap: 0.5rem;
}

.input-field {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  outline: none;
  transition: border-color 200ms ease;
}

.input-field:focus {
  border-color: #3b82f6;
}

.input-field:disabled {
  background: #f9fafb;
}

.send-button {
  padding: 0.75rem 1.25rem;
  background: #111827;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
}

.send-button:hover:not(:disabled) {
  background: #1f2937;
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Actions */
.assistant-actions {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid #f3f4f6;
}

.action-link {
  background: none;
  border: none;
  font-size: 0.75rem;
  color: #6b7280;
  cursor: pointer;
  transition: color 200ms ease;
}

.action-link:hover {
  color: #3b82f6;
}

/* Responsive */
@media (max-width: 640px) {
  .assistant-content {
    max-height: 400px;
  }
  
  .conversation {
    max-height: 200px;
  }
}
</style>
