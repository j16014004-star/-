import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('初始状态', () => {
    const store = useUserStore()
    expect(store.token).toBe('')
    expect(store.userInfo).toBe(null)
    expect(store.isLoggedIn).toBe(false)
    expect(store.username).toBe('用户')
  })

  it('setAuth 设置 token 和用户信息', () => {
    const store = useUserStore()
    const user = { id: 1, username: 'test', email: 'test@test.com', created_at: '2026-01-01' }
    store.setAuth('token123', user)

    expect(store.token).toBe('token123')
    expect(store.userInfo).toEqual(user)
    expect(store.isLoggedIn).toBe(true)
    expect(store.username).toBe('test')
    expect(storage.get(TOKEN_KEY)).toBe('token123')
  })

  it('logout 清除状态', () => {
    const store = useUserStore()
    store.setAuth('token123', { id: 1, username: 'test', email: 'test@test.com', created_at: '2026-01-01' })
    store.logout()

    expect(store.token).toBe('')
    expect(store.userInfo).toBe(null)
    expect(store.isLoggedIn).toBe(false)
    expect(storage.get(TOKEN_KEY)).toBe(null)
  })

  it('updateProfile 更新用户信息', () => {
    const store = useUserStore()
    store.setAuth('token', { id: 1, username: 'test', email: 'old@test.com', created_at: '2026-01-01' })
    store.updateProfile({ email: 'new@test.com' })

    expect(store.userInfo?.email).toBe('new@test.com')
  })

  it('updateProfile 在 userInfo 为 null 时不报错', () => {
    const store = useUserStore()
    expect(() => store.updateProfile({ email: 'new@test.com' })).not.toThrow()
  })

  it('avatar 返回正确值', () => {
    const store = useUserStore()
    expect(store.avatar).toBe('')
    store.setAuth('token', { id: 1, username: 'test', email: 'test@test.com', avatar: 'avatar.png', created_at: '2026-01-01' })
    expect(store.avatar).toBe('avatar.png')
  })

  it('从 localStorage 恢复 token', () => {
    storage.set(TOKEN_KEY, 'existing_token')
    const store = useUserStore()
    expect(store.token).toBe('existing_token')
    expect(store.isLoggedIn).toBe(true)
  })
})