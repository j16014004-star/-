<template>
  <div class="career-assessment-view min-h-screen bg-gray-50 p-6">
    <div class="mx-auto max-w-5xl">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <el-button text class="mb-2 !px-0" @click="router.push('/career/check-in')">← 返回计划执行打卡</el-button>
          <h1 class="text-2xl font-bold text-gray-800">阶段考核</h1>
          <p class="mt-1 text-sm text-gray-500">根据本阶段任务、打卡记录和学习答疑生成，检验真实掌握情况</p>
        </div>
        <el-tag v-if="assessment" :type="assessmentStatusMeta.type" size="large">
          {{ assessmentStatusMeta.label }}
        </el-tag>
      </div>

      <el-card v-if="loading" class="border-0 py-24 text-center" shadow="never">
        <el-icon class="is-loading text-5xl text-indigo-500"><Loading /></el-icon>
        <div class="mt-4 text-gray-500">正在加载阶段考核...</div>
      </el-card>

      <el-card v-else-if="loadError || !assessment" class="border-0 py-16 text-center" shadow="never">
        <el-empty :description="loadError || '没有找到阶段考核'">
          <el-button type="primary" @click="loadAssessment">重新加载</el-button>
        </el-empty>
      </el-card>

      <template v-else-if="result">
        <el-card class="mb-6 overflow-hidden border-0 result-hero" shadow="never">
          <div class="grid grid-cols-1 gap-6 md:grid-cols-[180px_1fr] md:items-center">
            <el-progress
              type="dashboard"
              :percentage="Math.round(result.score)"
              :color="result.passed ? '#22c55e' : '#f59e0b'"
              :width="150"
            >
              <template #default>
                <div class="text-3xl font-bold" :class="result.passed ? 'text-green-600' : 'text-orange-500'">
                  {{ Math.round(result.score) }} 分
                </div>
                <div class="mt-1 text-xs text-gray-400">及格线 {{ result.passing_score }}</div>
              </template>
            </el-progress>
            <div>
              <el-tag :type="result.passed ? 'success' : 'warning'" effect="dark">
                {{ result.passed ? '考核通过' : '需要继续巩固' }}
              </el-tag>
              <h2 class="mt-3 text-xl font-bold text-gray-800">{{ result.stage }}</h2>
              <p class="mt-2 text-sm leading-7 text-gray-600">{{ result.summary }}</p>
            </div>
          </div>
        </el-card>

        <el-row :gutter="20" class="mb-6">
          <el-col :xs="24" :md="12" class="mb-4 md:mb-0">
            <el-card class="h-full border-0" shadow="never">
              <template #header><span class="font-semibold text-green-600">已经掌握</span></template>
              <ul class="space-y-2 text-sm leading-6 text-gray-600">
                <li v-for="item in result.strengths" :key="item">✓ {{ item }}</li>
              </ul>
            </el-card>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-card class="h-full border-0" shadow="never">
              <template #header><span class="font-semibold text-orange-600">需要加强</span></template>
              <ul class="space-y-2 text-sm leading-6 text-gray-600">
                <li v-for="item in result.weaknesses" :key="item">• {{ item }}</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>

        <el-card class="mb-6 border-0" shadow="never">
          <template #header><span class="font-semibold text-gray-800">逐题解析</span></template>
          <el-collapse>
            <el-collapse-item
              v-for="(item, index) in result.question_results"
              :key="item.question_id"
              :name="item.question_id"
            >
              <template #title>
                <div class="flex flex-1 items-center justify-between pr-4">
                  <span>第 {{ index + 1 }} 题</span>
                  <el-tag :type="item.score >= item.max_score ? 'success' : 'warning'" size="small">
                    {{ item.score }}/{{ item.max_score }} 分
                  </el-tag>
                </div>
              </template>
              <div class="space-y-3 text-sm leading-7 text-gray-600">
                <div><b>你的答案：</b><span class="whitespace-pre-wrap">{{ displayAnswer(item.user_answer) }}</span></div>
                <div v-if="item.reference_answer !== null && item.reference_answer !== undefined">
                  <b>参考答案：</b><span class="whitespace-pre-wrap">{{ displayAnswer(item.reference_answer) }}</span>
                </div>
                <div><b>AI 点评：</b>{{ item.feedback }}</div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <el-card class="mb-6 border-0" shadow="never">
          <template #header><span class="font-semibold text-gray-800">下一步建议</span></template>
          <ul class="space-y-2 text-sm leading-6 text-gray-600">
            <li v-for="item in result.improvement_advice" :key="item">• {{ item }}</li>
          </ul>
          <div class="mt-6 flex flex-wrap justify-center gap-3">
            <el-button @click="router.push('/career/check-in')">返回打卡计划</el-button>
            <el-button
              v-if="result.passed"
              type="success"
              :loading="transitioning"
              @click="handleEnterNextStage"
            >进入下一阶段</el-button>
            <el-button
              v-else-if="result.remediation_available"
              type="warning"
              :loading="transitioning"
              @click="handleAcceptRemediation"
            >接受补强计划</el-button>
          </div>
        </el-card>
      </template>

      <template v-else>
        <el-card class="mb-6 border-0 assessment-intro" shadow="never">
          <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <div class="text-xs text-indigo-500">考核阶段</div>
              <div class="mt-1 font-semibold text-gray-800">{{ assessment.stage }}</div>
            </div>
            <div>
              <div class="text-xs text-indigo-500">题目数量</div>
              <div class="mt-1 font-semibold text-gray-800">{{ assessment.questions.length }} 题 · {{ totalPoints }} 分</div>
            </div>
            <div>
              <div class="text-xs text-indigo-500">通过标准</div>
              <div class="mt-1 font-semibold text-gray-800">{{ assessment.passing_score }} 分</div>
            </div>
          </div>
          <el-alert
            class="mt-5"
            title="答案会自动保存在当前浏览器中。代码题只提交文本，前端不会直接运行代码。"
            type="info"
            :closable="false"
            show-icon
          />
        </el-card>

        <div class="sticky top-3 z-10 mb-5 rounded-xl border border-indigo-100 bg-white px-5 py-3 shadow-sm">
          <div class="flex items-center justify-between gap-4">
            <span class="text-sm text-gray-600">答题进度 {{ answeredCount }}/{{ assessment.questions.length }}</span>
            <el-progress class="w-48" :percentage="answerProgress" :show-text="false" />
          </div>
        </div>

        <el-card
          v-for="(question, index) in assessment.questions"
          :key="question.id"
          class="mb-5 border-0"
          shadow="never"
        >
          <template #header>
            <div class="flex items-start justify-between gap-4">
              <div class="font-semibold text-gray-800">
                <span class="mr-2 text-indigo-600">{{ index + 1 }}.</span>{{ question.title }}
              </div>
              <el-tag size="small">{{ question.points }} 分</el-tag>
            </div>
          </template>
          <p v-if="question.description" class="mb-4 whitespace-pre-wrap text-sm leading-7 text-gray-500">
            {{ question.description }}
          </p>

          <el-radio-group
            v-if="question.question_type === 'single_choice'"
            v-model="answers[question.id]"
            class="flex !flex-col !items-start gap-3"
          >
            <el-radio v-for="option in question.options || []" :key="option.key" :value="option.key">
              {{ option.key }}. {{ option.label }}
            </el-radio>
          </el-radio-group>

          <el-checkbox-group
            v-else-if="question.question_type === 'multiple_choice'"
            v-model="answers[question.id]"
            class="flex !flex-col !items-start gap-3"
          >
            <el-checkbox v-for="option in question.options || []" :key="option.key" :value="option.key">
              {{ option.key }}. {{ option.label }}
            </el-checkbox>
          </el-checkbox-group>

          <el-input
            v-else
            v-model="answers[question.id]"
            type="textarea"
            :rows="question.question_type === 'code' ? 10 : 5"
            maxlength="5000"
            show-word-limit
            :class="{ 'code-answer': question.question_type === 'code' }"
            :placeholder="question.question_type === 'code' ? `请输入${question.code_language || ''}代码或伪代码，并说明思路` : '请结合自己的理解作答'"
          />
        </el-card>

        <div class="mb-10 flex justify-center">
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            {{ submitting ? 'AI 正在评分...' : '提交考核并由 AI 评分' }}
          </el-button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { aiApi } from '@/api/ai'
