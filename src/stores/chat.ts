import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatSession, ChatMessage } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const streamingText = ref('')

  function setSessions(list: ChatSession[]) {
    sessions.value = list
  }

  function setCurrentSession(session: ChatSession | null) {
    currentSession.value = session
    messages.value = session?.messages || []
  }

  function addMessage(message: ChatMessage) {
    messages.value.push(message)
  }

  function addSession(session: ChatSession) {
    sessions.value.unshift(session)
  }

  function removeSession(id: number) {
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSession.value?.id === id) {
      currentSession.value = null
      messages.value = []
    }
  }

  function startStreaming() {
    isStreaming.value = true
    streamingText.value = ''
  }

  function appendStreamText(text: string) {
    streamingText.value += text
  }

  function endStreaming() {
    if (streamingText.value) {
      addMessage({
        id: 'msg_' + Date.now(),
        role: 'assistant',
        content: streamingText.value,
        created_at: new Date().toISOString(),
      })
    }
    isStreaming.value = false
    streamingText.value = ''
  }

  return {
    sessions, currentSession, messages, isStreaming, streamingText,
    setSessions, setCurrentSession, addMessage, addSession, removeSession,
    startStreaming, appendStreamText, endStreaming
  }
})
