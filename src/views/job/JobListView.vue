<template>
  <div v-loading="isInitialLoading" class="job-list-view min-h-screen bg-gray-50 p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">岗位推荐</h1>
      <p class="mt-1 text-sm text-gray-500">选择招聘平台，登录后按简历内容生成推荐岗位</p>
    </div>

    <el-card class="workflow-card mb-6 border-0" shadow="never">
      <div class="grid gap-5 lg:grid-cols-[1.1fr_1fr]">
        <div class="rounded-lg border border-gray-100 bg-gray-50 p-4">
          <div class="mb-3 flex items-center justify-between gap-3">
            <div class="font-semibold text-gray-800">当前简历</div>
            <el-button size="small" :icon="Refresh" :loading="isInitialLoading" :disabled="isBusy" @click="loadInitialData">
              刷新
            </el-button>
          </div>

          <template v-if="currentResume">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-medium text-gray-800">{{ currentResume.title }}</span>
              <el-tag size="small" :type="currentResume.status === 'completed' ? 'success' : 'warning'" effect="plain">
                {{ getResumeStatusText(currentResume.status) }}
              </el-tag>
            </div>
            <div class="mt-2 text-sm text-gray-500">
              上传时间：{{ formatDate(currentResume.created_at) }}
            </div>
          </template>

          <el-empty v-else description="暂无简历" :image-size="80" class="py-2">
            <el-button type="primary" :icon="Upload" @click="goUploadResume">上传简历</el-button>
          </el-empty>
        </div>

        <div class="rounded-lg border border-gray-100 p-4">
          <div class="mb-3 font-semibold text-gray-800">招聘平台</div>
          <div class="flex flex-col gap-3 sm:flex-row">
            <el-select
              v-model="selectedSource"
              class="flex-1"
              :disabled="!currentResume || isBusy"
              placeholder="选择平台"
              filterable
            >
              <el-option
                v-for="platform in platforms"
                :key="platform.source"
                :label="getPlatformLabel(platform)"
                :value="platform.source"
                :disabled="!platform.enabled"
              />
            </el-select>
            <el-button
              type="primary"
              :icon="Link"
              :loading="isStarting"
              :disabled="!canStart"
              @click="handleStartFlow"
            >
              {{ startButtonText }}
            </el-button>
          </div>

          <div v-if="selectedPlatform" class="mt-3 text-sm text-gray-500">
            登录状态：{{ getLoginStatusText(selectedPlatform.login_status) }}
          </div>
        </div>
      </div>

      <div v-if="showTaskStatus" class="mt-5 rounded-lg border border-gray-100 bg-gray-50 p-4">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <el-tag :type="statusTagType" effect="light">{{ statusTitle }}</el-tag>
            <span class="text-sm text-gray-600">{{ statusMessage }}</span>
          </div>
          <span v-if="taskId" class="text-xs text-gray-400">任务 {{ taskId }}</span>
        </div>

        <el-progress
          :percentage="progress"
          :status="progressStatus"
          :stroke-width="10"
        />

        <div class="mt-4 grid gap-3 text-sm text-gray-600 sm:grid-cols-3">
          <div class="rounded bg-white px-3 py-2">
            发现岗位 <span class="font-semibold text-gray-800">{{ taskStats.totalFound }}</span>
          </div>
          <div class="rounded bg-white px-3 py-2">
            入库岗位 <span class="font-semibold text-gray-800">{{ taskStats.totalSaved }}</span>
          </div>
          <div class="rounded bg-white px-3 py-2">
            匹配岗位 <span class="font-semibold text-gray-800">{{ taskStats.totalMatched }}</span>
          </div>
        </div>

        <div v-if="extractedSkills.length" class="mt-4 flex flex-wrap gap-2">
          <el-tag v-for="skill in extractedSkills" :key="skill" size="small" effect="plain">
            {{ skill }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <template v-if="flowStatus === 'success'">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div class="text-sm text-gray-500">
          共生成 <span class="font-semibold text-indigo-600">{{ total }}</span> 个推荐岗位
        </div>
        <el-radio-group v-model="sortBy" size="small">
          <el-radio-button label="match">匹配度</el-radio-button>
          <el-radio-button label="salary">薪资</el-radio-button>
          <el-radio-button label="date">最新</el-radio-button>
        </el-radio-group>
      </div>

      <el-empty v-if="!isResultLoading && sortedJobs.length === 0" description="暂无匹配岗位" class="py-16" />

      <el-row v-else v-loading="isResultLoading" :gutter="20">
        <el-col v-for="job in sortedJobs" :key="job.id" :xs="24" :sm="12" :lg="8" class="mb-4">
          <el-card
            class="job-card h-full cursor-pointer border-0"
            shadow="hover"
            body-style="padding: 24px"
            @click="openDetail(job.id)"
          >
            <div class="mb-3 flex items-start justify-between">
              <div class="min-w-0 flex-1">
                <div class="mb-1 flex items-center gap-2">
                  <img
                    v-if="job.companyLogo"
                    :src="job.companyLogo"
                    :alt="job.company"
                    class="h-7 w-7 rounded object-cover"
                  >
                  <h3 class="truncate text-lg font-semibold text-gray-800">{{ job.title }}</h3>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-500">
                  <span class="font-medium">{{ job.company }}</span>
                  <span>·</span>
                  <span>{{ job.city }}</span>
                </div>
              </div>
              <div class="ml-4 flex-shrink-0">
                <div class="relative h-16 w-16">
                  <svg class="h-16 w-16 -rotate-90 transform" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#eef2f7" stroke-width="3" />
                    <circle
                      cx="18"
                      cy="18"
                      r="16"
                      fill="none"
                      :stroke="getMatchColor(job.matchScore)"
                      stroke-width="3"
                      :stroke-dasharray="100"
                      :stroke-dashoffset="100 - job.matchScore"
                      stroke-linecap="round"
                    />
                  </svg>
                  <div class="absolute inset-0 flex items-center justify-center text-xs font-bold" :style="{ color: getMatchColor(job.matchScore) }">
                    {{ job.matchScore }}%
                  </div>
                </div>
              </div>
            </div>

            <div class="mb-3 text-2xl font-bold text-indigo-600">
              {{ formatSalaryRange(job) }}
            </div>

            <div class="mb-3 flex flex-wrap gap-1 text-xs">
              <el-tag size="small" type="info" effect="plain">{{ job.experience }}</el-tag>
              <el-tag size="small" type="info" effect="plain">{{ job.education }}</el-tag>
              <el-tag size="small" :type="job.isActive ? 'success' : 'danger'" effect="plain">
                {{ job.isActive ? '有效' : '已失效' }}
              </el-tag>
            </div>

            <div class="mb-4 flex flex-wrap gap-1">
              <el-tag v-for="skill in job.skills" :key="skill" size="small" effect="light">{{ skill }}</el-tag>
            </div>

            <div class="mb-4 text-xs text-gray-500">
              <div class="mb-1 font-medium">匹配原因：</div>
              <ul class="list-inside list-disc space-y-1">
                <li v-for="(reason, i) in job.matchReasons" :key="i">{{ reason }}</li>
              </ul>
            </div>

            <div class="mb-4 flex flex-wrap items-center gap-2 text-xs text-gray-400">
              <el-tag size="small" effect="plain">{{ job.sourceName }}</el-tag>
              <span>爬取于 {{ formatDate(job.crawlTime || job.createdAt) }}</span>
            </div>

            <div class="flex gap-2" @click.stop>
              <el-button
                type="primary"
                size="small"
                class="flex-1"
                :icon="Position"
                :loading="applyingId === job.id"
                :disabled="!job.isActive || !currentResume"
                @click="handleApply(job)"
              >
                记录投递
              </el-button>
              <el-button size="small" :icon="TopRight" :disabled="!job.sourceUrl" @click="openSource(job)">
                原站
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div v-if="total > pageSize" class="mt-8 flex justify-center">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[9, 18, 27]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </template>

    <el-empty
      v-else-if="!showTaskStatus && !currentResume"
      description="上传简历后开始岗位推荐"
      class="py-16"
    >
      <el-button type="primary" :icon="Upload" @click="goUploadResume">上传简历</el-button>
    </el-empty>

    <el-empty
      v-else-if="!showTaskStatus"
      description="选择招聘平台后生成岗位推荐"
      class="py-16"
    />

    <el-drawer v-model="detailVisible" title="岗位详情" size="520px">
      <div v-loading="isDetailLoading" class="min-h-80">
        <template v-if="detailJob">
          <div class="mb-5">
            <h2 class="mb-2 text-xl font-bold text-gray-800">{{ detailJob.title }}</h2>
            <div class="text-sm text-gray-500">{{ detailJob.company }} · {{ detailJob.city }}</div>
          </div>

          <div class="mb-5 flex flex-wrap gap-2">
            <el-tag type="primary" effect="light">{{ formatSalaryRange(detailJob) }}</el-tag>
            <el-tag effect="plain">{{ detailJob.experience }}</el-tag>
            <el-tag effect="plain">{{ detailJob.education }}</el-tag>
            <el-tag :type="detailJob.isActive ? 'success' : 'danger'" effect="plain">
              {{ detailJob.isActive ? '岗位有效' : '岗位已失效' }}
            </el-tag>
          </div>

          <div class="mb-5">
            <h3 class="mb-2 font-semibold text-gray-700">技能要求</h3>
            <div class="flex flex-wrap gap-2">
              <el-tag v-for="skill in detailJob.skills" :key="skill" size="small">{{ skill }}</el-tag>
            </div>
          </div>

          <div class="mb-5">
            <h3 class="mb-2 font-semibold text-gray-700">岗位描述</h3>
            <div class="whitespace-pre-wrap break-words rounded-lg bg-gray-50 p-4 text-sm leading-6 text-gray-600">
              {{ detailJob.description || '暂无岗位描述' }}
            </div>
          </div>

          <div class="mb-5">
            <h3 class="mb-2 font-semibold text-gray-700">匹配原因</h3>
            <ul class="space-y-2 text-sm text-gray-600">
              <li v-for="(reason, index) in detailJob.matchReasons" :key="index">
                {{ index + 1 }}. {{ reason }}
              </li>
            </ul>
          </div>

          <div class="mb-6 rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
            <div class="mb-1 flex items-center gap-2">
              <el-icon><Briefcase /></el-icon>
              <span>来源平台：{{ detailJob.sourceName }}</span>
            </div>
            <div class="flex items-center gap-2">
              <el-icon><Timer /></el-icon>
              <span>爬取时间：{{ formatDate(detailJob.crawlTime || detailJob.createdAt) }}</span>
            </div>
          </div>

          <div class="flex gap-3">
            <el-button
              type="primary"
              :icon="Position"
              :loading="applyingId === detailJob.id"
              :disabled="!detailJob.isActive || !currentResume"
              @click="handleApply(detailJob)"
            >
              记录投递
            </el-button>
            <el-button :icon="TopRight" :disabled="!detailJob.sourceUrl" @click="openSource(detailJob)">
              打开原站
            </el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Briefcase, Link, Position, Refresh, Timer, TopRight, Upload } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { jobApi } from '@/api/job'
