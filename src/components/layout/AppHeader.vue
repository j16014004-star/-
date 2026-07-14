<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { Expand, Fold, User, ArrowRight } from '@element-plus/icons-vue'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((r) => r.meta?.title)
  const crumbs: { title: string; path: string }[] = [
    { title: '首页', path: '/' },
  ]
  matched.forEach((r) => {
    crumbs.push({
      title: (r.meta?.title as string) || r.name as string,
      path: r.path,
    })
  })
  return crumbs
})

const userName = computed(() => appStore.user.name)
const userAvatar = computed(() => appStore.user.avatar)

onMounted(() => {
  // 从 storage 加载用户信息
  const storedUser = storage.get<any>(USER_KEY)
  if (storedUser) {
    if (storedUser.username) appStore.user.name = storedUser.username
    if (storedUser.avatar) appStore.user.avatar = storedUser.avatar
  }
  const storedAvatar = localStorage.getItem('userAvatar')
  if (storedAvatar) appStore.user.avatar = storedAvatar
})

function handleCommand(command: string) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    appStore.logout()
    storage.remove(TOKEN_KEY)
    storage.remove(USER_KEY)
    localStorage.removeItem('userAvatar')
    router.push('/login')
  }
}
</script>

<template>
  <el-header
    class="app-header flex items-center justify-between border-b px-6"
    :class="['bg-white dark:bg-gray-800', 'border-gray-200 dark:border-gray-700']"
    style="height: 60px"
  >
    <!-- Left side: toggle button + breadcrumb -->
    <div class="flex items-center gap-4">
      <!-- Sidebar toggle -->
      <el-button
        :icon="appStore.sidebarCollapsed ? Expand : Fold"
        text
        size="small"
        @click="appStore.toggleSidebar()"
        class="text-gray-500 dark:text-gray-400 hover:text-indigo-600"
      />

      <!-- Breadcrumb divider -->
      <el-divider direction="vertical" class="!mx-1" />

      <!-- Breadcrumb -->
      <el-breadcrumb :separator-icon="ArrowRight">
        <el-breadcrumb-item
          v-for="(crumb, index) in breadcrumbs"
          :key="index"
          :to="index < breadcrumbs.length - 1 ? { path: crumb.path } : undefined"
        >
          {{ crumb.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- Right side: user info -->
    <div class="flex items-center gap-3">
      <!-- User dropdown -->
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg px-3 py-1.5 transition-colors">
          <el-avatar
            v-if="userAvatar"
            :size="32"
            :src="userAvatar"
            class="bg-indigo-100 text-indigo-600"
          />
          <el-avatar
            v-else
            :size="32"
            class="bg-indigo-100 text-indigo-600"
          >
            <el-icon :size="18"><User /></el-icon>
          </el-avatar>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-200 hidden sm:block">
            {{ userName }}
          </span>
          <el-icon class="text-gray-400"><ArrowRight /></el-icon>
        </div>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon class="mr-2"><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon class="mr-2"><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"/></svg></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<style scoped>
.app-header {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  z-index: 100;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.el-dropdown-menu__item {
  font-size: 14px;
}
</style>