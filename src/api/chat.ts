import request from '@/utils/request'
import type { ApiResponse, ChatSession, ChatMessage } from '@/types'
import type { ChatSendParams } from './types/chat'
import type { AxiosResponse } from 'axios'
import { API_BASE_URL } from '@/utils/request'

type ApiPromise<T> = Promise<ApiResponse<T>>

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

export const chatApi = {
  getSessions() {
    return asApiPromise(request.get<ApiResponse<ChatSession[]>>('/chat/sessions'))
  },

  getMessages(sessionId: number) {
    return asApiPromise(request.get<ApiResponse<ChatMessage[]>>(`/chat/sessions/${sessionId}/messages`))
  },

  sendMessage(params: ChatSendParams) {
    return asApiPromise(request.post<ApiResponse<ChatMessage>>('/chat/send', params))
  },

  sendMessageStream(params: ChatSendParams) {
    // Returns an EventSource URL for SSE streaming
    const token = localStorage.getItem('ai_career_token')
    return `${API_BASE_URL}/chat/send/stream?session_id=${params.session_id || ''}&message=${encodeURIComponent(params.message)}&token=${token}`
  },

  deleteSession(id: number) {
    return asApiPromise(request.delete<ApiResponse<null>>(`/chat/sessions/${id}`))
  },
}
