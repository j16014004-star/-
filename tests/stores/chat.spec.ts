import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

describe('useChatStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始状态', () => {
    const store = useChatStore()
    expect(store.sessions).toEqual([])
    expect(store.currentSession).toBe(null)
    expect(store.messages).toEqual([])
    expect(store.isStreaming).toBe(false)
    expect(store.streamingText).toBe('')
  })

  it('setSessions 设置会话列表', () => {
    const store = useChatStore()
    const sessions = [{ id: 1, title: '会话1', messages: [], created_at: '', updated_at: '' }]
    store.setSessions(sessions)
    expect(store.sessions.length).toBe(1)
  })

  it('addSession 添加到列表开头', () => {
    const store = useChatStore()
    store.addSession({ id: 1, title: '会话1', messages: [], created_at: '', updated_at: '' })
    store.addSession({ id: 2, title: '会话2', messages: [], created_at: '', updated_at: '' })
    expect(store.sessions[0].id).toBe(2)
  })

  it('setCurrentSession 设置当前会话并加载消息', () => {
    const store = useChatStore()
    const session = {
      id: 1,
      title: '会话1',
      messages: [
        { id: 'm1', role: 'user', content: '你好', created_at: '' },
        { id: 'm2', role: 'assistant', content: '你好！', created_at: '' },
      ],
      created_at: '',
      updated_at: '',
    }
    store.setCurrentSession(session)
    expect(store.currentSession?.id).toBe(1)
    expect(store.messages.length).toBe(2)
  })

  it('addMessage 添加消息', () => {
    const store = useChatStore()
    store.addMessage({ id: 'm1', role: 'user', content: '你好', created_at: '' })
    expect(store.messages.length).toBe(1)
    expect(store.messages[0].content).toBe('你好')
  })

  it('removeSession 删除会话', () => {
    const store = useChatStore()
    store.sessions = [
      { id: 1, title: '会话1', messages: [], created_at: '', updated_at: '' },
      { id: 2, title: '会话2', messages: [], created_at: '', updated_at: '' },
    ]
    store.removeSession(1)
    expect(store.sessions.length).toBe(1)
  })

  it('removeSession 删除当前会话时清空', () => {
    const store = useChatStore()
    store.currentSession = { id: 1, title: '会话1', messages: [], created_at: '', updated_at: '' }
    store.removeSession(1)
    expect(store.currentSession).toBe(null)
    expect(store.messages).toEqual([])
  })

  describe('流式消息', () => {
    it('startStreaming 开始流式', () => {
      const store = useChatStore()
      store.startStreaming()
      expect(store.isStreaming).toBe(true)
      expect(store.streamingText).toBe('')
    })

    it('appendStreamText 追加文本', () => {
      const store = useChatStore()
      store.startStreaming()
      store.appendStreamText('你好')
      store.appendStreamText('世界')
      expect(store.streamingText).toBe('你好世界')
    })

    it('endStreaming 完成流式并添加消息', () => {
      const store = useChatStore()
      store.startStreaming()
      store.appendStreamText('AI回复内容')
      store.endStreaming()
      expect(store.isStreaming).toBe(false)
      expect(store.streamingText).toBe('')
      expect(store.messages.length).toBe(1)
      expect(store.messages[0].role).toBe('assistant')
      expect(store.messages[0].content).toBe('AI回复内容')
    })

    it('endStreaming 空文本时不添加消息', () => {
      const store = useChatStore()
      store.startStreaming()
      store.endStreaming()
      expect(store.messages.length).toBe(0)
    })
  })
})