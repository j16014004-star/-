import request from '@/utils/request'
import type { AxiosResponse } from 'axios'
import type { ApiResponse, Job, PaginatedData } from '@/types'
import type {
  JobApplication,
  JobApplyParams,
  JobPlatformList,
  JobRecommendResultParams,
  JobRecommendResults,
  JobRecommendTask,
  JobSearchParams,
  PlatformLoginSession,
  PlatformLoginStatus,
  StartPlatformLoginParams,
  StartRecommendationParams,
} from './types/job'

type ApiPromise<T> = Promise<ApiResponse<T>>

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

export const jobApi = {
  getPlatforms() {
    return asApiPromise(request.get<ApiResponse<JobPlatformList>>('/job-platforms'))
  },

  startPlatformLogin(data: StartPlatformLoginParams) {
    return asApiPromise(request.post<ApiResponse<PlatformLoginSession>>('/job-platforms/login/start', data))
  },

  getPlatformLoginStatus(loginSessionId: string) {
    return asApiPromise(request.get<ApiResponse<PlatformLoginStatus>>(`/job-platforms/login/${loginSessionId}`))
  },

  startRecommendation(data: StartRecommendationParams) {
    return asApiPromise(request.post<ApiResponse<JobRecommendTask>>('/jobs/recommend/start', data))
  },

  getRecommendationTask(taskId: string) {
    return asApiPromise(request.get<ApiResponse<JobRecommendTask>>(`/jobs/recommend/tasks/${taskId}`))
  },

  getRecommendationResults(taskId: string, params?: JobRecommendResultParams) {
    return asApiPromise(request.get<ApiResponse<JobRecommendResults>>(`/jobs/recommend/tasks/${taskId}/results`, { params }))
  },

  getRecommendations(params?: JobSearchParams) {
    return asApiPromise(request.get<ApiResponse<PaginatedData<Job>>>('/jobs/recommendations', { params }))
  },

  getDetail(id: number) {
    return asApiPromise(request.get<ApiResponse<Job>>(`/jobs/${id}`))
  },

  apply(id: number, data: JobApplyParams) {
    return asApiPromise(request.post<ApiResponse<JobApplication>>(`/jobs/${id}/apply`, data))
  },
}
