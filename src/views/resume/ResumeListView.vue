<template>
  <div class="resume-list-view p-6 bg-gray-50 min-h-screen">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">我的简历</h1>
        <p class="text-gray-500 text-sm mt-1">管理你的简历，使用AI分析优化</p>
      </div>
      <el-button type="primary" size="large" @click="$router.push('/resume/upload')">
        <el-icon class="mr-1"><Plus /></el-icon>
        上传简历
      </el-button>
    </div>

    <!-- Empty State -->
    <div v-if="resumes.length === 0" class="text-center py-20">
      <div class="text-6xl mb-4">&#x1F4C4;</div>
      <h3 class="text-lg font-medium text-gray-600 mb-2">暂无简历</h3>
      <p class="text-gray-400 mb-6">上传你的第一份简历，开始AI智能分析</p>
      <el-button type="primary" size="large" @click="$router.push('/resume/upload')">
        上传简历
      </el-button>
    </div>

    <!-- Resume Grid -->
    <div v-else>
      <el-row :gutter="20">
        <el-col
          v-for="resume in resumes"
          :key="resume.id"
          :xs="24"
          :sm="12"
          :lg="8"
          class="mb-6"
        >
          <el-card
            class="resume-card border-0 cursor-pointer transition-all duration-200"
            shadow="hover"
            body-style="padding: 0"
            @click="goToDetail(resume.id)"
          >
            <!-- Card Header -->
            <div class="p-6 pb-4">
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                  <div
                    class="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                    :class="getFileTypeClass(resume.fileType)"
                  >
                    {{ getFileTypeIcon(resume.fileType) }}
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-800">{{ resume.title }}</h3>
                    <p class="text-xs text-gray-400">{{ resume.fileType.toUpperCase() }}</p>
                  </div>
                </div>
                <el-tag
                  :type="getStatusType(resume.status)"
                  size="small"
                  effect="light"
                  round
                >
                  {{ getStatusLabel(resume.status) }}
                </el-tag>
              </div>

              <!-- AI Score -->
              <div v-if="resume.aiScore" class="flex items-center gap-3 mt-4">
                <div class="flex-1">
                  <div class="flex items-center justify-between text-sm mb-1">
                    <span class="text-gray-500">AI评分</span>
                    <span class="font-bold" :class="getScoreColor(resume.aiScore)">{{ resume.aiScore }}</span>
                  </div>
                  <el-progress
                    :percentage="resume.aiScore"
                    :color="getScoreBarColor(resume.aiScore)"
                    :show-text="false"
                    :stroke-width="6"
                  />
                </div>
              </div>
            </div>

            <!-- Card Footer -->
            <div class="border-t border-gray-100 px-6 py-3 flex items-center justify-between bg-gray-50/50">
              <span class="text-xs text-gray-400">
                <el-icon class="mr-1"><Calendar /></el-icon>
                {{ resume.uploadDate }}
              </span>
              <div class="flex gap-1" @click.stop>
                <el-tooltip content="AI分析" placement="top">
                  <el-button text size="small" @click="handleAnalyze(resume.id)">
                    <el-icon><DataAnalysis /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="AI优化" placement="top">
                  <el-button text size="small" @click="handleOptimize(resume.id)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="删除" placement="top">
                  <el-button text size="small" type="danger" @click="handleDelete(resume.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Calendar, DataAnalysis, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

interface Resume {
  id: number
  title: string
  fileType: string
  uploadDate: string
  aiScore: number | null
  status: 'pending' | 'analyzing' | 'analyzed' | 'error'
}

const resumes = ref<Resume[]>([
  {
    id: 1,
    title: '前端工程师_张三',
    fileType: 'pdf',
    uploadDate: '2026-07-10',
    aiScore: 85,
    status: 'analyzed'
  },
  {
    id: 2,
    title: '全栈开发工程师',
    fileType: 'docx',
    uploadDate: '2026-07-08',
    aiScore: 72,
    status: 'analyzed'
  },
  {
    id: 3,
    title: '高级前端工程师_v3',
    fileType: 'pdf',
    uploadDate: '2026-07-05',
    aiScore: null,
    status: 'pending'
  },
  {
    id: 4,
    title: '实习生简历',
    fileType: 'docx',
    uploadDate: '2026-07-01',
    aiScore: 62,
    status: 'analyzed'
  }
])

const getFileTypeClass = (type: string) => {
  if (type === 'pdf') return 'bg-red-50 text-red-500'
  return 'bg-blue-50 text-blue-500'
}

const getFileTypeIcon = (type: string) => {
  if (type === 'pdf') return '📄'
  return '📄'
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'analyzed': return 'success'
    case 'analyzing': return 'warning'
    case 'pending': return 'info'
    case 'error': return 'danger'
    default: return 'info'
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'analyzed': return '已分析'
    case 'analyzing': return '分析中'
    case 'pending': return '待分析'
    case 'error': return '分析失败'
    default: return '未知'
  }
}

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-yellow-500'
  return 'text-red-500'
}

const getScoreBarColor = (score: number) => {
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

const goToDetail = (id: number) => {
  router.push(`/resume/detail/${id}`)
}

const handleAnalyze = (id: number) => {
  ElMessage.info(`开始分析简历 #${id}`)
  router.push(`/resume/detail/${id}`)
}

const handleOptimize = (id: number) => {
  router.push(`/resume/optimize/${id}`)
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这份简历吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    resumes.value = resumes.value.filter(r => r.id !== id)
    ElMessage.success('删除成功')
  } catch {
    // cancelled
  }
}
</script>

<style scoped>
.resume-list-view :deep(.el-card) {
  border-radius: 16px;
  overflow: hidden;
}

.resume-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08) !important;
}

:deep(.el-progress__bar) {
  border-radius: 3px;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>