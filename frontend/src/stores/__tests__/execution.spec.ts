/**
 * Execution Store Unit Tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useExecutionStore } from '../execution'

// Mock API services
vi.mock('@/api/services', () => ({
  sessionService: {
    getSession: vi.fn(),
    getSessionMessages: vi.fn(),
    getSessionArtifacts: vi.fn(),
  },
  createSSEConnection: vi.fn(() => ({
    close: vi.fn(),
  })),
  SSEEventType: {
    AGENT_THINKING: 'agent_thinking',
    AGENT_TOOL_CALL: 'agent_tool_call',
    AGENT_TOOL_RESULT: 'agent_tool_result',
    NODE_STARTED: 'node_started',
    NODE_COMPLETED: 'node_completed',
    NODE_FAILED: 'node_failed',
    FILE_CREATED: 'file_created',
    FILE_MODIFIED: 'file_modified',
    FILE_DELETED: 'file_deleted',
    SESSION_COMPLETED: 'session_completed',
    SESSION_FAILED: 'session_failed',
  },
}))

describe('ExecutionStore', () => {
  beforeEach(() => {
    // Create a fresh pinia instance for each test
    setActivePinia(createPinia())
  })

  describe('initial state', () => {
    it('should have null sessionId initially', () => {
      const store = useExecutionStore()
      expect(store.sessionId).toBeNull()
    })

    it('should have empty nodes and edges', () => {
      const store = useExecutionStore()
      expect(store.nodes).toHaveLength(0)
      expect(store.edges).toHaveLength(0)
    })

    it('should have empty logs', () => {
      const store = useExecutionStore()
      expect(store.logs).toHaveLength(0)
    })

    it('should not be running initially', () => {
      const store = useExecutionStore()
      expect(store.isRunning).toBe(false)
    })
  })

  describe('addLog', () => {
    it('should add a log entry', () => {
      const store = useExecutionStore()
      
      store.addLog({
        type: 'thinking',
        nodeId: '1',
        content: 'Test thinking',
      })

      expect(store.logs).toHaveLength(1)
      expect(store.logs[0].type).toBe('thinking')
      expect(store.logs[0].content).toBe('Test thinking')
      expect(store.logs[0].nodeId).toBe('1')
    })

    it('should auto-generate id and timestamp', () => {
      const store = useExecutionStore()
      
      store.addLog({
        type: 'tool-call',
        nodeId: '2',
        content: 'Test tool call',
      })

      expect(store.logs[0].id).toBeDefined()
      expect(store.logs[0].timestamp).toBeDefined()
    })

    it('should limit log count to maxLogs', () => {
      const store = useExecutionStore()
      
      // Add more than maxLogs entries
      for (let i = 0; i < 1100; i++) {
        store.addLog({
          type: 'thinking',
          nodeId: '1',
          content: `Log ${i}`,
        })
      }

      expect(store.logs.length).toBeLessThanOrEqual(1000)
    })
  })

  describe('updateNodeStatus', () => {
    it('should update node status', () => {
      const store = useExecutionStore()
      
      // Initialize with a node
      store.nodes.push({
        id: '1',
        type: 'manus',
        status: 'inactive',
        label: 'Test Node',
        x: 100,
        y: 100,
      })

      store.updateNodeStatus('1', 'active')

      expect(store.nodes[0].status).toBe('active')
    })

    it('should do nothing for non-existent node', () => {
      const store = useExecutionStore()
      
      store.updateNodeStatus('non-existent', 'active')

      // Should not throw
      expect(store.nodes).toHaveLength(0)
    })
  })

  describe('addFileOperation', () => {
    it('should add file operation to the beginning', () => {
      const store = useExecutionStore()
      
      store.addFileOperation({
        path: 'src/test.ts',
        action: 'created',
        timestamp: Date.now(),
      })

      store.addFileOperation({
        path: 'src/test2.ts',
        action: 'modified',
        timestamp: Date.now(),
      })

      expect(store.fileOperations).toHaveLength(2)
      expect(store.fileOperations[0].path).toBe('src/test2.ts')
    })

    it('should limit file operations to 100', () => {
      const store = useExecutionStore()
      
      for (let i = 0; i < 150; i++) {
        store.addFileOperation({
          path: `src/file${i}.ts`,
          action: 'created',
          timestamp: Date.now(),
        })
      }

      expect(store.fileOperations.length).toBeLessThanOrEqual(100)
    })
  })

  describe('reset', () => {
    it('should reset all state', () => {
      const store = useExecutionStore()
      
      // Set some state
      store.sessionId = 'test-session'
      store.nodes.push({
        id: '1',
        type: 'manus',
        status: 'active',
        label: 'Test',
        x: 0,
        y: 0,
      })
      store.addLog({
        type: 'thinking',
        nodeId: '1',
        content: 'Test',
      })

      // Reset
      store.reset()

      expect(store.sessionId).toBeNull()
      expect(store.nodes).toHaveLength(0)
      expect(store.logs).toHaveLength(0)
      expect(store.error).toBeNull()
    })
  })

  describe('computed', () => {
    it('activeNodeId should return the active node', () => {
      const store = useExecutionStore()
      
      store.nodes.push(
        { id: '1', type: 'manus', status: 'success', label: 'Node 1', x: 0, y: 0 },
        { id: '2', type: 'manus', status: 'active', label: 'Node 2', x: 0, y: 0 },
        { id: '3', type: 'coworker', status: 'inactive', label: 'Node 3', x: 0, y: 0 },
      )

      expect(store.activeNodeId).toBe('2')
    })

    it('activeNodeId should return undefined if no active node', () => {
      const store = useExecutionStore()
      
      store.nodes.push(
        { id: '1', type: 'manus', status: 'success', label: 'Node 1', x: 0, y: 0 },
      )

      expect(store.activeNodeId).toBeUndefined()
    })
  })
})
