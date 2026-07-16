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
            <el-form-item label="优化类型">
              <el-select v-model="optimizationType" class="w-full">
                <el-option label="通用优化" value="general" />
                <el-option label="针对目标岗位优化" value="target_role" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="目标岗位方向">
              <el-select
                v-model="targetPosition"
                class="w-full"
                filterable
                allow-create
                clearable
                default-first-option
                placeholder="请选择或输入目标岗位方向"
                @change="handleTargetPositionChange"
              >
                <el-option
                  v-for="position in targetPositionOptions"
                  :key="position"
                  :label="position"
                  :value="position"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="优化重点">
              <el-select v-model="optimizationFocus" multiple class="w-full">
                <el-option label="全面优化" value="all" />
                <el-option label="工作经历" value="work_experience" />
                <el-option label="项目经历" value="project_experience" />
                <el-option label="技能表达" value="skills" />
                <el-option label="ATS友好度" value="ats" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="表达风格">
              <el-select v-model="style" class="w-full">
                <el-option label="专业简洁" value="professional" />
                <el-option label="技术型" value="technical" />
                <el-option label="管理型" value="management" />
                <el-option label="应届生" value="graduate" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-checkbox v-model="preserveStructure">尽量保留原有简历结构</el-checkbox>
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
      <p class="text-gray-500 mb-4">{{ taskStatusText }}</p>
      <el-progress :percentage="optimizeProgress" :stroke-width="8" class="max-w-md mx-auto" />
    </el-card>

    <!-- Results Section -->
    <template v-if="showResult">
      <el-alert
        v-if="optimizationSummary"
        :title="optimizationSummary"
        type="success"
        :closable="false"
        show-icon
        class="mb-6"
      />
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
            <div class="text-3xl font-bold text-green-600">{{ scoreImprovement === null ? '暂未评分' : scoreImprovement + '分' }}</div>
            <div class="text-sm text-gray-500 mt-1">简历评分</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="border-0 text-center">
            <div class="text-3xl font-bold text-blue-600">{{ confirmationQuestions.length }}</div>
            <div class="text-sm text-gray-500 mt-1">待确认信息</div>
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
                  <span v-if="change.requires_confirmation" class="text-orange-500">待用户确认</span>
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

      <el-card v-if="confirmationQuestions.length" class="mt-6 border-0">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <span class="font-semibold text-orange-600">需要用户确认的信息</span>
            <el-tag type="warning" effect="plain">建议处理后再保存</el-tag>
          </div>
        </template>
        <div class="space-y-4">
          <div
            v-for="(question, index) in confirmationQuestions"
            :key="question"
            class="rounded-xl border border-orange-100 bg-orange-50/40 p-4"
          >
            <div class="mb-3 flex items-start gap-2 text-sm leading-6 text-gray-700">
              <span class="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-orange-400"></span>
              <span>{{ question }}</span>
            </div>
            <el-input
              v-model="questionConfirmations[question]"
              type="textarea"
              :rows="2"
              maxlength="800"
              show-word-limit
              placeholder="请确认这个问题的真实信息，例如：已部署上线，GitHub链接是 https://..."
            />
            <div class="mt-3 flex justify-end">
              <el-button
                type="primary"
                plain
                :loading="confirmingQuestionIndex === index"
                @click="handleConfirmQuestion(question, index)"
              >
                确认并让 AI 补全
              </el-button>
            </div>
          </div>
        </div>
        <div class="mt-5 flex flex-wrap items-center gap-3">
          <el-button type="primary" plain :loading="applyingAiConfirmation" @click="handleAiFillConfirmation">
            <el-icon class="mr-1"><MagicStick /></el-icon>
            AI 补全到简历
          </el-button>
          <el-button plain @click="openManualConfirmationDialog">
            手动填写后加入简历
          </el-button>
          <el-button text type="info" :loading="dismissingConfirmation" @click="handleDismissConfirmation">
            暂不需要这些信息
          </el-button>
        </div>
      </el-card>

      <el-card v-if="confirmationPreview" class="mt-6 border-0 preview-card">
        <template #header>
          <div class="flex items-center justify-between gap-4">
            <span class="font-semibold">
              {{ confirmationPreviewType === 'ai' ? 'AI 补全预览' : '手动补充预览' }}
            </span>
            <el-tag :type="confirmationPreviewType === 'ai' ? 'primary' : 'success'" effect="plain">
              尚未采用
            </el-tag>
          </div>
        </template>

        <div class="space-y-5">
          <div>
            <div class="mb-2 text-sm font-medium text-gray-700">本次新增内容</div>
            <pre class="rounded-lg bg-indigo-50 p-4 text-sm leading-6 text-indigo-900 whitespace-pre-wrap">{{ confirmationPreview.added_content || '后端未返回新增内容摘要' }}</pre>
          </div>

          <div v-if="confirmationPreview.summary">
            <div class="mb-2 text-sm font-medium text-gray-700">处理说明</div>
            <div class="rounded-lg bg-gray-50 p-4 text-sm leading-6 text-gray-600">{{ confirmationPreview.summary }}</div>
          </div>

          <el-alert
            v-if="!confirmationPreview.has_changes"
            title="AI 没有找到可确认的真实依据，本次未修改简历。请手动填写真实信息，或告诉 AI 明确的事实后再生成。"
            type="warning"
            :closable="false"
            show-icon
          />

          <div>
            <div class="mb-2 text-sm font-medium text-gray-700">合并后的优化简历预览</div>
            <pre class="max-h-96 overflow-y-auto rounded-lg bg-gray-50 p-4 text-sm leading-6 text-gray-700 whitespace-pre-wrap">{{ confirmationPreview.optimized_content }}</pre>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <el-button type="primary" :disabled="!confirmationPreview.has_changes" @click="acceptConfirmationPreview">
              {{ confirmationPreviewType === 'ai' ? '采用 AI 补全内容' : '采用手动补充内容' }}
            </el-button>
            <el-button v-if="confirmationPreviewType === 'ai'" plain @click="openAiFeedbackDialog">
              不满意，告诉 AI 怎么改
            </el-button>
            <el-button v-else plain @click="openManualConfirmationDialog">
              继续修改手动内容
            </el-button>
            <el-button text @click="clearConfirmationPreview">暂不采用</el-button>
          </div>
        </div>
      </el-card>

      <el-card v-if="confirmationActions.length" class="mt-6 border-0">
        <template #header><span class="font-semibold">确认信息处理记录</span></template>
        <div class="space-y-3">
          <div
            v-for="(action, index) in confirmationActions"
            :key="`${action.type}-${index}`"
            class="rounded-xl border border-gray-100 bg-gray-50 p-4"
          >
            <div class="mb-2 flex items-center gap-2">
              <el-tag size="small" :type="action.type === 'dismiss' ? 'info' : action.type === 'ai' ? 'primary' : 'success'">
                {{ action.title }}
              </el-tag>
              <span class="text-xs text-gray-400">{{ action.created_at }}</span>
            </div>
            <div v-if="action.summary" class="text-sm leading-6 text-gray-600">{{ action.summary }}</div>
            <pre v-if="action.added_content" class="mt-2 rounded-lg bg-white p-3 text-sm leading-6 text-gray-700 whitespace-pre-wrap">{{ action.added_content }}</pre>
          </div>
        </div>
      </el-card>

      <!-- Actions -->
      <div class="flex justify-center gap-4 mt-6">
        <el-button size="large" @click="showResult = false">重新优化</el-button>
        <el-button type="primary" size="large" :loading="savingOptimization" @click="openSaveConfirmDialog">
          <el-icon class="mr-1"><Check /></el-icon>
          保存更改内容
        </el-button>
      </div>
    </template>

    <el-dialog v-model="manualDialogVisible" title="手动补充确认信息" width="720px">
      <div class="space-y-4">
        <div
          v-for="(question, index) in confirmationQuestions"
          :key="question"
          class="rounded-xl border border-gray-100 bg-gray-50 p-4"
        >
          <div class="mb-2 text-sm font-medium text-gray-700">{{ index + 1 }}. {{ question }}</div>
          <el-input
            v-model="manualConfirmations[index]"
            type="textarea"
            :rows="3"
            maxlength="1000"
            show-word-limit
            placeholder="请填写要补充到简历中的真实信息"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="manualDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applyingManualConfirmation" @click="handleManualFillConfirmation">
          生成手动补充预览
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="aiFeedbackDialogVisible" title="告诉 AI 哪里不满意" width="640px">
      <el-input
        v-model="aiFeedback"
        type="textarea"
        :rows="5"
        maxlength="1000"
        show-word-limit
        placeholder="例如：内容太泛泛了，请重点补充项目中的量化成果，不要编造没有确认的信息。"
      />
      <template #footer>
        <el-button @click="aiFeedbackDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="applyingAiConfirmation" @click="regenerateAiPreview">
          让 AI 重新生成
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="saveConfirmVisible" title="保存前确认更改" width="960px">
      <el-alert
        title="请确认最终优化内容。你可以在下方直接微调，确认后会保存到“我的简历 - 优化简历”。"
        type="info"
        :closable="false"
        show-icon
        class="mb-4"
      />
      <el-row :gutter="16" class="mb-4">
        <el-col :span="12">
          <div class="mb-2 text-sm font-medium text-gray-700">原始简历</div>
          <pre class="save-preview-box whitespace-pre-wrap">{{ originalContent }}</pre>
        </el-col>
        <el-col :span="12">
          <div class="mb-2 text-sm font-medium text-gray-700">最终优化内容（可编辑）</div>
          <el-input
            v-model="finalEditableContent"
            type="textarea"
            :rows="16"
            maxlength="50000"
            show-word-limit
          />
        </el-col>
      </el-row>
      <div v-if="confirmationActions.length" class="mb-4">
        <div class="mb-2 text-sm font-medium text-gray-700">已处理的确认信息</div>
        <div class="space-y-2">
          <div v-for="(action, index) in confirmationActions" :key="`save-${index}`" class="rounded-lg bg-gray-50 p-3 text-sm text-gray-600">
            <span class="font-medium text-gray-800">{{ action.title }}：</span>{{ action.summary || action.added_content || '已处理' }}
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="saveConfirmVisible = false">取消</el-button>
        <el-button @click="showResult = false; saveConfirmVisible = false">返回重新优化</el-button>
        <el-button type="primary" :loading="savingOptimization" @click="handleSaveOptimization">
          确认保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, MagicStick, Check, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api/resume'
