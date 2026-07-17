<template>
  <div class="report-page p-6 min-h-screen" v-loading="loading">
    <template v-if="data">
      <div class="flex justify-between items-center mb-6">
        <div><h1 class="text-2xl font-bold">面试评估报告</h1>
          <p class="text-gray-500 mt-1">{{ data.target_role }} · {{ data.company || '模拟面试' }}</p>
        </div>
        <div class="flex gap-2">
          <el-button @click="$router.push('/interview')">返回面试大厅</el-button>
          <el-button type="primary" :loading="retrying" @click="retryWeaknesses">针对薄弱项再面试</el-button>
        </div>
      </div>

      <el-card class="score-card mb-6" shadow="never">
        <div class="score-grid">
          <div><ScoreRing :score="data.report.overall_score" :size="126" :stroke-width="9" />
            <b>综合评分 · {{ scoreLevel(data.report.overall_score) }}</b>
          </div>
          <div><strong>{{ data.questions.length }}</strong><span>已回答题目</span></div>
          <div><strong>{{ totalMinutes }}</strong><span>总用时（分钟）</span></div>
          <div><strong>{{ data.question_bank.length }}</strong><span>针对性练习题</span></div>
        </div>
      </el-card>

      <el-row :gutter="20" class="mb-6">
        <el-col :span="12"><el-card shadow="never" class="full-card">
          <template #header><strong>能力维度</strong></template>
          <div v-for="(score, key) in data.report.dimension_scores" :key="key" class="dimension">
            <div><span>{{ dimensionLabel(key) }}</span><b>{{ score }}分</b></div>
            <el-progress :percentage="score" :color="scoreColor(score)" :stroke-width="9" />
          </div>
        </el-card></el-col>
        <el-col :span="12"><el-card shadow="never" class="full-card">
          <template #header><strong>AI 总结</strong></template>
          <p class="summary">{{ data.report.summary }}</p>
        </el-card></el-col>
      </el-row>

      <el-row :gutter="20" class="mb-6">
        <el-col :span="12"><el-card shadow="never">
          <template #header><strong class="good">能力优势</strong></template>
          <ul><li v-for="item in data.report.strengths" :key="item">✓ {{ item }}</li></ul>
        </el-card></el-col>
        <el-col :span="12"><el-card shadow="never">
          <template #header><strong class="warn">重点薄弱项</strong></template>
          <ul><li v-for="item in data.report.weaknesses" :key="item">• {{ item }}</li></ul>
        </el-card></el-col>
      </el-row>

      <el-card shadow="never" class="mb-6">
        <template #header><strong>改进计划</strong></template>
        <el-row :gutter="20">
          <el-col :span="12"><h3>未来 7 天</h3>
            <ol><li v-for="(item, i) in data.report.improvement_plan_7_days" :key="item">
              <span>{{ i + 1 }}</span>{{ item }}
            </li></ol>
          </el-col>
          <el-col :span="12"><h3>未来 30 天</h3>
            <ol><li v-for="(item, i) in data.report.improvement_plan_30_days" :key="item">
              <span>{{ i + 1 }}</span>{{ item }}
            </li></ol>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="never" class="mb-6">
        <template #header><strong>逐题复盘</strong></template>
        <el-collapse>
          <el-collapse-item v-for="question in data.questions" :key="question.id"
            :title="`Q${question.order_no} · ${question.question}（${question.score ?? 0}分）`">
            <div class="review-block answer"><b>你的回答</b><p>{{ question.answer || '未作答' }}</p></div>
            <div class="review-block feedback"><b>AI 评价</b><p>{{ question.feedback || '无' }}</p></div>
            <div v-if="question.missing_points?.length" class="review-block missing">
              <b>缺失要点</b><el-tag v-for="item in question.missing_points" :key="item" type="warning">{{ item }}</el-tag>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>

      <el-card shadow="never">
        <template #header><strong>薄弱项专属题库</strong></template>
        <div v-for="(item, index) in data.question_bank" :key="item.id" class="bank-item">
          <div class="flex justify-between"><b>{{ index + 1 }}. {{ item.question }}</b>
            <el-tag>{{ difficultyLabel(item.difficulty) }}</el-tag></div>
          <p>针对：{{ item.weakness }}</p>
          <el-collapse><el-collapse-item title="查看参考要点">
            <ul><li v-for="point in item.reference_points" :key="point">{{ point }}</li></ul>
          </el-collapse-item></el-collapse>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ScoreRing from '@/components/business/ScoreRing.vue'
