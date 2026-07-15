<template>
  <div class="resume-upload-view p-6 bg-gray-50 min-h-screen">
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">上传简历</h1>
      <p class="text-gray-500 text-sm mt-1">支持PDF、DOC、DOCX格式，最大10MB</p>
    </div>

    <el-row :gutter="24">
      <el-col :xs="24" :lg="16">
        <el-card class="border-0" shadow="hover" body-style="padding: 32px">
          <h3 class="text-lg font-semibold text-gray-800 mb-6">上传文件</h3>

          <!-- Title Input -->
          <el-form label-position="top" class="mb-6">
            <el-form-item label="简历标题">
              <el-input
                v-model="title"
                placeholder="例如：前端工程师_张三_2026"
                size="large"
                clearable
              />
            </el-form-item>
          </el-form>

          <!-- Upload Area -->
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.doc,.docx"
            :on-change="handleFileChange"
            :on-exceed="handleExceed"
            class="w-full"
          >
            <div class="py-12">
              <div class="text-5xl mb-4 text-gray-300">&#x1F4C1;</div>
              <div class="text-lg font-medium text-gray-600 mb-2">
                拖拽文件到此处，或<span class="text-blue-600">点击选择文件</span>
              </div>
              <div class="text-sm text-gray-400">
                支持 PDF、DOC、DOCX 格式，最大 10MB
              </div>
            </div>
          </el-upload>

          <!-- Upload Progress -->
          <div v-if="uploading" class="mt-6">
            <div class="flex items-center justify-between text-sm mb-2">
              <span class="text-gray-600">上传中...</span>
              <span class="text-gray-500">{{ uploadProgress }}%</span>
            </div>
            <el-progress
              :percentage="uploadProgress"
              :stroke-width="8"
              :color="uploadProgress === 100 ? '#10b981' : '#3b82f6'"
            />
          </div>

          <!-- Upload Button -->
          <div class="mt-6">
            <el-button
              type="primary"
              size="large"
              :disabled="!selectedFile"
              :loading="uploading"
              @click="handleUpload"
              class="w-full md:w-auto"
            >
              {{ uploading ? '上传中...' : '开始上传' }}
            </el-button>
            <el-button
              size="large"
              @click="resetUpload"
              :disabled="uploading"
              class="ml-3"
            >
              重置
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- Instructions Sidebar -->
      <el-col :xs="24" :lg="8" class="mt-6 lg:mt-0">
        <el-card class="border-0" shadow="hover">
          <template #header>
            <span class="font-semibold text-gray-800">上传须知</span>
          </template>
          <div class="space-y-4">
            <div class="flex gap-3">
              <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500 flex-shrink-0">1</div>
              <div>
                <div class="font-medium text-gray-700 text-sm">格式要求</div>
                <div class="text-gray-400 text-xs mt-0.5">支持PDF、Word文档格式</div>
              </div>
            </div>
            <div class="flex gap-3">
              <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500 flex-shrink-0">2</div>
              <div>
                <div class="font-medium text-gray-700 text-sm">文件大小</div>
                <div class="text-gray-400 text-xs mt-0.5">单个文件不超过10MB</div>
              </div>
            </div>
            <div class="flex gap-3">
              <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500 flex-shrink-0">3</div>
              <div>
                <div class="font-medium text-gray-700 text-sm">AI优化</div>
                <div class="text-gray-400 text-xs mt-0.5">解析完成后，可在简历详情中启动AI优化</div>
              </div>
            </div>
            <div class="flex gap-3">
              <div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-500 flex-shrink-0">4</div>
              <div>
                <div class="font-medium text-gray-700 text-sm">隐私保护</div>
                <div class="text-gray-400 text-xs mt-0.5">你的简历数据安全加密存储</div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="border-0 mt-4" shadow="hover">
          <template #header>
            <span class="font-semibold text-gray-800">上传建议</span>
          </template>
          <div class="text-sm text-gray-500 space-y-2">
            <p>&#x1F4A1; 使用清晰的文件名，如"姓名_岗位_日期"</p>
            <p>&#x1F4A1; 确保简历内容是最新版本</p>
            <p>&#x1F4A1; PDF格式能保持排版不失真</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { UploadInstance, UploadFile, UploadFiles } from 'element-plus'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api/resume'

const router = useRouter()
const uploadRef = ref<UploadInstance>()
const title = ref('')
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)

const validateFile = (file: File) => {
  const isAllowedType = ['.pdf', '.doc', '.docx'].some((extension) =>
    file.name.toLowerCase().endsWith(extension)
  )
  if (!isAllowedType) {
    ElMessage.error('仅支持 PDF、DOC 或 DOCX 格式的简历文件')
    return false
  }

  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('简历文件不能超过 10MB')
    return false
  }

  return true
}

const handleFileChange = (uploadFile: UploadFile, _uploadFiles: UploadFiles) => {
  if (uploadFile.raw && validateFile(uploadFile.raw)) {
    selectedFile.value = uploadFile.raw
    if (!title.value) {
      title.value = uploadFile.name.replace(/\.[^/.]+$/, '')
    }
  } else {
    selectedFile.value = null
    uploadRef.value?.clearFiles()
  }
}

const handleExceed = () => {
  ElMessage.warning('只能上传一个文件')
}

const resetUpload = () => {
  selectedFile.value = null
  uploadProgress.value = 0
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  uploadProgress.value = 0

  try {
    // 调用后端 API 上传简历
    const response = await resumeApi.upload(selectedFile.value, title.value, (percentage) => {
      uploadProgress.value = Math.max(uploadProgress.value, percentage)
    })

    uploadProgress.value = 100

    setTimeout(() => {
      uploading.value = false
      ElMessage.success({
        message: '简历上传成功！正在跳转到详情页...',
        duration: 2000
      })

      const newId = response.data?.id
      if (!newId) {
        ElMessage.error('上传成功，但后端未返回简历 ID，请前往“我的简历”查看')
        router.push('/resume')
        return
      }
      setTimeout(() => {
        router.push(`/resume/detail/${newId}`)
      }, 500)
    }, 500)
  } catch (error: unknown) {
    uploading.value = false
    uploadProgress.value = 0
    const message = error instanceof Error ? error.message : '上传失败，请稍后重试'
    ElMessage.error(message)
  }
}
</script>

<style scoped>
.resume-upload-view :deep(.el-card) {
  border-radius: 16px;
}

:deep(.el-upload-dragger) {
  border: 2px dashed #d1d5db;
  border-radius: 16px;
  background: #fafafa;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #3b82f6;
  background: #f0f7ff;
}

:deep(.el-upload-dragger.is-dragover) {
  border-color: #3b82f6;
  background: #eff6ff;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}

:deep(.el-upload) {
  width: 100%;
}
</style>