import { resumeApi } from '@/api/resume'
import type { Job, Resume } from '@/types'
import type { JobPlatform, JobRecommendTask } from '@/api/types/job'

type SortKey = 'match' | 'salary' | 'date'
type FlowStatus = 'idle' | 'waiting_login' | 'crawling' | 'matching' | 'success' | 'failed' | 'need_login'

interface JobItem {
  id: number
  title: string
  company: string
  companyLogo?: string
  city: string
  salaryMin: number
  salaryMax: number
  experience: string
  education: string
  skills: string[]
  description: string
  matchScore: number
  matchReasons: string[]
  source?: string
  sourceName: string
  sourceUrl?: string
  isActive: boolean
  crawlTime?: string
  createdAt: string
}

const router = useRouter()

const resumes = ref<Resume[]>([])
const platforms = ref<JobPlatform[]>([])
const selectedResumeId = ref<number | null>(null)
const selectedSource = ref('')
const sortBy = ref<SortKey>('match')
const currentPage = ref(1)
const pageSize = ref(9)
const total = ref(0)
const isInitialLoading = ref(false)
const isStarting = ref(false)
const isPollingLogin = ref(false)
const isPollingTask = ref(false)
const isResultLoading = ref(false)
const isDetailLoading = ref(false)
const detailVisible = ref(false)
const applyingId = ref<number | null>(null)

