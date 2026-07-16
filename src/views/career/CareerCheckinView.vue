<template>
  <div class="career-checkin-view min-h-screen bg-gray-50 p-6">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">计划执行打卡</h1>
        <p class="mt-1 text-sm text-gray-500">把已确认的职业规划拆成每天可完成的小任务，持续积累进步</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadOverview">刷新进度</el-button>
    </div>

    <div v-if="loading && !overview" class="rounded-2xl bg-white py-24 text-center shadow-sm">
      <el-icon class="is-loading text-4xl text-indigo-500"><Loading /></el-icon>
      <div class="mt-4 text-sm text-gray-500">正在加载执行计划...</div>
    </div>

    <el-card v-else-if="!overview" class="border-0 py-16 text-center" shadow="never">
      <el-empty description="还没有正在执行的职业规划">
        <p class="mb-5 text-sm text-gray-500">请先生成职业规划，并点击“确认采用并开始执行”。</p>
        <el-button type="primary" @click="router.push('/career')">去制定职业规划</el-button>
      </el-empty>
    </el-card>

    <template v-else>
      <el-card class="mb-6 overflow-hidden border-0 progress-hero" shadow="never">
        <div class="grid grid-cols-1 gap-6 lg:grid-cols-[1.5fr_1fr] lg:items-center">
          <div>
            <div class="mb-2 flex flex-wrap items-center gap-2">
              <el-tag type="success" effect="dark">执行中</el-tag>
              <span class="text-sm text-indigo-100">第 {{ overview.current_week }} 周</span>
              <el-tag v-if="overview.ahead_task_count" type="warning" effect="dark">
                已提前 {{ overview.ahead_task_count }} 项
              </el-tag>
            </div>
            <h2 class="text-xl font-bold text-white">{{ overview.current_stage || '按计划稳步前进' }}</h2>
            <p class="mt-2 text-sm text-indigo-100">今天是 {{ todayText }}，完成一次任务就是一次有效积累。</p>
          </div>
          <div>
            <div class="mb-2 flex items-center justify-between text-sm text-indigo-100">
              <span>总体完成进度</span>
              <span>{{ overview.completed_tasks }} / {{ overview.total_tasks }} 项</span>
            </div>
            <el-progress
              :percentage="normalizedProgress"
              :stroke-width="12"
              color="#fbbf24"
              :text-inside="true"
            />
          </div>
        </div>
      </el-card>

      <div class="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div v-for="stat in stats" :key="stat.label" class="rounded-2xl bg-white p-5 shadow-sm">
          <div class="text-xs text-gray-400">{{ stat.label }}</div>
          <div class="mt-2 text-2xl font-bold" :class="stat.color">{{ stat.value }}</div>
          <div class="mt-1 text-xs text-gray-400">{{ stat.tip }}</div>
        </div>
      </div>

      <el-card
        v-if="todayCompleted && !advancePromptDismissed"
        class="mb-6 border-0 completion-card"
        shadow="never"
      >
        <div class="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
          <div>
            <div class="text-lg font-bold text-gray-800">
              {{ assessmentReady ? '🎓 当前阶段任务已经完成' : '🎉 今天的计划已经完成' }}
            </div>
            <p class="mt-2 text-sm leading-6 text-gray-600">
              <template v-if="assessmentReady">
                AI 将结合本阶段打卡记录、执行备注和学习答疑生成针对性考核，检验你是否真正掌握。
              </template>
              <template v-else-if="canAdvance">
                今天状态不错，可以提前解锁下一项任务；也可以选择今天先到这里，保持稳定节奏。
              </template>
              <template v-else>
                今天没有更多可提前执行的任务，可以安心休息并保持明天的学习节奏。
              </template>
            </p>
            <div v-if="overview.stage_progress !== undefined" class="mt-3 max-w-lg">
              <div class="mb-1 flex justify-between text-xs text-gray-500">
                <span>当前阶段进度</span><span>{{ Math.round(overview.stage_progress) }}%</span>
              </div>
              <el-progress :percentage="Math.round(overview.stage_progress)" :show-text="false" color="#8b5cf6" />
            </div>
          </div>
          <div class="flex shrink-0 flex-wrap gap-3">
            <el-button @click="advancePromptDismissed = true">今天先到这里</el-button>
            <el-button
              v-if="assessmentReady"
              type="warning"
              :loading="startingAssessment"
              @click="handleStartAssessment"
            >开始阶段考核</el-button>
            <el-button
              v-else-if="canAdvance"
              type="primary"
              :loading="advancing"
              @click="handleAdvanceNextTask"
            >继续下一项任务</el-button>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20">
        <el-col :xs="24" :lg="16" class="mb-6">
          <el-card class="h-full border-0" shadow="never">
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <div>
                  <div class="font-semibold text-gray-800">今日打卡</div>
                  <div class="mt-1 text-xs text-gray-400">优先完成今天安排的任务，也可以补充执行备注</div>
                </div>
                <el-tag type="primary">{{ todayCompletedCount }}/{{ overview.today_tasks.length }}</el-tag>
              </div>
            </template>

            <el-empty v-if="!overview.today_tasks.length" description="今天暂时没有安排任务" :image-size="90" />
            <div v-else class="space-y-3">
              <div
                v-for="task in overview.today_tasks"
                :key="task.id"
                class="task-card rounded-xl border p-4"
                :class="task.status === 'completed' ? 'is-completed' : task.status === 'skipped' ? 'is-skipped' : ''"
              >
                <div class="flex flex-wrap items-start justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <el-tag size="small" :type="taskTypeMeta(task.task_type).type">
                        {{ taskTypeMeta(task.task_type).label }}
                      </el-tag>
                      <span class="font-medium text-gray-800" :class="{ 'line-through text-gray-400': task.status === 'completed' }">
                        {{ task.title }}
                      </span>
                      <span v-if="task.is_required" class="text-xs text-red-400">必做</span>
                      <el-tag v-if="task.is_advanced" size="small" type="warning">提前执行</el-tag>
                    </div>
                    <p v-if="task.description" class="mt-2 text-sm leading-6 text-gray-500">{{ task.description }}</p>
                  </div>
                  <el-tag v-if="task.status === 'completed'" type="success">已完成</el-tag>
                  <el-tag v-else-if="task.status === 'skipped'" type="warning">已暂缓</el-tag>
                  <el-tag v-else type="info">待完成</el-tag>
                </div>

                <div class="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
                  <el-input
                    v-model="taskNotes[task.id]"
                    maxlength="300"
                    clearable
                    :disabled="task.status === 'completed'"
                    placeholder="记录今天学了什么、遇到什么问题（可选）"
                  />
                  <div class="flex shrink-0 gap-2">
                    <el-button
                      v-if="task.status !== 'completed'"
                      type="success"
                      :loading="updatingTaskIds.includes(task.id)"
                      @click="updateTask(task, 'completed')"
                    >
                      <el-icon class="mr-1"><Check /></el-icon>完成打卡
                    </el-button>
                    <el-button
                      v-if="task.status === 'pending'"
                      :disabled="updatingTaskIds.includes(task.id)"
                      @click="updateTask(task, 'skipped')"
                    >暂缓</el-button>
                    <el-button
                      v-if="task.status === 'completed'"
                      :loading="updatingTaskIds.includes(task.id)"
                      @click="updateTask(task, 'pending')"
                    >撤销</el-button>
                  </div>
                </div>

                <div class="mt-3 border-t border-gray-100 pt-3">
                  <el-button text type="primary" @click="toggleQuestionPanel(task.id)">
                    <el-icon class="mr-1"><ChatDotSquare /></el-icon>
                    {{ expandedQuestionTaskIds.includes(task.id) ? '收起 AI 学习答疑' : '学习遇到问题？问 AI' }}
                  </el-button>

                  <div v-if="expandedQuestionTaskIds.includes(task.id)" class="mt-3 rounded-xl bg-indigo-50 p-4">
                    <div class="mb-3 text-xs leading-5 text-indigo-600">
                      AI 会结合当前任务、职业规划阶段和你的问题进行回答。请勿上传密码、密钥或其他隐私信息。
                    </div>
                    <el-input
                      v-model="questionInputs[task.id]"
                      type="textarea"
                      :rows="3"
                      maxlength="1000"
                      show-word-limit
                      placeholder="例如：FastAPI 的 Depends 和直接调用函数有什么区别？我应该怎样在这个练习里使用依赖注入？"
                    />
                    <div class="mt-3 flex justify-end">
                      <el-button
                        type="primary"
                        :loading="askingTaskIds.includes(task.id)"
                        @click="submitQuestion(task)"
                      >
                        {{ askingTaskIds.includes(task.id) ? 'AI 正在思考...' : '提交问题给 AI' }}
                      </el-button>
                    </div>

                    <div v-if="loadingQuestionTaskIds.includes(task.id)" class="py-5 text-center text-sm text-gray-400">
                      <el-icon class="is-loading mr-1"><Loading /></el-icon>正在加载历史问答
                    </div>
                    <div v-else-if="taskQuestions[task.id]?.length" class="mt-4 space-y-4">
                      <div v-for="item in taskQuestions[task.id]" :key="item.id" class="rounded-xl bg-white p-4 shadow-sm">
                        <div class="flex gap-2 text-sm leading-6 text-gray-700">
                          <span class="shrink-0 font-semibold text-indigo-600">我的问题：</span>
                          <span>{{ item.question }}</span>
                        </div>
                        <div class="mt-3 border-t border-gray-100 pt-3 text-sm leading-7 text-gray-600">
                          <div v-if="item.status === 'answered' && item.answer" class="whitespace-pre-wrap">
                            <span class="font-semibold text-green-600">AI 回答：</span>{{ item.answer }}
                          </div>
                          <div v-else-if="item.status === 'failed'" class="text-red-500">
                            回答失败：{{ item.error_message || '请稍后重新提交问题' }}
                          </div>
                          <div v-else class="text-indigo-500">
                            <el-icon class="is-loading mr-1"><Loading /></el-icon>AI 正在结合学习任务生成回答...
                          </div>
                        </div>
                        <div class="mt-2 text-right text-xs text-gray-400">{{ formatDateTime(item.created_at) }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8" class="mb-6">
          <el-card class="h-full border-0" shadow="never">
            <template #header><span class="font-semibold text-gray-800">最近打卡</span></template>
            <el-empty v-if="!overview.recent_checkins.length" description="完成任务后会留下打卡记录" :image-size="80" />
            <el-timeline v-else>
              <el-timeline-item
                v-for="record in overview.recent_checkins"
                :key="record.id"
                :timestamp="formatDateTime(record.checked_in_at)"
                :type="record.status === 'completed' ? 'success' : 'warning'"
              >
                <div class="text-sm font-medium text-gray-700">{{ record.task_title }}</div>
                <div v-if="record.note" class="mt-1 text-xs leading-5 text-gray-500">{{ record.note }}</div>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header>
          <div>
            <div class="font-semibold text-gray-800">本周任务清单</div>
            <div class="mt-1 text-xs text-gray-400">用于提前了解本周节奏，实际打卡以每日任务为主</div>
          </div>
        </template>
        <el-table :data="overview.week_tasks" stripe empty-text="本周暂无任务">
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusMeta(row.status).type" size="small">{{ statusMeta(row.status).label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="任务" min-width="240" />
          <el-table-column prop="stage" label="阶段" min-width="160" />
          <el-table-column label="类型" width="110">
            <template #default="{ row }">{{ taskTypeMeta(row.task_type).label }}</template>
          </el-table-column>
          <el-table-column label="计划日期" width="130">
            <template #default="{ row }">{{ row.planned_date || '本周内' }}</template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotSquare, Check, Loading, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { careerApi } from '@/api/career'
import { aiApi } from '@/api/ai'
import type { AITask } from '@/api/types/ai'
import type {
  CareerCheckinTask,
  CareerCheckinTaskStatus,
  CareerExecutionOverview,
  CareerTaskQuestion,
} from '@/api/types/career'

const router = useRouter()
const loading = ref(false)
const overview = ref<CareerExecutionOverview | null>(null)
const updatingTaskIds = ref<number[]>([])
const taskNotes = reactive<Record<number, string>>({})
const questionInputs = reactive<Record<number, string>>({})
const taskQuestions = reactive<Record<number, CareerTaskQuestion[]>>({})
const expandedQuestionTaskIds = ref<number[]>([])
const loadedQuestionTaskIds = ref<number[]>([])
const loadingQuestionTaskIds = ref<number[]>([])
const askingTaskIds = ref<number[]>([])
const advancing = ref(false)
const startingAssessment = ref(false)
const advancePromptDismissed = ref(false)
const completionPromptShown = ref(false)

const normalizedProgress = computed(() => {
  const value = overview.value?.progress_percent || 0
  return Math.min(100, Math.max(0, Math.round(value)))
})

const todayCompletedCount = computed(() =>
  overview.value?.today_tasks.filter((task) => task.status === 'completed').length || 0,
)

const todayCompleted = computed(() => {
  if (!overview.value) return false
  if (overview.value.today_completed !== undefined) return overview.value.today_completed
  return Boolean(
    overview.value.today_tasks.length &&
    overview.value.today_tasks.every((task) => task.status === 'completed'),
  )
})

const canAdvance = computed(() => Boolean(
  overview.value?.can_advance ?? overview.value?.next_task_available,
))

const assessmentReady = computed(() => Boolean(overview.value?.assessment_ready))

const stats = computed(() => [
  { label: '连续打卡', value: `${overview.value?.current_streak || 0} 天`, tip: '保持节奏比突击更重要', color: 'text-orange-500' },
  { label: '最长连续', value: `${overview.value?.longest_streak || 0} 天`, tip: '刷新你的个人纪录', color: 'text-purple-500' },
  { label: '累计完成', value: `${overview.value?.completed_tasks || 0} 项`, tip: '每项任务都有记录', color: 'text-green-600' },
  { label: '当前周次', value: `第 ${overview.value?.current_week || 1} 周`, tip: overview.value?.current_stage || '执行阶段', color: 'text-indigo-600' },
])

const todayText = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric', month: 'long', day: 'numeric', weekday: 'long',
}).format(new Date())

