import type { AxiosProgressEvent, AxiosResponse } from 'axios'
import request from '@/utils/request'
import type { ApiResponse } from '@/types'
import type {
  CareerPlan,
  CareerPlanAcceptResult,
  CareerPlanCreateParams,
  CareerPlanRegenerateParams,
  CareerPlanRegenerateResult,
  CareerPlanStartResult,
  CareerExecutionOverview,
  CareerPlanningProfile,
  CareerPlanningProfileParams,
  CareerProjectAttachment,
  CareerTaskCheckinParams,
  CareerTaskQuestion,
  CareerTaskQuestionParams,
  CareerTaskQuestionStartResult,
  CareerAdvanceResult,
  CareerCompleteAllResult,
  CareerAssessmentResult,
  CareerAssessmentStartResult,
  CareerAssessmentSubmitParams,
  CareerAssessmentSubmitResult,
  CareerStageAssessment,
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

  acceptPlan(planId: number) {
    return asApiPromise(
      request.post<ApiResponse<CareerPlanAcceptResult>>(`/career-plans/${planId}/accept`),
    )
  },

  regeneratePlan(planId: number, params: CareerPlanRegenerateParams) {
    return asApiPromise(
      request.post<ApiResponse<CareerPlanRegenerateResult>>(
        `/career-plans/${planId}/regenerate`,
        params,
      ),
    )
  },

  getCurrentExecution() {
    return asApiPromise(
      request.get<ApiResponse<CareerExecutionOverview>>('/career-plan-executions/current'),
    )
  },

  checkInTask(taskId: number, params: CareerTaskCheckinParams) {
    return asApiPromise(
      request.post<ApiResponse<CareerExecutionOverview>>(
        `/career-plan-executions/tasks/${taskId}/check-in`,
        params,
      ),
    )
  },

  askTaskQuestion(taskId: number, params: CareerTaskQuestionParams) {
    return asApiPromise(
      request.post<ApiResponse<CareerTaskQuestionStartResult>>(
        `/career-plan-executions/tasks/${taskId}/questions`,
        params,
      ),
    )
  },

  getTaskQuestions(taskId: number) {
    return asApiPromise(
      request.get<ApiResponse<CareerTaskQuestion[]>>(
        `/career-plan-executions/tasks/${taskId}/questions`,
      ),
    )
  },

  getTaskQuestion(questionId: number) {
    return asApiPromise(
      request.get<ApiResponse<CareerTaskQuestion>>(
        `/career-plan-executions/questions/${questionId}`,
      ),
    )
  },

  advanceNextTask(executionPlanId: number) {
    return asApiPromise(
      request.post<ApiResponse<CareerAdvanceResult>>(
        `/career-plan-executions/${executionPlanId}/advance`,
      ),
    )
  },

  completeAllTasks(executionPlanId: number) {
    return asApiPromise(
      request.post<ApiResponse<CareerCompleteAllResult>>(
        `/career-plan-executions/${executionPlanId}/complete-all`,
      ),
    )
  },

  createStageAssessment(executionPlanId: number) {
    return asApiPromise(
      request.post<ApiResponse<CareerAssessmentStartResult>>(
        `/career-plan-executions/${executionPlanId}/assessments`,
      ),
    )
  },

  getStageAssessment(assessmentId: number) {
    return asApiPromise(
      request.get<ApiResponse<CareerStageAssessment>>(
        `/career-plan-executions/assessments/${assessmentId}`,
      ),
    )
  },

  submitStageAssessment(assessmentId: number, params: CareerAssessmentSubmitParams) {
    return asApiPromise(
      request.post<ApiResponse<CareerAssessmentSubmitResult>>(
        `/career-plan-executions/assessments/${assessmentId}/submit`,
        params,
      ),
    )
  },

  getStageAssessmentResult(assessmentId: number) {
    return asApiPromise(
      request.get<ApiResponse<CareerAssessmentResult>>(
        `/career-plan-executions/assessments/${assessmentId}/result`,
      ),
    )
  },

  acceptAssessmentRemediation(assessmentId: number) {
    return asApiPromise(
      request.post<ApiResponse<CareerExecutionOverview>>(
        `/career-plan-executions/assessments/${assessmentId}/remediation`,
      ),
    )
  },

  enterNextStage(assessmentId: number) {
    return asApiPromise(
      request.post<ApiResponse<CareerExecutionOverview>>(
        `/career-plan-executions/assessments/${assessmentId}/next-stage`,
      ),
    )
  },
}
