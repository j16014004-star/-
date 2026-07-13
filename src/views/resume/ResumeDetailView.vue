<template>
  <div class="resume-detail-view p-6 bg-gray-50 min-h-screen">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <el-button text @click="$router.push('/resume')">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div>
          <h1 class="text-2xl font-bold text-gray-800">{{ resume.title }}</h1>
          <p class="text-sm text-gray-500">上传于 {{ resume.uploadDate }}</p>
        </div>
      </div>
      <div class="flex gap-3">
        <el-button type="primary" @click="handleOptimize" :icon="Edit">AI优化简历</el-button>
        <el-button @click="handleReAnalyze" :icon="Refresh" :loading="reAnalyzing">
          重新分析
        </el-button>
      </div>
    </div>

    <el-row :gutter="24">
      <!-- Left Panel: Resume Content -->
      <el-col :xs="24" :lg="12" class="mb-6">
        <el-card class="border-0" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-gray-800">简历内容</span>
              <el-tag :type="resume.fileType === 'pdf' ? 'danger' : 'primary'" size="small">
                {{ resume.fileType.toUpperCase() }}
              </el-tag>
            </div>
          </template>

          <div class="space-y-6">
            <!-- Basic Info -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><User /></el-icon> 基本信息
              </h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="姓名">{{ resumeContent.name }}</el-descriptions-item>
                <el-descriptions-item label="电话">{{ resumeContent.phone }}</el-descriptions-item>
                <el-descriptions-item label="邮箱">{{ resumeContent.email }}</el-descriptions-item>
                <el-descriptions-item label="工作经验">{{ resumeContent.experience }}</el-descriptions-item>
                <el-descriptions-item label="最高学历">{{ resumeContent.education }}</el-descriptions-item>
                <el-descriptions-item label="现居城市">{{ resumeContent.city }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- Education -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><School /></el-icon> 教育背景
              </h3>
              <el-timeline>
                <el-timeline-item
                  v-for="edu in resumeContent.educationList"
                  :key="edu.school"
                  :timestamp="edu.period"
                  placement="top"
                >
                  <div class="font-medium">{{ edu.school }}</div>
                  <div class="text-sm text-gray-500">{{ edu.major }} | {{ edu.degree }}</div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- Work Experience -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><Briefcase /></el-icon> 工作经历
              </h3>
              <el-timeline>
                <el-timeline-item
                  v-for="work in resumeContent.workList"
                  :key="work.company"
                  :timestamp="work.period"
                  placement="top"
                >
                  <div class="font-medium">{{ work.company }}</div>
                  <div class="text-sm text-gray-500">{{ work.position }}</div>
                  <div class="text-sm text-gray-500 mt-1">{{ work.description }}</div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- Skills -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><Coin /></el-icon> 技能标签
              </h3>
              <div class="flex flex-wrap gap-2">
                <el-tag
                  v-for="skill in resumeContent.skills"
                  :key="skill"
                  effect="plain"
                  round
                >
                  {{ skill }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Right Panel: AI Analysis -->
      <el-col :xs="24" :lg="12" class="mb-6">
        <!-- Not Analyzed Yet -->
        <div v-if="!resume.analyzed" class="text-center py-20">
          <el-card class="border-0" shadow="hover">
            <div class="text-5xl mb-4">&#x1F916;</div>
            <h3 class="text-lg font-medium text-gray-600 mb-2">尚未进行AI分析</h3>
            <p class="text-gray-400 mb-6">点击下方按钮开始AI智能分析</p>
            <el-button type="primary" size="large" :icon="DataAnalysis" @click="startAnalysis">
              开始分析
            </el-button>
          </el-card>
        </div>

        <!-- Analysis Results -->
        <div v-else>
          <!-- Overall Score -->
          <el-card class="border-0 mb-4" shadow="hover">
            <div class="text-center py-4">
              <div class="relative inline-flex items-center justify-center">
                <el-progress
                  type="circle"
                  :percentage="analysis.overallScore"
                  :stroke-width="10"
                  :width="140"
                  :color="getScoreBarColor(analysis.overallScore)"
                >
                  <span class="text-3xl font-bold" :class="getScoreColor(analysis.overallScore)">
                    {{ analysis.overallScore }}
                  </span>
                </el-progress>
              </div>
              <h3 class="text-lg font-semibold text-gray-800 mt-4">AI综合评分</h3>
              <p class="text-sm text-gray-500">{{ getScoreComment(analysis.overallScore) }}</p>
            </div>
          </el-card>

          <!-- Dimension Scores -->
          <el-card class="border-0 mb-4" shadow="hover">
            <template #header>
              <span class="font-semibold text-gray-800">维度评分</span>
            </template>
            <div class="space-y-4">
              <div v-for="dim in analysis.dimensions" :key="dim.name">
                <div class="flex items-center justify-between text-sm mb-1">
                  <span class="text-gray-600">{{ dim.name }}</span>
                  <span class="font-medium" :class="getScoreColor(dim.score)">{{ dim.score }}分</span>
                </div>
                <el-progress
                  :percentage="dim.score"
                  :color="getScoreBarColor(dim.score)"
                  :stroke-width="8"
                  :show-text="false"
                />
              </div>
            </div>
          </el-card>

          <!-- Strengths & Weaknesses -->
          <el-row :gutter="16">
            <el-col :span="12">
              <el-card class="border-0 mb-4" shadow="hover">
                <template #header>
                  <span class="font-semibold text-green-600 flex items-center gap-1">
                    <el-icon><CircleCheck /></el-icon> 优势
                  </span>
                </template>
                <ul class="space-y-2">
                  <li
                    v-for="(item, i) in analysis.strengths"
                    :key="i"
                    class="text-sm text-gray-600 flex items-start gap-2"
                  >
                    <span class="text-green-500 mt-0.5">&#x2713;</span>
                    {{ item }}
                  </li>
                </ul>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="border-0 mb-4" shadow="hover">
                <template #header>
                  <span class="font-semibold text-orange-600 flex items-center gap-1">
                    <el-icon><WarningFilled /></el-icon> 不足
                  </span>
                </template>
                <ul class="space-y-2">
                  <li
                    v-for="(item, i) in analysis.weaknesses"
                    :key="i"
                    class="text-sm text-gray-600 flex items-start gap-2"
                  >
                    <span class="text-orange-500 mt-0.5">&#x26A0;</span>
                    {{ item }}
                  </li>
                </ul>
              </el-card>
            </el-col>
          </el-row>

          <!-- Suggestions -->
          <el-card class="border-0 mb-4" shadow="hover">
            <template #header>
              <span class="font-semibold text-blue-600 flex items-center gap-1">
                <el-icon><Lightbulb /></el-icon> 改进建议
              </span>
            </template>
            <div class="space-y-3">
              <div
                v-for="(sug, i) in analysis.suggestions"
                :key="i"
                class="flex gap-3 p-3 rounded-lg bg-blue-50"
              >
                <span class="w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                  {{ i + 1 }}
                </span>
                <div>
                  <div class="text-sm font-medium text-gray-700">{{ sug.title }}</div>
                  <div class="text-xs text-gray-500 mt-0.5">{{ sug.detail }}</div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- Missing Keywords -->
          <el-card class="border-0" shadow="hover">
            <template #header>
              <span class="font-semibold text-gray-800">缺失关键词</span>
            </template>
            <div class="flex flex-wrap gap-2">
              <el-tag
                v-for="kw in analysis.missingKeywords"
                :key="kw"
                type="danger"
                effect="light"
                hit
                round
              >
                {{ kw }}
              </el-tag>
            </div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Edit, Refresh, User, School, Briefcase, Coin,
  DataAnalysis, CircleCheck, WarningFilled, Lightbulb
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api/resume'

const route = useRoute()
const router = useRouter()
const reAnalyzing = ref(false)

const resumeId = Number(route.params.id) || 1
const reAnalyzing = ref(false)
const isLoading = ref(true)

const resume = ref({
  id: resumeId,
  title: '',
  fileType: 'pdf',
  uploadDate: '',
  analyzed: false
})

const resumeContent = ref({
  name: '',
  phone: '',
  email: '',
  experience: '',
  education: '',
  city: '',
  educationList: [] as any[],
  workList: [] as any[],
  skills: [] as string[]
})

const analysis = ref({
  overallScore: 0,
  dimensions: [] as any[],
  strengths: [] as string[],
  weaknesses: [] as string[],
  suggestions: [] as any[],
  missingKeywords: [] as string[]
})

// 从后端 API 加载简历详情和分析结果
onMounted(async () => {
  isLoading.value = true
  try {
    const response = await resumeApi.getDetail(resumeId)
    const data = response.data

    resume.value.title = data.title || '未命名简历'
    resume.value.fileType = data.file_type || 'pdf'
    resume.value.uploadDate = data.created_at?.split('T')[0] || ''
    resume.value.analyzed = !!data.analysis

    if (data.content) {
      resumeContent.value = {
        name: data.content.name || '',
        phone: data.content.phone || '',
        email: data.content.email || '',
        experience: data.content.experience || '',
        education: data.content.education || '',
        city: data.content.city || '',
        educationList: data.content.education_list || [],
        workList: data.content.work_list || [],
        skills: data.content.skills || []
      }
    }

    if (data.analysis) {
      analysis.value = {
        overallScore: data.analysis.overall_score || 0,
        dimensions: data.analysis.dimensions || [],
        strengths: data.analysis.strengths || [],
        weaknesses: data.analysis.weaknesses || [],
        suggestions: data.analysis.suggestions || [],
        missingKeywords: data.analysis.missing_keywords || []
      }
    }
  } catch (error) {
    ElMessage.error('加载简历详情失败')
  } finally {
    isLoading.value = false
  }
})

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-yellow-500'
  return 'text-red-500'
}

const getScoreBarColor = (score: number) => {
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

const getScoreComment = (score: number) => {
  if (score >= 90) return '优秀！简历极具竞争力'
  if (score >= 80) return '良好，有少量优化空间'
  if (score >= 70) return '一般，建议针对性优化'
  if (score >= 60) return '需较大改进'
  return '建议重新整理简历'
}

const startAnalysis = async () => {
  try {
    ElMessage.info('开始AI分析...')
    const response = await resumeApi.analyze({ resume_id: resumeId })
    const data = response.data

    // 更新分析结果
    analysis.value = {
      overallScore: data.overall_score || 0,
      dimensions: data.dimensions || [],
      strengths: data.strengths || [],
      weaknesses: data.weaknesses || [],
      suggestions: data.suggestions || [],
      missingKeywords: data.missing_keywords || []
    }
    resume.value.analyzed = true
    ElMessage.success('分析完成')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '分析失败，请稍后重试')
  }
}

const handleReAnalyze = async () => {
  reAnalyzing.value = true
  try {
    const response = await resumeApi.analyze({ resume_id: resumeId })
    const data = response.data

    // 更新分析结果
    analysis.value = {
      overallScore: data.overall_score || 0,
      dimensions: data.dimensions || [],
      strengths: data.strengths || [],
      weaknesses: data.weaknesses || [],
      suggestions: data.suggestions || [],
      missingKeywords: data.missing_keywords || []
    }
    ElMessage.success('重新分析完成')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '分析失败，请稍后重试')
  } finally {
    reAnalyzing.value = false
  }
}

const handleOptimize = () => {
  router.push(`/resume/optimize/${resume.value.id}`)
}
</script>

<style scoped>
.resume-detail-view :deep(.el-card) {
  border-radius: 16px;
}

:deep(.el-descriptions) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-progress-circle) {
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>