const loadOverview = async () => {
  loading.value = true
  try {
    const response = await careerApi.getCurrentExecution()
    overview.value = response.data
    response.data.today_tasks.forEach((task) => {
      taskNotes[task.id] = task.checkin_note || ''
    })
  } catch {
    overview.value = null
  } finally {
    loading.value = false
  }
}

const updateTask = async (task: CareerCheckinTask, status: 'completed' | 'pending' | 'skipped') => {
  if (updatingTaskIds.value.includes(task.id)) return
  updatingTaskIds.value.push(task.id)
  try {
    const response = await careerApi.checkInTask(task.id, {
      status,
      note: taskNotes[task.id]?.trim() || undefined,
    })
    const completedBeforeUpdate = todayCompleted.value
    overview.value = response.data
    response.data.today_tasks.forEach((item) => {
      taskNotes[item.id] = item.checkin_note || taskNotes[item.id] || ''
    })
    ElMessage.success(status === 'completed' ? '打卡成功，继续保持！' : status === 'skipped' ? '任务已暂缓' : '已撤销本次打卡')
    if (status === 'completed' && !completedBeforeUpdate && todayCompleted.value) {
      advancePromptDismissed.value = false
      void promptNextAction()
    }
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '更新打卡状态失败'))
  } finally {
    updatingTaskIds.value = updatingTaskIds.value.filter((id) => id !== task.id)
  }
}