import { careerApi } from '@/api/career'
import type { AITask } from '@/api/types/ai'
import type {
  CareerAssessmentResult,
  CareerStageAssessment,
} from '@/api/types/career'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const transitioning = ref(false)
const loadError = ref('')
const assessment = ref<CareerStageAssessment | null>(null)
const result = ref<CareerAssessmentResult | null>(null)
const answers = reactive<Record<number, string | string[]>>({})

const assessmentId = computed(() => Number(route.params.id))
const storageKey = computed(() => `career_assessment_draft_${assessmentId.value}`)
const totalPoints = computed(() => assessment.value?.questions.reduce((sum, item) => sum + item.points, 0) || 0)
const answeredCount = computed(() => assessment.value?.questions.filter((question) => hasAnswer(answers[question.id])).length || 0)
const answerProgress = computed(() => assessment.value?.questions.length
  ? Math.round((answeredCount.value / assessment.value.questions.length) * 100)
  : 0)

const assessmentStatusMeta = computed(() => {
  const status = assessment.value?.status
  if (status === 'passed') return { label: '考核通过', type: 'success' as const }
  if (status === 'needs_improvement') return { label: '需要巩固', type: 'warning' as const }
  if (status === 'evaluating' || status === 'submitted') return { label: 'AI 评分中', type: 'primary' as const }
  if (status === 'failed') return { label: '处理失败', type: 'danger' as const }
  return { label: '等待作答', type: 'info' as const }
})

