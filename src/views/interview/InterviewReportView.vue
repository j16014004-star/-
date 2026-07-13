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
import ScoreRing from '@/components/business/ScoreRing.vue'
import { CircleCheck, Select, WarningFilled, Warning } from '@element-plus/icons-vue'

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

const report = {
  overallScore: 82,
  totalQuestions: 5,
  avgScore: 82,
  duration: 26,
  dimensionScores: {
    technical: 85,
    behavioral: 78,
    communication: 88,
    logic: 75,
  },
  summary: '整体表现良好，展现了扎实的前端技术基础和良好的沟通能力。在Vue3核心原理方面理解深入，能够清晰地解释Composition API和响应式系统的设计思想。在行为面试环节表现稳定，展现了良好的团队协作意识。逻辑思维能力有进一步提升的空间，建议加强系统性思考和问题拆解能力。',
  strengths: [
    'Vue3 Composition API理解深入，能清晰对比Options API的优劣',
    '对Proxy响应式系统的底层原理有扎实掌握',
    '沟通表达清晰，能够用简洁的语言解释复杂概念',
    '项目经验丰富，有实际的企业级开发经验',
  ],
  weaknesses: [
    '微前端架构原理掌握不够深入，缺乏实际项目经验',
    '算法和数据结构基础有待加强',
    '系统设计能力需要进一步提升',
  ],
  suggestions: [
    { title: '深入学习微前端架构', desc: '通过实际项目练习qiankun框架，理解沙箱隔离和通信机制' },
    { title: '强化算法训练', desc: '建议每周完成3-5道LeetCode题目，重点练习动态规划和树相关算法' },
    { title: '提升系统设计能力', desc: '学习系统设计方法论，阅读《系统设计面试指南》等书籍' },
    { title: '扩大技术视野', desc: '关注业界前沿技术趋势，参与技术社区和开源项目' },
  ],
  questionReview: [
    {
      id: 1,
      question: '请解释Vue3中Composition API与Options API的区别，以及各自的使用场景。',
      answer: 'Composition API相比Options API有更好的逻辑复用能力，通过setup函数可以将相关逻辑组织在一起，而不是分散在data/methods/computed等选项中。特别适合大型项目和需要复用业务逻辑的场景。Options API在小型组件中仍然简洁好用...',
      score: 88,
      feedback: '回答很全面，涵盖了核心区别和使用场景。建议补充一些具体的代码示例。',
    },
    {
      id: 2,
      question: 'Vue3的响应式系统是如何实现的？Proxy相比Object.defineProperty有什么优势？',
      answer: 'Vue3使用ES6 Proxy作为响应式系统的核心，通过代理对象来拦截get/set等操作，实现数据变化的自动追踪。相比Vue2的Object.defineProperty，Proxy不需要递归遍历对象的所有属性...',
      score: 90,
      feedback: '回答准确且深入，清楚地说明了Proxy的优势。',
    },
    {
      id: 3,
      question: '请描述你最有成就感的一个项目，你在其中承担的角色和做出的技术决策。',
      answer: '我之前负责一个企业级后台管理系统的重构项目。在项目中，我将Vue2升级到Vue3，使用Composition API重构了业务逻辑，引入了TypeScript提升代码质量...',
      score: 85,
      feedback: '项目描述清晰，建议用量化数据展示项目成果（如性能提升百分比）。',
    },
    {
      id: 4,
      question: '当团队中出现技术分歧时，你会如何处理？',
      answer: '我认为技术分歧是正常的，关键是要基于数据和事实来做决策。我通常会先充分了解各方观点，然后做一个小型的POC来验证不同方案的可行性...',
      score: 80,
      feedback: '回答展示了良好的沟通能力和决策思维。',
    },
    {
      id: 5,
      question: '请解释微前端架构的核心思想，以及qiankun的工作原理。',
      answer: '微前端的核心思想是将一个大型前端应用拆分成多个小型、独立的应用，每个应用可以独立开发、独立部署。qiankun是基于single-spa封装的...',
      score: 70,
      feedback: '基本概念理解正确，但对沙箱隔离和样式隔离的具体实现细节不够深入。',
    },
  ],
}
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