const promptNextAction = async () => {
  if (completionPromptShown.value || (!assessmentReady.value && !canAdvance.value)) return
  completionPromptShown.value = true
  try {
    if (assessmentReady.value) {
      await ElMessageBox.confirm(
        '当前阶段任务已全部完成，是否现在开始阶段考核？',
        '阶段任务完成',
        { confirmButtonText: '开始阶段考核', cancelButtonText: '稍后考核', type: 'success' },
      )
      await handleStartAssessment()
    } else {
      await ElMessageBox.confirm(
        '今天的任务已经全部完成，是否提前继续下一项任务？',
        '今日计划完成',
        { confirmButtonText: '继续下一项', cancelButtonText: '今天先到这里', type: 'success' },
      )
      await handleAdvanceNextTask()
    }
  } catch (error: unknown) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getErrorMessage(error, '处理下一步操作失败'))
    }
  } finally {
    completionPromptShown.value = false
  }
}

const handleAdvanceNextTask = async () => {
  if (!overview.value || advancing.value) return
  advancing.value = true
  try {
    const response = await careerApi.advanceNextTask(overview.value.id)
    overview.value = response.data.overview
    const task = response.data.advanced_task
    taskNotes[task.id] = task.checkin_note || ''
    advancePromptDismissed.value = false
    ElMessage.success(`已提前解锁：${task.title}`)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '提前解锁下一任务失败'))
  } finally {
    advancing.value = false
  }
}

