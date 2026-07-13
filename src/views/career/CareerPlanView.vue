<template>
  <div class="career-plan-view p-6 bg-gray-50 min-h-screen">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">职业规划中心</h1>
      <p class="text-gray-500 text-sm mt-1">AI分析您的背景，生成个性化职业规划</p>
    </div>

    <!-- Input Form -->
    <el-card class="mb-6 border-0">
      <template #header>
        <span class="font-semibold">个人背景信息</span>
      </template>
      <el-form :model="form" label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="教育背景">
              <el-select v-model="form.education" placeholder="选择学历" class="w-full">
                <el-option label="高中及以下" value="high_school" />
                <el-option label="大专" value="college" />
                <el-option label="本科" value="bachelor" />
                <el-option label="硕士" value="master" />
                <el-option label="博士" value="phd" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作年限">
              <el-select v-model="form.experience" placeholder="选择工作年限" class="w-full">
                <el-option label="应届生" value="fresh" />
                <el-option label="1-3年" value="1-3" />
                <el-option label="3-5年" value="3-5" />
                <el-option label="5-10年" value="5-10" />
                <el-option label="10年以上" value="10+" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="技能标签">
          <el-select v-model="form.skills" multiple filterable allow-create placeholder="输入技能后回车添加" class="w-full">
            <el-option v-for="s in skillOptions" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>

        <el-form-item label="工作经历描述">
          <el-input
            v-model="form.workDesc"
            type="textarea"
            :rows="3"
            placeholder="描述你的主要工作内容和职责..."
          />
        </el-form-item>

        <el-form-item label="项目经验（可添加多个）">
          <div v-for="(project, index) in form.projects" :key="index" class="w-full mb-3 p-4 rounded-lg bg-gray-50 border">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700">项目 {{ index + 1 }}</span>
              <el-button text size="small" type="danger" @click="removeProject(index)" v-if="form.projects.length > 1">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-input v-model="project.name" placeholder="项目名称" class="mb-2" />
            <el-input v-model="project.description" type="textarea" :rows="2" placeholder="项目描述和你的角色..." />
          </div>
          <el-button text type="primary" @click="addProject">
            <el-icon class="mr-1"><Plus /></el-icon>
            添加项目
          </el-button>
        </el-form-item>
      </el-form>

      <div class="flex justify-center mt-6">
        <el-button type="primary" size="large" :loading="generating" @click="handleGenerate">
          <el-icon class="mr-1"><TrendCharts /></el-icon>
          {{ generating ? 'AI分析中...' : '生成职业规划' }}
        </el-button>
      </div>
    </el-card>

    <!-- Loading -->
    <el-card v-if="generating" class="border-0 text-center py-12">
      <div class="text-5xl mb-4 animate-bounce">🧠</div>
      <h3 class="text-lg font-semibold text-gray-700 mb-2">AI正在分析您的职业背景</h3>
      <p class="text-gray-500">正在匹配岗位、规划学习路线...</p>
      <el-progress :percentage="generateProgress" :stroke-width="8" class="max-w-md mx-auto mt-4" />
    </el-card>

    <!-- Results -->
    <template v-if="showResult">
      <!-- Career Direction -->
      <el-card class="mb-6 border-0 bg-gradient-to-r from-indigo-50 to-purple-50">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-xl">🎯</span>
            <span class="font-semibold text-indigo-800">推荐职业方向</span>
          </div>
        </template>
        <p class="text-gray-700 leading-relaxed mb-4">{{ result.direction }}</p>
        <div class="flex flex-wrap gap-2">
          <el-tag v-for="pos in result.positions" :key="pos" size="large" effect="plain" type="primary">
            {{ pos }}
          </el-tag>
        </div>
      </el-card>

      <!-- Learning Path -->
      <el-card class="mb-6 border-0">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-xl">📚</span>
            <span class="font-semibold">学习路线</span>
          </div>
        </template>
        <el-steps direction="vertical" :active="0" finish-status="success">
          <el-step v-for="(step, index) in result.learningPath" :key="index" :title="step.stage" :description="step.duration">
            <template #icon>
              <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">
                {{ index + 1 }}
              </div>
            </template>
            <div class="mt-2">
              <div class="flex flex-wrap gap-1 mb-2">
                <el-tag v-for="skill in step.skills" :key="skill" size="small" type="info" effect="light">{{ skill }}</el-tag>
              </div>
              <div class="text-xs text-gray-400">
                <span v-for="(res, i) in step.resources" :key="i">
                  <a href="#" class="text-indigo-500 hover:underline">{{ res }}</a>
                  <span v-if="i < step.resources.length - 1"> | </span>
                </span>
              </div>
            </div>
          </el-step>
        </el-steps>
      </el-card>

      <!-- Skill Suggestions -->
      <el-card class="mb-6 border-0">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-xl">💡</span>
            <span class="font-semibold">技能提升建议</span>
          </div>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="(suggestion, index) in result.skillSuggestions" :key="index" class="p-4 rounded-lg bg-gray-50 border border-gray-100">
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0 text-green-600">
                <el-icon><Check /></el-icon>
              </div>
              <div>
                <div class="font-medium text-gray-800 mb-1">{{ suggestion.title }}</div>
                <div class="text-sm text-gray-500">{{ suggestion.desc }}</div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Market Analysis -->
      <el-card class="border-0">
        <template #header>
          <div class="flex items-center gap-2">
            <span class="text-xl">📊</span>
            <span class="font-semibold">市场分析</span>
          </div>
        </template>
        <p class="text-gray-700 leading-relaxed">{{ result.marketAnalysis }}</p>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Delete, Plus, TrendCharts, Check } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { careerApi } from '@/api/career'

const generating = ref(false)
const generateProgress = ref(0)
const showResult = ref(false)

const skillOptions = ['Vue.js', 'React', 'TypeScript', 'Node.js', 'Python', 'Java', 'Go', 'Docker', 'Kubernetes', 'AWS', 'SQL', 'MongoDB', 'GraphQL', 'Next.js', 'Tailwind CSS']

const form = reactive({
  education: '',
  experience: '',
  skills: [] as string[],
  workDesc: '',
  projects: [{ name: '', description: '' }],
})

const result = reactive({
  direction: '',
  positions: [] as string[],
  learningPath: [] as any[],
  skillSuggestions: [] as any[],
  marketAnalysis: '',
})

function addProject() {
  form.projects.push({ name: '', description: '' })
}

function removeProject(index: number) {
  form.projects.splice(index, 1)
}

async function handleGenerate() {
  generating.value = true
  generateProgress.value = 10

  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (generateProgress.value < 90) {
        generateProgress.value += Math.random() * 20
      }
    }, 400)

    // 调用后端 API 生成职业规划
    const response = await careerApi.getPlan({
      education: form.education,
      experience: form.experience,
      skills: form.skills,
      work_description: form.workDesc,
      projects: form.projects
    })
    const data = response.data

    clearInterval(progressInterval)
    generateProgress.value = 100

    // 映射返回结果
    result.direction = data.direction || ''
    result.positions = data.positions || []
    result.learningPath = data.learning_path || []
    result.skillSuggestions = data.skill_suggestions || []
    result.marketAnalysis = data.market_analysis || ''

    setTimeout(() => {
      generating.value = false
      showResult.value = true
    }, 500)
  } catch (error: any) {
    generating.value = false
    generateProgress.value = 0
    ElMessage.error(error.response?.data?.message || '生成职业规划失败，请稍后重试')
  }
}
</script>

<style scoped>
.career-plan-view :deep(.el-card) {
  border-radius: 16px;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
