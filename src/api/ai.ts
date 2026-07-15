import type { AxiosResponse } from 'axios'
import request from '@/utils/request'
import type { ApiResponse } from '@/types'
import type { AITask } from './types/ai'

type ApiPromise<T> = Promise<ApiResponse<T>>

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

export const aiApi = {
  getTask(taskId: string) {
    return asApiPromise(request.get<ApiResponse<AITask>>(`/ai/tasks/${taskId}`))
  },
}