const flowStatus = ref<FlowStatus>('idle')
const statusMessage = ref('')
const progress = ref(0)
const loginSessionId = ref('')
const taskId = ref('')
const extractedSkills = ref<string[]>([])
const recommendationStartRequested = ref(false)
const taskStats = reactive({
  totalFound: 0,
  totalSaved: 0,
  totalMatched: 0,
})

const jobs = ref<JobItem[]>([])
const detailJob = ref<JobItem | null>(null)
let loginPollTimer: number | undefined
let taskPollTimer: number | undefined

const currentResume = computed(() => {
  return resumes.value.find((resume) => resume.id === selectedResumeId.value) || null
})

const selectedPlatform = computed(() => {
  return platforms.value.find((platform) => platform.source === selectedSource.value) || null
})

const isBusy = computed(() => {
  return isStarting.value || ['waiting_login', 'crawling', 'matching'].includes(flowStatus.value)
})

const canStart = computed(() => {
  return Boolean(currentResume.value && selectedSource.value && selectedPlatform.value?.enabled && !isBusy.value)
})

const showTaskStatus = computed(() => {
  return flowStatus.value !== 'idle' || Boolean(taskId.value || loginSessionId.value)
})

const sortedJobs = computed(() => {
  return [...jobs.value].sort((a, b) => {
    if (sortBy.value === 'salary') {
      return b.salaryMax - a.salaryMax
    }
    if (sortBy.value === 'date') {
      return getTimeValue(b.crawlTime || b.createdAt) - getTimeValue(a.crawlTime || a.createdAt)
    }
    return b.matchScore - a.matchScore
  })
})

