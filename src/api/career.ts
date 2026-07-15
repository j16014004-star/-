import type { AxiosProgressEvent, AxiosResponse } from 'axios'
import request from '@/utils/request'
import type { ApiResponse } from '@/types'
import type {
  CareerPlan,
  CareerPlanCreateParams,
  CareerPlanStartResult,
  CareerPlanningProfile,
  CareerPlanningProfileParams,
  CareerProjectAttachment,
} from './types/career'

type ApiPromise<T> = Promise<ApiResponse<T>>

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

export const careerApi = {
  createProfile(params: CareerPlanningProfileParams) {
    return asApiPromise(
      request.post<ApiResponse<CareerPlanningProfile>>('/career-planning/profiles', params),
    )
  },

  uploadProjectFile(file: File, onProgress?: (percentage: number) => void) {
    const form = new FormData()
    form.append('file', file)
    return asApiPromise(
      request.post<ApiResponse<CareerProjectAttachment>>('/career-plans/project-files/upload', form, {
        onUploadProgress: (event: AxiosProgressEvent) => {
          if (!event.total) return
          onProgress?.(Math.min(99, Math.round((event.loaded / event.total) * 100)))
        },
      }),
    )
  },

  deleteProjectFile(fileId: number) {
    return asApiPromise(
      request.delete<ApiResponse<null>>(`/career-plans/project-files/${fileId}`),
    )
  },

  createPlan(params: CareerPlanCreateParams) {
    return asApiPromise(
      request.post<ApiResponse<CareerPlanStartResult>>('/career-plans', params),
    )
  },

  getPlan(planId: number) {
    return asApiPromise(request.get<ApiResponse<CareerPlan>>(`/career-plans/${planId}`))
  },
}