import { jobApi } from '@/api/job'
import { useAITask } from '@/composables/useAITask'
import type { OptimizeChange, ResumeOptimizeResult } from '@/types'
import type {
  ResumeOptimizationConfirmationAction,
  ResumeOptimizationConfirmationPreview,
  ResumeOptimizeParams
} from '@/api/types/resume'

const route = useRoute()
const resumeId = Number(route.params.id) || 1

const targetPosition = ref(String(route.query.target_role || ''))
const optimizationType = ref<ResumeOptimizeParams['optimization_type']>(targetPosition.value ? 'target_role' : 'general')
const optimizationFocus = ref<ResumeOptimizeParams['optimization_focus']>(['all'])
const style = ref<ResumeOptimizeParams['style']>('professional')
const preserveStructure = ref(true)
const optimizing = ref(false)
const optimizeProgress = ref(0)
const showResult = ref(false)
const scoreImprovement = ref<number | null>(null)
const optimizationSummary = ref('')
const confirmationQuestions = ref<string[]>([])
const currentOptimizationId = ref<number | null>(null)
const applyingAiConfirmation = ref(false)
const applyingManualConfirmation = ref(false)
const dismissingConfirmation = ref(false)
const savingOptimization = ref(false)
const manualDialogVisible = ref(false)
const manualConfirmations = ref<string[]>([])
const questionConfirmations = ref<Record<string, string>>({})
const confirmingQuestionIndex = ref<number | null>(null)
const confirmationPreview = ref<ResumeOptimizationConfirmationPreview | null>(null)
const confirmationPreviewType = ref<'ai' | 'manual'>('ai')
const confirmationPreviewQuestions = ref<string[]>([])
const confirmationPreviewConfirmedAnswers = ref<Array<{ question: string; answer: string }>>([])
const aiFeedbackDialogVisible = ref(false)
const aiFeedback = ref('')
const saveConfirmVisible = ref(false)
const finalEditableContent = ref('')
const confirmationActions = ref<ResumeOptimizationConfirmationAction[]>([])
const { currentTask, pollTask } = useAITask()