const startButtonText = computed(() => {
  if (flowStatus.value === 'waiting_login') return '等待登录'
  if (flowStatus.value === 'crawling' || flowStatus.value === 'matching') return '生成中'
  if (flowStatus.value === 'success' || flowStatus.value === 'failed' || flowStatus.value === 'need_login') return '重新生成推荐'
  return '登录并生成推荐'
})

const statusTitle = computed(() => {
  const titles: Record<FlowStatus, string> = {
    idle: '待开始',
    waiting_login: '等待登录',
    crawling: '采集中',
    matching: '匹配中',
    success: '已完成',
    failed: '失败',
    need_login: '需要登录',
  }
  return titles[flowStatus.value]
})

const statusTagType = computed(() => {
  if (flowStatus.value === 'success') return 'success'
  if (flowStatus.value === 'failed' || flowStatus.value === 'need_login') return 'danger'
  if (flowStatus.value === 'waiting_login') return 'warning'
  return 'info'
})

const progressStatus = computed(() => {
  if (flowStatus.value === 'success') return 'success'
  if (flowStatus.value === 'failed' || flowStatus.value === 'need_login') return 'exception'
  return undefined
})

onMounted(() => {
  loadInitialData()
})

onBeforeUnmount(() => {
  clearLoginPolling()
  clearTaskPolling()
})

async function loadInitialData() {
  isInitialLoading.value = true
  try {
    const [resumeResponse, platformResponse] = await Promise.all([
      resumeApi.getList({ page: 1, page_size: 20 }),
      jobApi.getPlatforms(),
    ])

    resumes.value = resumeResponse.data.items || []
    platforms.value = platformResponse.data.items || []

    const firstCompletedResume = resumes.value.find((resume) => resume.status === 'completed')
    selectedResumeId.value = firstCompletedResume?.id || resumes.value[0]?.id || null

    const firstEnabledPlatform = platforms.value.find((platform) => platform.enabled)
    selectedSource.value = selectedSource.value || firstEnabledPlatform?.source || ''
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载岗位推荐初始化数据失败'))
  } finally {
    isInitialLoading.value = false
  }
}

function goUploadResume() {
  router.push('/resume/upload')
}

