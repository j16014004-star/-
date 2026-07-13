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

const router = useRouter()

const username = ref('用户')

onMounted(() => {
  const stored = localStorage.getItem('user')
  if (stored) {
    try {
      const user = JSON.parse(stored)
      username.value = user.username || '用户'
    } catch {
      // ignore
    }
  }
})

const todayDate = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
})

const todayWeekday = new Date().toLocaleDateString('zh-CN', { weekday: 'long' })

const stats = [
  { label: '简历数', value: '3', icon: '📄', trend: 12, bgColor: 'linear-gradient(135deg, #dbeafe, #bfdbfe)' },
  { label: '面试次数', value: '5', icon: '💬', trend: 8, bgColor: 'linear-gradient(135deg, #d1fae5, #a7f3d0)' },
  { label: '匹配岗位', value: '12', icon: '🎯', trend: -3, bgColor: 'linear-gradient(135deg, #fef3c7, #fde68a)' },
  { label: 'AI对话', value: '28', icon: '🤖', trend: 25, bgColor: 'linear-gradient(135deg, #e0e7ff, #c7d2fe)' }
]

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

const activities = [
  {
    title: '简历"前端工程师_v3" 分析完成',
    desc: 'AI评分 85分，已为你生成优化建议',
    time: '10 分钟前',
    icon: '✅',
    color: '#d1fae5'
  },
  {
    title: '新增 3 个匹配岗位',
    desc: '阿里巴巴、字节跳动、腾讯等公司',
    time: '1 小时前',
    icon: '🎯',
    color: '#dbeafe'
  },
  {
    title: 'AI面试模拟完成',
    desc: '技术岗位面试，得分 78分',
    time: '3 小时前',
    icon: '💬',
    color: '#fef3c7'
  },
  {
    title: '职业规划报告已更新',
    desc: '基于你的技能和经历生成新的建议',
    time: '昨天',
    icon: '👨‍💻',
    color: '#e0e7ff'
  },
  {
    title: 'HR消息回复提醒',
    desc: '阿里巴巴HR已查看你的简历',
    time: '昨天',
    icon: '📨',
    color: '#fce7f3'
  }
]

const upcomingInterviews = [
  {
    id: 1,
    company: '阿里巴巴',
    position: '前端开发工程师',
    date: '2026-07-15',
    time: '14:00'
  },
  {
    id: 2,
    company: '字节跳动',
    position: '高级前端工程师',
    date: '2026-07-18',
    time: '10:30'
  }
]
</script>

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