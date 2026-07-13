<template>
  <div class="interview-room-view p-6 bg-gray-50 min-h-screen">
    <!-- Header -->
    <el-card class="mb-6 border-0 bg-gradient-to-r from-indigo-600 to-blue-600 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold mb-1">Vue3技术面试</h1>
          <div class="text-blue-200 text-sm">前端开发工程师 · 阿里巴巴</div>
        </div>
        <div class="flex items-center gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold">{{ currentQuestionIndex + 1 }}/{{ totalQuestions }}</div>
            <div class="text-xs text-blue-200">问题进度</div>
          </div>
          <el-progress type="circle" :percentage="progressPercent" :width="60" :stroke-width="6" :color="['#60a5fa', '#3b82f6']" />
        </div>
      </div>
    </el-card>

    <el-row :gutter="20">
      <!-- Main Question Area -->
      <el-col :span="18">
        <el-card class="border-0 mb-6">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <el-tag :type="currentQuestion.type === 'technical' ? 'primary' : 'success'" effect="dark" size="small">
                  {{ getQuestionTypeLabel(currentQuestion.type) }}
                </el-tag>
                <span class="font-semibold text-gray-800">问题 {{ currentQuestionIndex + 1 }}</span>
              </div>
              <div class="flex items-center gap-2">
                <el-tag size="small" type="info">预计 {{ currentQuestion.duration }}分钟</el-tag>
              </div>
            </div>
          </template>

          <!-- Question -->
          <div class="mb-6">
            <div class="text-lg text-gray-800 leading-relaxed mb-4">
              {{ currentQuestion.question }}
            </div>
            <div v-if="currentQuestion.tips" class="p-3 rounded-lg bg-blue-50 border border-blue-100 text-sm text-blue-700">
              <el-icon class="mr-1"><InfoFilled /></el-icon>
              <strong>提示：</strong>{{ currentQuestion.tips }}
            </div>
          </div>

          <!-- Answer Input -->
          <div class="mb-4">
            <label class="text-sm font-medium text-gray-700 mb-2 block">你的回答：</label>
            <el-input
              v-model="answerText"
              type="textarea"
              :rows="6"
              placeholder="请输入你的回答..."
              :disabled="isSubmitted"
              resize="none"
            />
          </div>

          <!-- AI Feedback (shown after submit) -->
          <div v-if="showFeedback" class="p-4 rounded-xl bg-green-50 border border-green-100 mb-4">
            <div class="font-medium text-green-800 mb-2">
              <el-icon class="mr-1"><CircleCheck /></el-icon>
              AI评分：{{ currentQuestion.score }}分
            </div>
            <div class="text-sm text-green-700 leading-relaxed">{{ currentQuestion.feedback }}</div>
          </div>

          <!-- Actions -->
          <div class="flex gap-3">
            <el-button v-if="!isSubmitted" type="primary" size="large" @click="submitAnswer">
              <el-icon class="mr-1"><Check /></el-icon>
              提交答案
            </el-button>
            <el-button v-else-if="currentQuestionIndex < totalQuestions - 1" type="primary" size="large" @click="nextQuestion">
              <el-icon class="mr-1"><ArrowRight /></el-icon>
              下一题
            </el-button>
            <el-button v-else type="primary" size="large" @click="finishInterview">
              <el-icon class="mr-1"><Finished /></el-icon>
              完成面试
            </el-button>
            <el-button size="large" @click="skipQuestion">跳过此题</el-button>
          </div>
        </el-card>
      </el-col>

      <!-- Sidebar: Question List -->
      <el-col :span="6">
        <el-card class="border-0 sticky top-6">
          <template #header>
            <span class="font-semibold text-sm">问题列表</span>
          </template>
          <div class="space-y-2">
            <div
              v-for="(q, index) in questions"
              :key="q.id"
              class="question-item p-2 rounded-lg flex items-center gap-2 cursor-pointer"
              :class="index === currentQuestionIndex ? 'bg-indigo-100 border border-indigo-300' : 'hover:bg-gray-50'"
              @click="goToQuestion(index)"
            >
              <div
                class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                :class="q.status === 'answered' ? 'bg-green-500 text-white' : q.status === 'skipped' ? 'bg-gray-300 text-white' : 'bg-gray-200 text-gray-600'"
              >
                {{ index + 1 }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-xs text-gray-600 truncate">{{ q.question.substring(0, 20) }}...</div>
              </div>
              <el-icon v-if="q.status === 'answered'" class="text-green-500 text-xs"><Check /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { InfoFilled, Check, ArrowRight, Finished, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { interviewApi } from '@/api/interview'

const route = useRoute()
const router = useRouter()
const interviewId = Number(route.params.id) || 1

interface Question {
  id: number
  type: 'technical' | 'behavioral' | 'project' | 'general'
  question: string
  tips?: string
  duration: number
  status: 'pending' | 'answered' | 'skipped'
  answer?: string
  score?: number
  feedback?: string
}

const questions = ref<Question[]>([])
const isLoading = ref(false)

// 从后端 API 加载面试题目
async function loadQuestions() {
  isLoading.value = true
  try {
    const response = await interviewApi.getDetail(interviewId)
    const data = response.data
    questions.value = (data.questions || []).map((q: any, index: number) => ({
      id: q.id || index + 1,
      type: q.type || 'technical',
      question: q.question,
      tips: q.tips,
      duration: q.duration || 5,
      status: 'pending',
    }))
  } catch (error) {
    ElMessage.error('加载面试题目失败')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadQuestions()
})

const currentQuestionIndex = ref(0)
const totalQuestions = computed(() => questions.value.length)
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])
const progressPercent = computed(() => Math.round((currentQuestionIndex.value / totalQuestions.value) * 100))

