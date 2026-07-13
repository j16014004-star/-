import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useAppStore = defineStore('app', () => {
  // 从 localStorage 读取初始值
  const getInitialTheme = (): 'light' | 'dark' | 'auto' => {
    const stored = localStorage.getItem('theme')
    if (stored === 'light' || stored === 'dark' || stored === 'auto') {
      return stored
    }
    return 'light'
  }

  const sidebarCollapsed = ref(false)
  const user = ref({
    name: '用户',
    avatar: '',
    role: '求职者',
  })
  const theme = ref<'light' | 'dark' | 'auto'>(getInitialTheme())

  const sidebarWidth = computed(() => (sidebarCollapsed.value ? 64 : 240))

  // 应用主题
  function applyTheme() {
    const html = document.documentElement
    const isDark = theme.value === 'dark' ||
      (theme.value === 'auto' && typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)')?.matches)

    if (isDark) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 监听主题变化
  watch(theme, (newTheme) => {
    localStorage.setItem('theme', newTheme)
    applyTheme()
  }, { immediate: true })

  // 监听系统主题变化（当设置为 auto 时）
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (theme.value === 'auto') {
        applyTheme()
      }
    })
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setSidebarCollapsed(val: boolean) {
    sidebarCollapsed.value = val
    localStorage.setItem('sidebarExpanded', String(!val))
  }

  function setTheme(newTheme: 'light' | 'dark' | 'auto') {
    theme.value = newTheme
  }

  function setAvatar(avatarUrl: string) {
    user.value.avatar = avatarUrl
    localStorage.setItem('userAvatar', avatarUrl)
  }

  function logout() {
    user.value = { name: '', avatar: '', role: '' }
  }

  return {
    sidebarCollapsed,
    sidebarWidth,
    user,
    theme,
    toggleSidebar,
    setSidebarCollapsed,
    setTheme,
    setAvatar,
    logout,
  }
})