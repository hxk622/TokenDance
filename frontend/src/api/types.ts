// Message types
export interface MessageRequest {
  content: string
  stream?: boolean
}

export interface MessageResponse {
  id: string
  role: 'user' | 'assistant' | 'error'
  content: string
  timestamp: string
}

// SSE Event types
export interface SSEEvent {
  event: string
  data: any
}

export interface StartEvent {
  message: string
}

export interface IterationEvent {
  iteration: number
}

export interface ReasoningEvent {
  reasoning: string
}

export interface ToolCallEvent {
  tool: string
  args: Record<string, any>
}

export interface ToolResultEvent {
  tool: string
  result: string
  success: boolean
}

export interface AnswerEvent {
  answer: string
}

export interface ErrorEvent {
  error: string
}

// Session types
export interface Session {
  id: string
  workspace_id: string
  title: string
  status: 'active' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  message_count: number
  total_tokens_used: number
}

// Working Memory types
export interface WorkingMemoryFile {
  path: string
  content: string
  size: number
}

export interface WorkingMemoryResponse {
  task_plan: WorkingMemoryFile
  findings: WorkingMemoryFile
  progress: WorkingMemoryFile
}
