<template>
  <div v-loading="isLoading" class="resume-list-view p-6 bg-gray-50 min-h-screen">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">我的简历</h1>
        <p class="text-gray-500 text-sm mt-1">管理你的简历，使用 AI 智能优化</p>
      </div>
      <el-button type="primary" size="large" @click="$router.push('/resume/upload')">
        <el-icon class="mr-1"><Plus /></el-icon>
        上传简历
      </el-button>
    </div>

    <el-tabs v-model="activeTab" class="resume-tabs">
      <el-tab-pane label="原始简历" name="original" />
      <el-tab-pane label="优化简历" name="optimized" />
    </el-tabs>

    <template v-if="activeTab === 'original'">
      <!-- Empty State -->
      <div v-if="resumes.length === 0" class="text-center py-20">
        <div class="text-6xl mb-4">&#x1F4C4;</div>
        <h3 class="text-lg font-medium text-gray-600 mb-2">暂无简历</h3>
        <p class="text-gray-400 mb-6">上传你的第一份简历，开始 AI 智能优化</p>
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

            </div>

            <!-- Card Footer -->
            <div class="border-t border-gray-100 px-6 py-3 flex items-center justify-between bg-gray-50/50">
              <span class="text-xs text-gray-400">
                <el-icon class="mr-1"><Calendar /></el-icon>
                {{ resume.uploadDate }}
              </span>
              <div class="flex gap-1" @click.stop>
                <el-tooltip content="AI优化" placement="top">
                  <el-button class="optimize-action" text size="small" @click="handleOptimize(resume.id)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="下载" placement="top">
                  <el-button
                    text
                    size="small"
                    :loading="downloadingId === resume.id"
                    :disabled="deletingId === resume.id"
                    @click="handleDownload(resume)"
                  >
                    <el-icon><Download /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="删除" placement="top">
                  <el-button
                    text
                    size="small"
                    type="danger"
                    :loading="deletingId === resume.id"
                    :disabled="downloadingId === resume.id"
                    @click="handleDelete(resume.id)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      </div>
    </template>

    <template v-else>
      <div v-if="savedOptimizations.length === 0" class="text-center py-20">
        <div class="text-6xl mb-4">&#x2728;</div>
        <h3 class="text-lg font-medium text-gray-600 mb-2">暂无优化简历</h3>
        <p class="text-gray-400 mb-6">保存 AI 优化结果后，会在这里统一管理</p>
      </div>

      <el-row v-else :gutter="20">
        <el-col
          v-for="item in savedOptimizations"
          :key="item.id"
          :xs="24"
          :sm="12"
          :lg="8"
          class="mb-6"
        >
          <el-card
            class="resume-card optimized-resume-card border-0 cursor-pointer transition-all duration-200"
            shadow="hover"
            body-style="padding: 0"
            @click="goToSavedOptimizationDetail(item.id)"
          >
            <div class="p-6 pb-4">
              <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg flex items-center justify-center text-lg bg-indigo-50 text-indigo-500">
                    ✨
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-800">{{ item.title }}</h3>
                    <p class="text-xs text-gray-400">AI优化版</p>
                  </div>
                </div>
                <el-tag type="success" size="small" effect="light" round>已保存</el-tag>
              </div>
              <p class="line-clamp-2 text-sm leading-6 text-gray-500">
                {{ item.summary || '已保存的优化简历，可查看、下载或删除。' }}
              </p>
            </div>

            <div class="border-t border-gray-100 px-6 py-3 flex items-center justify-between bg-gray-50/50">
              <span class="text-xs text-gray-400">
                <el-icon class="mr-1"><Calendar /></el-icon>
                {{ item.savedAt }}
              </span>
              <div class="flex gap-1" @click.stop>
                <el-tooltip content="下载优化简历" placement="top">
                  <el-button
                    text
                    size="small"
                    :loading="downloadingSavedId === item.id"
                    :disabled="deletingSavedId === item.id"
                    @click="handleDownloadSavedOptimization(item)"
                  >
                    <el-icon><Download /></el-icon>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="删除优化简历" placement="top">
                  <el-button
                    text
                    size="small"
                    type="danger"
                    :loading="deletingSavedId === item.id"
                    :disabled="downloadingSavedId === item.id"
                    @click="handleDeleteSavedOptimization(item.id)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Calendar, Edit, Delete, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resumeApi } from '@/api/resume'
import type { Resume as ResumeModel, ResumeOptimizeResult } from '@/types'

const router = useRouter()
type ResumeStatus = ResumeModel['status']

interface ResumeItem {
  id: number
  title: string
  fileType: string
  uploadDate: string
  status: ResumeStatus
}

interface SavedOptimizationItem {
  id: number
  resumeId: number
  title: string
  summary: string
  savedAt: string
}

const resumes = ref<ResumeItem[]>([])
const savedOptimizations = ref<SavedOptimizationItem[]>([])
const activeTab = ref<'original' | 'optimized'>('original')
const isLoading = ref(false)
const downloadingId = ref<number | null>(null)
const deletingId = ref<number | null>(null)
const downloadingSavedId = ref<number | null>(null)
const deletingSavedId = ref<number | null>(null)

const normalizeResume = (item: ResumeModel): ResumeItem => ({
  id: item.id,
  title: item.title || '未命名简历',
  fileType: item.file_type || 'pdf',
  uploadDate: item.created_at?.split('T')[0] || '',
  status: item.status || 'pending'
})

const normalizeSavedOptimization = (item: ResumeOptimizeResult): SavedOptimizationItem => ({
  id: Number(item.id || 0),
  resumeId: Number(item.resume_id || 0),
  title: item.title || `优化简历 #${item.id || ''}`,
  summary: item.optimization_summary || '',
  savedAt: item.saved_at?.split('T')[0] || item.created_at?.split('T')[0] || ''
})