import { interviewApi } from '@/api/interview'
import type { InterviewReportDetail } from '@/api/types/interview'

const route = useRoute()
const router = useRouter()
const interviewId = Number(route.params.id)
const data = ref<InterviewReportDetail | null>(null)
const loading = ref(false)
const retrying = ref(false)
const totalMinutes = computed(() => Math.max(1, Math.round(
  (data.value?.questions.reduce((n, q) => n + (q.duration_seconds || 0), 0) || 0) / 60
)))

async function load() {
  loading.value = true
  try { data.value = (await interviewApi.getReport(interviewId)).data }
  catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载面试报告失败')
    if (error.response?.status === 404) router.replace(`/interview/${interviewId}`)
  } finally { loading.value = false }
}
async function retryWeaknesses() {
  retrying.value = true
  try {
    const response = await interviewApi.retryWeaknesses(interviewId)
    ElMessage.success('薄弱项专属复试已生成')
    await router.push(`/interview/${response.data.id}`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成薄弱项复试失败')
  } finally { retrying.value = false }
}
const scoreLevel = (v: number) => v >= 90 ? '优秀' : v >= 80 ? '良好' : v >= 60 ? '合格' : '需要提升'
const scoreColor = (v: number) => v >= 80 ? '#10b981' : v >= 60 ? '#f59e0b' : '#ef4444'
const dimensionLabel = (v: string) => ({ professional: '专业能力', analysis: '分析能力', evidence: '实践证据', communication: '沟通结构' }[v] || v)
const difficultyLabel = (v: string) => ({ junior: '初级', middle: '中级', senior: '高级' }[v] || v)
onMounted(load)
</script>

<style scoped>
.report-page { background:var(--app-bg, #f6f8fb); color:var(--app-text, #1f2937); }
.report-page :deep(.el-card) { border-radius:14px; }
.score-card { background:linear-gradient(120deg, #eef2ff, #eff6ff); }
.score-grid { display:grid; grid-template-columns:2fr 1fr 1fr 1fr; align-items:center; text-align:center; padding:22px; }
.score-grid > div { display:flex; flex-direction:column; align-items:center; gap:8px; }
.score-grid strong { font-size:30px; color:#4f46e5; }
.score-grid span { color:#6b7280; }
.full-card { height:100%; }
.dimension { margin-bottom:18px; }.dimension > div { display:flex; justify-content:space-between; margin-bottom:5px; }
.summary { line-height:1.9; white-space:pre-wrap; }
ul { display:grid; gap:10px; line-height:1.7; }.good { color:#059669; }.warn { color:#d97706; }
h3 { font-weight:700; margin-bottom:14px; }
ol { display:grid; gap:10px; } ol li { display:flex; gap:10px; align-items:flex-start; }
ol span { width:24px; height:24px; border-radius:50%; background:#eef2ff; color:#4f46e5; display:grid; place-items:center; flex:none; }
.review-block { padding:14px; border-radius:10px; margin-bottom:10px; }.review-block p { margin-top:7px; line-height:1.7; white-space:pre-wrap; }
.answer { background:#eff6ff; }.feedback { background:#ecfdf5; }.missing { background:#fffbeb; }
.missing .el-tag { margin:8px 8px 0 0; }
.bank-item { padding:16px; border:1px solid var(--el-border-color-lighter); border-radius:10px; margin-bottom:12px; }
.bank-item > p { color:#d97706; margin:8px 0; font-size:13px; }
</style>
