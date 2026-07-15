import request from '@/utils/request'
import type { AxiosProgressEvent, AxiosResponse } from 'axios'
import type { ApiResponse, Resume, ResumeOptimizeResult, PaginatedData } from '@/types'
import type {
  ResumeOptimizationAiPreviewParams,
  ResumeOptimizationConfirmationPreview,
  ResumeOptimizationDismissConfirmParams,
  ResumeOptimizationManualPreviewParams,
  ResumeOptimizationSaveParams,
  ResumeOptimizeParams,
} from './types/resume'
import type { AIStartTaskResult } from './types/ai'

type ApiPromise<T> = Promise<ApiResponse<T>>
type UploadProgressHandler = (percentage: number) => void

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

function getUploadPercentage(event: AxiosProgressEvent) {
  if (!event.total) return 0
  return Math.min(99, Math.round((event.loaded / event.total) * 100))
}

export const resumeApi = {
  getList(params?: { page?: number; page_size?: number }) {
    return asApiPromise(request.get<ApiResponse<PaginatedData<Resume>>>('/resumes', { params }))
  },

  getDetail(id: number) {
    return asApiPromise(request.get<ApiResponse<Resume>>(`/resumes/${id}`))
  },

  upload(file: File, title?: string, onProgress?: UploadProgressHandler) {
    const form = new FormData()
    form.append('file', file)
    if (title) form.append('title', title)
    return asApiPromise(request.post<ApiResponse<Resume>>('/resumes/upload', form, {
      onUploadProgress: (event) => {
        const percentage = getUploadPercentage(event)
        if (percentage > 0) {
          onProgress?.(percentage)
        }
      },
    }))
  },

  delete(id: number) {
    return asApiPromise(request.delete<ApiResponse<null>>(`/resumes/${id}`))
  },

  download(id: number) {
    return request.get<Blob, AxiosResponse<Blob>>(`/resumes/${id}/download`, {
      responseType: 'blob',
    })
  },

  startOptimization(params: ResumeOptimizeParams) {
    const { resume_id, ...body } = params
    return asApiPromise(
      request.post<ApiResponse<AIStartTaskResult>>(`/resumes/${resume_id}/optimizations`, body),
    )
  },

  getOptimization(resumeId: number, optimizationId: number) {
    return asApiPromise(
      request.get<ApiResponse<ResumeOptimizeResult>>(
        `/resumes/${resumeId}/optimizations/${optimizationId}`,
      ),
    )
  },

  getSavedOptimizations(params?: { page?: number; page_size?: number }) {
    return asApiPromise(
      request.get<ApiResponse<PaginatedData<ResumeOptimizeResult>>>(
        '/resume-optimizations/saved',
        { params },
      ),
    )
  },

  getSavedOptimizationDetail(savedOptimizationId: number) {
    return asApiPromise(
      request.get<ApiResponse<ResumeOptimizeResult>>(
        `/resume-optimizations/saved/${savedOptimizationId}`,
      ),
    )
  },

  deleteSavedOptimization(savedOptimizationId: number) {
    return asApiPromise(
      request.delete<ApiResponse<null>>(`/resume-optimizations/saved/${savedOptimizationId}`),
    )
  },

  downloadSavedOptimization(savedOptimizationId: number) {
    return request.get<Blob, AxiosResponse<Blob>>(
      `/resume-optimizations/saved/${savedOptimizationId}/download`,
      { responseType: 'blob' },
    )
  },

  previewAiConfirmation(params: ResumeOptimizationAiPreviewParams) {
    const { resume_id, optimization_id, ...body } = params
    return asApiPromise(
      request.post<ApiResponse<ResumeOptimizationConfirmationPreview>>(
        `/resumes/${resume_id}/optimizations/${optimization_id}/confirmations/ai-preview`,
        body,
      ),
    )
  },

  previewManualConfirmation(params: ResumeOptimizationManualPreviewParams) {
    const { resume_id, optimization_id, ...body } = params
    return asApiPromise(
      request.post<ApiResponse<ResumeOptimizationConfirmationPreview>>(
        `/resumes/${resume_id}/optimizations/${optimization_id}/confirmations/manual-preview`,
        body,
      ),
    )
  },

  dismissConfirmations(params: ResumeOptimizationDismissConfirmParams) {
    const { resume_id, optimization_id, ...body } = params
    return asApiPromise(
      request.post<ApiResponse<ResumeOptimizeResult>>(
        `/resumes/${resume_id}/optimizations/${optimization_id}/confirmations/dismiss`,
        body,
      ),
    )
  },

  saveOptimization(params: ResumeOptimizationSaveParams) {
    const { resume_id, optimization_id, ...body } = params
    return asApiPromise(
      request.post<ApiResponse<ResumeOptimizeResult>>(
        `/resumes/${resume_id}/optimizations/${optimization_id}/save`,
        body,
      ),
    )
  },
}
