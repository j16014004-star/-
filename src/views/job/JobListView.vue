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

          <template v-if="currentResumeOption">
            <el-select
              v-model="selectedResumeKey"
              class="w-full"
              :disabled="isBusy"
              placeholder="选择原始简历或优化简历"
              @change="handleResumeChange"
            >
              <el-option-group v-if="originalResumeOptions.length" label="原始简历">
                <el-option
                  v-for="resume in originalResumeOptions"
                  :key="resume.key"
                  :label="resume.title"
                  :value="resume.key"
                />
              </el-option-group>
              <el-option-group v-if="optimizedResumeOptions.length" label="优化简历">
                <el-option
                  v-for="resume in optimizedResumeOptions"
                  :key="resume.key"
                  :label="resume.title"
                  :value="resume.key"
                />
              </el-option-group>
            </el-select>
            <div class="flex flex-wrap items-center gap-2">
              <span class="mt-3 font-medium text-gray-800">{{ currentResumeOption.title }}</span>
              <el-tag size="small" :type="currentResumeOption.source === 'optimized' ? 'primary' : 'success'" effect="plain">
                {{ currentResumeOption.source === 'optimized' ? '优化简历' : '原始简历' }}
              </el-tag>
            </div>
            <div class="mt-2 text-sm text-gray-500">
              {{ currentResumeOption.source === 'optimized' ? '保存时间' : '上传时间' }}：{{ formatDate(currentResumeOption.createdAt) }}
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
              :disabled="!currentResumeOption || isBusy"
              placeholder="选择平台"
              filterable
              @change="handlePlatformChange"
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

          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <div>
              <div class="mb-2 flex items-center justify-between gap-2 text-sm text-gray-600">
                <span>具体岗位 <span class="text-red-500">*</span></span>
                <el-button
                  link
                  type="primary"
                  :disabled="isBusy"
                  @click="openCustomRoleDialog"
                >
                  + 新增自定义岗位
                </el-button>
              </div>
              <el-select
                v-model="selectedTargetRole"
                class="w-full"
                :disabled="isBusy"
                filterable
                allow-create
                default-first-option
                clearable
                reserve-keyword
                placeholder="选择岗位，或输入新岗位后按回车"
                no-data-text="按回车添加该自定义岗位"
                @change="handleTargetRoleChange"
              >
                <el-option v-for="role in targetRoleOptions" :key="role" :label="role" :value="role" />
              </el-select>
              <div class="mt-1 text-xs text-gray-400">支持搜索、下拉选择，也可以直接输入任意岗位名称。</div>
            </div>
            <div>
              <div class="mb-2 text-sm text-gray-600">目标城市 <span class="text-red-500">*</span></div>
              <el-select
                v-model="selectedCity"
                class="w-full"
                :disabled="isBusy"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="选择或输入目标城市"
                @change="handleIntentChange"
              >
                <el-option v-for="city in cityOptions" :key="city" :label="city" :value="city" />
              </el-select>
              <div class="mt-1 text-xs text-gray-400">请选择招聘平台支持的城市。</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="showTaskStatus" class="mt-5 rounded-lg border border-gray-100 bg-gray-50 p-4">
        <el-alert
          v-if="flowStatus === 'need_login'"
          title="58同城登录状态已经失效，请点击下方“重新登录并推荐”后继续。"
          type="error"
          :closable="false"
          show-icon
          class="mb-4"
        />
        <el-alert
          v-if="flowStatus === 'waiting_login'"
          title="登录窗口由后端受控浏览器打开，请在那里完成扫码、验证码或登录操作；不要另开普通浏览器标签登录。"
          type="warning"
          :closable="false"
          show-icon
          class="mb-4"
        />
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <el-tag :type="statusTagType" effect="light">{{ statusTitle }}</el-tag>
            <span class="text-sm text-gray-600">{{ statusMessage }}</span>
            <el-tag v-if="failureCode" size="small" type="danger" effect="plain">{{ failureCode }}</el-tag>
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

        <div v-if="searchKeywords.length" class="mt-4 text-xs text-gray-500">
          <span class="font-medium">搜索关键词：</span>{{ searchKeywords.join('、') }}
        </div>

        <el-collapse v-if="hasCrawlDiagnostics" class="mt-3">
          <el-collapse-item title="采集诊断信息" name="diagnostics">
            <div class="grid gap-2 text-xs text-gray-500 sm:grid-cols-3">
              <span>查询次数：{{ crawlDiagnostics.query_count || 0 }}</span>
              <span>源站岗位：{{ crawlDiagnostics.raw_items || 0 }}</span>
              <span>解析成功：{{ crawlDiagnostics.parsed_items || 0 }}</span>
              <span>最终接受：{{ crawlDiagnostics.accepted_items || 0 }}</span>
              <span>无效数据：{{ crawlDiagnostics.invalid_items || 0 }}</span>
              <span>重复数据：{{ crawlDiagnostics.duplicate_items || 0 }}</span>
            </div>
          </el-collapse-item>
        </el-collapse>
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

            <div class="mb-4 line-clamp-3 min-h-12 text-xs leading-5 text-gray-500">
              {{ job.description || '点击“工作详情”查看完整岗位要求。' }}
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
                :disabled="!job.isActive || !currentResumeOption"
                @click="handleAiApply(job)"
              >
                AI 帮你投
              </el-button>
              <el-button size="small" @click="openDetail(job.id)">工作详情</el-button>
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
      v-else-if="flowStatus === 'no_results'"
      :description="statusMessage || '当前条件暂无精准岗位，请调整目标岗位或城市后重试'"
      class="py-16"
    />

    <el-empty
      v-else-if="!showTaskStatus && !currentResumeOption"
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
              :disabled="!detailJob.isActive || !currentResumeOption"
              @click="handleAiApply(detailJob)"
            >
              AI 帮你投
            </el-button>
            <el-button :icon="TopRight" :disabled="!detailJob.sourceUrl" @click="openSource(detailJob)">
              打开原站
            </el-button>
          </div>
        </template>
      </div>
    </el-drawer>

    <el-dialog
      v-model="customRoleDialogVisible"
      title="新增自定义岗位"
      width="440px"
      destroy-on-close
      @closed="customRoleInput = ''"
    >
      <el-input
        v-model="customRoleInput"
        maxlength="100"
        show-word-limit
        clearable
        autofocus
        placeholder="例如：大模型应用开发工程师"
        @keyup.enter="confirmCustomRole"
      />
      <div class="mt-2 text-xs text-gray-400">保存后会自动选中，并按该岗位生成推荐。</div>
      <template #footer>
        <el-button @click="customRoleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmCustomRole">添加并选中</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Briefcase, Link, Position, Refresh, Timer, TopRight, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { jobApi } from '@/api/job'
