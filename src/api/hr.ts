import request from '@/utils/request'
import type { AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types'
import type {
  ConfirmHrActionParams,
  CreateHrWorkspaceParams,
  HrAutomationOverview,
  HrAutomationPreflight,
  HrAutomationPreflightParams,
  HrConversationMessage,
  HrInterviewCreateParams,
  HrInterviewDetectionResult,
  HrInterviewList,
  HrMessageSendResult,
  HrMessageSyncResult,
  HrOperationLog,
  HrReplySuggestionResult,
  HrWorkspace,
  HrWorkspaceControlParams,
  HrWorkspaceList,
  SendHrMessageParams,
  UpdateHrWorkspaceModeParams,
} from './types/hr'

type ApiPromise<T> = Promise<ApiResponse<T>>

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}
export const hrApi = {
  getOverview() {
    return asApiPromise(request.get<ApiResponse<HrAutomationOverview>>('/hr/automation/overview'))
  },

  checkPreflight(params: HrAutomationPreflightParams) {
    return asApiPromise(request.get<ApiResponse<HrAutomationPreflight>>('/hr/automation/preflight', { params }))
  },

  createWorkspace(data: CreateHrWorkspaceParams) {
    return asApiPromise(request.post<ApiResponse<HrWorkspace>>('/hr/workspaces', data))
  },

  getWorkspaces(params?: { status?: string }) {
    return asApiPromise(request.get<ApiResponse<HrWorkspaceList>>('/hr/workspaces', { params }))
  },

  getWorkspace(id: number) {
    return asApiPromise(request.get<ApiResponse<HrWorkspace>>(`/hr/workspaces/${id}`))
  },

  updateMode(id: number, data: UpdateHrWorkspaceModeParams) {
    return asApiPromise(request.patch<ApiResponse<HrWorkspace>>(`/hr/workspaces/${id}/mode`, data))
  },

  controlWorkspace(id: number, data: HrWorkspaceControlParams) {
    return asApiPromise(request.post<ApiResponse<HrWorkspace>>(`/hr/workspaces/${id}/control`, data))
  },

  getMessages(id: number) {
    return asApiPromise(request.get<ApiResponse<{ items: HrConversationMessage[] }>>(`/hr/workspaces/${id}/messages`))
  },

  getSuggestions(id: number) {
    return asApiPromise(request.post<ApiResponse<HrReplySuggestionResult>>(`/hr/workspaces/${id}/reply-suggestions`))
  },

  sendMessage(id: number, data: SendHrMessageParams) {
    return asApiPromise(request.post<ApiResponse<HrMessageSendResult>>(`/hr/workspaces/${id}/messages`, data))
  },

  confirmAction(id: number, actionId: number, data: ConfirmHrActionParams) {
    return asApiPromise(request.post<ApiResponse<HrWorkspace>>(`/hr/workspaces/${id}/actions/${actionId}/confirm`, data))
  },

  getLogs(id: number) {
    return asApiPromise(request.get<ApiResponse<{ items: HrOperationLog[] }>>(`/hr/workspaces/${id}/logs`))
  },

  syncMessages(id: number) {
    return asApiPromise(request.post<ApiResponse<HrMessageSyncResult>>(`/hr/workspaces/${id}/messages/sync`))
  },

  detectInterview(id: number, messageId?: number) {
    return asApiPromise(request.post<ApiResponse<HrInterviewDetectionResult>>(
      `/hr/workspaces/${id}/interviews/detect`,
      messageId ? { message_id: messageId } : {},
    ))
  },

  createInterview(id: number, data: HrInterviewCreateParams) {
    return asApiPromise(request.post<ApiResponse<{ interview: HrInterviewList['items'][number]; action_id: number }>>(
      `/hr/workspaces/${id}/interviews`,
      data,
    ))
  },

  getInterviews(id: number) {
    return asApiPromise(request.get<ApiResponse<HrInterviewList>>(`/hr/workspaces/${id}/interviews`))
  },

  getUpcomingInterviews() {
    return asApiPromise(request.get<ApiResponse<HrInterviewList>>('/hr/interviews/upcoming'))
  },
}
