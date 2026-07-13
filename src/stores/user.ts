import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'
import type { UserInfo } from '@/types'

export const useUserStore = defineStore('user', () => {
  const token = ref(storage.get<string>(TOKEN_KEY) || '')
  const userInfo = ref<UserInfo | null>(storage.get<UserInfo>(USER_KEY))

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '用户')
  const avatar = computed(() => userInfo.value?.avatar || '')

  function setAuth(tokenValue: string, user: UserInfo) {
    token.value = tokenValue
    userInfo.value = user
    storage.set(TOKEN_KEY, tokenValue)
    storage.set(USER_KEY, user)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    storage.remove(TOKEN_KEY)
    storage.remove(USER_KEY)
  }

  function updateProfile(data: Partial<UserInfo>) {
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, ...data }
      storage.set(USER_KEY, userInfo.value)
    }
  }

  return { token, userInfo, isLoggedIn, username, avatar, setAuth, logout, updateProfile }
})
