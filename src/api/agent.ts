import request from '@/utils/request'
import type { ApiResponse, AgentTask } from '@/types'
import type { AgentTaskCreateParams } from './types/agent'

export const agentApi = {
  getTasks() {
    return request.get<ApiResponse<AgentTask[]>>('/agent/tasks')
  },

  getTaskDetail(id: number) {
    return request.get<ApiResponse<AgentTask>>(`/agent/tasks/${id}`)
  },

  createTask(params: AgentTaskCreateParams) {
    return request.post<ApiResponse<AgentTask>>('/agent/tasks', params)
  },

  startTask(id: number) {
    return request.post<ApiResponse<AgentTask>>(`/agent/tasks/${id}/start`)
  },

  pauseTask(id: number) {
    return request.post<ApiResponse<AgentTask>>(`/agent/tasks/${id}/pause`)
  },

  stopTask(id: number) {
    return request.post<ApiResponse<AgentTask>>(`/agent/tasks/${id}/stop`)
  },

  deleteTask(id: number) {
    return request.delete<ApiResponse<null>>(`/agent/tasks/${id}`)
  },
}