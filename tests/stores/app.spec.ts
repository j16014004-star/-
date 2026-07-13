import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '@/stores/app'

describe('useAppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始 sidebarCollapsed 为 false', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('toggleSidebar 切换状态', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('setSidebarCollapsed 设置指定值', () => {
    const store = useAppStore()
    store.setSidebarCollapsed(true)
    expect(store.sidebarCollapsed).toBe(true)
    store.setSidebarCollapsed(false)
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('sidebarWidth 根据状态返回正确值', () => {
    const store = useAppStore()
    expect(store.sidebarWidth).toBe(240)
    store.setSidebarCollapsed(true)
    expect(store.sidebarWidth).toBe(64)
  })

  it('logout 清空用户信息', () => {
    const store = useAppStore()
    store.user = { name: '张三', avatar: 'avatar.png', role: 'admin' }
    store.logout()
    expect(store.user.name).toBe('')
    expect(store.user.role).toBe('')
  })
})