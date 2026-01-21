/**
 * API Services - Central Export
 */

// Session API
export { sessionService } from './session'
export type {
  Session,
  SessionDetail,
  SessionCreate,
  SessionUpdate,
  SessionListResponse,
  Message,
  MessageListResponse,
  Artifact,
  ArtifactListResponse,
} from './session'
export { SessionStatus } from './session'

// Research API
export { researchService } from './research'
export type {
  InterventionResponse,
  PendingInterventionsResponse,
} from './research'

// SSE (Server-Sent Events)
export {
  SSEConnection,
  SSEEventType,
  createSSEConnection,
} from './sse'
export type {
  SSEEvent,
  SSEOptions,
  SSEConnectionError,
  AgentThinkingEvent,
  AgentToolCallEvent,
  AgentToolResultEvent,
  NodeEvent,
  FileEvent,
  // Timeline events
  TimelineSearchEvent,
  TimelineReadEvent,
  TimelineScreenshotEvent,
  TimelineFindingEvent,
  TimelineMilestoneEvent,
} from './sse'