const originalContent = ref('')
const optimizedContent = ref('')
const changes = ref<OptimizeChange[]>([])
const recommendedTargetPositions = ref<string[]>([])
const defaultTargetPositions = [
  '后端开发工程师',
  '前端开发工程师',
  'Java开发工程师',
  'Python开发工程师',
  'AI算法工程师',
  '测试工程师',
  '产品经理',
  '运维工程师',
  '全栈开发工程师',
  '数据分析师',
  '数据开发工程师',
  'UI设计师',
]
const targetPositionOptions = computed(() => {
  return Array.from(new Set([...defaultTargetPositions, ...recommendedTargetPositions.value]))
})
const taskStatusText = computed(() => {
  const labels = {
    pending: '优化任务已创建',
    preparing: '正在整理简历内容',
    generating: 'AI 正在生成优化版本',
    validating: '正在校验优化内容',
    saving: '正在保存优化版本',
    success: '优化版本已生成',
    failed: '简历优化失败',
    cancelled: '优化任务已取消',
  }
  return currentTask.value ? labels[currentTask.value.status] : '正在准备优化任务'
})

const loadRecommendedTargetPositions = async () => {
  try {
    const response = await jobApi.getRecommendations({ page: 1, page_size: 30 })
    const titles = response.data.items
      .map(job => job.title?.trim())
      .filter((title): title is string => Boolean(title))
    recommendedTargetPositions.value = Array.from(new Set(titles))
  } catch {
    recommendedTargetPositions.value = []
  }
}

