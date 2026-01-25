/**
 * Project types for Project-First architecture
 */

// Project status enum
export type ProjectStatus = 'draft' | 'in_progress' | 'completed' | 'archived'

// Project type enum
export type ProjectType =
  | 'research'
  | 'document'
  | 'slides'
  | 'code'
  | 'data_analysis'
  | 'quick_task'

// Conversation purpose enum
export type ConversationPurpose =
  | 'general'
  | 'initial_draft'
  | 'refinement'
  | 'review'
  | 'export'

// Conversation status enum
export type ConversationStatus = 'active' | 'completed' | 'archived'

// Context types
export interface Decision {
  decision: string
  reason?: string
  timestamp: string
}

export interface Failure {
  type: string
  message: string
  learning?: string
  timestamp: string
}

export interface Finding {
  finding: string
  source?: string
  timestamp: string
}

export interface ProjectContext {
  decisions: Decision[]
  failures: Failure[]
  key_findings: Finding[]
  tags: string[]
}

export interface ProjectSettings {
  llm_model: string
  skill_id?: string
}

// Selection context for in-place editing
export interface SelectionRange {
  start: number
  end: number
}

export interface SelectionContext {
  artifact_id: string
  selected_text: string
  selection_range: SelectionRange
}

// Project model
export interface Project {
  id: string
  workspace_id: string
  title: string
  description?: string
  project_type: ProjectType
  status: ProjectStatus
  intent: string
  context?: ProjectContext
  settings?: ProjectSettings
  total_tokens_used: number
  conversation_count: number
  artifact_count: number
  created_at: string
  updated_at: string
  last_accessed_at?: string
}

// Conversation model
export interface Conversation {
  id: string
  project_id: string
  title: string
  purpose: ConversationPurpose
  status: ConversationStatus
  tokens_used: number
  message_count: number
  created_at: string
  updated_at: string
  completed_at?: string
  selection_context?: SelectionContext
}

// API request/response types
export interface ProjectCreate {
  workspace_id: string
  intent: string
  title?: string
  description?: string
  project_type?: ProjectType
  settings?: ProjectSettings
}

export interface ProjectUpdate {
  title?: string
  description?: string
  status?: ProjectStatus
  context?: Partial<ProjectContext>
  settings?: Partial<ProjectSettings>
}

export interface ConversationCreate {
  purpose?: ConversationPurpose
  title?: string
  selection?: SelectionContext
}

export interface ChatMessage {
  message: string
  conversation_id?: string
  selection?: SelectionContext
}

export interface ChatResponse {
  status: string
  project_id: string
  conversation_id: string
  session_id: string  // For SSE streaming connection
  message: string
  context_available: {
    intent: boolean
    decisions_count: number
    failures_count: number
    findings_count: number
    artifacts_count: number
  }
  selection?: SelectionContext
  sse_endpoint?: string  // SSE endpoint URL
}

export interface ProjectList {
  items: Project[]
  total: number
  limit: number
  offset: number
}

export interface ConversationList {
  items: Conversation[]
  total: number
}

export interface ProjectContextResponse {
  intent: string
  decisions: Decision[]
  failures: Failure[]
  key_findings: Finding[]
  artifacts: Array<{
    id: string
    name: string
    type: string
    preview?: string
  }>
}