import { hrApi } from '@/api/hr'
import { resumeApi } from '@/api/resume'
import type { Job, Resume, ResumeOptimizeResult } from '@/types'
import type { JobCrawlDiagnostics, JobPlatform, JobRecommendTask, JobResumeSource } from '@/api/types/job'

type SortKey = 'match' | 'salary' | 'date'
type FlowStatus = 'idle' | 'waiting_login' | 'pending' | 'crawling' | 'matching' | 'success' | 'no_results' | 'failed' | 'need_login'

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

interface RecommendationResumeOption {
  key: string
  source: JobResumeSource
  resumeId: number
  optimizationId?: number
  title: string
  createdAt?: string
}

const router = useRouter()

const resumes = ref<Resume[]>([])
const savedOptimizations = ref<ResumeOptimizeResult[]>([])
const platforms = ref<JobPlatform[]>([])
const selectedResumeKey = ref('')
const selectedSource = ref('')
const selectedTargetRole = ref('')
const selectedCity = ref('北京')
const customTargetRoles = ref<string[]>([])
const customRoleDialogVisible = ref(false)
const customRoleInput = ref('')
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
const isBackgroundChecking = ref(false)
const detailVisible = ref(false)
const applyingId = ref<number | null>(null)

const flowStatus = ref<FlowStatus>('idle')
const statusMessage = ref('')
const progress = ref(0)
const loginSessionId = ref('')
const taskId = ref('')
const extractedSkills = ref<string[]>([])
const searchKeywords = ref<string[]>([])
const failureCode = ref<string | null>(null)
const crawlDiagnostics = reactive<JobCrawlDiagnostics>({})
const taskStats = reactive({
  totalFound: 0,
  totalSaved: 0,
  totalMatched: 0,
})

