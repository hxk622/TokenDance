/**
 * Chat Message Types for StreamingInfo
 * 
 * Supports text messages, interactive forms, and various content types
 */

// Message content types
export type MessageContentType = 'text' | 'form' | 'code' | 'image' | 'browser'

// Message role (who sent the message)
export type MessageRole = 'user' | 'assistant' | 'system'

// Message status
export type MessageStatus = 'thinking' | 'streaming' | 'complete' | 'error'

// Form field types
export type FormFieldType = 'radio' | 'checkbox' | 'input' | 'textarea' | 'tags'

// Form field option
export interface FormFieldOption {
  value: string
  label: string
  description?: string
  icon?: string
}

// Form field definition
export interface FormField {
  id: string
  type: FormFieldType
  label: string
  description?: string
  options?: FormFieldOption[]
  placeholder?: string
  required?: boolean
  // Current value (for controlled form)
  value?: string | string[] | boolean
  // Validation
  minLength?: number
  maxLength?: number
}

// Form group (for collapsible sections)
export interface FormGroup {
  id: string
  title: string
  description?: string
  fields: FormField[]
  collapsed?: boolean
}

// Tool call info
export interface ToolCall {
  name: string
  args?: string
  status?: 'pending' | 'running' | 'success' | 'error'
}

// Chat message
export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  status: MessageStatus
  timestamp: number
  
  // Content type (default: text)
  contentType?: MessageContentType
  
  // For thinking status: specific action being performed
  statusText?: string
  
  // For form content type
  formFields?: FormField[]
  formGroups?: FormGroup[]
  isInteractive?: boolean  // Can user interact with form
  formSubmitted?: boolean  // Has form been submitted
  formValues?: Record<string, unknown>  // Submitted form values
  
  // For tool calls display
  toolCalls?: ToolCall[]
  
  // For code content type
  language?: string
  
  // AnyGen-style: Planning card data
  planning?: PlanningData
  
  // AnyGen-style: Execution timeline steps
  executionSteps?: ExecutionStep[]
  
  // Message metadata
  edited?: boolean
  editedAt?: number
  deprecated?: boolean  // Marked as deprecated after edit
  branchId?: string     // For conversation branching
  parentMessageId?: string
  
  // Quote/reply
  quotedMessageId?: string
  quotedContent?: string
}

// Quote info for input
export interface QuoteInfo {
  messageId: string
  content: string
  role: MessageRole
}

// Image attachment for preview
export interface ImageAttachment {
  id: string
  file: File
  previewUrl: string // blob URL for preview
  dataUrl?: string   // base64 data URL for sending
}

// Document attachment for preview
export interface FileAttachment {
  id: string
  file: File
  dataUrl?: string   // base64 data URL for sending
}

// Chat input state
export interface ChatInputState {
  text: string
  quote?: QuoteInfo
  images?: ImageAttachment[]
  files?: FileAttachment[]
}

// Supported document MIME types
export const SUPPORTED_DOCUMENT_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'text/plain',
  'text/csv',
  'text/markdown',
] as const

export type SupportedDocumentType = typeof SUPPORTED_DOCUMENT_TYPES[number]

// Attachment format for API (matches backend schema)
export interface Attachment {
  type: 'image' | 'document'
  url: string  // base64 data URL
  name?: string
}

// Event payloads
export interface SendMessagePayload {
  content: string
  quote?: QuoteInfo
  attachments?: Attachment[]  // API format
}

export interface FormSubmitPayload {
  messageId: string
  values: Record<string, unknown>
}

export interface EditMessagePayload {
  messageId: string
  newContent: string
}

// Browser action types (for inline browser preview cards)
export type BrowserAction = 'navigate' | 'click' | 'scroll' | 'type' | 'screenshot' | 'extract'

// Browser event for inline preview card
export interface BrowserEvent {
  id: string
  url: string
  action: BrowserAction
  actionDescription?: string
  screenshot?: string  // Base64 encoded
  title?: string
  timestamp: number
  loading?: boolean
}

// ========================================
// AnyGen-style Planning & Timeline Types
// ========================================

// Planning data (思考/规划卡片)
export interface PlanningData {
  title: string          // e.g., "Planning financial analysis"
  content: string        // 思考内容 (支持流式追加)
  collapsed: boolean
  status?: 'thinking' | 'done'
}

// Timeline step icon types
export type StepIconType = 'search' | 'analyze' | 'write' | 'tool' | 'read' | 'plan'

// Timeline step status
export type StepStatus = 'pending' | 'running' | 'done' | 'failed'

// Source (来源信息，带 favicon)
export interface Source {
  url: string
  domain: string
  favicon?: string       // favicon URL, defaults to Google's favicon service
  title?: string
}

// Step child content (步骤内的子内容)
export interface StepChild {
  id: string
  type: 'search' | 'read' | 'analyze' | 'extract'
  title: string
  sources?: Source[]     // 来源 favicon 列表
  collapsed: boolean
  content?: string       // 可选的详细内容
}

// Execution step (单个执行步骤)
export interface ExecutionStep {
  id: string
  title: string          // e.g., "搜索三季报与财务数据"
  status: StepStatus
  collapsed: boolean
  icon: StepIconType
  // 子内容 (搜索结果等)
  children?: StepChild[]
  // 直接关联的来源 (用于简单展示)
  sources?: Source[]
  // 开始和结束时间
  startTime?: number
  endTime?: number
}
