<template>
  <div v-loading="isLoading" class="saved-optimization-detail-view min-h-screen bg-gray-50 p-6">
    <div class="mb-6 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <el-button text @click="$router.push('/resume')">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div>
          <h1 class="text-2xl font-bold text-gray-800">{{ detail.title || '优化简历' }}</h1>
          <p class="mt-1 text-sm text-gray-500">保存于 {{ savedAt || '-' }}</p>
        </div>
      </div>
      <div class="flex gap-3">
        <el-button :loading="downloading" @click="handleDownload">
          <el-icon class="mr-1"><Download /></el-icon>
          下载优化简历
        </el-button>
        <el-button type="danger" plain :loading="deleting" @click="handleDelete">
          <el-icon class="mr-1"><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <el-alert
      v-if="detail.optimization_summary"
      :title="detail.optimization_summary"
      type="success"
      :closable="false"
      show-icon
      class="mb-6"
    />

    <el-row :gutter="20">
      <el-col :xs="24" :lg="12" class="mb-6">
        <el-card class="h-full border-0 optimized-card" shadow="never">
          <template #header>
            <div class="flex items-center gap-2">
              <el-tag type="success" effect="plain">优化简历</el-tag>
              <span class="text-sm font-medium text-green-600">已保存版本 · 优化后</span>
            </div>
          </template>
          <pre class="whitespace-pre-wrap break-words text-sm leading-6 text-gray-700">{{ originalText }}</pre>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12" class="mb-6">
        <el-card class="h-full border-0" shadow="never">
          <template #header>
            <div class="flex items-center gap-2">
              <el-tag type="info" effect="plain">原始简历</el-tag>
              <span class="text-sm text-gray-500">优化前</span>
            </div>
          </template>
          <pre class="whitespace-pre-wrap break-words text-sm leading-6 text-gray-700">{{ optimizedText }}</pre>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="changes.length" class="border-0" shadow="never">
      <template #header><span class="font-semibold">修改记录</span></template>
      <div class="space-y-4">
        <div
          v-for="(change, index) in changes"
          :key="`${change.section}-${index}`"
          class="rounded-xl border border-gray-100 bg-gray-50 p-4"
        >
          <div class="mb-2 flex items-center gap-2">
            <el-tag size="small">{{ change.section }}</el-tag>
            <span class="text-sm text-gray-500">{{ change.reason }}</span>
          </div>
          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="rounded-lg border border-red-100 bg-red-50 p-3 text-sm text-red-700">
              <div class="mb-1 text-xs font-medium text-red-500">修改前</div>
              {{ change.original }}
            </div>
            <div class="rounded-lg border border-green-100 bg-green-50 p-3 text-sm text-green-700">
              <div class="mb-1 text-xs font-medium text-green-500">修改后</div>
              {{ change.optimized }}
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-card v-if="confirmationActions.length" class="mt-6 border-0" shadow="never">
      <template #header><span class="font-semibold">确认补充记录</span></template>
      <div class="space-y-4">
        <div
          v-for="(action, index) in confirmationActions"
          :key="`${action.type}-${action.created_at}-${index}`"
          class="rounded-xl border border-gray-100 bg-gray-50 p-4"
        >
          <div class="mb-2 flex items-center gap-2">
            <el-tag :type="action.type === 'dismiss' ? 'info' : action.type === 'ai' ? 'primary' : 'success'" size="small">
              {{ action.title }}
            </el-tag>
            <span class="text-xs text-gray-400">{{ action.created_at }}</span>
          </div>
          <div v-if="action.summary" class="text-sm leading-6 text-gray-600">{{ action.summary }}</div>
          <pre v-if="action.added_content" class="mt-2 whitespace-pre-wrap rounded-lg bg-white p-3 text-sm leading-6 text-gray-700">{{ action.added_content }}</pre>
          <div v-if="action.feedback" class="mt-2 text-sm text-gray-500">用户要求：{{ action.feedback }}</div>
        </div>
      </div>
    </el-card>

    <el-card v-if="pendingQuestions.length" class="mt-6 border-0" shadow="never">
      <template #header><span class="font-semibold text-orange-600">仍待确认的信息</span></template>
      <ul class="space-y-2 text-sm text-gray-600">
        <li v-for="question in pendingQuestions" :key="question">• {{ question }}</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Delete, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { resumeApi } from '@/api/resume'