const handleStartAssessment = async () => {
  if (!overview.value || startingAssessment.value) return
  if (overview.value.active_assessment_id) {
    await router.push(`/career/check-in/assessment/${overview.value.active_assessment_id}`)
    return
  }

  startingAssessment.value = true
  try {
    const response = await careerApi.createStageAssessment(overview.value.id)
    const finishedTask = await pollGenericTask(response.data.task_id, '阶段考核题目生成失败')
    const assessmentId = finishedTask.result_id || response.data.assessment_id
    if (!assessmentId) throw new Error('考核生成完成但未返回考核 ID')
    await router.push(`/career/check-in/assessment/${assessmentId}`)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '生成阶段考核失败，请稍后重试'))
  } finally {
    startingAssessment.value = false
  }
}

const toggleQuestionPanel = (taskId: number) => {
  if (expandedQuestionTaskIds.value.includes(taskId)) {
    expandedQuestionTaskIds.value = expandedQuestionTaskIds.value.filter((id) => id !== taskId)
    return
  }
  expandedQuestionTaskIds.value.push(taskId)
  if (!loadedQuestionTaskIds.value.includes(taskId)) void loadTaskQuestions(taskId)
}

const loadTaskQuestions = async (taskId: number) => {
  if (loadingQuestionTaskIds.value.includes(taskId)) return
  loadingQuestionTaskIds.value.push(taskId)
  try {
    const response = await careerApi.getTaskQuestions(taskId)
    taskQuestions[taskId] = response.data
    if (!loadedQuestionTaskIds.value.includes(taskId)) loadedQuestionTaskIds.value.push(taskId)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载学习问答失败'))
  } finally {
    loadingQuestionTaskIds.value = loadingQuestionTaskIds.value.filter((id) => id !== taskId)
  }
}

