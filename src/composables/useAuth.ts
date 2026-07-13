import { useUserStore } from '@/stores/user'
import { computed } from 'vue'

export function useAuth() {
  const userStore = useUserStore()
  return {
    isLoggedIn: computed(() => userStore.isLoggedIn),
    userInfo: computed(() => userStore.userInfo),
    setAuth: userStore.setAuth,
    logout: userStore.logout,
    updateProfile: userStore.updateProfile,
  }
}
