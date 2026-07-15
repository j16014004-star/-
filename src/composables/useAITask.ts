import { onBeforeUnmount, ref } from 'vue'
import { aiApi } from '@/api/ai'
import type { AITask } from '@/api/types/ai'

type TaskUpdateHandler = (task: AITask) => void

const terminalStatuses = new Set(['success', 'failed', 'cancelled'])

export function useAITask() {
  const currentTask = ref<AITask | null>(null)
  let stopped = false
  let timer: ReturnType<typeof setTimeout> | null = null
  let releaseWait: (() => void) | null = null

  const stopPolling = () => {
    stopped = true
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    releaseWait?.()
    releaseWait = null
  }

  const wait = (milliseconds: number) => new Promise<void>((resolve) => {
    releaseWait = resolve
    timer = setTimeout(() => {
      timer = null
      releaseWait = null
      resolve()
    }, milliseconds)
  })

  const pollTask = async (taskId: string, onUpdate?: TaskUpdateHandler) => {
    stopPolling()
    stopped = false

    while (!stopped) {
      const response = await aiApi.getTask(taskId)
      const task = response.data
      currentTask.value = task
      onUpdate?.(task)

      if (terminalStatuses.has(task.status)) {
        if (task.status !== 'success') {
          throw new Error(task.error_message || 'AI 任务执行失败')
        }
        return task
      }

      const delay = Math.max(1, task.poll_after_seconds || 2) * 1000
      await wait(delay)
    }

    throw new Error('AI 任务已停止')
  }

  onBeforeUnmount(stopPolling)

  return {
    currentTask,
    pollTask,
    stopPolling,
  }
}