async function handleStartFlow() {
  if (isBusy.value) return
  if (!currentResume.value) {
    ElMessage.warning('请先上传简历')
    goUploadResume()
    return
  }
  if (!selectedSource.value) {
    ElMessage.warning('请先选择招聘平台')
    return
  }
  if (!selectedPlatform.value?.enabled) {
    ElMessage.warning('该招聘平台暂未开放')
    return
  }

  resetRecommendationState()
  const loginWindow = window.open('', '_blank')
  if (loginWindow) {
    loginWindow.opener = null
  }
  isStarting.value = true
  flowStatus.value = 'waiting_login'
  statusMessage.value = '正在打开招聘平台登录页'
  progress.value = 5

  try {
    const response = await jobApi.startPlatformLogin({
      source: selectedSource.value,
      resume_id: currentResume.value.id,
    })
    const session = response.data
    loginSessionId.value = session.login_session_id
    statusMessage.value = '请完成招聘平台登录'
    progress.value = 10

    if (session.status === 'logged_in') {
      loginWindow?.close()
      await startRecommendationTask()
      return
    }

    if (session.login_url) {
      if (loginWindow) {
        loginWindow.location.href = session.login_url
        loginWindow.focus()
      } else {
        window.open(session.login_url, '_blank', 'noopener,noreferrer')
      }
    } else if (loginWindow) {
      loginWindow.close()
    }

    startLoginPolling()
  } catch (error: unknown) {
    loginWindow?.close()
    flowStatus.value = 'failed'
    statusMessage.value = getErrorMessage(error, '启动平台登录失败')
    progress.value = 0
  } finally {
    isStarting.value = false
  }
}

function startLoginPolling() {
  clearLoginPolling()
  pollLoginStatus()
  loginPollTimer = window.setInterval(pollLoginStatus, 3000)
}

function clearLoginPolling() {
  if (loginPollTimer) {
    window.clearInterval(loginPollTimer)
    loginPollTimer = undefined
  }
}

async function pollLoginStatus() {
  if (!loginSessionId.value || isPollingLogin.value) return
  isPollingLogin.value = true
  try {
    const response = await jobApi.getPlatformLoginStatus(loginSessionId.value)
    const loginStatus = response.data
    statusMessage.value = loginStatus.message || '等待用户完成登录'

    if (loginStatus.status === 'logged_in' || loginStatus.is_authenticated) {
      clearLoginPolling()
      await startRecommendationTask()
      return
    }

    if (loginStatus.status === 'expired' || loginStatus.status === 'failed') {
      clearLoginPolling()
      flowStatus.value = loginStatus.status === 'expired' ? 'need_login' : 'failed'
      statusMessage.value = loginStatus.message || '平台登录失败'
      progress.value = 0
    }
  } catch (error: unknown) {
    clearLoginPolling()
    flowStatus.value = 'failed'
    statusMessage.value = getErrorMessage(error, '查询登录状态失败')
    progress.value = 0
  } finally {
    isPollingLogin.value = false
  }
}

async function startRecommendationTask() {
  if (!currentResume.value || !loginSessionId.value) return
  if (recommendationStartRequested.value) return
  recommendationStartRequested.value = true
  clearLoginPolling()
  flowStatus.value = 'crawling'
  statusMessage.value = '正在启动岗位采集'
  progress.value = 20

  try {
    const response = await jobApi.startRecommendation({
      resume_id: currentResume.value.id,
      source: selectedSource.value,
      login_session_id: loginSessionId.value,
      limit: 50,
    })
    applyTaskState(response.data)
    startTaskPolling()
  } catch (error: unknown) {
    recommendationStartRequested.value = false
    flowStatus.value = 'failed'
    statusMessage.value = getErrorMessage(error, '启动岗位推荐任务失败')
    progress.value = 0
  }
}

function startTaskPolling() {
  clearTaskPolling()
  pollRecommendationTask()
  taskPollTimer = window.setInterval(pollRecommendationTask, 3000)
}

function clearTaskPolling() {
  if (taskPollTimer) {
    window.clearInterval(taskPollTimer)
    taskPollTimer = undefined
  }
}