const handleTargetPositionChange = (value: string) => {
  if (value.trim()) {
    optimizationType.value = 'target_role'
  }
}

// 从后端加载原始简历内容
onMounted(async () => {
  loadRecommendedTargetPositions()

  try {
    const response = await resumeApi.getDetail(resumeId)
    const data = response.data
    // 如果有原始内容字段，使用它；否则构造一个
    originalContent.value = data.extracted_text || data.content?.raw_text || data.title || '暂无可优化内容'
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载简历内容失败'))
  }
})

const handleOptimize = async () => {
  optimizing.value = true
  optimizeProgress.value = 5

  try {
    if (optimizationType.value === 'target_role' && !targetPosition.value.trim()) {
      ElMessage.warning('请选择或输入目标岗位方向')
      return
    }
    if (!optimizationFocus.value.length) {
      ElMessage.warning('请至少选择一个优化重点')
      return
    }

    confirmationActions.value = []
    clearConfirmationPreview()

    const startResponse = await resumeApi.startOptimization({
      resume_id: resumeId,
      optimization_type: optimizationType.value,
      target_role: optimizationType.value === 'target_role' ? targetPosition.value.trim() : undefined,
      optimization_focus: optimizationFocus.value,
      style: style.value,
      preserve_structure: preserveStructure.value,
    })
    const task = await pollTask(startResponse.data.task_id, (updatedTask) => {
      optimizeProgress.value = updatedTask.progress
    })
    if (!task.result_id) throw new Error('优化任务完成但未返回结果 ID')
    currentOptimizationId.value = task.result_id
    const response = await resumeApi.getOptimization(resumeId, task.result_id)
    applyOptimizationResult(response.data)
    optimizeProgress.value = 100
    showResult.value = true
    ElMessage.success('简历优化版本已生成')
  } catch (error: unknown) {
    optimizeProgress.value = 0
    ElMessage.error(getErrorMessage(error, '优化失败，请稍后重试'))
  } finally {
    optimizing.value = false
  }
}

const applyOptimizationResult = (data: ResumeOptimizeResult) => {
  originalContent.value = data.original || originalContent.value
  optimizedContent.value = data.optimized_content || data.optimized || optimizedContent.value
  changes.value = data.change_items || data.changes || changes.value
  scoreImprovement.value = data.score_improvement ?? scoreImprovement.value
  optimizationSummary.value = data.optimization_summary || optimizationSummary.value
  confirmationQuestions.value = data.confirmation_questions || []
  if (data.confirmation_actions) {
    confirmationActions.value = data.confirmation_actions
  }
}

