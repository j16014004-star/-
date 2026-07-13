import request from '@/utils/request'
import type { ApiResponse, HRMessage } from '@/types'
import type { HrMessageReplyParams } from './types/hr'

export const hrApi = {
  getMessages() {
    return request.get<ApiResponse<HRMessage[]>>('/hr/messages')
  },

  getSuggestions(messageId: number) {
    return request.get<ApiResponse<{ suggestions: string[] }>>(`/hr/messages/${messageId}/suggestions`)
  },

  reply(params: HrMessageReplyParams) {
    return request.post<ApiResponse<null>>('/hr/reply', params)
  },

  archiveMessage(id: number) {
    return request.post<ApiResponse<null>>(`/hr/messages/${id}/archive`)
  },
}