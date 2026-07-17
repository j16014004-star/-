import request from '@/utils/request'
import type { ApiResponse } from '@/types'
import type { AxiosResponse } from 'axios'
import type {
  AnswerSubmitResult,
  InterviewAnswerParams,
  InterviewCreateParams,
  InterviewItem,
  InterviewOptions,
  InterviewQuestion,
  InterviewReportDetail,
} from './types/interview'

type ApiPromise<T> = Promise<ApiResponse<T>>

function api<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

export const interviewApi = {
  getOptions: () => api(request.get<ApiResponse<InterviewOptions>>('/interviews/options')),
  getList: () => api(request.get<ApiResponse<InterviewItem[]>>('/interviews')),
  getDetail: (id: number) => api(request.get<ApiResponse<InterviewItem>>(`/interviews/${id}`)),
  create: (params: InterviewCreateParams) =>
    api(request.post<ApiResponse<InterviewItem>>('/interviews', params)),
  startInterview: (id: number) =>
    api(request.post<ApiResponse<InterviewItem>>(`/interviews/${id}/start`)),
  getNextQuestion: (id: number) =>
    api(request.get<ApiResponse<InterviewQuestion | null>>(`/interviews/${id}/next-question`)),
  submitAnswer: (id: number, params: InterviewAnswerParams) =>
    api(request.post<ApiResponse<AnswerSubmitResult>>(`/interviews/${id}/answer`, params)),
  finishInterview: (id: number) =>
    api(request.post<ApiResponse<InterviewReportDetail>>(`/interviews/${id}/finish`)),
  getReport: (id: number) =>
    api(request.get<ApiResponse<InterviewReportDetail>>(`/interviews/${id}/report`)),
  retryWeaknesses: (id: number) =>
    api(request.post<ApiResponse<InterviewItem>>(`/interviews/${id}/retry`)),
  delete: (id: number) => api(request.delete<ApiResponse<null>>(`/interviews/${id}`)),
}
