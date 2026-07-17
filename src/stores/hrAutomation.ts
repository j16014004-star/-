import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { hrApi } from '@/api/hr'
import type { HrAutomationOverview } from '@/api/types/hr'

const emptyOverview = (): HrAutomationOverview => ({
  total_workspaces: 0,
  active_workspaces: 0,
  unread_messages: 0,
  pending_confirmations: 0,
  upcoming_interviews: 0,
})

export const useHrAutomationStore = defineStore('hr-automation', () => {
  const overview = ref<HrAutomationOverview>(emptyOverview())
  const loaded = ref(false)
  const loading = ref(false)

  const hasWorkspace = computed(() => overview.value.total_workspaces > 0)

  async function loadOverview(force = false) {
    if (loading.value || (loaded.value && !force)) return
    loading.value = true
    try {
      const response = await hrApi.getOverview()
      overview.value = response.data
    } catch {
      overview.value = emptyOverview()
    } finally {
      loaded.value = true
      loading.value = false
    }
  }

  function markWorkspaceCreated() {
    overview.value.total_workspaces = Math.max(1, overview.value.total_workspaces + 1)
    overview.value.active_workspaces += 1
    loaded.value = true
  }

  return { overview, loaded, loading, hasWorkspace, loadOverview, markWorkspaceCreated }
})
