import request from '@/utils/request'
import type { ApiResponse, ChatSession, ChatMessage } from '@/types'
import type { ChatSendParams } from './types/chat'

export const chatApi = {
  getSessions() {
    return request.get<ApiResponse<ChatSession[]>>('/chat/sessions')
  },

  getMessages(sessionId: number) {
    return request.get<ApiResponse<ChatMessage[]>>(`/chat/sessions/${sessionId}/messages`)
  },

  sendMessage(params: ChatSendParams) {
    return request.post<ApiResponse<ChatMessage>>('/chat/send', params)
  },

  sendMessageStream(params: ChatSendParams) {
    // Returns an EventSource URL for SSE streaming
    const token = localStorage.getItem('ai_career_token')
    return `/api/chat/send/stream?session_id=${params.session_id || ''}&message=${encodeURIComponent(params.message)}&token=${token}`
  },

  deleteSession(id: number) {
    return request.delete<ApiResponse<null>>(`/chat/sessions/${id}`)
  },
}