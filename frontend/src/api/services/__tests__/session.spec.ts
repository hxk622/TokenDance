/**
 * Session Service Unit Tests
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { sessionService, SessionStatus } from '../session'
import apiClient from '../../client'

// Mock apiClient
vi.mock('../../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('SessionService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createSession', () => {
    it('should create a session', async () => {
      const mockSession = {
        id: 'session-1',
        workspace_id: 'workspace-1',
        user_id: 'user-1',
        title: 'Test Session',
        status: SessionStatus.PENDING,
        created_at: '2026-01-14T00:00:00Z',
        updated_at: '2026-01-14T00:00:00Z',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockSession })

      const result = await sessionService.createSession({
        workspace_id: 'workspace-1',
        title: 'Test Session',
      })

      expect(apiClient.post).toHaveBeenCalledWith('/sessions', {
        workspace_id: 'workspace-1',
        title: 'Test Session',
      })
      expect(result).toEqual(mockSession)
    })
  })

  describe('listSessions', () => {
    it('should list sessions with default params', async () => {
      const mockResponse = {
        sessions: [],
        total: 0,
        limit: 20,
        offset: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const result = await sessionService.listSessions({
        workspace_id: 'workspace-1',
      })

      expect(apiClient.get).toHaveBeenCalledWith('/sessions', {
        params: { workspace_id: 'workspace-1' },
      })
      expect(result).toEqual(mockResponse)
    })

    it('should list sessions with filters', async () => {
      const mockResponse = {
        sessions: [],
        total: 0,
        limit: 10,
        offset: 5,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const result = await sessionService.listSessions({
        workspace_id: 'workspace-1',
        limit: 10,
        offset: 5,
        status: SessionStatus.RUNNING,
      })

      expect(apiClient.get).toHaveBeenCalledWith('/sessions', {
        params: {
          workspace_id: 'workspace-1',
          limit: 10,
          offset: 5,
          status: SessionStatus.RUNNING,
        },
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSession', () => {
    it('should get session without details', async () => {
      const mockSession = {
        id: 'session-1',
        workspace_id: 'workspace-1',
        user_id: 'user-1',
        title: 'Test Session',
        status: SessionStatus.RUNNING,
        created_at: '2026-01-14T00:00:00Z',
        updated_at: '2026-01-14T00:00:00Z',
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockSession })

      const result = await sessionService.getSession('session-1')

      expect(apiClient.get).toHaveBeenCalledWith('/sessions/session-1', {
        params: { include_details: false },
      })
      expect(result).toEqual(mockSession)
    })

    it('should get session with details', async () => {
      const mockSessionDetail = {
        id: 'session-1',
        workspace_id: 'workspace-1',
        user_id: 'user-1',
        title: 'Test Session',
        status: SessionStatus.RUNNING,
        message_count: 10,
        artifact_count: 2,
        created_at: '2026-01-14T00:00:00Z',
        updated_at: '2026-01-14T00:00:00Z',
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockSessionDetail })

      const result = await sessionService.getSession('session-1', true)

      expect(apiClient.get).toHaveBeenCalledWith('/sessions/session-1', {
        params: { include_details: true },
      })
      expect(result).toEqual(mockSessionDetail)
    })
  })

  describe('updateSession', () => {
    it('should update session', async () => {
      const mockSession = {
        id: 'session-1',
        workspace_id: 'workspace-1',
        user_id: 'user-1',
        title: 'Updated Title',
        status: SessionStatus.RUNNING,
        created_at: '2026-01-14T00:00:00Z',
        updated_at: '2026-01-14T00:00:00Z',
      }

      vi.mocked(apiClient.patch).mockResolvedValue({ data: mockSession })

      const result = await sessionService.updateSession('session-1', {
        title: 'Updated Title',
      })

      expect(apiClient.patch).toHaveBeenCalledWith('/sessions/session-1', {
        title: 'Updated Title',
      })
      expect(result).toEqual(mockSession)
    })
  })

  describe('deleteSession', () => {
    it('should delete session', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({})

      await sessionService.deleteSession('session-1')

      expect(apiClient.delete).toHaveBeenCalledWith('/sessions/session-1')
    })
  })

  describe('completeSession', () => {
    it('should complete session', async () => {
      const mockSession = {
        id: 'session-1',
        workspace_id: 'workspace-1',
        user_id: 'user-1',
        title: 'Test Session',
        status: SessionStatus.COMPLETED,
        created_at: '2026-01-14T00:00:00Z',
        updated_at: '2026-01-14T00:00:00Z',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockSession })

      const result = await sessionService.completeSession('session-1')

      expect(apiClient.post).toHaveBeenCalledWith('/sessions/session-1/complete')
      expect(result.status).toBe(SessionStatus.COMPLETED)
    })
  })

  describe('getSessionMessages', () => {
    it('should get session messages', async () => {
      const mockResponse = {
        messages: [
          {
            id: 'msg-1',
            session_id: 'session-1',
            role: 'user',
            content: 'Hello',
            created_at: '2026-01-14T00:00:00Z',
          },
        ],
        total: 1,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const result = await sessionService.getSessionMessages('session-1')

      expect(apiClient.get).toHaveBeenCalledWith('/sessions/session-1/messages', {
        params: { limit: undefined },
      })
      expect(result).toEqual(mockResponse)
    })

    it('should get session messages with limit', async () => {
      const mockResponse = {
        messages: [],
        total: 0,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      await sessionService.getSessionMessages('session-1', 50)

      expect(apiClient.get).toHaveBeenCalledWith('/sessions/session-1/messages', {
        params: { limit: 50 },
      })
    })
  })

  describe('getSessionArtifacts', () => {
    it('should get session artifacts', async () => {
      const mockResponse = {
        artifacts: [
          {
            id: 'artifact-1',
            session_id: 'session-1',
            type: 'report',
            title: 'Research Report',
            created_at: '2026-01-14T00:00:00Z',
          },
        ],
        total: 1,
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse })

      const result = await sessionService.getSessionArtifacts('session-1')

      expect(apiClient.get).toHaveBeenCalledWith('/sessions/session-1/artifacts')
      expect(result).toEqual(mockResponse)
    })
  })
})