async function pollRecommendationTask() {
  if (!taskId.value || isPollingTask.value) return
  isPollingTask.value = true
  try {
    const response = await jobApi.getRecommendationTask(taskId.value)
    applyTaskState(response.data)

    if (response.data.status === 'success') {
      clearTaskPolling()
      await loadRecommendationResults()
    }

    if (response.data.status === 'failed' || response.data.status === 'need_login') {
      clearTaskPolling()
    }
  } catch (error: unknown) {
    clearTaskPolling()
    flowStatus.value = 'failed'
    statusMessage.value = getErrorMessage(error, '查询推荐任务失败')
    progress.value = 0
  } finally {
    isPollingTask.value = false
  }
}

function applyTaskState(task: JobRecommendTask) {
  taskId.value = task.task_id || taskId.value
  flowStatus.value = normalizeTaskStatus(task.status)
  progress.value = Math.max(progress.value, task.progress ?? getFallbackProgress(task.status))
  extractedSkills.value = task.extracted_skills || extractedSkills.value
  taskStats.totalFound = task.total_found ?? taskStats.totalFound
  taskStats.totalSaved = task.total_saved ?? taskStats.totalSaved
  taskStats.totalMatched = task.total_matched ?? taskStats.totalMatched
  statusMessage.value = task.message || getDefaultStatusMessage(flowStatus.value)
}

function normalizeTaskStatus(status: JobRecommendTask['status']): FlowStatus {
  if (status === 'pending') return 'crawling'
  return status
}

function getFallbackProgress(status: JobRecommendTask['status']) {
  if (status === 'success') return 100
  if (status === 'matching') return 75
  if (status === 'crawling') return 45
  return progress.value
}

async function loadRecommendationResults() {
  if (!taskId.value) return
  isResultLoading.value = true
  try {
    const response = await jobApi.getRecommendationResults(taskId.value, {
      page: currentPage.value,
      page_size: pageSize.value,
    })
    jobs.value = (response.data.items || []).map((job) => normalizeJob(job))
    total.value = response.data.total || 0
    extractedSkills.value = response.data.extracted_skills || extractedSkills.value
    flowStatus.value = 'success'
    progress.value = 100
    statusMessage.value = '推荐岗位已生成'
  } catch (error: unknown) {
    flowStatus.value = 'failed'
    statusMessage.value = getErrorMessage(error, '加载推荐结果失败')
  } finally {
    isResultLoading.value = false
  }
}

function resetRecommendationState() {
  clearLoginPolling()
  clearTaskPolling()
  recommendationStartRequested.value = false
  loginSessionId.value = ''
  taskId.value = ''
  extractedSkills.value = []
  taskStats.totalFound = 0
  taskStats.totalSaved = 0
  taskStats.totalMatched = 0
  progress.value = 0
  total.value = 0
  currentPage.value = 1
  jobs.value = []
  detailJob.value = null
  detailVisible.value = false
}

function getTimeValue(value?: string) {
  if (!value) return 0
  const time = new Date(value).getTime()
  return Number.isNaN(time) ? 0 : time
}

function getSourceName(source?: string, sourceName?: string) {
  if (sourceName) return sourceName
  const sourceMap: Record<string, string> = {
    '58': '58同城',
    boss: 'BOSS直聘',
    lagou: '拉勾网',
    liepin: '猎聘',
  }
  return source ? sourceMap[source] || source : '招聘网站'
}

