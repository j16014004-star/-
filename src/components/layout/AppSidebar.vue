<script setup lang="ts">
import { computed, onMounted } from 'vue'
import type { Component } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useHrAutomationStore } from '@/stores/hrAutomation'
import { storage, USER_KEY } from '@/utils/storage'
import {
  Calendar,
  DataBoard,
  Document,
  Briefcase,
  Message,
  TrendCharts,
  User,
  VideoCamera,
} from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()
const hrStore = useHrAutomationStore()

const isCollapsed = computed(() => appStore.sidebarCollapsed)
const activeIndex = computed(() => route.path.startsWith('/resume') ? '/resume' : route.path)
const userName = computed(() => appStore.user.name || '求职用户')
const userAvatar = computed(() => appStore.user.avatar)

interface NavigationItem {
  index: string
  title: string
  icon: Component
  badge?: string
}

interface NavigationGroup {
  title: string
  items: NavigationItem[]
}

const groups = computed<NavigationGroup[]>(() => [
  {
    title: '我的工作台',
    items: [
      { index: '/', title: '工作台首页', icon: DataBoard },
      { index: '/resume', title: '我的简历', icon: Document },
      { index: '/resume/upload', title: '上传新简历', icon: Document },
    ],
  },
  {
    title: '自动化求职',
    items: [
      { index: '/jobs', title: '筛选推荐岗位', icon: Briefcase, badge: 'AI' },
      ...(hrStore.hasWorkspace ? [{ index: '/hr', title: '自动投递与 HR', icon: Message, badge: String(hrStore.overview.unread_messages || '') }] : []),
    ],
  },
  {
    title: '能力成长',
    items: [
      { index: '/interview', title: 'AI 模拟面试', icon: VideoCamera },
      { index: '/career', title: '职业生涯规划', icon: TrendCharts },
      { index: '/career/check-in', title: '计划执行打卡', icon: Calendar },
    ],
  },
  {
    title: '账号设置',
    items: [{ index: '/profile', title: '个人中心', icon: User }],
  },
])

onMounted(() => {
  const storedUser = storage.get<any>(USER_KEY)
  if (storedUser?.username) appStore.user.name = storedUser.username
  if (storedUser?.avatar) appStore.setAvatar(storedUser.avatar)
  const storedAvatar = localStorage.getItem('userAvatar')
  if (storedAvatar) appStore.setAvatar(storedAvatar)
  void hrStore.loadOverview()
})
</script>

<template>
  <aside class="contact-window" :class="{ collapsed: isCollapsed }">
    <header class="contact-titlebar">
      <img src="/hakimi-logo.png" alt="哈基米AI" class="mini-logo" />
      <strong v-if="!isCollapsed">哈基米 AI</strong>
      <span v-if="!isCollapsed" class="window-tools">— □</span>
    </header>

    <section class="user-card">
      <el-avatar v-if="userAvatar" :size="isCollapsed ? 38 : 58" :src="userAvatar" />
      <img v-else src="/hakimi-logo.png" alt="用户头像" class="user-logo" />
      <div v-if="!isCollapsed" class="user-copy">
        <strong>{{ userName }}</strong>
        <span><i></i> 在线 · AI 助手已连接</span>
        <small>自动化求职工作台</small>
      </div>
    </section>

    <div v-if="!isCollapsed" class="search-box">
      <span>搜索功能...</span><b>⌕</b>
    </div>

    <el-menu :default-active="activeIndex" router class="contact-menu" :collapse="isCollapsed" :collapse-transition="false">
      <template v-for="group in groups" :key="group.title">
        <div v-if="!isCollapsed" class="group-title"><span>▾</span>{{ group.title }}</div>
        <el-menu-item v-for="item in group.items" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>
            <span>{{ item.title }}</span>
            <em v-if="item.badge" class="menu-badge">{{ item.badge }}</em>
          </template>
        </el-menu-item>
      </template>
    </el-menu>

    <footer class="contact-footer">
      <button type="button" @click="appStore.toggleSidebar()">{{ isCollapsed ? '»' : '« 收起导航' }}</button>
    </footer>
  </aside>
</template>

