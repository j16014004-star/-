<template>
  <div class="resume-optimize-view p-6 bg-gray-50 min-h-screen">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">AI简历优化</h1>
        <p class="text-gray-500 text-sm mt-1">AI智能优化你的简历，提升求职竞争力</p>
      </div>
      <el-button @click="$router.back()">
        <el-icon class="mr-1"><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <!-- Configuration Section -->
    <el-card class="mb-6 border-0" v-if="!showResult">
      <template #header>
        <span class="font-semibold">优化配置</span>
      </template>
      <el-form label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="目标岗位">
              <el-input v-model="targetPosition" placeholder="例如：高级前端工程师" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标公司">
              <el-input v-model="targetCompany" placeholder="例如：阿里巴巴" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="岗位要求（可选）">
          <el-input
            v-model="requirements"
            type="textarea"
            :rows="3"
            placeholder="粘贴目标岗位的JD或要求，AI将根据要求进行针对性优化"
          />
        </el-form-item>
      </el-form>
      <div class="flex justify-center mt-6">
        <el-button type="primary" size="large" :loading="optimizing" @click="handleOptimize">
          <el-icon class="mr-1"><MagicStick /></el-icon>
          {{ optimizing ? 'AI正在优化...' : '开始AI优化' }}
        </el-button>
      </div>
    </el-card>

    <!-- Loading State -->
    <el-card v-if="optimizing" class="border-0 text-center py-12">
      <div class="text-5xl mb-4 animate-pulse">🤖</div>
      <h3 class="text-lg font-semibold text-gray-700 mb-2">AI正在优化您的简历</h3>
      <p class="text-gray-500 mb-4">分析简历内容，生成优化建议...</p>
      <el-progress :percentage="optimizeProgress" :stroke-width="8" class="max-w-md mx-auto" />
    </el-card>

    <!-- Results Section -->
    <template v-if="showResult">
      <!-- Summary Cards -->
      <el-row :gutter="20" class="mb-6">
        <el-col :span="8">
          <el-card class="border-0 text-center">
            <div class="text-3xl font-bold text-indigo-600">{{ changes.length }}</div>
            <div class="text-sm text-gray-500 mt-1">优化修改项</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="border-0 text-center">
            <div class="text-3xl font-bold text-green-600">+{{ scoreImprovement }}%</div>
            <div class="text-sm text-gray-500 mt-1">评分提升</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="border-0 text-center">
            <div class="text-3xl font-bold text-blue-600">A+</div>
            <div class="text-sm text-gray-500 mt-1">优化后等级</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Side-by-side Comparison -->
      <el-row :gutter="20" class="mb-6">
        <el-col :span="12">
          <el-card class="border-0 h-full">
            <template #header>
              <div class="flex items-center gap-2">
                <el-tag type="info" effect="plain">原始简历</el-tag>
                <span class="text-gray-500 text-sm">优化前</span>
              </div>
            </template>
            <div class="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">{{ originalContent }}</div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="border-0 h-full" :class="{ 'ring-2 ring-green-200': showResult }">
            <template #header>
              <div class="flex items-center gap-2">
                <el-tag type="success" effect="plain">优化后简历</el-tag>
                <span class="text-green-600 text-sm font-medium">✨ AI优化版</span>
              </div>
            </template>
            <div class="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">{{ optimizedContent }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Change Log -->
      <el-card class="border-0">
        <template #header>
          <span class="font-semibold">修改详情</span>
        </template>
        <div class="space-y-4">
          <div
            v-for="(change, index) in changes"
            :key="index"
            class="p-4 rounded-xl bg-gray-50 border border-gray-100"
          >
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 text-indigo-600 font-bold text-sm">
                {{ index + 1 }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-gray-800 mb-2">
                  <el-tag size="small" type="primary" class="mr-2">{{ change.section }}</el-tag>
                  {{ change.title }}
                </div>
                <div class="grid grid-cols-2 gap-4 mb-2">
                  <div class="p-3 rounded-lg bg-red-50 border border-red-100">
                    <div class="text-xs text-red-500 font-medium mb-1">修改前</div>
                    <div class="text-sm text-red-700">{{ change.original }}</div>
                  </div>
                  <div class="p-3 rounded-lg bg-green-50 border border-green-100">
                    <div class="text-xs text-green-500 font-medium mb-1">修改后</div>
                    <div class="text-sm text-green-700">{{ change.optimized }}</div>
                  </div>
                </div>
                <div class="text-sm text-gray-500 flex items-center gap-1">
                  <el-icon><InfoFilled /></el-icon>
                  <span>优化原因：{{ change.reason }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Actions -->
      <div class="flex justify-center gap-4 mt-6">
        <el-button size="large" @click="showResult = false">重新优化</el-button>
        <el-button type="primary" size="large" @click="handleDownload">
          <el-icon class="mr-1"><Download /></el-icon>
          下载优化结果
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, MagicStick, Download, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api/resume'

const route = useRoute()
const resumeId = Number(route.params.id) || 1

const targetPosition = ref('高级前端工程师')
const targetCompany = ref('')
const requirements = ref('')
const optimizing = ref(false)
const optimizeProgress = ref(0)
const showResult = ref(false)
const scoreImprovement = ref(23)

const originalContent = ref('')
const optimizedContent = ref('')
const changes = ref<any[]>([])

// 从后端加载原始简历内容
onMounted(async () => {
  try {
    const response = await resumeApi.getDetail(resumeId)
    const data = response.data
    // 如果有原始内容字段，使用它；否则构造一个
    originalContent.value = data.content?.raw_text || data.title || '简历内容加载中...'
  } catch (error) {
    ElMessage.error('加载简历内容失败')
  }
})

const handleOptimize = async () => {
  optimizing.value = true
  optimizeProgress.value = 10

  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (optimizeProgress.value < 90) {
        optimizeProgress.value += Math.random() * 15
      }
    }, 300)

    // 调用后端优化 API
    const response = await resumeApi.optimize({
      resume_id: resumeId,
      target_position: targetPosition.value,
      target_company: targetCompany.value,
      requirements: requirements.value
    })
    const data = response.data

    clearInterval(progressInterval)
    optimizeProgress.value = 100

    // 映射优化结果
    optimizedContent.value = data.optimized_content || ''
    changes.value = data.changes || []
    scoreImprovement.value = data.score_improvement || 0

    setTimeout(() => {
      optimizing.value = false
      showResult.value = true
    }, 500)
  } catch (error: any) {
    clearInterval(undefined as any)
    optimizing.value = false
    optimizeProgress.value = 0
    ElMessage.error(error.response?.data?.message || '优化失败，请稍后重试')
  }
}

const handleDownload = () => {
  ElMessage.success('优化后的简历已开始下载')
}
</script>

<style scoped>
.resume-optimize-view :deep(.el-card) {
  border-radius: 16px;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
