import { ref } from 'vue'

export function useSSE() {
  const eventSource = ref<EventSource | null>(null)
  const isConnected = ref(false)

  function connect(url: string, onMessage: (data: string) => void) {
    close()
    eventSource.value = new EventSource(url)
    isConnected.value = true

    eventSource.value.onmessage = (event) => {
      if (event.data === '[DONE]') {
        close()
        return
      }
      onMessage(event.data)
    }

    eventSource.value.onerror = () => {
      close()
    }
  }

  function close() {
    eventSource.value?.close()
    eventSource.value = null
    isConnected.value = false
  }

  return { connect, close, isConnected }
}