const mergeChanges = (current: OptimizeChange[], incoming: OptimizeChange[]) => {
  const merged: OptimizeChange[] = []
  const seen = new Set<string>()
  for (const item of [...current, ...incoming]) {
    const key = `${item.section}\u0000${item.original}\u0000${item.optimized}`
    if (seen.has(key)) continue
    seen.add(key)
    merged.push(item)
  }
  return merged.slice(0, 50)
}

const getNowText = () => new Date().toLocaleString('zh-CN', { hour12: false })

const requireOptimizationId = () => {
  if (!currentOptimizationId.value) {
    ElMessage.warning('请先完成一次简历优化')
    return null
  }
  return currentOptimizationId.value
}

const handleAiFillConfirmation = async () => {
  await createAiPreview({
    questions: confirmationQuestions.value,
  })
}

const createAiPreview = async (options: {
  questions?: string[]
  confirmedAnswers?: Array<{ question: string; answer: string }>
  feedback?: string
} = {}) => {
  const optimizationId = requireOptimizationId()
  if (!optimizationId) return
  const questions = options.questions?.length
    ? options.questions
    : confirmationQuestions.value
  const confirmedAnswers = (options.confirmedAnswers || []).map(item => ({ ...item }))
  applyingAiConfirmation.value = true
  try {
    const response = await resumeApi.previewAiConfirmation({
      resume_id: resumeId,
      optimization_id: optimizationId,
      optimized_content: optimizedContent.value,
      confirmation_questions: questions,
      confirmed_answers: confirmedAnswers,
      feedback: options.feedback?.trim() || undefined,
    })
    confirmationPreview.value = response.data
    confirmationPreviewType.value = 'ai'
    confirmationPreviewQuestions.value = response.data.resolved_questions?.length
      ? [...response.data.resolved_questions]
      : [...questions]
    confirmationPreviewConfirmedAnswers.value = confirmedAnswers
    aiFeedbackDialogVisible.value = false
    ElMessage.success('AI 补全预览已生成，请确认是否采用')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '生成 AI 补全预览失败'))
  } finally {
    applyingAiConfirmation.value = false
  }
}

const handleConfirmQuestion = async (question: string, index: number) => {
  const answer = questionConfirmations.value[question]?.trim()
  if (!answer) {
    ElMessage.warning('请先填写这条问题的确认内容')
    return
  }
  confirmingQuestionIndex.value = index
  try {
    await createAiPreview({
      questions: [question],
      confirmedAnswers: [{ question, answer }],
    })
  } finally {
    confirmingQuestionIndex.value = null
  }
}

const openManualConfirmationDialog = () => {
  manualConfirmations.value = confirmationQuestions.value.map(() => '')
  manualDialogVisible.value = true
}

const handleManualFillConfirmation = async () => {
  const optimizationId = requireOptimizationId()
  if (!optimizationId) return
  const confirmations = confirmationQuestions.value
    .map((question, index) => ({ question, answer: manualConfirmations.value[index]?.trim() || '' }))
    .filter(item => item.answer)
  if (!confirmations.length) {
    ElMessage.warning('请至少填写一条需要加入简历的信息')
    return
  }

  applyingManualConfirmation.value = true
  try {
    const response = await resumeApi.previewManualConfirmation({
      resume_id: resumeId,
      optimization_id: optimizationId,
      optimized_content: optimizedContent.value,
      confirmations,
    })
    confirmationPreview.value = response.data
    confirmationPreviewType.value = 'manual'
    confirmationPreviewQuestions.value = confirmations.map(item => item.question)
    confirmationPreviewConfirmedAnswers.value = []
    manualDialogVisible.value = false
    ElMessage.success('手动补充预览已生成，请确认是否采用')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '生成手动补充预览失败'))
  } finally {
    applyingManualConfirmation.value = false
  }
}

const clearConfirmationPreview = () => {
  confirmationPreview.value = null
  confirmationPreviewQuestions.value = []
  confirmationPreviewConfirmedAnswers.value = []
}

