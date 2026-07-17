<template>
  <div class="room-page p-6 min-h-screen" v-loading="loading">
    <el-card v-if="interview" class="hero mb-6" shadow="never">
      <div class="flex items-center justify-between">
        <div><h1 class="text-xl font-bold">{{ interview.title }}</h1>
          <p>{{ interview.target_role }} · {{ interview.company || '模拟面试' }}</p>
        </div>
        <div class="text-right"><div class="text-2xl font-bold">{{ answeredCount }}/{{ interview.question_count }}</div>
          <div class="text-sm">答题进度</div>
        </div>
      </div>
      <el-progress :percentage="progress" :show-text="false" class="mt-4" />
    </el-card>

    <el-row v-if="interview" :gutter="20">
      <el-col :span="18">
        <el-card v-if="currentQuestion" shadow="never">
          <template #header>
            <div class="flex items-center justify-between">
              <div><el-tag>{{ typeLabel(currentQuestion.question_type) }}</el-tag>
                <strong class="ml-3">问题 {{ currentQuestion.order_no }}</strong>
              </div>
              <el-tag type="info">{{ difficultyLabel(currentQuestion.difficulty) }}</el-tag>
            </div>
          </template>
          <div class="question-text">{{ currentQuestion.question }}</div>
          <el-alert title="请按真实面试方式作答。评分会在全部结束后统一展示，避免影响后续发挥。"
            type="info" :closable="false" class="mb-5" />
          <el-input v-model="answerText" type="textarea" :rows="9" maxlength="8000"
            show-word-limit resize="vertical" placeholder="请输入你的回答，可使用“背景—行动—结果—复盘”组织内容" />
          <div class="flex items-center justify-between mt-5">
            <span class="text-sm text-gray-500">本题用时 {{ elapsedText }}</span>
            <div>
              <el-button :disabled="answeredCount === 0" @click="confirmFinish">提前结束并生成报告</el-button>
              <el-button type="primary" :loading="submitting" @click="submitAnswer">
                {{ isLastPending ? '提交最后一题' : '提交并进入下一题' }}
              </el-button>
            </div>
          </div>
        </el-card>

        <el-card v-else shadow="never" class="text-center py-12">
          <el-result icon="success" title="本场题目已全部作答" sub-title="现在生成综合评分、薄弱项建议和专属题库">
            <template #extra><el-button type="primary" :loading="finishing" @click="finish">
              生成面试报告
            </el-button></template>
          </el-result>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="never">
          <template #header><strong>问题进度</strong></template>
          <div v-for="item in interview.questions || []" :key="item.id" class="question-item"
            :class="{ active: currentQuestion?.id === item.id, answered: item.status === 'answered' }">
            <span>{{ item.order_no }}</span>
            <div><b>{{ typeLabel(item.question_type) }}</b>
              <p>{{ item.status === 'answered' ? '已回答' : '待回答' }}</p>
            </div>
          </div>
          <el-divider />
          <div class="privacy-tip">AI 仅根据本场回答、岗位和所选简历进行评估，不执行你输入的代码，也不会把知识库内容当作你的经历。</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { interviewApi } from '@/api/interview'
import type { InterviewItem, InterviewQuestion } from '@/api/types/interview'

const route = useRoute()
const router = useRouter()
const interviewId = Number(route.params.id)
const interview = ref<InterviewItem | null>(null)
const currentQuestion = ref<InterviewQuestion | null>(null)
const answerText = ref('')
const loading = ref(false)
const submitting = ref(false)
const finishing = ref(false)
const elapsedSeconds = ref(0)
let timer: ReturnType<typeof setInterval> | undefined

const answeredCount = computed(() => interview.value?.questions?.filter(q => q.status === 'answered').length || 0)
const progress = computed(() => interview.value ? Math.round(answeredCount.value / interview.value.question_count * 100) : 0)
const isLastPending = computed(() => {
  const pending = interview.value?.questions?.filter(q => q.status === 'pending') || []
  return pending.length === 1
})
const elapsedText = computed(() => `${Math.floor(elapsedSeconds.value / 60)}分${elapsedSeconds.value % 60}秒`)

async function load() {
  if (!interviewId) return router.replace('/interview')
  loading.value = true
  try {
    await interviewApi.startInterview(interviewId)
    const response = await interviewApi.getDetail(interviewId)
    interview.value = response.data
    if (response.data.status === 'completed') return router.replace(`/interview/report/${interviewId}`)
    currentQuestion.value = response.data.questions?.find(q => q.status === 'pending') || null
    resetTimer()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载面试失败')
  } finally { loading.value = false }
}

async function submitAnswer() {
  if (!currentQuestion.value || !answerText.value.trim()) return ElMessage.warning('请先输入回答')
  submitting.value = true
  try {
    const response = await interviewApi.submitAnswer(interviewId, {
      question_id: currentQuestion.value.id,
      answer: answerText.value.trim(),
      duration_seconds: elapsedSeconds.value,
    })
    const answered = interview.value?.questions?.find(q => q.id === currentQuestion.value?.id)
    if (answered) answered.status = 'answered'
    currentQuestion.value = response.data.next_question || null
    answerText.value = ''
    resetTimer()
    ElMessage.success(currentQuestion.value ? '回答已记录，进入下一题' : '全部题目已回答')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交回答失败')
  } finally { submitting.value = false }
}

async function confirmFinish() {
  try {
    await ElMessageBox.confirm('未回答的题目不会计分，确认提前结束？', '结束面试', { type: 'warning' })
    await finish()
  } catch (error) { /* cancelled */ }
}

async function finish() {
  finishing.value = true
  try {
    await interviewApi.finishInterview(interviewId)
    ElMessage.success('面试报告已生成')
    await router.replace(`/interview/report/${interviewId}`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成报告失败')
  } finally { finishing.value = false }
}

function resetTimer() {
  elapsedSeconds.value = 0
  if (timer) clearInterval(timer)
  timer = setInterval(() => elapsedSeconds.value++, 1000)
}
const typeLabel = (v: string) => ({ technical: '专业能力', project: '项目经历', behavioral: '行为沟通', scenario: '情境处理' }[v] || v)
const difficultyLabel = (v: string) => ({ junior: '初级', middle: '中级', senior: '高级' }[v] || v)
onMounted(load)
onBeforeUnmount(() => timer && clearInterval(timer))
</script>

<style scoped>
.room-page { background: var(--app-bg, #f6f8fb); color: var(--app-text, #1f2937); }
.room-page :deep(.el-card) { border-radius: 14px; }
.hero { background: linear-gradient(120deg, #315efb, #6d3bf5); color: white; }
.hero p { color: #dbeafe; margin-top: 6px; }
.question-text { font-size: 18px; line-height: 1.8; margin-bottom: 22px; white-space: pre-wrap; }
.question-item { display:flex; gap:10px; padding:10px; margin-bottom:8px; border-radius:9px; background:#f5f7fa; }
.question-item > span { width:28px; height:28px; border-radius:50%; display:grid; place-items:center; background:#e5e7eb; }
.question-item p { font-size:12px; color:#909399; margin-top:2px; }
.question-item.active { background:#eef2ff; outline:1px solid #818cf8; }
.question-item.answered > span { background:#10b981; color:white; }
.privacy-tip { font-size:12px; color:#909399; line-height:1.7; }
</style>
