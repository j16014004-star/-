import request from '@/utils/request'
import type { ApiResponse, AgentTask } from '@/types'
import type { AgentTaskCreateParams } from './types/agent'
import type { AxiosResponse } from 'axios'

type ApiPromise<T> = Promise<ApiResponse<T>>

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

export const agentApi = {
  getTasks() {
    return asApiPromise(request.get<ApiResponse<AgentTask[]>>('/agent/tasks'))
  },

  getTaskDetail(id: number) {
    return asApiPromise(request.get<ApiResponse<AgentTask>>(`/agent/tasks/${id}`))
  },

  createTask(params: AgentTaskCreateParams) {
    return asApiPromise(request.post<ApiResponse<AgentTask>>('/agent/tasks', params))
  },

  startTask(id: number) {
    return asApiPromise(request.post<ApiResponse<AgentTask>>(`/agent/tasks/${id}/start`))
  },

  pauseTask(id: number) {
    return asApiPromise(request.post<ApiResponse<AgentTask>>(`/agent/tasks/${id}/pause`))
  },

  stopTask(id: number) {
    return asApiPromise(request.post<ApiResponse<AgentTask>>(`/agent/tasks/${id}/stop`))
  },

  deleteTask(id: number) {
    return asApiPromise(request.delete<ApiResponse<null>>(`/agent/tasks/${id}`))
  },
}
