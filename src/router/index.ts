import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { storage, TOKEN_KEY } from '@/utils/storage'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录', requiresAuth: false },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { title: '注册', requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '首页', icon: 'DataBoard' },
      },
      {
        path: 'resume',
        name: 'resume-list',
        component: () => import('@/views/resume/ResumeListView.vue'),
        meta: { title: '我的简历', icon: 'Document' },
      },
      {
        path: 'resume/upload',
        name: 'resume-upload',
        component: () => import('@/views/resume/ResumeUploadView.vue'),
        meta: { title: '上传简历', icon: 'Upload' },
      },
      {
        path: 'resume/detail/:id',
        name: 'resume-detail',
        component: () => import('@/views/resume/ResumeDetailView.vue'),
        meta: { title: '简历详情', icon: 'Document' },
        props: true,
      },
      {
        path: 'resume/optimize/:id',
        name: 'resume-optimize',
        component: () => import('@/views/resume/ResumeOptimizeView.vue'),
        meta: { title: 'AI简历优化', icon: 'MagicStick' },
        props: true,
      },
      {
        path: 'career',
        name: 'career',
        component: () => import('@/views/career/CareerPlanView.vue'),
        meta: { title: '职业规划', icon: 'TrendCharts' },
      },
      {
        path: 'jobs',
        name: 'jobs',
        component: () => import('@/views/job/JobListView.vue'),
        meta: { title: '岗位推荐', icon: 'Briefcase' },
      },
      {
        path: 'chat',
        name: 'chat',
        component: () => import('@/views/chat/ChatAssistantView.vue'),
        meta: { title: 'AI助手', icon: 'ChatDotSquare' },
      },
      {
        path: 'agent',
        name: 'agent',
        component: () => import('@/views/agent/AgentTaskView.vue'),
        meta: { title: 'Agent任务中心', icon: 'Monitor' },
      },
      {
        path: 'hr',
        name: 'hr',
        component: () => import('@/views/hr/HrChatView.vue'),
        meta: { title: 'HR助手', icon: 'Message' },
      },
      {
        path: 'interview',
        name: 'interview',
        component: () => import('@/views/interview/InterviewLobbyView.vue'),
        meta: { title: 'AI面试', icon: 'VideoCamera' },
      },
      {
        path: 'interview/lobby',
        name: 'interview-lobby',
        component: () => import('@/views/interview/InterviewLobbyView.vue'),
        meta: { title: '面试大厅', icon: 'VideoCamera' },
      },
      {
        path: 'interview/:id',
        name: 'interview-room',
        component: () => import('@/views/interview/InterviewRoomView.vue'),
        meta: { title: '面试房间', icon: 'VideoCamera' },
        props: true,
      },
      {
        path: 'interview/report/:id',
        name: 'interview-report',
        component: () => import('@/views/interview/InterviewReportView.vue'),
        meta: { title: '面试报告', icon: 'Document' },
        props: true,
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { title: '个人中心', icon: 'User' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = storage.get<string>(TOKEN_KEY)
  const requiresAuth = to.matched.some(r => r.meta?.requiresAuth !== false)
  const isAuthPage = to.path === '/login' || to.path === '/register'

  if (requiresAuth && !token && !isAuthPage) {
    next('/login')
  } else if (isAuthPage && token) {
    next('/')
  } else {
    next()
  }
})

export default router