const jobs = ref<JobItem[]>([])
const detailJob = ref<JobItem | null>(null)
let loginPollTimer: number | undefined
let taskPollTimer: number | undefined
let backgroundStatusTimer: number | undefined

const defaultTargetRoleOptions = [
  'Python后端开发工程师', 'Java开发工程师', 'Web前端开发工程师', '数据分析师',
  '产品经理', '测试工程师', '运维工程师', '秘书', '文秘', '行政助理',
  '办公室文员', '经理助理', '厨师',
]
const cityOptions = [
  '北京', '上海', '广州', '深圳', '杭州', '成都', '西安', '武汉', '南京', '重庆',
  '苏州', '天津', '郑州', '东莞', '青岛', '沈阳', '宁波', '昆明', '大连', '长沙',
]

const originalResumeOptions = computed<RecommendationResumeOption[]>(() => {
  return resumes.value
    .filter((resume) => resume.status === 'completed')
    .map((resume) => ({
      key: `original:${resume.id}`,
      source: 'original',
      resumeId: resume.id,
      title: resume.title || `原始简历 ${resume.id}`,
      createdAt: resume.created_at,
    }))
})

const optimizedResumeOptions = computed<RecommendationResumeOption[]>(() => {
  return savedOptimizations.value
    .filter((resume) => Number(resume.id) > 0 && Number(resume.resume_id) > 0)
    .map((resume) => ({
      key: `optimized:${resume.id}`,
      source: 'optimized',
      resumeId: Number(resume.resume_id),
      optimizationId: Number(resume.id),
      title: resume.title || `优化简历 ${resume.id}`,
      createdAt: resume.saved_at || resume.created_at,
    }))
})

const allResumeOptions = computed(() => [...originalResumeOptions.value, ...optimizedResumeOptions.value])

const currentResumeOption = computed(() => {
  return allResumeOptions.value.find((resume) => resume.key === selectedResumeKey.value) || null
})

const selectedPlatform = computed(() => {
  return platforms.value.find((platform) => platform.source === selectedSource.value) || null
})

const targetRoleOptions = computed(() => {
  const selectedRole = selectedTargetRole.value.trim()
  return Array.from(new Set([
    ...defaultTargetRoleOptions,
    ...customTargetRoles.value,
    ...(selectedRole ? [selectedRole] : []),
  ]))
})

const isBusy = computed(() => {
  return isStarting.value || ['waiting_login', 'pending', 'crawling', 'matching'].includes(flowStatus.value)
})

const canStart = computed(() => {
  return Boolean(
    currentResumeOption.value
      && selectedSource.value
      && selectedPlatform.value?.enabled
      && selectedTargetRole.value.trim()
      && selectedCity.value
      && !isBusy.value,
  )
})

const showTaskStatus = computed(() => {
  return flowStatus.value !== 'idle' || Boolean(taskId.value || loginSessionId.value)
})

const hasCrawlDiagnostics = computed(() => Object.values(crawlDiagnostics).some((value) => typeof value === 'number' && value > 0))

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
  if (flowStatus.value === 'pending' || flowStatus.value === 'crawling' || flowStatus.value === 'matching') return '生成中'
  if (flowStatus.value === 'need_login') return '重新登录并推荐'
  if (['success', 'no_results', 'failed'].includes(flowStatus.value)) return '重新抓取最新岗位'
  return '登录并生成推荐'
})

const RECOMMENDATION_STALE_MINUTES = 15

const statusTitle = computed(() => {
  const titles: Record<FlowStatus, string> = {
    idle: '待开始',
    waiting_login: '等待登录',
    pending: '等待执行',
    crawling: '采集中',
    matching: '匹配中',
    success: '已完成',
    no_results: '暂无结果',
    failed: '失败',
    need_login: '需要登录',
  }
  return titles[flowStatus.value]
})

