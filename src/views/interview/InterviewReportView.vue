<template>
  <div class="interview-report-view p-6 bg-gray-50 min-h-screen">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">面试报告</h1>
        <p class="text-gray-500 text-sm mt-1">Vue3技术面试 · 阿里巴巴</p>
      </div>
      <div class="flex gap-2">
        <el-button @click="$router.back()">返回大厅</el-button>
        <el-button type="primary" @click="$router.push('/interview')">重新面试</el-button>
      </div>
    </div>

    <!-- Overall Score -->
    <el-card class="mb-6 border-0 bg-gradient-to-r from-indigo-50 to-blue-50">
      <div class="flex items-center justify-around py-8">
        <div class="text-center">
          <ScoreRing :score="report.overallScore" :size="120" :stroke-width="8" />
          <div class="text-lg font-bold text-gray-800 mt-2">综合评分</div>
          <div class="text-sm text-gray-500">{{ getScoreLevel(report.overallScore) }}</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-indigo-600">{{ report.totalQuestions }}</div>
          <div class="text-sm text-gray-500 mt-1">问题总数</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-green-600">{{ report.avgScore }}</div>
          <div class="text-sm text-gray-500 mt-1">平均得分</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-blue-600">{{ report.duration }}</div>
          <div class="text-sm text-gray-500 mt-1">用时（分钟）</div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="20" class="mb-6">
      <!-- Dimension Scores -->
      <el-col :span="12">
        <el-card class="border-0">
          <template #header><span class="font-semibold">维度评分</span></template>
          <div class="space-y-5">
            <div v-for="(score, key) in report.dimensionScores" :key="key">
              <div class="flex items-center justify-between text-sm mb-1">
                <span class="text-gray-700 font-medium">{{ getDimensionLabel(key as keyof typeof report.dimensionScores) }}</span>
                <span class="font-bold" :class="getScoreColor(score)">{{ score }}分</span>
              </div>
              <el-progress
                :percentage="score"
                :color="score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'"
                :stroke-width="8"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Summary -->
      <el-col :span="12">
        <el-card class="border-0">
          <template #header><span class="font-semibold">面试总结</span></template>
          <p class="text-sm text-gray-600 leading-relaxed">{{ report.summary }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mb-6">
      <!-- Strengths -->
      <el-col :span="12">
        <el-card class="border-0">
          <template #header>
            <div class="flex items-center gap-2">
              <span class="text-green-500"><el-icon><CircleCheck /></el-icon></span>
              <span class="font-semibold">优势</span>
            </div>
          </template>
          <ul class="space-y-2">
            <li v-for="(item, index) in report.strengths" :key="index" class="flex items-start gap-2">
              <el-icon class="text-green-500 mt-0.5"><Select /></el-icon>
              <span class="text-sm text-gray-600">{{ item }}</span>
            </li>
          </ul>
        </el-card>
      </el-col>

      <!-- Weaknesses -->
      <el-col :span="12">
        <el-card class="border-0">
          <template #header>
            <div class="flex items-center gap-2">
              <span class="text-orange-500"><el-icon><WarningFilled /></el-icon></span>
              <span class="font-semibold">待提升</span>
            </div>
          </template>
          <ul class="space-y-2">
            <li v-for="(item, index) in report.weaknesses" :key="index" class="flex items-start gap-2">
              <el-icon class="text-orange-500 mt-0.5"><Warning /></el-icon>
              <span class="text-sm text-gray-600">{{ item }}</span>
            </li>
          </ul>
        </el-card>
      </el-col>
    </el-row>

    <!-- Question Review -->
    <el-card class="border-0 mb-6">
      <template #header><span class="font-semibold">题目回顾</span></template>
      <div class="space-y-4">
        <el-collapse>
          <el-collapse-item v-for="(item, index) in report.questionReview" :key="item.id" :title="`Q${index + 1}：${item.question.substring(0, 50)}...`">
            <div class="text-sm text-gray-700 leading-relaxed mb-3">
              <strong>问题：</strong>{{ item.question }}
            </div>
            <div class="mb-3 p-3 rounded-lg bg-blue-50 border border-blue-100">
              <div class="text-xs text-blue-500 font-medium mb-1">你的回答：</div>
              <div class="text-sm text-gray-700 leading-relaxed">{{ item.answer }}</div>
            </div>
            <div v-if="item.feedback" class="p-3 rounded-lg bg-green-50 border border-green-100">
              <div class="flex items-center justify-between mb-1">
                <div class="text-xs text-green-500 font-medium">AI反馈：</div>
                <el-tag :type="item.score >= 80 ? 'success' : item.score >= 60 ? 'warning' : 'danger'" size="small">
                  {{ item.score }}分
                </el-tag>
              </div>
              <div class="text-sm text-gray-700 leading-relaxed">{{ item.feedback }}</div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>

    <!-- Suggestions -->
    <el-card class="border-0">
      <template #header>
        <div class="flex items-center gap-2">
          <span class="text-xl">&#x1F4A1;</span>
          <span class="font-semibold">改进建议</span>
        </div>
      </template>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="(suggestion, index) in report.suggestions" :key="index" class="p-4 rounded-xl bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200">
          <div class="flex items-start gap-3">
            <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm flex-shrink-0">
              {{ index + 1 }}
            </div>
            <div>
              <div class="font-medium text-gray-800 mb-1">{{ suggestion.title }}</div>
              <div class="text-sm text-gray-500">{{ suggestion.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ScoreRing from '@/components/business/ScoreRing.vue'
import { CircleCheck, Select, WarningFilled, Warning } from '@element-plus/icons-vue'
import { interviewApi } from '@/api/interview'

const route = useRoute()
const router = useRouter()
const interviewId = Number(route.params.id) || 1
const isLoading = ref(false)

const report = ref<any>({
  overallScore: 0,
  totalQuestions: 0,
  avgScore: 0,
  duration: 0,
  dimensionScores: {},
  summary: '',
  strengths: [],
  weaknesses: [],
  suggestions: [],
  questionReview: [],
})

function getScoreLevel(score: number): string {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 60) return '一般'
  return '需要改进'
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-yellow-500'
  return 'text-red-500'
}

function getDimensionLabel(key: string): string {
  const labels: Record<string, string> = {
    technical: '技术深度',
    behavioral: '行为表现',
    communication: '沟通表达',
    logic: '逻辑思维',
  }
  return labels[key] || key
}

// 从后端 API 加载面试报告
async function loadReport() {
  isLoading.value = true
  try {
    const response = await interviewApi.getReport(interviewId)
    const data = response.data
    report.value = {
      overallScore: data.overall_score || 0,
      totalQuestions: data.total_questions || 0,
      avgScore: data.avg_score || 0,
      duration: data.duration || 0,
      dimensionScores: data.dimension_scores || {},
      summary: data.summary || '',
      strengths: data.strengths || [],
      weaknesses: data.weaknesses || [],
      suggestions: data.suggestions || [],
      questionReview: data.question_review || [],
    }
  } catch (error) {
    ElMessage.error('加载面试报告失败')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.interview-report-view :deep(.el-card) {
  border-radius: 16px;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