const acceptConfirmationPreview = () => {
  const preview = confirmationPreview.value
  if (!preview) return
  if (!preview.has_changes) {
    ElMessage.warning('本次没有产生可采用的简历修改，请先补充真实信息')
    return
  }
  optimizedContent.value = preview.optimized_content || optimizedContent.value
  if (preview.change_items?.length) {
    changes.value = mergeChanges(changes.value, preview.change_items)
  }
  confirmationQuestions.value = preview.remaining_questions || []
  confirmationPreviewQuestions.value.forEach((question) => {
    delete questionConfirmations.value[question]
  })
  confirmationActions.value.push({
    type: confirmationPreviewType.value,
    title: confirmationPreviewType.value === 'ai' ? 'AI 补全到简历' : '手动填写后加入简历',
    questions: confirmationPreviewQuestions.value,
    added_content: preview.added_content,
    summary: preview.summary,
    feedback: confirmationPreviewType.value === 'ai' ? aiFeedback.value.trim() || undefined : undefined,
    created_at: getNowText(),
  })
  clearConfirmationPreview()
  aiFeedback.value = ''
  ElMessage.success('补充内容已采用，并已更新优化后简历')
}

const openAiFeedbackDialog = () => {
  aiFeedbackDialogVisible.value = true
}

const regenerateAiPreview = async () => {
  if (!aiFeedback.value.trim()) {
    ElMessage.warning('请填写不满意的原因或修改要求')
    return
  }
  await createAiPreview({
    questions: confirmationPreviewQuestions.value.length ? confirmationPreviewQuestions.value : confirmationQuestions.value,
    confirmedAnswers: confirmationPreviewConfirmedAnswers.value,
    feedback: aiFeedback.value,
  })
}

const handleDismissConfirmation = async () => {
  const optimizationId = requireOptimizationId()
  if (!optimizationId) return
  dismissingConfirmation.value = true
  try {
    const dismissedQuestions = [...confirmationQuestions.value]
    const response = await resumeApi.dismissConfirmations({
      resume_id: resumeId,
      optimization_id: optimizationId,
      confirmation_questions: dismissedQuestions,
    })
    applyOptimizationResult(response.data)
    confirmationActions.value.push({
      type: 'dismiss',
      title: '暂不需要这些信息',
      questions: dismissedQuestions,
      summary: '用户选择不补充这些待确认信息。',
      created_at: getNowText(),
    })
    clearConfirmationPreview()
    ElMessage.success('已标记为不需要补充这些信息')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '忽略确认信息失败'))
  } finally {
    dismissingConfirmation.value = false
  }
}

const openSaveConfirmDialog = () => {
  finalEditableContent.value = optimizedContent.value
  saveConfirmVisible.value = true
}

const handleSaveOptimization = async () => {
  const optimizationId = requireOptimizationId()
  if (!optimizationId) return
  if (!finalEditableContent.value.trim()) {
    ElMessage.warning('暂无可保存的优化内容')
    return
  }
  const missingConfirmedChanges = changes.value.filter(change => (
    change.evidence_source === 'user_confirmation'
    && Boolean(change.optimized?.trim())
    && !finalEditableContent.value.includes(change.optimized.trim())
  ))
  if (missingConfirmedChanges.length) {
    ElMessage.error('最终简历缺少已采用的确认补充内容，请恢复补充内容后再保存')
    return
  }

  savingOptimization.value = true
  try {
    const response = await resumeApi.saveOptimization({
      resume_id: resumeId,
      optimization_id: optimizationId,
      optimized_content: finalEditableContent.value,
      confirmation_actions: confirmationActions.value,
      change_items: changes.value,
      confirmation_questions: confirmationQuestions.value,
    })
    applyOptimizationResult(response.data)
    saveConfirmVisible.value = false
    ElMessage.success('更改内容已保存，可在“我的简历 - 优化简历”中查看')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '保存更改内容失败'))
  } finally {
    savingOptimization.value = false
  }
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  const message = (error as { response?: { data?: { message?: unknown } } })?.response?.data?.message
  return typeof message === 'string' ? message : fallback
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