import type { OptimizeChange, ResumeOptimizeResult } from '@/types'

const route = useRoute()
const router = useRouter()
const savedOptimizationId = Number(route.params.id)

const isLoading = ref(false)
const downloading = ref(false)
const deleting = ref(false)
const detail = ref<ResumeOptimizeResult>({ change_items: [], confirmation_questions: [] })
const authoritativeOriginal = ref('')

const savedAt = computed(() => detail.value.saved_at?.split('T')[0] || detail.value.created_at?.split('T')[0] || '')
const originalText = computed(() => (
  authoritativeOriginal.value
  || detail.value.original_content
  || detail.value.original
  || '暂无原始内容'
))
const optimizedText = computed(() => detail.value.optimized_content || detail.value.optimized || '暂无优化内容')
const changes = computed<OptimizeChange[]>(() => detail.value.change_items || detail.value.changes || [])
const confirmationActions = computed(() => detail.value.confirmation_actions || [])
const pendingQuestions = computed(() => detail.value.confirmation_questions || [])

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error && typeof error === 'object') {
    const response = (error as { response?: { data?: { message?: unknown; detail?: unknown } } }).response
    if (typeof response?.data?.detail === 'string') return response.data.detail
    if (typeof response?.data?.message === 'string') return response.data.message

    const message = (error as { message?: unknown }).message
    if (typeof message === 'string') return message
  }
  return fallback
}

const readBlobErrorMessage = async (error: unknown, fallback: string) => {
  const data = (error as { response?: { data?: unknown } })?.response?.data
  if (data instanceof Blob && data.type.includes('application/json')) {
    try {
      const parsed = JSON.parse(await data.text()) as { message?: unknown; detail?: unknown }
      if (typeof parsed.detail === 'string') return parsed.detail
      if (typeof parsed.message === 'string') return parsed.message
    } catch {
      return fallback
    }
  }
  return getErrorMessage(error, fallback)
}

const getDownloadFileName = (disposition: string) => {
  const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  const plainName = disposition.match(/filename="?([^";]+)"?/i)?.[1]
  if (encodedName) return decodeURIComponent(encodedName)
  return plainName || `${detail.value.title || '优化简历'}.docx`
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

const loadDetail = async () => {
  isLoading.value = true
  try {
    const response = await resumeApi.getSavedOptimizationDetail(savedOptimizationId)
    detail.value = response.data
    if (response.data.resume_id) {
      try {
        const originalResponse = await resumeApi.getDetail(response.data.resume_id)
        authoritativeOriginal.value = (
          originalResponse.data.extracted_text
          || originalResponse.data.content?.raw_text
          || ''
        )
      } catch {
        // 历史原简历不可用时，仍可使用优化版本中保存的原文快照。
        authoritativeOriginal.value = ''
      }
    }
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载优化简历失败'))
  } finally {
    isLoading.value = false
  }
}

const handleDownload = async () => {
  downloading.value = true
  try {
    const response = await resumeApi.downloadSavedOptimization(savedOptimizationId)
    if (!(response.data instanceof Blob)) {
      throw new Error('下载接口未返回文件流')
    }
    const disposition = response.headers?.['content-disposition'] || ''
    saveBlob(response.data, getDownloadFileName(disposition))
  } catch (error: unknown) {
    ElMessage.error(await readBlobErrorMessage(error, '下载优化简历失败，请稍后重试'))
  } finally {
    downloading.value = false
  }
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这份优化简历吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    deleting.value = true
    await resumeApi.deleteSavedOptimization(savedOptimizationId)
    ElMessage.success('优化简历已删除')
    router.push('/resume')
  } catch (error: unknown) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getErrorMessage(error, '删除优化简历失败，请稍后重试'))
    }
  } finally {
    deleting.value = false
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.saved-optimization-detail-view :deep(.el-card) {
  border-radius: 16px;
}

.optimized-card {
  background: linear-gradient(145deg, #ffffff 0%, #f6fff9 100%);
}
</style>