const loadAssessment = async () => {
  if (!Number.isFinite(assessmentId.value) || assessmentId.value <= 0) {
    loadError.value = '考核 ID 无效'
    return
  }
  loading.value = true
  loadError.value = ''
  try {
    const response = await careerApi.getStageAssessment(assessmentId.value)
    assessment.value = response.data
    if (['passed', 'needs_improvement'].includes(response.data.status)) {
      await loadResult()
      return
    }
    restoreDraft(response.data)
  } catch (error: unknown) {
    loadError.value = getErrorMessage(error, '加载阶段考核失败')
  } finally {
    loading.value = false
  }
}

const restoreDraft = (data: CareerStageAssessment) => {
  let saved: Record<number, string | string[]> = {}
  try {
    saved = JSON.parse(localStorage.getItem(storageKey.value) || '{}') as Record<number, string | string[]>
  } catch {
    saved = {}
  }
  data.questions.forEach((question) => {
    answers[question.id] = saved[question.id] ?? (question.question_type === 'multiple_choice' ? [] : '')
  })
}

const handleSubmit = async () => {
  if (!assessment.value || submitting.value) return
  const unansweredIndex = assessment.value.questions.findIndex((question) => !hasAnswer(answers[question.id]))
  if (unansweredIndex >= 0) {
    ElMessage.warning(`请先完成第 ${unansweredIndex + 1} 题`)
    return
  }
  try {
    await ElMessageBox.confirm(
      '提交后不能修改本次答案，AI 将结合评分规则生成逐题点评。',
      '确认提交阶段考核',
      { confirmButtonText: '确认提交', cancelButtonText: '继续检查', type: 'warning' },
    )
  } catch {
    return
  }

  submitting.value = true
  try {
    const response = await careerApi.submitStageAssessment(assessment.value.id, {
      answers: assessment.value.questions.map((question) => ({
        question_id: question.id,
        answer: answers[question.id],
      })),
    })
    await pollTask(response.data.task_id, '阶段考核评分失败')
    localStorage.removeItem(storageKey.value)
    await loadResult()
    if (assessment.value && result.value) assessment.value.status = result.value.status
    ElMessage.success('阶段考核评分完成')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '提交阶段考核失败'))
  } finally {
    submitting.value = false
  }
}

const loadResult = async () => {
  const response = await careerApi.getStageAssessmentResult(assessmentId.value)
  result.value = response.data
}

const handleEnterNextStage = async () => {
  if (!result.value || transitioning.value) return
  transitioning.value = true
  try {
    await careerApi.enterNextStage(result.value.assessment_id)
    ElMessage.success('下一阶段计划已启用')
    await router.push('/career/check-in')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '进入下一阶段失败'))
  } finally {
    transitioning.value = false
  }
}

const handleAcceptRemediation = async () => {
  if (!result.value || transitioning.value) return
  transitioning.value = true
  try {
    await careerApi.acceptAssessmentRemediation(result.value.assessment_id)
    ElMessage.success('补强任务已加入执行计划，完成后可以重新考核')
    await router.push('/career/check-in')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '生成补强计划失败'))
  } finally {
    transitioning.value = false
  }
}

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const pollTask = async (taskId: string, failureMessage: string) => {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const response = await aiApi.getTask(taskId)
    const task: AITask = response.data
    if (task.status === 'success') return task
    if (task.status === 'failed') throw new Error(task.error_message || failureMessage)
    if (task.status === 'cancelled') throw new Error(task.error_message || 'AI 任务已取消')
    await wait(Math.min(Math.max(task.poll_after_seconds || 1, 1), 5) * 1000)
  }
  throw new Error('AI 评分超时，请稍后重新进入页面查看结果')
}

const hasAnswer = (answer: string | string[] | undefined) => Array.isArray(answer)
  ? answer.length > 0
  : Boolean(answer?.trim())

const displayAnswer = (answer: string | string[]) => Array.isArray(answer) ? answer.join('、') : answer

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  const data = (error as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data
  if (typeof data?.message === 'string') return data.message
  if (typeof data?.detail === 'string') return data.detail
  return fallback
}

watch(answers, (value) => {
  if (!assessment.value || result.value) return
  localStorage.setItem(storageKey.value, JSON.stringify(value))
}, { deep: true })

onMounted(() => {
  void loadAssessment()
})
</script>

<style scoped>
.career-assessment-view :deep(.el-card) {
  border-radius: 16px;
}

.result-hero,
.assessment-intro {
  background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
}

.code-answer :deep(textarea) {
  font-family: "Cascadia Code", Consolas, monospace;
  line-height: 1.7;
  tab-size: 2;
}
</style>
