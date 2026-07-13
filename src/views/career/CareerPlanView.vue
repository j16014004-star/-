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
  direction: '基于您的技术背景和项目经验，建议向高级前端工程师或全栈工程师方向发展。当前市场对具备深厚前端功底和后端视野的复合型人才需求旺盛，尤其是掌握Vue3/React生态、TypeScript和微前端架构的开发者。',
  positions: ['高级前端工程师', '前端技术负责人', '全栈开发工程师', '前端架构师', '技术经理'],
  learningPath: [
    {
      stage: '夯实基础 (1-2个月)',
      duration: '预计1-2个月',
      skills: ['TypeScript 进阶', 'Vue3 Composition API', 'Webpack/Vite 深度'],
      resources: ['TypeScript Handbook', 'Vue3 官方文档'],
    },
    {
      stage: '工程化实践 (2-3个月)',
      duration: '预计2-3个月',
      skills: ['微前端架构', 'CI/CD', '性能优化', '自动化测试'],
      resources: ['qiankun 文档', 'Jest 官方教程'],
    },
    {
      stage: '后端拓展 (2-4个月)',
      duration: '预计2-4个月',
      skills: ['Node.js', '数据库设计', 'RESTful API', 'Docker'],
      resources: ['Node.js 实战', 'Docker 入门'],
    },
    {
      stage: '架构与领导力 (持续)',
      duration: '持续学习',
      skills: ['系统设计', '技术管理', '开源贡献', '技术分享'],
      resources: ['系统设计面试', '技术博客写作'],
    },
  ],
  skillSuggestions: [
    { title: '深入TypeScript', desc: '当前TypeScript已成为前端必备技能，建议系统学习泛型、类型体操等高级特性' },
    { title: '掌握微前端架构', desc: '大型项目趋势，学习qiankun或Module Federation，提升架构能力' },
    { title: '后端能力补充', desc: '学习Node.js或Go，具备全栈开发能力，增强职场竞争力' },
    { title: '开源项目参与', desc: '通过参与开源项目积累技术影响力，展示代码质量和协作能力' },
  ],
  marketAnalysis: '2026年前端市场呈现以下趋势：1) TypeScript使用率超过85%，成为标配技能；2) 微前端架构在大中型企业普及率超过60%；3) AI辅助编程工具普及，要求开发者具备AI协作能力；4) 全栈化趋势明显，纯前端岗位减少30%；5) 远程工作机会增加，全球化竞争加剧。建议重点关注AI+前端交叉领域，这是未来2年的蓝海方向。',
})

function addProject() {
  form.projects.push({ name: '', description: '' })
}

function removeProject(index: number) {
  form.projects.splice(index, 1)
}

function handleGenerate() {
  generating.value = true
  generateProgress.value = 0
  const interval = setInterval(() => {
    generateProgress.value += Math.random() * 20
    if (generateProgress.value >= 100) {
      generateProgress.value = 100
      clearInterval(interval)
      setTimeout(() => {
        generating.value = false
        showResult.value = true
      }, 500)
    }
  }, 400)
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
