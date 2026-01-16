/**
 * TimeLapse API
 * 
 * 时光长廊 - 研究过程视觉记录
 */

import api from './client'
import type { TimeLapsePlayback, TimeLapseSession } from '@/components/execution/browser/types'

export interface TimeLapseSessionSummary {
  sessionId: string
  taskId: string
  title: string
  createdAt: string
  totalDurationMs: number
  frameCount: number
  frameTypes: Record<string, number>
}

/**
 * 获取任务的 TimeLapse 会话摘要
 */
export async function getTimeLapseSession(taskId: string): Promise<TimeLapseSessionSummary | null> {
  try {
    const response = await api.get<TimeLapseSessionSummary>(`/timelapse/task/${taskId}`)
    return response.data
  } catch (error) {
    console.error('Failed to get timelapse session:', error)
    return null
  }
}

/**
 * 获取 TimeLapse 回放数据
 */
export async function getTimeLapsePlayback(sessionId: string): Promise<TimeLapsePlayback | null> {
  try {
    const response = await api.get<TimeLapsePlayback>(`/timelapse/${sessionId}/playback`)
    return response.data
  } catch (error) {
    console.error('Failed to get timelapse playback:', error)
    return null
  }
}

/**
 * 获取完整会话数据
 */
export async function getFullSession(sessionId: string): Promise<TimeLapseSession | null> {
  try {
    const response = await api.get<TimeLapseSession>(`/timelapse/${sessionId}`)
    return response.data
  } catch (error) {
    console.error('Failed to get full session:', error)
    return null
  }
}

/**
 * 列出所有 TimeLapse 会话
 */
export async function listTimeLapseSessions(limit = 20): Promise<TimeLapseSessionSummary[]> {
  try {
    const response = await api.get<TimeLapseSessionSummary[]>('/timelapse', {
      params: { limit }
    })
    return response.data
  } catch (error) {
    console.error('Failed to list timelapse sessions:', error)
    return []
  }
}