const statusTagType = computed(() => {
  if (flowStatus.value === 'success') return 'success'
  if (flowStatus.value === 'no_results') return 'warning'
  if (flowStatus.value === 'failed' || flowStatus.value === 'need_login') return 'danger'
  if (flowStatus.value === 'waiting_login') return 'warning'
  return 'info'
})

const progressStatus = computed(() => {
  if (flowStatus.value === 'success') return 'success'
  if (flowStatus.value === 'no_results') return 'warning'
  if (flowStatus.value === 'failed' || flowStatus.value === 'need_login') return 'exception'
  return undefined
})

onMounted(() => {
  loadInitialData()
  backgroundStatusTimer = window.setInterval(checkBackgroundStatus, 30000)
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onBeforeUnmount(() => {
  clearLoginPolling()
  clearTaskPolling()
  if (backgroundStatusTimer) window.clearInterval(backgroundStatusTimer)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})

async function loadInitialData() {
  isInitialLoading.value = true
  try {
    const [resumeResponse, savedOptimizationResponse, platformResponse] = await Promise.all([
      resumeApi.getList({ page: 1, page_size: 100 }),
      resumeApi.getSavedOptimizations({ page: 1, page_size: 100 }).catch(() => null),
      jobApi.getPlatforms(),
    ])

    resumes.value = resumeResponse.data.items || []
    savedOptimizations.value = savedOptimizationResponse?.data.items || []
    platforms.value = platformResponse.data.items || []

    const firstResume = optimizedResumeOptions.value[0] || originalResumeOptions.value[0]
    if (!allResumeOptions.value.some((resume) => resume.key === selectedResumeKey.value)) {
      selectedResumeKey.value = firstResume?.key || ''
    }

    const firstEnabledPlatform = platforms.value.find((platform) => platform.enabled)
    selectedSource.value = selectedSource.value || firstEnabledPlatform?.source || ''
    await restoreCurrentTask()
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载岗位推荐初始化数据失败'))
  } finally {
    isInitialLoading.value = false
  }
}

async function restoreCurrentTask() {
  const selectedResume = currentResumeOption.value
  if (!selectedResume || !selectedSource.value) return
  try {
    const response = await jobApi.getCurrentRecommendation({
      resume_id: selectedResume.resumeId,
      resume_source: selectedResume.source,
      resume_optimization_id: selectedResume.optimizationId,
      source: selectedSource.value,
    })
    const task = response.data.task
    if (!task) return
    applyTaskState(task)
    selectedTargetRole.value = task.target_role || selectedTargetRole.value
    selectedCity.value = task.target_city || selectedCity.value
    if (task.status === 'need_login') {
      const platform = platforms.value.find((item) => item.source === selectedSource.value)
      if (platform) platform.login_status = 'expired'
      ElMessage.warning('58同城登录状态已失效，请重新登录后拉取最新岗位')
    }
    if (task.status === 'success' || task.status === 'no_results') {
      await loadRecommendationResults()
      if (isRecommendationStale(task)) {
        statusMessage.value = `岗位结果已超过${RECOMMENDATION_STALE_MINUTES}分钟，建议重新抓取最新岗位`
        ElMessage.warning(statusMessage.value)
      }
    } else if (['pending', 'crawling', 'matching'].includes(task.status)) {
      startTaskPolling()
    }
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '恢复岗位推荐任务失败'))
  }
}

async function checkBackgroundStatus() {
  const selectedResume = currentResumeOption.value
  if (document.hidden || isBackgroundChecking.value || !selectedResume || !selectedSource.value) return
  isBackgroundChecking.value = true
  try {
    const [platformResponse, taskResponse] = await Promise.all([
      jobApi.getPlatforms(),
      jobApi.getCurrentRecommendation({
        resume_id: selectedResume.resumeId,
        resume_source: selectedResume.source,
        resume_optimization_id: selectedResume.optimizationId,
        source: selectedSource.value,
      }),
    ])
    platforms.value = platformResponse.data.items || platforms.value
    const platform = platforms.value.find((item) => item.source === selectedSource.value)
    const latestTask = taskResponse.data.task
    if (latestTask && latestTask.task_id !== taskId.value) {
      applyTaskState(latestTask)
      if (['pending', 'crawling', 'matching'].includes(latestTask.status)) startTaskPolling()
      else if (latestTask.status === 'success' || latestTask.status === 'no_results') await loadRecommendationResults()
    }
    if (platform?.login_status === 'expired' && flowStatus.value !== 'waiting_login') {
      const wasNeedLogin = flowStatus.value === 'need_login'
      flowStatus.value = 'need_login'
      statusMessage.value = '58同城登录状态已失效，请重新登录后拉取最新岗位'
      if (!wasNeedLogin) ElMessage.warning(statusMessage.value)
    }
  } catch {
    // 后台状态探测失败不打断用户当前页面，下个周期自动重试。
  } finally {
    isBackgroundChecking.value = false
  }
}