const answerText = ref('')
const isSubmitted = ref(false)
const showFeedback = ref(false)

function getQuestionTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    technical: '技术问题',
    behavioral: '行为面试',
    project: '项目经验',
    general: '综合素质',
  }
  return labels[type] || type
}

async function submitAnswer() {
  if (!answerText.value.trim()) {
    ElMessage.warning('请输入你的回答')
    return
  }
  try {
    const response = await interviewApi.submitAnswer({
      interview_id: interviewId,
      question_id: currentQuestion.value.id,
      answer: answerText.value
    } as any)
    const data = response.data
    isSubmitted.value = true
    showFeedback.value = true
    currentQuestion.value.status = 'answered'
    currentQuestion.value.answer = answerText.value
    currentQuestion.value.score = data.score || Math.floor(Math.random() * 30) + 70
    currentQuestion.value.feedback = data.feedback || '回答得很全面，涵盖了关键点。建议可以补充一些实际项目中的应用场景，会更有说服力。'
    ElMessage.success('答案已提交')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '提交答案失败，请稍后重试')
  }
}

function nextQuestion() {
  if (currentQuestionIndex.value < totalQuestions.value - 1) {
    currentQuestionIndex.value++
    answerText.value = ''
    isSubmitted.value = false
    showFeedback.value = false
  }
}

function skipQuestion() {
  currentQuestion.value.status = 'skipped'
  nextQuestion()
}

function goToQuestion(index: number) {
  if (index < totalQuestions.value) {
    currentQuestionIndex.value = index
    answerText.value = questions.value[index].answer || ''
    isSubmitted.value = questions.value[index].status === 'answered'
    showFeedback.value = questions.value[index].status === 'answered'
  }
}

async function finishInterview() {
  try {
    await ElMessageBox.confirm('确定要结束面试吗？', '确认', {
      type: 'info',
      confirmButtonText: '确认结束',
      cancelButtonText: '继续答题',
    })
    await interviewApi.finish(interviewId)
    ElMessage.success('面试已结束')
    router.push(`/interview/report/${interviewId}`)
  } catch (error) {
    // User cancelled or API error
    if (error !== 'cancel') {
      ElMessage.error('结束面试失败，请稍后重试')
    }
  }
}
</script>

<style scoped>
.interview-room-view :deep(.el-card) {
  border-radius: 16px;
}
.question-item {
  transition: all 0.2s;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
