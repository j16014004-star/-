<template>
  <div class="dashboard-view p-6 bg-gray-50 min-h-screen">
    <!-- Welcome Section -->
    <div class="mb-8">
      <el-card class="border-0 overflow-hidden" :body-style="{ padding: '0' }">
        <div class="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 p-8 text-white">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold mb-2">早上好，{{ username }} &#x1F44B;</h1>
              <p class="text-blue-200 text-lg">欢迎回来，这是你的职业发展概览</p>
            </div>
            <div class="hidden md:block">
              <div class="bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 text-center">
                <div class="text-2xl font-bold">{{ todayDate }}</div>
                <div class="text-blue-200 text-sm">{{ todayWeekday }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Stats Cards Row -->
    <el-row :gutter="20" class="mb-8">
      <el-col :xs="12" :sm="6" v-for="stat in stats" :key="stat.label" class="mb-4">
        <el-card class="stat-card border-0" shadow="hover" body-style="padding: 20px">
          <div class="flex items-center gap-4">
            <div
              class="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
              :style="{ background: stat.bgColor }"
            >
              <span>{{ stat.icon }}</span>
            </div>
            <div>
              <div class="text-2xl font-bold text-gray-800">{{ stat.value }}</div>
              <div class="text-sm text-gray-500">{{ stat.label }}</div>
            </div>
          </div>
          <div class="mt-3 text-xs text-gray-400">
            <span :class="stat.trend >= 0 ? 'text-green-500' : 'text-red-500'">
              {{ stat.trend >= 0 ? '↑' : '↓' }} {{ Math.abs(stat.trend) }}%
            </span>
            <span class="ml-1">较上周</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Actions -->
    <div class="mb-8">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">快捷操作</h2>
      <el-row :gutter="16">
        <el-col :xs="12" :sm="6" v-for="action in quickActions" :key="action.label" class="mb-3">
          <el-card
            class="quick-action-card border-0 cursor-pointer transition-all duration-200"
            shadow="hover"
            body-style="padding: 24px; text-align: center;"
            @click="action.handler"
          >
            <div class="text-3xl mb-2">{{ action.icon }}</div>
            <div class="font-medium text-gray-700">{{ action.label }}</div>
            <div class="text-xs text-gray-400 mt-1">{{ action.desc }}</div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Bottom Row: Activity + Upcoming -->
    <el-row :gutter="20">
      <!-- Recent Activity -->
      <el-col :xs="24" :md="14" class="mb-6">
        <el-card class="border-0" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-gray-800">最近动态</span>
              <el-button text type="primary" size="small" @click="router.push('/resume')">查看全部</el-button>
            </div>
          </template>
          <div class="space-y-0">
            <div
              v-for="(activity, index) in activities"
              :key="index"
              class="flex gap-4 pb-6 relative"
              :class="{ 'border-l-2 border-blue-200 ml-2': index < activities.length - 1 }"
            >
              <div
                class="w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 -ml-4 z-10 border-2 border-white shadow-sm"
                :style="{ background: activity.color }"
              >
                <span>{{ activity.icon }}</span>
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-gray-700 text-sm">{{ activity.title }}</div>
                <div class="text-gray-400 text-xs mt-1">{{ activity.desc }}</div>
                <div class="text-gray-400 text-xs mt-1">{{ activity.time }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Upcoming Interviews -->
      <el-col :xs="24" :md="10" class="mb-6">
        <el-card class="border-0" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-gray-800">即将到来的面试</span>
              <el-tag type="warning" size="small">{{ upcomingInterviews.length }} 项</el-tag>
            </div>
          </template>
          <div v-if="upcomingInterviews.length === 0" class="text-center py-8 text-gray-400">
            <div class="text-4xl mb-2">&#x1F4AD;</div>
            <p>暂无即将到来的面试</p>
          </div>
          <div v-else class="space-y-4">
            <div
              v-for="item in upcomingInterviews"
              :key="item.id"
              class="flex items-center gap-4 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
            >
              <div class="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                {{ item.company.charAt(0) }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-gray-800 text-sm">{{ item.position }}</div>
                <div class="text-gray-400 text-xs">{{ item.company }}</div>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="text-sm font-medium text-gray-700">{{ item.date }}</div>
                <div class="text-xs text-gray-400">{{ item.time }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api/resume'
import { interviewApi } from '@/api/interview'
import { chatApi } from '@/api/chat'
import { jobApi } from '@/api/job'

const router = useRouter()

const username = ref('用户')
const isLoading = ref(false)

const todayDate = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
})

const todayWeekday = new Date().toLocaleDateString('zh-CN', { weekday: 'long' })

const stats = ref([
  { label: '简历数', value: '0', icon: '📄', trend: 0, bgColor: 'linear-gradient(135deg, #dbeafe, #bfdbfe)' },
  { label: '面试次数', value: '0', icon: '💬', trend: 0, bgColor: 'linear-gradient(135deg, #d1fae5, #a7f3d0)' },
  { label: '匹配岗位', value: '0', icon: '🎯', trend: 0, bgColor: 'linear-gradient(135deg, #fef3c7, #fde68a)' },
  { label: 'AI对话', value: '0', icon: '🤖', trend: 0, bgColor: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)' }
])

const activities = ref<any[]>([])
const upcomingInterviews = ref<any[]>([])

const quickActions = [
  {
    icon: '📄',
    label: '上传简历',
    desc: '上传并分析简历',
    handler: () => router.push('/resume/upload')
  },
  {
    icon: '💬',
    label: '开始面试',
    desc: 'AI模拟面试训练',
    handler: () => router.push('/interview/lobby')
  },
  {
    icon: '🤖',
    label: 'AI咨询',
    desc: '智能问答助手',
    handler: () => router.push('/chat')
  },
  {
    icon: '🔍',
    label: '查看岗位',
    desc: '浏览推荐职位',
    handler: () => router.push('/jobs')
  }
]

// 从后端 API 加载仪表盘数据
async function loadDashboardData() {
  isLoading.value = true
  try {
    // 并行加载所有数据
    const [resumeRes, interviewRes, chatRes, jobRes] = await Promise.all([
      resumeApi.getList({ page: 1, page_size: 10 }).catch(() => null),
      interviewApi.getList().catch(() => null),
      chatApi.getSessions().catch(() => null),
      jobApi.getRecommendations({ page: 1, page_size: 10 }).catch(() => null)
    ])

    // 更新统计数据
    const resumeCount = resumeRes?.data?.total || 0
    const interviewCount = interviewRes?.data?.length || 0
    const jobCount = jobRes?.data?.total || 0
    const chatCount = chatRes?.data?.length || 0

    stats.value[0].value = resumeCount.toString()
    stats.value[1].value = interviewCount.toString()
    stats.value[2].value = jobCount.toString()
    stats.value[3].value = chatCount.toString()

    // 构建最近动态
    activities.value = []
    if (resumeRes?.data?.items?.length > 0) {
      const latestResume = resumeRes.data.items[0]
      activities.value.push({
        title: `简历"${latestResume.title}" 分析完成`,
        desc: latestResume.score ? `AI评分 ${latestResume.score}分` : '已为你生成分析结果',
        time: formatTimeAgo(latestResume.created_at),
        icon: '✅',
        color: '#d1fae5'
      })
    }
    if (interviewRes?.data?.length > 0) {
      const latestInterview = interviewRes.data[0]
      activities.value.push({
        title: `AI面试模拟完成`,
        desc: `${latestInterview.position}面试，得分 ${latestInterview.score || '待评分'}分`,
        time: formatTimeAgo(latestInterview.created_at),
        icon: '💬',
        color: '#fef3c7'
      })
    }
    if (jobRes?.data?.items?.length > 0) {
      activities.value.push({
        title: `新增 ${jobCount} 个匹配岗位`,
        desc: '基于你的技能和经历推荐',
        time: '今天',
        icon: '🎯',
        color: '#dbeafe'
      })
    }

    // 加载即将到来的面试
    const pendingInterviews = interviewRes?.data?.filter((i: any) => i.status === 'pending' || i.status === 'in_progress') || []
    upcomingInterviews.value = pendingInterviews.slice(0, 2).map((i: any) => ({
      id: i.id,
      company: i.company || '未指定',
      position: i.position,
      date: i.scheduled_date || i.created_at?.split('T')[0] || '',
      time: i.scheduled_time || '10:00'
    }))
  } catch (error) {
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    isLoading.value = false
  }
}

function formatTimeAgo(dateStr: string): string {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  // 加载用户名
  const stored = localStorage.getItem('user')
  if (stored) {
    try {
      const user = JSON.parse(stored)
      username.value = user.username || '用户'
    } catch {
      // ignore
    }
  }
  // 加载仪表盘数据
  loadDashboardData()
})

<style scoped>
.dashboard-view :deep(.el-card) {
  border-radius: 16px;
}

.stat-card {
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.quick-action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1) !important;
}
</style>