import request from '@/utils/request'
import type { ApiResponse, CareerPlan } from '@/types'
import type { CareerPlanParams } from './types/career'

export const careerApi = {
  getPlan(params: CareerPlanParams) {
    return request.post<ApiResponse<CareerPlan>>('/career/plan', params)
  },
}