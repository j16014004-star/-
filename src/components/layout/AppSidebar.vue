<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import {
  DataBoard,
  Document,
  TrendCharts,
  Briefcase,
  ChatDotSquare,
  VideoCamera,
  Monitor,
  Message,
  User,
} from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()

const isCollapsed = computed(() => appStore.sidebarCollapsed)

// Determine active menu index based on current route
const activeIndex = computed(() => {
  const path = route.path
  if (path.startsWith('/resume')) return '/resume'
  return path
})

const menuItems = [
  { index: '/', title: '首页', icon: DataBoard },
  {
    index: '/resume',
    title: '简历管理',
    icon: Document,
    children: [
      { index: '/resume', title: '我的简历' },
      { index: '/resume/upload', title: '上传简历' },
    ],
  },
  { index: '/career', title: '职业规划', icon: TrendCharts },
  { index: '/jobs', title: '岗位推荐', icon: Briefcase },
  { index: '/chat', title: 'AI助手', icon: ChatDotSquare },
  { index: '/interview', title: 'AI面试', icon: VideoCamera },
  { index: '/agent', title: 'Agent任务中心', icon: Monitor },
  { index: '/hr', title: 'HR助手', icon: Message },
  { index: '/profile', title: '个人中心', icon: User },
]
</script>

<template>
  <el-menu
    :default-active="activeIndex"
    :collapse="isCollapsed"
    :collapse-transition="false"
    unique-opened
    router
    class="app-sidebar h-full flex flex-col border-r border-gray-200 dark:border-gray-700"
    :class="['bg-white dark:bg-gray-800']"
    :style="{ width: isCollapsed ? '64px' : '240px' }"
  >
    <!-- Logo area -->
    <div
      class="sidebar-header flex items-center justify-center h-16 border-b border-gray-100 dark:border-gray-700"
    >
      <div
        v-if="!isCollapsed"
        class="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-lg"
      >
        <svg class="w-8 h-8" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="#4f46e5" />
          <path
            d="M16 6C10.477 6 6 10.477 6 16s4.477 10 10 10 10-4.477 10-10S21.523 6 16 6zm0 18c-4.411 0-8-3.589-8-8s3.589-8 8-8 8 3.589 8 8-3.589 8-8 8z"
            fill="white"
          />
          <path
            d="M16 10c-3.309 0-6 2.691-6 6s2.691 6 6 6 6-2.691 6-6-2.691-6-6-6zm0 10c-2.206 0-4-1.794-4-4s1.794-4 4-4 4 1.794 4 4-1.794 4-4 4z"
            fill="white"
          />
          <path d="M18 15h-3v2h3v-2z" fill="#4f46e5" />
        </svg>
        <span>AI Career</span>
      </div>
      <div v-else class="flex items-center justify-center">
        <svg class="w-8 h-8" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="#4f46e5" />
          <path
            d="M16 6C10.477 6 6 10.477 6 16s4.477 10 10 10 10-4.477 10-10S21.523 6 16 6z"
            fill="white"
          />
        </svg>
      </div>
    </div>

    <!-- Menu items -->
    <div class="flex-1 overflow-y-auto py-2">
      <template v-for="item in menuItems" :key="item.index">
        <!-- Item with children -->
        <el-sub-menu v-if="item.children" :index="item.index">
          <template #title>
            <el-icon><component :is="item.icon" /></el-icon>
            <span v-show="!isCollapsed">{{ item.title }}</span>
          </template>
          <el-menu-item
            v-for="child in item.children"
            :key="child.index"
            :index="child.index"
          >
            <template #title>
              <router-link :to="child.index" class="w-full block">
                {{ child.title }}
              </router-link>
            </template>
          </el-menu-item>
        </el-sub-menu>

        <!-- Leaf item -->
        <el-menu-item v-else :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>
            <router-link :to="item.index" class="w-full block">
              {{ item.title }}
            </router-link>
          </template>
        </el-menu-item>
      </template>
    </div>

    <!-- Collapse button at bottom -->
    <div
      class="sidebar-footer border-t border-gray-100 dark:border-gray-700 p-3 flex justify-center"
    >
      <el-button
        :icon="isCollapsed ? 'Expand' : 'Fold'"
        text
        size="small"
        @click="appStore.toggleSidebar()"
      >
        <template v-if="!isCollapsed">收起</template>
      </el-button>
    </div>
  </el-menu>
</template>

<style scoped>
.app-sidebar {
  transition: width 0.3s ease, background-color 0.3s ease;
  overflow: hidden;
}

.app-sidebar .el-menu {
  border-right: none;
}

.sidebar-header {
  transition: all 0.3s ease;
}

/* Override Element Plus menu styles for collapsible */
:deep(.el-menu--collapse) {
  width: 64px;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
  border-radius: 0;
  margin: 2px 0;
}

:deep(.el-menu-item.is-active) {
  background-color: #eef2ff !important;
  color: #4f46e5 !important;
  font-weight: 600;
  border-right: 3px solid #4f46e5;
}

html.dark :deep(.el-menu-item.is-active) {
  background-color: rgba(79, 70, 229, 0.15) !important;
  color: #818cf8 !important;
  border-right-color: #818cf8;
}

:deep(.el-menu-item:hover) {
  background-color: #f5f3ff !important;
}

html.dark :deep(.el-menu-item:hover) {
  background-color: rgba(79, 70, 229, 0.1) !important;
}
</style>