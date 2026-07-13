<template>
  <div class="agent-task-view p-6 bg-gray-50 min-h-screen">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">Agent任务中心</h1>
      <p class="text-gray-500 text-sm mt-1">AI自动执行求职任务：搜索、筛选、投递、跟踪</p>
    </div>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="mb-6">
      <el-col :span="6" v-for="stat in stats" :key="stat.label">
        <el-card class="border-0" body-style="padding: 20px">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center text-xl" :style="{ background: stat.bgColor }">
              {{ stat.icon }}
            </div>
            <div>
              <div class="text-2xl font-bold text-gray-800">{{ stat.value }}</div>
              <div class="text-sm text-gray-500">{{ stat.label }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Task List -->
    <el-card class="border-0">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-semibold">任务列表</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true">
            <el-icon class="mr-1"><Plus /></el-icon>
            新建任务
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" style="width: 100%" stripe>
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.type)" size="small">{{ getTaskTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusColor(row.status)" size="small" effect="dark">
              {{ getTaskStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="150">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="row.status === 'completed' ? 'success' : ''" :stroke-width="6" />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="viewDetails(row.id)">详情</el-button>
              <el-button v-if="row.status === 'running'" size="small" @click="pauseTask(row.id)">暂停</el-button>
              <el-button v-if="row.status === 'paused'" size="small" @click="resumeTask(row.id)">恢复</el-button>
              <el-button v-if="row.status === 'pending' || row.status === 'paused'" size="small" type="primary" @click="startTask(row.id)">启动</el-button>
              <el-button size="small" type="danger" @click="deleteTask(row.id)">删除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create Task Dialog -->
    <el-dialog v-model="showCreateDialog" title="创建新任务" width="600px">
      <el-form :model="newTask" label-width="100px">
        <el-form-item label="任务类型">
          <el-select v-model="newTask.type" class="w-full">
            <el-option label="职位搜索" value="search" />
            <el-option label="职位筛选" value="filter" />
            <el-option label="自动投递" value="apply" />
            <el-option label="进度跟踪" value="track" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标岗位">
          <el-input v-model="newTask.targetPosition" placeholder="例如：前端开发工程师" />
        </el-form-item>
        <el-form-item label="目标城市">
          <el-select v-model="newTask.targetCities" multiple placeholder="选择城市" class="w-full">
            <el-option v-for="city in cities" :key="city" :label="city" :value="city" />
          </el-select>
        </el-form-item>
        <el-form-item label="薪资范围">
          <el-input-number v-model="newTask.salaryMin" :min="0" :step="5" :max="200" /> -
          <el-input-number v-model="newTask.salaryMax" :min="0" :step="5" :max="200" /> k/月
        </el-form-item>
        <el-form-item label="执行频率">
          <el-radio-group v-model="newTask.frequency">
            <el-radio label="once">一次性</el-radio>
            <el-radio label="daily">每天</el-radio>
            <el-radio label="weekly">每周</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTask">创建任务</el-button>
      </template>
    </el-dialog>

    <!-- Task Detail Drawer -->
    <el-drawer v-model="showDetailDrawer" title="任务详情" size="600px">
      <div v-if="selectedTask" class="p-4">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="任务名称">{{ selectedTask.name }}</el-descriptions-item>
          <el-descriptions-item label="任务类型">
            <el-tag>{{ getTaskTypeLabel(selectedTask.type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getTaskStatusColor(selectedTask.status)">{{ getTaskStatusLabel(selectedTask.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">
            <el-progress :percentage="selectedTask.progress" :status="selectedTask.status === 'completed' ? 'success' : ''" />
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ selectedTask.createdAt }}</el-descriptions-item>
        </el-descriptions>

        <div class="mt-6">
          <h3 class="font-semibold text-gray-800 mb-3">执行日志</h3>
          <div class="space-y-2 max-h-96 overflow-y-auto">
            <div v-for="log in selectedTask.logs" :key="log.id" class="p-3 rounded-lg bg-gray-50 text-sm">
              <div class="flex items-center gap-2 mb-1">
                <el-icon :color="getLogLevelColor(log.level)"><InfoFilled /></el-icon>
                <span class="text-xs text-gray-500">{{ log.time }}</span>
              </div>
              <div class="text-gray-700">{{ log.message }}</div>
            </div>
          </div>
        </div>

        <div v-if="selectedTask.applications.length > 0" class="mt-6">
          <h3 class="font-semibold text-gray-800 mb-3">投递记录</h3>
          <el-table :data="selectedTask.applications" size="small">
            <el-table-column prop="company" label="公司" />
            <el-table-column prop="position" label="职位" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getApplicationStatusColor(row.status)" size="small">{{ getApplicationStatusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="appliedAt" label="投递时间" width="120" />
          </el-table>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { agentApi } from '@/api/agent'

const stats = ref([
  { label: '运行中', value: 0, icon: '⚡', bgColor: '#dbeafe' },
  { label: '已完成', value: 0, icon: '✅', bgColor: '#d1fae5' },
  { label: '投递成功', value: 0, icon: '📨', bgColor: '#fef3c7' },
  { label: '面试邀请', value: 0, icon: '🎯', bgColor: '#fce7f3' },
])

const cities = ['北京', '上海', '深圳', '杭州', '广州', '成都', '南京', '武汉']

interface Task {
  id: number
  name: string
  type: 'search' | 'filter' | 'apply' | 'track'
  status: 'pending' | 'running' | 'completed' | 'paused' | 'failed'
  progress: number
  createdAt: string
  logs: { id: number; message: string; level: 'info' | 'warn' | 'error'; time: string }[]
  applications: { id: number; company: string; position: string; status: 'submitted' | 'viewed' | 'interview' | 'rejected'; appliedAt: string }[]
}

const tasks = ref<Task[]>([])

// 从后端 API 加载任务列表
async function loadTasks() {
  try {
    const response = await agentApi.getTasks()
    tasks.value = (response.data || []).map((task: any) => ({
      id: task.id,
      name: task.name,
      type: task.type,
      status: task.status,
      progress: task.progress || 0,
      createdAt: task.created_at,
      logs: task.logs || [],
      applications: task.applications || []
    }))

    // 更新统计数据
    stats.value[0].value = tasks.value.filter(t => t.status === 'running').length
    stats.value[1].value = tasks.value.filter(t => t.status === 'completed').length
    stats.value[2].value = tasks.value.reduce((sum, t) => sum + (t.applications?.length || 0), 0)
    stats.value[3].value = tasks.value.reduce((sum, t) =>
      sum + (t.applications?.filter(a => a.status === 'interview').length || 0), 0)
  } catch (error) {
    ElMessage.error('加载任务列表失败')
  }
}

onMounted(() => {
  loadTasks()
})

const showCreateDialog = ref(false)
const showDetailDrawer = ref(false)
const selectedTask = ref<Task | null>(null)

const newTask = reactive({
  type: 'search',
  targetPosition: '',
  targetCities: [] as string[],
  salaryMin: 20,
  salaryMax: 40,
  frequency: 'once',
})

function getTaskTypeColor(type: string): string {
  const colors: Record<string, string> = { search: 'primary', filter: 'success', apply: 'warning', track: 'info' }
  return colors[type] || 'info'
}

function getTaskTypeLabel(type: string): string {
  const labels: Record<string, string> = { search: '搜索', filter: '筛选', apply: '投递', track: '跟踪' }
  return labels[type] || type
}

function getTaskStatusColor(status: string): string {
  const colors: Record<string, string> = { pending: 'info', running: 'warning', completed: 'success', paused: '', failed: 'danger' }
  return colors[status] || 'info'
}

function getTaskStatusLabel(status: string): string {
  const labels: Record<string, string> = { pending: '待执行', running: '运行中', completed: '已完成', paused: '已暂停', failed: '失败' }
  return labels[status] || status
}

function getLogLevelColor(level: string): string {
  const colors: Record<string, string> = { info: '#3b82f6', warn: '#f59e0b', error: '#ef4444' }
  return colors[level] || '#6b7280'
}

function getApplicationStatusColor(status: string): string {
  const colors: Record<string, string> = { submitted: 'info', viewed: 'warning', interview: 'success', rejected: 'danger' }
  return colors[status] || 'info'
}

function getApplicationStatusLabel(status: string): string {
  const labels: Record<string, string> = { submitted: '已投递', viewed: '已查看', interview: '面试', rejected: '被拒' }
  return labels[status] || status
}

function viewDetails(id: number) {
  selectedTask.value = tasks.value.find(t => t.id === id) || null
  showDetailDrawer.value = true
}

async function pauseTask(id: number) {
  try {
    await agentApi.pauseTask(id)
    ElMessage.success('任务已暂停')
    loadTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '暂停失败，请稍后重试')
  }
}

async function resumeTask(id: number) {
  try {
    await agentApi.startTask(id)
    ElMessage.success('任务已恢复')
    loadTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '恢复失败，请稍后重试')
  }
}

async function startTask(id: number) {
  try {
    await agentApi.startTask(id)
    ElMessage.success('任务已启动')
    loadTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '启动失败，请稍后重试')
  }
}

async function deleteTask(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await agentApi.deleteTask(id)
    ElMessage.success('任务已删除')
    loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

async function createTask() {
  if (!newTask.targetPosition) {
    ElMessage.warning('请填写目标岗位')
    return
  }
  try {
    await agentApi.createTask({
      name: `${newTask.targetPosition} - ${getTaskTypeLabel(newTask.type)}任务`,
      type: newTask.type,
      target_position: newTask.targetPosition,
      target_cities: newTask.targetCities,
      salary_min: newTask.salaryMin,
      salary_max: newTask.salaryMax,
      frequency: newTask.frequency
    } as any)
    showCreateDialog.value = false
    ElMessage.success('任务创建成功')
    loadTasks()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '创建失败，请稍后重试')
  }
}
</script>

<style scoped>
.agent-task-view :deep(.el-card) {
  border-radius: 16px;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