async function handleResumeChange() {
  resetRecommendationState()
  await restoreCurrentTask()
}

async function handlePlatformChange() {
  resetRecommendationState()
  await restoreCurrentTask()
}

function handleIntentChange() {
  if (!isBusy.value) resetRecommendationState()
}

function handleTargetRoleChange(value: string) {
  const normalizedRole = value?.trim() || ''
  selectedTargetRole.value = normalizedRole
  if (normalizedRole && !defaultTargetRoleOptions.includes(normalizedRole) && !customTargetRoles.value.includes(normalizedRole)) {
    customTargetRoles.value.push(normalizedRole)
    ElMessage.success(`已添加自定义岗位“${normalizedRole}”`)
  }
  handleIntentChange()
}

function openCustomRoleDialog() {
  customRoleInput.value = ''
  customRoleDialogVisible.value = true
}

function confirmCustomRole() {
  const role = customRoleInput.value.trim()
  if (!role) {
    ElMessage.warning('请输入自定义岗位名称')
    return
  }
  if (role.length > 100) {
    ElMessage.warning('目标岗位不能超过 100 个字符')
    return
  }
  selectedTargetRole.value = role
  if (!defaultTargetRoleOptions.includes(role) && !customTargetRoles.value.includes(role)) {
    customTargetRoles.value.push(role)
  }
  customRoleDialogVisible.value = false
  handleIntentChange()
  ElMessage.success(`已选择自定义岗位“${role}”`)
}

function goUploadResume() {
  router.push('/resume/upload')
}