<style scoped>
.contact-window {
  display: flex;
  width: 270px;
  flex: 0 0 270px;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,.78);
  border-radius: 12px;
  background: #f8fbff;
  box-shadow: 0 18px 46px rgba(1,12,30,.38), 0 0 0 1px rgba(4,44,91,.46);
  transition: width .22s ease, flex-basis .22s ease;
}
.contact-window.collapsed { width: 66px; flex-basis: 66px; }
.contact-titlebar { display: flex; min-height: 43px; align-items: center; gap: 9px; padding: 0 12px; color: #fff; background: linear-gradient(180deg,#36b5ed 0%,#168fd5 52%,#0874bd 100%); border-bottom: 1px solid #0969aa; text-shadow: 0 1px 1px rgba(0,60,110,.5); }
.mini-logo { width: 25px; height: 25px; border-radius: 7px; object-fit: cover; border: 1px solid rgba(255,255,255,.6); }
.contact-titlebar strong { font-size: 14px; letter-spacing: .04em; }
.window-tools { margin-left: auto; font-size: 12px; opacity: .86; }
.user-card { display: flex; min-height: 92px; align-items: center; gap: 12px; padding: 14px; color: #fff; background: linear-gradient(135deg,#169cd8,#55c6e8); }
.collapsed .user-card { justify-content: center; padding: 9px; }
.user-logo { width: 58px; height: 58px; flex: 0 0 auto; border-radius: 12px; object-fit: cover; border: 2px solid rgba(255,255,255,.9); box-shadow: 0 5px 12px rgba(3,65,112,.25); }
.collapsed .user-logo { width: 38px; height: 38px; }
.user-copy { display: flex; min-width: 0; flex-direction: column; }
.user-copy strong { overflow: hidden; font-size: 16px; text-overflow: ellipsis; white-space: nowrap; }
.user-copy span { margin-top: 4px; font-size: 11px; color: #e7f8ff; }
.user-copy span i { display: inline-block; width: 7px; height: 7px; margin-right: 4px; border-radius: 50%; background: #4ade80; }
.user-copy small { margin-top: 5px; font-size: 11px; color: rgba(255,255,255,.75); }
.search-box { display: flex; height: 31px; align-items: center; justify-content: space-between; margin: 9px 10px 7px; padding: 0 10px; color: #8293a7; font-size: 12px; border: 1px solid #aac4db; border-radius: 16px; background: #fff; box-shadow: inset 0 1px 2px rgba(15,65,105,.08); }
.search-box b { color: #168ed1; font-size: 18px; }
.contact-menu { flex: 1; overflow-y: auto; border: 0; background: transparent; }
.group-title { display: flex; height: 30px; align-items: center; gap: 5px; padding: 0 12px; color: #183e64; font-size: 12px; font-weight: 800; border-top: 1px solid #d9e6f1; border-bottom: 1px solid #d9e6f1; background: linear-gradient(#f6fbff,#e7f2fa); }
.group-title span { color: #1992d0; }
:deep(.el-menu-item) { height: 38px; margin: 0 6px; padding: 0 10px !important; color: #334b65; border-radius: 5px; line-height: 38px; }
:deep(.el-menu-item .el-icon) { color: #178ac9; font-size: 17px; }
:deep(.el-menu-item:hover) { color: #075f9b; background: #def2fd !important; }
:deep(.el-menu-item.is-active) { color: #fff !important; font-weight: 700; background: linear-gradient(180deg,#52bff0,#168ed1) !important; box-shadow: inset 0 0 0 1px #0b78b8; }
:deep(.el-menu-item.is-active .el-icon) { color: #fff; }
.menu-badge { min-width: 18px; margin-left: auto; padding: 0 5px; color: #fff; font-size: 9px; font-style: normal; text-align: center; border-radius: 8px; background: #f59e0b; }
.contact-footer { min-height: 38px; padding: 5px 8px; border-top: 1px solid #cdddea; background: linear-gradient(#f8fbfe,#e4eef7); }
.contact-footer button { width: 100%; height: 27px; color: #37617f; font-size: 11px; border: 1px solid #b9cede; border-radius: 4px; background: linear-gradient(#fff,#e8f1f8); cursor: pointer; }
html.dark .contact-window { background: #172033; }
html.dark .group-title, html.dark .contact-footer { color: #d5e5f5; border-color: #334155; background: #1e293b; }
html.dark :deep(.el-menu-item) { color: #cbd5e1; }
@media (max-width: 900px) { .contact-window { border: 0; border-right: 1px solid #9dbbd2; border-radius: 0; box-shadow: none; } }
@media (max-width: 640px) { .contact-window:not(.collapsed) { width: 220px; flex-basis: 220px; } }
</style>
