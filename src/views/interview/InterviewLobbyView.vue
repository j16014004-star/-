<template>
  <div class="interview-lobby-view p-6 bg-gray-50 min-h-screen">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">AI面试大厅</h1>
      <p class="text-gray-500 text-sm mt-1">AI模拟真实面试场景，助你轻松应对技术面试</p>
    </div>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="mb-6">
      <el-col :span="8" v-for="stat in stats" :key="stat.label">
        <el-card class="border-0" body-style="padding: 20px">
          <div class="text-center">
            <div class="text-3xl font-bold mb-1" :style="{ color: stat.color }">{{ stat.value }}</div>
            <div class="text-sm text-gray-500">{{ stat.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Start -->
    <el-card class="mb-6 border-0 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-xl font-bold mb-2">&#x1F3AF; 开始新面试</h3>
          <p class="text-blue-200">AI将根据目标岗位生成面试问题，模拟真实面试场景</p>
        </div>
        <el-button type="primary" size="large" class="bg-white text-indigo-600 border-none hover:bg-blue-50" @click="showCreateDialog = true">
          <el-icon class="mr-1"><VideoPlay /></el-icon>
          立即开始
        </el-button>
      </div>
    </el-card>

    <!-- Interview History -->
    <el-card class="border-0">
      <template #header>
        <span class="font-semibold">面试记录</span>
      </template>

      <el-table :data="interviews" style="width: 100%" stripe>
        <el-table-column prop="title" label="面试标题" min-width="180" />
        <el-table-column prop="position" label="岗位" width="150" />
        <el-table-column prop="company" label="公司" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : row.status === 'in_progress' ? 'warning' : 'info'" size="small">
              {{ row.status === 'completed' ? '已完成' : row.status === 'in_progress' ? '进行中' : '待开始' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="评分" width="100">
          <template #default="{ row }">
            <span v-if="row.score !== null" class="font-bold" :class="row.score >= 80 ? 'text-green-500' : row.score >= 60 ? 'text-yellow-500' : 'text-red-500'">
              {{ row.score }}分
            </span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="150" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button v-if="row.status === 'completed'" size="small" @click="viewReport(row.id)">报告</el-button>
              <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="startInterview(row.id)">开始</el-button>
              <el-button v-if="row.status === 'in_progress'" size="small" type="primary" @click="resumeInterview(row.id)">继续</el-button>
              <el-button size="small" @click="goToRoom(row.id)">房间</el-button>
              <el-button size="small" type="danger" @click="deleteInterview(row.id)">删除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create Interview Dialog -->
    <el-dialog v-model="showCreateDialog" title="创建新面试" width="550px">
      <el-form :model="newInterview" label-width="100px">
        <el-form-item label="面试标题">
          <el-input v-model="newInterview.title" placeholder="例如：前端工程师面试" />
        </el-form-item>
        <el-form-item label="目标岗位">
          <el-select v-model="newInterview.position" filterable class="w-full" placeholder="选择或输入岗位">
            <el-option label="前端开发工程师" value="前端开发工程师" />
            <el-option label="后端开发工程师" value="后端开发工程师" />
            <el-option label="全栈开发工程师" value="全栈开发工程师" />
            <el-option label="前端技术负责人" value="前端技术负责人" />
            <el-option label="算法工程师" value="算法工程师" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标公司">
          <el-input v-model="newInterview.company" placeholder="可选" />
        </el-form-item>
        <el-form-item label="问题类型">
          <el-checkbox-group v-model="newInterview.questionTypes">
            <el-checkbox label="technical">技术问题</el-checkbox>
            <el-checkbox label="behavioral">行为面试</el-checkbox>
            <el-checkbox label="project">项目经验</el-checkbox>
            <el-checkbox label="general">综合素质</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="问题数量">
          <el-slider v-model="newInterview.questionCount" :min="3" :max="10" :step="1" show-stops />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建面试</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { VideoPlay } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { interviewApi } from '@/api/interview'

const router = useRouter()

const interviews = ref<any[]>([])
const isLoading = ref(false)

// 从后端 API 加载面试列表
async function loadInterviews() {
  isLoading.value = true
  try {
    const response = await interviewApi.getList()
    interviews.value = (response.data || []).map((item: any) => ({
      id: item.id,
      title: item.title,
      position: item.position,
      company: item.company || '未指定',
      status: item.status,
      score: item.score,
      date: item.created_at,
    }))
  } catch (error) {
    ElMessage.error('加载面试列表失败')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadInterviews()
})

// 统计卡片 - 使用 computed 确保动态更新
const stats = computed(() => [
  { label: '总面试数', value: interviews.value.length, color: '#4f46e5' },
  { label: '平均分', value: interviews.value.filter(i => i.score !== null).length > 0
    ? Math.round(interviews.value.filter(i => i.score !== null).reduce((sum, i) => sum + (i.score || 0), 0) / interviews.value.filter(i => i.score !== null).length)
    : 0, color: '#10b981' },
  { label: '待完成', value: interviews.value.filter(i => i.status !== 'completed').length, color: '#f59e0b' },
])

const showCreateDialog = ref(false)
const newInterview = reactive({
  title: '',
  position: '',
  company: '',
  questionTypes: ['technical', 'behavioral'],
  questionCount: 5,
})

function viewReport(id: number) {
  router.push(`/interview/report/${id}`)
}

function startInterview(id: number) {
  router.push(`/interview/${id}`)
}

function resumeInterview(id: number) {
  router.push(`/interview/${id}`)
}

function goToRoom(id: number) {
  router.push(`/interview/${id}`)
}

async function deleteInterview(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除此面试记录吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await interviewApi.delete(id)
    interviews.value = interviews.value.filter(i => i.id !== id)
    ElMessage.success('面试记录已删除')
  } catch (error) {
    // User cancelled or API error
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

async function handleCreate() {
  if (!newInterview.title || !newInterview.position) {
    ElMessage.warning('请填写面试标题和目标岗位')
    return
  }
  try {
    const response = await interviewApi.create({
      title: newInterview.title,
      position: newInterview.position,
      company: newInterview.company || undefined,
      question_types: newInterview.questionTypes,
      question_count: newInterview.questionCount
    } as any)
    const interview = response.data
    interviews.value.unshift({
      id: interview.id,
      title: interview.title,
      position: interview.position,
      company: interview.company || '未指定',
      status: interview.status || 'pending',
      score: null,
      date: interview.created_at || new Date().toLocaleString('zh-CN'),
    })
    showCreateDialog.value = false
    ElMessage.success('面试已创建，点击"开始"进入面试')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '创建失败，请稍后重试')
  }
}
</script>

<style scoped>
.interview-lobby-view :deep(.el-card) {
  border-radius: 16px;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