async function handleStartFlow() {
  if (isBusy.value) return
  const forceRefresh = Boolean(taskId.value)
    && !['waiting_login', 'pending', 'crawling', 'matching'].includes(flowStatus.value)
  const selectedResume = currentResumeOption.value
  if (!selectedResume) {
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
  if (!selectedTargetRole.value.trim()) {
    ElMessage.warning('请选择或输入目标岗位')
    return
  }
  if (selectedTargetRole.value.trim().length > 100) {
    ElMessage.warning('目标岗位不能超过 100 个字符')
    return
  }
  if (!selectedCity.value) {
    ElMessage.warning('请选择目标城市')
    return
  }

  resetRecommendationState()
  isStarting.value = true
  flowStatus.value = 'waiting_login'
  statusMessage.value = '正在启动平台登录与岗位推荐'
  progress.value = 5

  try {
    const response = await jobApi.startPlatformLogin({
      source: selectedSource.value,
      resume_id: selectedResume.resumeId,
      resume_source: selectedResume.source,
      resume_optimization_id: selectedResume.optimizationId,
      target_role: selectedTargetRole.value.trim(),
      target_city: selectedCity.value,
      limit: 20,
      force_refresh: forceRefresh,
    })
    const session = response.data
    loginSessionId.value = session.login_session_id
    taskId.value = session.recommend_task_id || ''
    if (session.status === 'waiting_login' && session.browser_url) {
      window.open(session.browser_url, '_blank', 'noopener,noreferrer')
    }
    statusMessage.value = session.status === 'logged_in'
      ? '已检测到登录态，正在生成岗位推荐'
      : session.login_mode === 'remote_browser'
        ? '请在新打开的远程受控浏览器中完成58同城登录'
        : '请在后端弹出的受控浏览器中完成58同城登录'
    progress.value = 10

    if (session.status === 'logged_in') {
      if (taskId.value) startTaskPolling()
      else {
        flowStatus.value = 'failed'
        statusMessage.value = '登录已成功，但后端没有返回推荐任务 ID'
      }
      return
    }

    if (session.status === 'waiting_login') {
      startLoginPolling()
    } else {
      flowStatus.value = session.status === 'expired' ? 'need_login' : 'failed'
      statusMessage.value = session.error_message || '招聘平台登录启动失败'
      progress.value = 0
    }
  } catch (error: unknown) {
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
  if (!loginSessionId.value || isPollingLogin.value || document.hidden) return
  isPollingLogin.value = true
  try {
    const response = await jobApi.getPlatformLoginStatus(loginSessionId.value)
    const loginStatus = response.data
    taskId.value = loginStatus.recommend_task_id || taskId.value
    statusMessage.value = loginStatus.error_message || '等待用户在后端弹出的浏览器中完成登录'

    if (loginStatus.status === 'logged_in') {
      clearLoginPolling()
      if (taskId.value) startTaskPolling()
      else {
        flowStatus.value = 'failed'
        statusMessage.value = '登录已成功，但后端没有返回推荐任务 ID'
      }
      return
    }

    if (loginStatus.status === 'expired' || loginStatus.status === 'failed') {
      clearLoginPolling()
      flowStatus.value = loginStatus.status === 'expired' ? 'need_login' : 'failed'
      statusMessage.value = loginStatus.error_message || '平台登录失败'
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
  if (!taskId.value || isPollingTask.value || document.hidden) return
  isPollingTask.value = true
  try {
    const response = await jobApi.getRecommendationTask(taskId.value)
    applyTaskState(response.data)

    if (response.data.status === 'success' || response.data.status === 'no_results') {
      clearTaskPolling()
      await loadRecommendationResults()
    }

    if (response.data.status === 'failed' || response.data.status === 'need_login') {
      clearTaskPolling()
      if (response.data.status === 'need_login') {
        const platform = platforms.value.find((item) => item.source === selectedSource.value)
        if (platform) platform.login_status = 'expired'
        ElMessage.warning('58同城登录状态已失效，请重新登录后继续推荐')
      }
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
  searchKeywords.value = task.search_keywords || searchKeywords.value
  failureCode.value = task.failure_code || null
  Object.keys(crawlDiagnostics).forEach((key) => delete crawlDiagnostics[key])
  Object.assign(crawlDiagnostics, task.crawl_diagnostics || {})
  taskStats.totalFound = task.total_found ?? taskStats.totalFound
  taskStats.totalSaved = task.total_saved ?? taskStats.totalSaved
  taskStats.totalMatched = task.total_matched ?? taskStats.totalMatched
  selectedTargetRole.value = task.target_role || selectedTargetRole.value
  selectedCity.value = task.target_city || selectedCity.value
  statusMessage.value = task.error_message || getFailureMessage(task.failure_code) || getDefaultStatusMessage(flowStatus.value)
}

function normalizeTaskStatus(status: JobRecommendTask['status']): FlowStatus {
  return status
}

function getFallbackProgress(status: JobRecommendTask['status']) {
  if (status === 'success' || status === 'no_results') return 100
  if (status === 'matching') return 75
  if (status === 'crawling') return 45
  if (status === 'pending') return 15
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
    searchKeywords.value = response.data.search_keywords || searchKeywords.value
    flowStatus.value = response.data.total > 0 ? 'success' : 'no_results'
    progress.value = 100
    statusMessage.value = response.data.total > 0
      ? '推荐岗位已生成'
      : getFailureMessage(failureCode.value) || '当前目标岗位和城市暂无精准岗位，请调整条件后重试'
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
  loginSessionId.value = ''
  taskId.value = ''
  extractedSkills.value = []
  searchKeywords.value = []
  failureCode.value = null
  Object.keys(crawlDiagnostics).forEach((key) => delete crawlDiagnostics[key])
  taskStats.totalFound = 0
  taskStats.totalSaved = 0
  taskStats.totalMatched = 0
  progress.value = 0
  total.value = 0
  currentPage.value = 1
  jobs.value = []
  detailJob.value = null
  detailVisible.value = false
  flowStatus.value = 'idle'
  statusMessage.value = ''
}

function handleVisibilityChange() {
  if (document.hidden) {
    clearLoginPolling()
    clearTaskPolling()
    return
  }
  if (flowStatus.value === 'waiting_login' && loginSessionId.value) {
    startLoginPolling()
  } else if (['pending', 'crawling', 'matching'].includes(flowStatus.value) && taskId.value) {
    startTaskPolling()
  }
}

function getTimeValue(value?: string) {
  if (!value) return 0
  const time = new Date(value).getTime()
  return Number.isNaN(time) ? 0 : time
}

function isRecommendationStale(task: JobRecommendTask) {
  const completedAt = getTimeValue(task.finished_at || task.created_at)
  return completedAt > 0
    && Date.now() - completedAt >= RECOMMENDATION_STALE_MINUTES * 60 * 1000
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

async function handleAiApply(job: JobItem) {
  const selectedResume = currentResumeOption.value
  if (!selectedResume) {
    ElMessage.warning('请先上传简历')
    return
  }
  const source = job.source || selectedSource.value
  if (!source) {
    ElMessage.warning('当前岗位缺少招聘平台信息，无法启动 AI 投递')
    return
  }
  applyingId.value = job.id
  try {
    const response = await hrApi.checkPreflight({ job_id: job.id, source })
    if (!response.data.can_start || !response.data.manual_login_verified) {
      const platform = platforms.value.find((item) => item.source === source)
      if (platform) platform.login_status = response.data.platform_login_status
      await ElMessageBox.alert(
        response.data.reason || `请先在后端打开的${response.data.source_name || '招聘平台'}受控浏览器中，由你本人手动完成登录。登录成功后才能启动自动投递。`,
        '需要先手动登录第三方网站',
        { type: 'warning', confirmButtonText: '我知道了' },
      )
      return
    }
    if (
      response.data.next_action === 'resume_communication'
      && response.data.workspace_id
    ) {
      ElMessage.info('该岗位已申请，正在进入 HR 沟通')
      await router.push({
        path: '/hr',
        query: { workspace_id: String(response.data.workspace_id) },
      })
      return
    }
    const workspaceResponse = await hrApi.createWorkspace({
      job_id: job.id,
      source,
      resume_id: selectedResume.resumeId,
      resume_source: selectedResume.source,
      resume_optimization_id: selectedResume.optimizationId,
      automation_mode: 'full_auto',
      permissions: {
        auto_apply: true,
        auto_greeting: true,
        auto_reply: true,
        auto_schedule_interview: true,
      },
      manual_login_confirmed: true,
    })
    ElMessage.success('AI 一键投递已启动，正在进入 HR 助手')
    await router.push({
      path: '/hr',
      query: { workspace_id: String(workspaceResponse.data.id) },
    })
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '检查第三方平台登录状态失败'))
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

function getLoginStatusText(status: JobPlatform['login_status']) {
  const statusMap: Record<JobPlatform['login_status'], string> = {
    not_logged_in: '未登录',
    waiting_login: '等待登录',
    logged_in: '已登录',
    expired: '已过期',
    failed: '登录失败',
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
    pending: '推荐任务已创建，等待执行',
    crawling: '正在采集岗位',
    matching: '正在计算匹配度',
    success: '推荐岗位已生成',
    no_results: '当前条件暂无精准岗位',
    failed: '推荐任务失败',
    need_login: '登录态已失效',
  }
  return messageMap[status]
}

function getFailureMessage(code?: string | null) {
  if (!code) return ''
  const messages: Record<string, string> = {
    no_exact_results: '源站没有找到当前岗位方向的精准结果，请调整目标岗位或城市后重试',
    no_matching_jobs: '已采集到岗位，但没有符合当前岗位方向的结果，请调整目标岗位',
    parse_failed: '招聘平台页面结构可能发生变化，岗位解析失败，请稍后重试',
    crawl_failed: '岗位采集遇到网络、浏览器或源站异常，请重新开始',
    network_access_denied: '运行环境无法访问58同城，请放行Python/Chromium网络后重试',
  }
  return messages[code] || `推荐任务失败（${code}）`
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error && typeof error === 'object') {
    const response = (error as { response?: { data?: { message?: unknown; detail?: unknown } } }).response
    if (typeof response?.data?.detail === 'string') {
      return response.data.detail
    }
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