function normalizeJob(job: Job, fallback?: JobItem): JobItem {
  return {
    id: job.id,
    title: job.title || fallback?.title || '未命名岗位',
    company: job.company || fallback?.company || '未知公司',
    companyLogo: job.company_logo || fallback?.companyLogo,
    city: job.city || fallback?.city || '未知城市',
    salaryMin: job.salary_min || fallback?.salaryMin || 0,
    salaryMax: job.salary_max || fallback?.salaryMax || 0,
    experience: job.experience_required || fallback?.experience || '经验不限',
    education: job.education_required || fallback?.education || '学历不限',
    skills: job.skills || fallback?.skills || [],
    description: job.description || fallback?.description || '',
    matchScore: Math.max(0, Math.min(100, job.match_score ?? fallback?.matchScore ?? 0)),
    matchReasons: job.match_reasons || fallback?.matchReasons || [],
    source: job.source || fallback?.source,
    sourceName: getSourceName(job.source || fallback?.source, job.source_name || fallback?.sourceName),
    sourceUrl: job.source_url || job.url || fallback?.sourceUrl,
    isActive: job.is_active ?? fallback?.isActive ?? true,
    crawlTime: job.crawl_time || fallback?.crawlTime,
    createdAt: job.created_at || fallback?.createdAt || new Date().toISOString(),
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadRecommendationResults()
}

function handlePageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadRecommendationResults()
}

async function openDetail(id: number) {
  detailVisible.value = true
  const fallback = jobs.value.find((job) => job.id === id)
  detailJob.value = fallback || null
  isDetailLoading.value = true
  try {
    const response = await jobApi.getDetail(id)
    detailJob.value = normalizeJob(response.data, fallback)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载岗位详情失败'))
  } finally {
    isDetailLoading.value = false
  }
}

function openSource(job: JobItem) {
  if (!job.sourceUrl) {
    ElMessage.warning('暂无原始岗位链接')
    return
  }
  window.open(job.sourceUrl, '_blank', 'noopener,noreferrer')
}

async function handleApply(job: JobItem) {
  if (!currentResume.value) {
    ElMessage.warning('请先上传简历')
    return
  }
  applyingId.value = job.id
  try {
    await jobApi.apply(job.id, { resume_id: currentResume.value.id })
    ElMessage.success('投递意向已记录')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '记录投递意向失败'))
  } finally {
    applyingId.value = null
  }
}

function formatSalaryValue(value: number) {
  if (!value) return ''
  const salary = value >= 1000 ? Math.round(value / 1000) : value
  return `${salary}k`
}

function formatSalaryRange(job: JobItem) {
  const min = formatSalaryValue(job.salaryMin)
  const max = formatSalaryValue(job.salaryMax)
  if (min && max) return `${min}-${max}`
  if (min) return `${min}以上`
  if (max) return `${max}以下`
  return '薪资面议'
}

function formatDate(value?: string) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '暂无'
  return date.toLocaleDateString('zh-CN')
}

function getMatchColor(score: number): string {
  if (score >= 85) return '#10b981'
  if (score >= 70) return '#f59e0b'
  return '#ef4444'
}

function getResumeStatusText(status: Resume['status']) {
  const statusMap: Record<Resume['status'], string> = {
    pending: '待解析',
    analyzing: '解析中',
    completed: '已完成',
    failed: '解析失败',
  }
  return statusMap[status] || status
}

function getLoginStatusText(status: JobPlatform['login_status']) {
  const statusMap: Record<JobPlatform['login_status'], string> = {
    not_logged_in: '未登录',
    logged_in: '已登录',
    expired: '已过期',
    unknown: '未知',
  }
  return statusMap[status] || status
}

function getPlatformLabel(platform: JobPlatform) {
  return platform.enabled ? platform.name : `${platform.name}（暂未开放）`
}

function getDefaultStatusMessage(status: FlowStatus) {
  const messageMap: Record<FlowStatus, string> = {
    idle: '等待选择平台',
    waiting_login: '等待招聘平台登录',
    crawling: '正在采集岗位',
    matching: '正在计算匹配度',
    success: '推荐岗位已生成',
    failed: '推荐任务失败',
    need_login: '登录态已失效',
  }
  return messageMap[status]
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error && typeof error === 'object') {
    const response = (error as { response?: { data?: { message?: unknown } } }).response
    if (typeof response?.data?.message === 'string') {
      return response.data.message
    }
    const message = (error as { message?: unknown }).message
    if (typeof message === 'string') {
      return message
    }
  }
  return fallback
}
</script>

<style scoped>
.job-list-view :deep(.el-card) {
  border-radius: 8px;
}

.workflow-card {
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.job-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.job-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08) !important;
}

:deep(.el-button--primary) {
  border-radius: 8px;
  font-weight: 500;
}
</style>
