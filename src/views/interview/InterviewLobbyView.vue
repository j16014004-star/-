<template>
  <div class="interview-page p-6 min-h-screen">
    <div class="mb-6">
      <h1 class="text-2xl font-bold">AI 模拟面试</h1>
      <p class="text-gray-500 mt-1">根据已投递岗位、意向岗位或自定义岗位生成专属面试与评估</p>
    </div>

    <el-row :gutter="20" class="mb-6">
      <el-col v-for="stat in stats" :key="stat.label" :span="8">
        <el-card shadow="never"><div class="text-center">
          <div class="text-3xl font-bold" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="text-gray-500 text-sm mt-1">{{ stat.label }}</div>
        </div></el-card>
      </el-col>
    </el-row>

    <el-card class="start-card mb-6" shadow="never">
      <div class="flex items-center justify-between">
        <div><h3 class="text-xl font-bold">开始新面试</h3>
          <p>支持 Python 后端开发与秘书学岗位，AI 会结合岗位、简历和专业知识库出题</p>
        </div>
        <el-button type="primary" size="large" @click="openCreate">立即开始</el-button>
      </div>
    </el-card>

    <el-card shadow="never" v-loading="loading">
      <template #header><strong>面试记录</strong></template>
      <el-table :data="interviews" empty-text="暂无面试记录">
        <el-table-column prop="title" label="面试标题" min-width="190" />
        <el-table-column prop="target_role" label="岗位" min-width="150" />
        <el-table-column label="来源" width="110">
          <template #default="{ row }">{{ sourceLabel(row.source_type) }}</template>
        </el-table-column>
        <el-table-column prop="company" label="公司" min-width="120">
          <template #default="{ row }">{{ row.company || '未指定' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><el-tag :type="statusType(row.status)">
            {{ statusLabel(row.status) }}
          </el-tag></template>
        </el-table-column>
        <el-table-column label="评分" width="90">
          <template #default="{ row }">
            <b v-if="row.overall_score !== null && row.overall_score !== undefined">
              {{ row.overall_score }}分
            </b><span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="日期" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'completed'" size="small" @click="viewReport(row.id)">报告</el-button>
            <el-button v-else size="small" type="primary" @click="enterRoom(row.id)">
              {{ row.status === 'pending' ? '开始' : '继续' }}
            </el-button>
            <el-button size="small" type="danger" plain @click="remove(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="创建 AI 模拟面试" width="640px" destroy-on-close>
      <el-form label-width="105px">
        <el-form-item label="岗位来源" required>
          <el-radio-group v-model="form.source_type">
            <el-radio-button value="applied">已投递岗位</el-radio-button>
            <el-radio-button value="intention">意向岗位</el-radio-button>
            <el-radio-button value="custom">自定义岗位</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.source_type === 'applied'" label="选择岗位" required>
          <el-select v-model="form.job_id" class="w-full" filterable placeholder="选择已投递岗位" @change="syncAppliedJob">
            <el-option v-for="job in options.applied_jobs" :key="job.job_id"
              :label="`${job.title} · ${job.company}`" :value="job.job_id" />
          </el-select>
          <div v-if="!options.applied_jobs.length" class="hint">暂无已投递岗位，可选择意向或自定义岗位。</div>
        </el-form-item>
        <template v-else>
          <el-form-item label="目标岗位" required>
            <el-select v-model="form.target_role" class="w-full" filterable allow-create default-first-option
              placeholder="例如：Python后端开发工程师、行政秘书">
              <el-option label="Python后端开发工程师" value="Python后端开发工程师" />
              <el-option label="行政秘书" value="行政秘书" />
              <el-option label="经理助理（秘书学）" value="经理助理（秘书学）" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标公司"><el-input v-model="form.company" placeholder="可选" /></el-form-item>
          <el-form-item v-if="form.source_type === 'custom'" label="岗位描述">
            <el-input v-model="form.job_description" type="textarea" :rows="3" maxlength="10000"
              show-word-limit placeholder="粘贴岗位职责和任职要求，可显著提高面试针对性" />
          </el-form-item>
          <el-form-item label="使用简历">
            <el-select v-model="resumeSelection" class="w-full" clearable placeholder="可选，建议选择">
              <el-option-group label="原始简历">
                <el-option v-for="item in options.resumes" :key="`r-${item.id}`"
                  :label="item.title" :value="`original:${item.id}`" />
              </el-option-group>
              <el-option-group label="优化简历">
                <el-option v-for="item in options.optimized_resumes" :key="`o-${item.id}`"
                  :label="item.title" :value="`optimized:${item.id}:${item.resume_id}`" />
              </el-option-group>
            </el-select>
          </el-form-item>
        </template>
        <el-form-item label="难度">
          <el-radio-group v-model="form.difficulty">
            <el-radio-button value="junior">初级</el-radio-button>
            <el-radio-button value="middle">中级</el-radio-button>
            <el-radio-button value="senior">高级</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="题型">
          <el-checkbox-group v-model="form.question_types">
            <el-checkbox value="technical">专业能力</el-checkbox>
            <el-checkbox value="project">项目经历</el-checkbox>
            <el-checkbox value="behavioral">行为沟通</el-checkbox>
            <el-checkbox value="scenario">情境处理</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="题目数量">
          <el-slider v-model="form.question_count" :min="3" :max="10" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createInterview">
          {{ creating ? 'AI 正在生成题目…' : '生成并进入面试' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { interviewApi } from '@/api/interview'
import type { InterviewCreateParams, InterviewItem, InterviewOptions } from '@/api/types/interview'

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const dialogVisible = ref(false)
const interviews = ref<InterviewItem[]>([])
const options = reactive<InterviewOptions>({ applied_jobs: [], resumes: [], optimized_resumes: [], supported_domains: [] })
const resumeSelection = ref('')
const form = reactive<InterviewCreateParams>({
  source_type: 'applied', difficulty: 'middle',
  question_types: ['technical', 'project', 'behavioral', 'scenario'], question_count: 6,
})

const stats = computed(() => {
  const done = interviews.value.filter(i => i.status === 'completed')
  return [
    { label: '总面试数', value: interviews.value.length, color: '#4f46e5' },
    { label: '平均分', value: done.length ? Math.round(done.reduce((n, i) => n + (i.overall_score || 0), 0) / done.length) : 0, color: '#10b981' },
    { label: '待完成', value: interviews.value.length - done.length, color: '#f59e0b' },
  ]
})

async function loadData() {
  loading.value = true
  try {
    const [list, opts] = await Promise.all([interviewApi.getList(), interviewApi.getOptions()])
    interviews.value = list.data || []
    Object.assign(options, opts.data)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载面试数据失败')
  } finally { loading.value = false }
}

function openCreate() {
  dialogVisible.value = true
  if (!form.job_id && options.applied_jobs.length) form.job_id = options.applied_jobs[0].job_id
}

function syncAppliedJob() {
  const job = options.applied_jobs.find(item => item.job_id === form.job_id)
  if (!job) return
  form.resume_id = job.resume_id
  form.resume_source = job.resume_source
  form.resume_optimization_id = job.resume_optimization_id
}

function syncResume() {
  delete form.resume_id
  delete form.resume_optimization_id
  if (!resumeSelection.value) return
  const [source, id, resumeId] = resumeSelection.value.split(':')
  form.resume_source = source as 'original' | 'optimized'
  if (source === 'original') form.resume_id = Number(id)
  else {
    form.resume_optimization_id = Number(id)
    form.resume_id = Number(resumeId)
  }
}

async function createInterview() {
  if (form.source_type === 'applied' && !form.job_id) return ElMessage.warning('请选择已投递岗位')
  if (form.source_type !== 'applied' && !form.target_role?.trim()) return ElMessage.warning('请输入目标岗位')
  if (!form.question_types.length) return ElMessage.warning('至少选择一种题型')
  syncResume()
  creating.value = true
  try {
    const response = await interviewApi.create({ ...form })
    dialogVisible.value = false
    ElMessage.success('专属面试题已生成')
    await router.push(`/interview/${response.data.id}`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成面试题失败')
  } finally { creating.value = false }
}

async function enterRoom(id: number) {
  try { await interviewApi.startInterview(id); router.push(`/interview/${id}`) }
  catch (error: any) { ElMessage.error(error.response?.data?.detail || '进入面试失败') }
}
const viewReport = (id: number) => router.push(`/interview/report/${id}`)
async function remove(id: number) {
  try {
    await ElMessageBox.confirm('确认删除这次面试记录？', '删除确认', { type: 'warning' })
    await interviewApi.delete(id)
    interviews.value = interviews.value.filter(item => item.id !== id)
  } catch (error) { if (error !== 'cancel') ElMessage.error('删除失败') }
}
const sourceLabel = (value: string) => ({ applied: '已投递', intention: '意向岗位', custom: '自定义' }[value] || value)
const statusLabel = (value: string) => ({ pending: '待开始', in_progress: '进行中', completed: '已完成' }[value] || value)
const statusType = (value: string) => value === 'completed' ? 'success' : value === 'in_progress' ? 'warning' : 'info'
const formatDate = (value: string) => value ? new Date(value).toLocaleString('zh-CN') : '-'
onMounted(loadData)
</script>

<style scoped>
.interview-page { background: var(--app-bg, #f6f8fb); color: var(--app-text, #1f2937); }
.interview-page :deep(.el-card) { border-radius: 14px; }
.start-card { background: linear-gradient(120deg, #315efb, #6d3bf5); color: white; }
.start-card p { color: #dbeafe; margin-top: 8px; }
.hint { width: 100%; color: #909399; font-size: 12px; margin-top: 5px; }
</style>