const submitQuestion = async (task: CareerCheckinTask) => {
  if (askingTaskIds.value.includes(task.id)) return
  const question = questionInputs[task.id]?.trim() || ''
  if (question.length < 5) {
    ElMessage.warning('请至少填写 5 个字，具体描述学习中遇到的问题')
    return
  }

  askingTaskIds.value.push(task.id)
  try {
    const startResponse = await careerApi.askTaskQuestion(task.id, { question })
    const finishedTask = await pollQuestionTask(startResponse.data.task_id)
    const questionId = finishedTask.result_id || startResponse.data.question_id
    if (!questionId) throw new Error('AI 回答完成但未返回问答记录 ID')

    const questionResponse = await careerApi.getTaskQuestion(questionId)
    const current = taskQuestions[task.id] || []
    taskQuestions[task.id] = [
      questionResponse.data,
      ...current.filter((item) => item.id !== questionResponse.data.id),
    ]
    questionInputs[task.id] = ''
    if (!loadedQuestionTaskIds.value.includes(task.id)) loadedQuestionTaskIds.value.push(task.id)
    ElMessage.success('AI 已回答你的学习问题')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, 'AI 学习答疑失败，请稍后重试'))
  } finally {
    askingTaskIds.value = askingTaskIds.value.filter((id) => id !== task.id)
  }
}

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const pollQuestionTask = async (taskId: string) => {
  return pollGenericTask(taskId, 'AI 学习答疑失败')
}

const pollGenericTask = async (taskId: string, failureMessage: string) => {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const response = await aiApi.getTask(taskId)
    const task: AITask = response.data
    if (task.status === 'success') return task
    if (task.status === 'failed') throw new Error(task.error_message || failureMessage)
    if (task.status === 'cancelled') throw new Error(task.error_message || 'AI 任务已取消')
    const delay = Math.min(Math.max(task.poll_after_seconds || 1, 1), 5) * 1000
    await wait(delay)
  }
  throw new Error('AI 任务处理超时，请稍后重试')
}

const taskTypeMeta = (type: CareerCheckinTask['task_type']) => ({
  learning: { label: '学习', type: 'primary' as const },
  practice: { label: '实践', type: 'success' as const },
  deliverable: { label: '产出', type: 'warning' as const },
  job_search: { label: '求职', type: 'danger' as const },
  review: { label: '复盘', type: 'info' as const },
})[type]

const statusMeta = (status: CareerCheckinTaskStatus) => ({
  pending: { label: '待完成', type: 'info' as const },
  completed: { label: '已完成', type: 'success' as const },
  skipped: { label: '已暂缓', type: 'warning' as const },
})[status]

const formatDateTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).format(date)
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  const message = (error as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data
  if (typeof message?.message === 'string') return message.message
  if (typeof message?.detail === 'string') return message.detail
  return fallback
}

onMounted(() => {
  void loadOverview()
})
</script>

<style scoped>
.career-checkin-view :deep(.el-card) {
  border-radius: 16px;
}

.progress-hero {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
}

.task-card {
  border-color: #e5e7eb;
  background: #fff;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.task-card:hover {
  border-color: #a5b4fc;
}

.task-card.is-completed {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.task-card.is-skipped {
  border-color: #fde68a;
  background: #fffbeb;
}

.completion-card {
  border: 1px solid #ddd6fe !important;
  background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);
}
</style>