// 从后端 API 加载简历列表
onMounted(async () => {
  isLoading.value = true
  try {
    const [response, savedResponse] = await Promise.all([
      resumeApi.getList(),
      resumeApi.getSavedOptimizations().catch(() => null)
    ])
    // 映射后端字段到前端字段
    resumes.value = (response.data?.items || []).map(normalizeResume)
    savedOptimizations.value = (savedResponse?.data?.items || []).map(normalizeSavedOptimization)
  } catch {
    ElMessage.error('加载简历列表失败')
  } finally {
    isLoading.value = false
  }
})

const getFileTypeClass = (type: string) => {
  if (type === 'pdf') return 'bg-red-50 text-red-500'
  return 'bg-blue-50 text-blue-500'
}

const getFileTypeIcon = (type: string) => {
  if (type === 'pdf') return '📄'
  return '📄'
}

const getStatusType = (status: ResumeStatus) => {
  switch (status) {
    case 'completed': return 'success'
    case 'processing': return 'warning'
    case 'pending': return 'info'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusLabel = (status: ResumeStatus) => {
  switch (status) {
    case 'completed': return '解析完成'
    case 'processing': return '解析中'
    case 'pending': return '待处理'
    case 'failed': return '处理失败'
    default: return '未知'
  }
}

const goToDetail = (id: number) => {
  router.push(`/resume/detail/${id}`)
}

const handleOptimize = (id: number) => {
  router.push(`/resume/optimize/${id}`)
}

const goToSavedOptimizationDetail = (id: number) => {
  router.push(`/resume/optimized/${id}`)
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error && typeof error === 'object') {
    const response = (error as { response?: { data?: { message?: unknown } } }).response
    if (typeof response?.data?.message === 'string') {
      return response.data.message
    }

    const message = (error as { message?: unknown }).message
    if (typeof message === 'string') {
      return message
    }
  }
  return fallback
}

const readBlobErrorMessage = async (error: unknown, fallback: string) => {
  const data = (error as { response?: { data?: unknown } })?.response?.data
  if (data instanceof Blob && data.type.includes('application/json')) {
    try {
      const parsed = JSON.parse(await data.text()) as { message?: unknown }
      if (typeof parsed.message === 'string') {
        return parsed.message
      }
    } catch {
      return fallback
    }
  }
  return getErrorMessage(error, fallback)
}

const getDownloadFileName = (resume: ResumeItem, disposition: string) => {
  const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  const plainName = disposition.match(/filename="?([^";]+)"?/i)?.[1]
  if (encodedName) return decodeURIComponent(encodedName)
  return plainName || `${resume.title}.${resume.fileType}`
}

const saveBlob = (blob: Blob, fileName: string) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

const handleDownload = async (resume: ResumeItem) => {
  downloadingId.value = resume.id
  try {
    const response = await resumeApi.download(resume.id)
    if (!(response.data instanceof Blob)) {
      throw new Error('下载接口未返回文件流')
    }
    const disposition = response.headers?.['content-disposition'] || ''
    saveBlob(response.data, getDownloadFileName(resume, disposition))
  } catch (error: unknown) {
    ElMessage.error(await readBlobErrorMessage(error, '下载失败，请稍后重试'))
  } finally {
    downloadingId.value = null
  }
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这份简历吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    deletingId.value = id
    // 调用后端 API 删除
    await resumeApi.delete(id)
    resumes.value = resumes.value.filter(r => r.id !== id)
    ElMessage.success('删除成功')
  } catch (error: unknown) {
    // 用户取消或 API 错误
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getErrorMessage(error, '删除失败，请稍后重试'))
    }
  } finally {
    deletingId.value = null
  }
}

const getSavedDownloadFileName = (item: SavedOptimizationItem, disposition: string) => {
  const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  const plainName = disposition.match(/filename="?([^";]+)"?/i)?.[1]
  if (encodedName) return decodeURIComponent(encodedName)
  return plainName || `${item.title}.docx`
}

const handleDownloadSavedOptimization = async (item: SavedOptimizationItem) => {
  downloadingSavedId.value = item.id
  try {
    const response = await resumeApi.downloadSavedOptimization(item.id)
    if (!(response.data instanceof Blob)) {
      throw new Error('下载接口未返回文件流')
    }
    const disposition = response.headers?.['content-disposition'] || ''
    saveBlob(response.data, getSavedDownloadFileName(item, disposition))
  } catch (error: unknown) {
    ElMessage.error(await readBlobErrorMessage(error, '下载优化简历失败，请稍后重试'))
  } finally {
    downloadingSavedId.value = null
  }
}

const handleDeleteSavedOptimization = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这份优化简历吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    deletingSavedId.value = id
    await resumeApi.deleteSavedOptimization(id)
    savedOptimizations.value = savedOptimizations.value.filter(item => item.id !== id)
    ElMessage.success('优化简历已删除')
  } catch (error: unknown) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getErrorMessage(error, '删除优化简历失败，请稍后重试'))
    }
  } finally {
    deletingSavedId.value = null
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

.resume-tabs {
  margin-bottom: 18px;
}

.optimized-resume-card {
  background: linear-gradient(145deg, #ffffff 0%, #f8faff 100%);
}

:deep(.el-progress__bar) {
  border-radius: 3px;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}

.optimize-action {
  color: #5b5bd6;
  border-radius: 8px;
  background: #eef2ff;
  transition: color 0.2s ease, background-color 0.2s ease, transform 0.2s ease;
}

.optimize-action:hover {
  color: #ffffff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  transform: translateY(-1px);
}
</style>
