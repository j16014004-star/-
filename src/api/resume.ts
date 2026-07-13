import request from '@/utils/request'
import type { ApiResponse, Resume, ResumeAnalysis, ResumeOptimizeResult, PaginatedData } from '@/types'
import type { ResumeAnalyzeParams, ResumeOptimizeParams } from './types/resume'

export const resumeApi = {
  getList(params?: { page?: number; page_size?: number }) {
    return request.get<ApiResponse<PaginatedData<Resume>>>('/resumes', { params })
  },

  getDetail(id: number) {
    return request.get<ApiResponse<Resume>>(`/resumes/${id}`)
  },

  upload(file: File, title?: string) {
    const form = new FormData()
    form.append('file', file)
    if (title) form.append('title', title)
    return request.post<ApiResponse<Resume>>('/resumes/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  delete(id: number) {
    return request.delete<ApiResponse<null>>(`/resumes/${id}`)
  },

  analyze(params: ResumeAnalyzeParams) {
    return request.post<ApiResponse<ResumeAnalysis>>(`/resumes/${params.resume_id}/analyze`)
  },

  optimize(params: ResumeOptimizeParams) {
    return request.post<ApiResponse<ResumeOptimizeResult>>(`/resumes/${params.resume_id}/optimize`, params)
  },
}