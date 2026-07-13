import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuth } from '@/composables/useAuth'

describe('useAuth', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('未登录时 isLoggedIn 为 false', () => {
    const { isLoggedIn, userInfo } = useAuth()
    expect(isLoggedIn.value).toBe(false)
    expect(userInfo.value).toBe(null)
  })

  it('登录后 isLoggedIn 为 true', () => {
    const { isLoggedIn, setAuth } = useAuth()
    setAuth('token123', { id: 1, username: 'test', email: 'test@test.com', created_at: '2026-01-01' })
    expect(isLoggedIn.value).toBe(true)
  })

  it('logout 清除登录状态', () => {
    const { isLoggedIn, setAuth, logout } = useAuth()
    setAuth('token', { id: 1, username: 'test', email: 'test@test.com', created_at: '2026-01-01' })
    expect(isLoggedIn.value).toBe(true)
    logout()
    expect(isLoggedIn.value).toBe(false)
  })

  it('updateProfile 更新用户信息', () => {
    const { userInfo, setAuth, updateProfile } = useAuth()
    setAuth('token', { id: 1, username: 'test', email: 'old@test.com', created_at: '2026-01-01' })
    updateProfile({ email: 'new@test.com' })
    expect(userInfo.value?.email).toBe('new@test.com')
  })
})