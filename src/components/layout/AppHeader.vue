<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { Briefcase, Document, House, Message, User, VideoCamera } from '@element-plus/icons-vue'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'
import { authApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const pageTitle = computed(() => String(route.meta?.title || 'AI 求职工作台'))
const userName = computed(() => appStore.user.name || '求职用户')
const userAvatar = computed(() => appStore.user.avatar)
const quickLinks = [
  { path: '/', label: '首页', icon: House },
  { path: '/resume', label: '简历', icon: Document },
  { path: '/jobs', label: '岗位', icon: Briefcase },
  { path: '/hr', label: 'HR', icon: Message },
  { path: '/interview', label: '面试', icon: VideoCamera },
]

onMounted(() => {
  const storedUser = storage.get<any>(USER_KEY)
  if (storedUser?.username) appStore.user.name = storedUser.username
  if (storedUser?.avatar) appStore.setAvatar(storedUser.avatar)
  const storedAvatar = localStorage.getItem('userAvatar')
  if (storedAvatar) appStore.setAvatar(storedAvatar)
})

async function handleCommand(command: string) {
  if (command === 'profile') return router.push('/profile')
  if (command !== 'logout') return
  try {
    await authApi.logout()
  } catch {
    // 即使服务端登出失败，也要清理本地登录状态。
  } finally {
    appStore.logout()
    storage.remove(TOKEN_KEY)
    storage.remove('refresh_token')
    storage.remove('token_type')
    storage.remove('expires_in')
    storage.remove('token_expires_at')
    storage.remove(USER_KEY)
    localStorage.removeItem('userAvatar')
    router.replace('/login')
  }
}
</script>

<template>
  <header class="workspace-header">
    <div class="window-titlebar">
      <div class="title-brand">
        <img src="/hakimi-logo.png" alt="" />
        <strong>{{ userName }} · {{ pageTitle }}</strong>
      </div>
      <div class="title-actions">
        <button type="button" aria-label="收起导航" @click="appStore.toggleSidebar()">—</button>
        <button type="button" aria-label="窗口模式">□</button>
        <button type="button" aria-label="保持当前页面">×</button>
      </div>
    </div>

    <div class="toolbar-row">
      <nav class="quick-nav" aria-label="快捷功能">
        <router-link v-for="link in quickLinks" :key="link.path" :to="link.path" :class="{ active: route.path === link.path || (link.path !== '/' && route.path.startsWith(link.path)) }">
          <el-icon><component :is="link.icon" /></el-icon>
          <span>{{ link.label }}</span>
        </router-link>
      </nav>

      <el-dropdown trigger="click" @command="handleCommand">
        <div class="account-entry">
          <el-avatar v-if="userAvatar" :size="31" :src="userAvatar" />
          <el-avatar v-else :size="31"><el-icon><User /></el-icon></el-avatar>
          <span>{{ userName }}</span>
          <b>▾</b>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="location-row">
      <div class="browser-controls"><button>‹</button><button>›</button><button>⌂</button></div>
      <div class="location-title"><span>当前位置</span><strong>{{ pageTitle }}</strong></div>
      <div class="automation-state"><i></i> 自动化助手在线</div>
    </div>
  </header>
</template>

<style scoped>
.workspace-header { position: relative; z-index: 10; flex: 0 0 auto; color: #24435f; border-bottom: 1px solid #a8c3d9; background: #edf6fc; }
.window-titlebar { display: flex; height: 38px; align-items: center; justify-content: space-between; padding: 0 10px; color: #fff; background: linear-gradient(180deg,#39b7ee 0%,#1592d7 52%,#0876bd 100%); border-bottom: 1px solid #075f9d; text-shadow: 0 1px 1px rgba(0,54,96,.48); }
.title-brand { display: flex; min-width: 0; align-items: center; gap: 8px; }
.title-brand img { width: 23px; height: 23px; border-radius: 6px; object-fit: cover; border: 1px solid rgba(255,255,255,.6); }
.title-brand strong { overflow: hidden; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.title-actions { display: flex; gap: 2px; }
.title-actions button { width: 28px; height: 23px; color: #fff; border: 0; border-radius: 3px; background: transparent; cursor: pointer; }
.title-actions button:hover { background: rgba(255,255,255,.2); }
.toolbar-row { display: flex; min-height: 61px; align-items: center; justify-content: space-between; gap: 16px; padding: 6px 15px; background: linear-gradient(#fafdff,#e3f1fa); border-bottom: 1px solid #b9d0e1; }
.quick-nav { display: flex; align-items: stretch; gap: 7px; }
.quick-nav a { display: flex; min-width: 55px; flex-direction: column; align-items: center; gap: 2px; padding: 5px 8px; color: #41647f; font-size: 11px; text-decoration: none; border: 1px solid transparent; border-radius: 6px; }
.quick-nav a .el-icon { color: #168dce; font-size: 23px; }
.quick-nav a:hover, .quick-nav a.active { color: #075f9b; border-color: #b5d7ea; background: linear-gradient(#fff,#dff2fc); box-shadow: 0 1px 2px rgba(10,87,136,.09); }
.account-entry { display: flex; align-items: center; gap: 8px; padding: 4px 7px; color: #2c526e; font-size: 12px; border: 1px solid #bdd5e5; border-radius: 6px; background: rgba(255,255,255,.7); cursor: pointer; }
.account-entry b { color: #168dce; }
.location-row { display: flex; height: 34px; align-items: center; gap: 10px; padding: 0 13px; background: linear-gradient(#fff,#edf4f9); }
.browser-controls { display: flex; gap: 3px; }
.browser-controls button { width: 24px; height: 22px; color: #527087; border: 1px solid #c4d4e0; border-radius: 3px; background: linear-gradient(#fff,#e9f0f5); }
.location-title { display: flex; flex: 1; align-items: center; gap: 8px; font-size: 11px; }
.location-title span { color: #8a9aaa; }
.location-title strong { color: #315d7c; }
.automation-state { color: #5b7183; font-size: 11px; }
.automation-state i { display: inline-block; width: 7px; height: 7px; margin-right: 5px; border-radius: 50%; background: #22c55e; }
html.dark .workspace-header { color: #cbd5e1; border-color: #334155; background: #172033; }
html.dark .toolbar-row, html.dark .location-row { color: #cbd5e1; border-color: #334155; background: #1e293b; }
html.dark .quick-nav a { color: #cbd5e1; }
@media (max-width: 700px) { .toolbar-row { padding: 5px 8px; } .quick-nav { gap: 1px; } .quick-nav a { min-width: 43px; padding-inline: 4px; } .quick-nav a span { display: none; } .account-entry span { display: none; } .automation-state { display: none; } }
</style>
