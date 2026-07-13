import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useSSE } from '@/composables/useSSE'

// Mock EventSource
class MockEventSource {
  onmessage: ((event: any) => void) | null = null
  onerror: (() => void) | null = null
  close = vi.fn()
  static instances: MockEventSource[] = []

  constructor(public url: string) {
    ;(MockEventSource as any).instances.push(this)
  }

  static emit(data: string) {
    const inst = MockEventSource.instances[MockEventSource.instances.length - 1]
    inst?.onmessage?.({ data })
  }

  static emitDone() {
    const inst = MockEventSource.instances[MockEventSource.instances.length - 1]
    inst?.onmessage?.({ data: '[DONE]' })
  }

  static emitError() {
    const inst = MockEventSource.instances[MockEventSource.instances.length - 1]
    inst?.onerror?.()
  }

  static reset() {
    MockEventSource.instances = []
  }
}

;(global as any).EventSource = MockEventSource

describe('useSSE', () => {
  beforeEach(() => {
    MockEventSource.reset()
  })

  it('初始状态未连接', () => {
    const { isConnected } = useSSE()
    expect(isConnected.value).toBe(false)
  })

  it('connect 后状态为已连接', () => {
    const { isConnected, connect } = useSSE()
    connect('http://example.com/sse', () => {})
    expect(isConnected.value).toBe(true)
  })

  it('接收到消息调用回调', () => {
    const { connect } = useSSE()
    const onMessage = vi.fn()
    connect('http://example.com/sse', onMessage)
    MockEventSource.emit('hello')
    expect(onMessage).toHaveBeenCalledWith('hello')
  })

  it('接收到 [DONE] 自动关闭', () => {
    const { isConnected, connect } = useSSE()
    connect('http://example.com/sse', () => {})
    MockEventSource.emitDone()
    expect(isConnected.value).toBe(false)
  })

  it('close 关闭连接', () => {
    const { isConnected, connect, close } = useSSE()
    connect('http://example.com/sse', () => {})
    close()
    expect(isConnected.value).toBe(false)
  })

  it('连接错误后关闭', () => {
    const { isConnected, connect } = useSSE()
    connect('http://example.com/sse', () => {})
    MockEventSource.emitError()
    expect(isConnected.value).toBe(false)
  })
})