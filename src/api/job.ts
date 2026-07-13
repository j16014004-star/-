import request from '@/utils/request'
import type { ApiResponse, Job, PaginatedData } from '@/types'
import type { JobSearchParams } from './types/job'

export const jobApi = {
  getRecommendations(params?: JobSearchParams) {
    return request.get<ApiResponse<PaginatedData<Job>>>('/jobs/recommendations', { params })
  },

  getDetail(id: number) {
    return request.get<ApiResponse<Job>>(`/jobs/${id}`)
  },
}