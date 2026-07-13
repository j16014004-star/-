import request from '@/utils/request'
import type { ApiResponse, Interview, InterviewQuestion } from '@/types'
import type { InterviewCreateParams, InterviewAnswerParams } from './types/interview'

export const interviewApi = {
  getList() {
    return request.get<ApiResponse<Interview[]>>('/interviews')
  },

  getDetail(id: number) {
    return request.get<ApiResponse<Interview>>(`/interviews/${id}`)
  },

  create(params: InterviewCreateParams) {
    return request.post<ApiResponse<Interview>>('/interviews', params)
  },

  startInterview(id: number) {
    return request.post<ApiResponse<Interview>>(`/interviews/${id}/start`)
  },

  getNextQuestion(id: number) {
    return request.get<ApiResponse<InterviewQuestion>>(`/interviews/${id}/next-question`)
  },

  submitAnswer(id: number, params: InterviewAnswerParams) {
    return request.post<ApiResponse<InterviewQuestion>>(`/interviews/${id}/answer`, params)
  },

  finishInterview(id: number) {
    return request.post<ApiResponse<Interview>>(`/interviews/${id}/finish`)
  },

  getReport(id: number) {
    return request.get<ApiResponse<Interview>>(`/interviews/${id}/report`)
  },

  delete(id: number) {
    return request.delete<ApiResponse<null>>(`/interviews/${id}`)
  },
}