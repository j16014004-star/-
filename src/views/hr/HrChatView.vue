<template>
  <div v-loading="initialLoading" class="min-h-screen bg-gray-50 p-6">
    <div class="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">HR 助手</h1>
        <p class="mt-1 text-sm text-gray-500">集中查看第三方招聘平台上的投递、HR 沟通和面试安排</p>
      </div>
      <el-button :icon="Refresh" :loading="initialLoading" @click="refreshPage">刷新状态</el-button>
    </div>

    <el-alert
      title="所有自动投递、自动沟通和自动约面试，必须在你本人手动登录第三方招聘网站后才能开始。"
      description="前端每次创建任务都会重新校验平台登录状态；登录过期后 Agent 会立即暂停，不会绕过登录继续操作。"
      type="warning"
      show-icon
      :closable="false"
      class="mb-6"
    />

    <el-card v-if="candidateJob" class="mb-6 border-0" shadow="never">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-semibold text-gray-800">确认 AI 投递设置</div>
            <div class="mt-1 text-xs text-gray-400">确认后创建工作区；全自动模式会按授权直接投递，敏感事项仍需二次确认</div>
          </div>
          <el-tag :type="preflight?.can_start ? 'success' : 'danger'" effect="plain">
            {{ preflight?.can_start ? '已确认本人登录' : '等待本人登录' }}
          </el-tag>
        </div>
      </template>

      <div class="grid gap-5 lg:grid-cols-[1fr_1.2fr]">
        <div class="rounded-xl bg-gray-50 p-5">
          <div class="mb-2 text-lg font-semibold text-gray-800">{{ candidateJob.title }}</div>
          <div class="text-sm text-gray-500">{{ candidateJob.company }} · {{ candidateJob.city }}</div>
          <div class="mt-4 text-xl font-bold text-indigo-600">{{ candidateSalary }}</div>
          <div class="mt-4 flex flex-wrap gap-2">
            <el-tag effect="plain">{{ preflight?.source_name || candidateJob.source_name || candidateJob.source || '招聘平台' }}</el-tag>
            <el-tag type="info" effect="plain">{{ candidateResumeText }}</el-tag>
          </div>
          <el-button class="mt-5" :icon="TopRight" :disabled="!candidateJob.source_url && !candidateJob.url" @click="openCandidateSource">
            查看第三方原站
          </el-button>
        </div>

        <div>
          <el-alert
            v-if="preflight && !preflight.can_start"
            :title="preflight.reason || '请先由你本人完成第三方平台登录'"
            type="error"
            :closable="false"
            show-icon
            class="mb-4"
          />

          <div class="mb-3 font-medium text-gray-700">选择操作模式</div>
          <el-radio-group v-model="setupMode" class="mode-group mb-5" @change="applyModeDefaults">
            <el-radio-button value="full_auto">AI 全自动</el-radio-button>
            <el-radio-button value="assisted">AI 辅助确认</el-radio-button>
            <el-radio-button value="manual">用户手动</el-radio-button>
          </el-radio-group>

          <div class="mb-3 font-medium text-gray-700">授权范围</div>
          <el-checkbox v-model="setupPermissions.auto_apply" :disabled="setupMode === 'manual'">自动投递简历</el-checkbox>
          <el-checkbox v-model="setupPermissions.auto_greeting" :disabled="setupMode === 'manual'">自动发送首次招呼</el-checkbox>
          <el-checkbox v-model="setupPermissions.auto_reply" :disabled="setupMode !== 'full_auto'">自动回复常规问题</el-checkbox>
          <el-checkbox v-model="setupPermissions.auto_schedule_interview" :disabled="setupMode !== 'full_auto'">在授权时间内协调面试</el-checkbox>

          <div class="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4">
            <el-checkbox v-model="manualLoginAcknowledged">
              我确认第三方招聘网站是由我本人手动登录，并授权按以上范围执行
            </el-checkbox>
            <div class="mt-2 text-xs leading-5 text-amber-700">薪资承诺、隐私信息、Offer、付费操作等高风险事项始终需要用户再次确认。</div>
          </div>

          <div class="mt-5 flex justify-end gap-3">
            <el-button @click="cancelCandidate">暂不投递</el-button>
            <el-button
              type="primary"
              :loading="creatingWorkspace"
              :disabled="!canCreateWorkspace"
              @click="createWorkspace"
            >
              确认并进入 HR 助手
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <el-empty v-if="!candidateJob && !workspaces.length && !initialLoading" description="还没有投递工作区">
      <el-button type="primary" @click="router.push('/jobs')">前往岗位推荐</el-button>
    </el-empty>

    <div v-else-if="workspaces.length" class="grid min-h-[650px] gap-5 lg:grid-cols-[320px_1fr]">
      <el-card class="border-0" shadow="never" body-style="padding: 0">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold">投递工作区</span>
            <el-badge :value="hrStore.overview.unread_messages" :hidden="!hrStore.overview.unread_messages" />
          </div>
        </template>
        <div class="max-h-[720px] overflow-y-auto">
          <button
            v-for="item in workspaces"
            :key="item.id"
            type="button"
            class="workspace-item w-full border-b border-gray-100 p-4 text-left"
            :class="{ active: selectedWorkspaceId === item.id }"
            @click="selectWorkspace(item.id)"
          >
            <div class="flex items-start justify-between gap-2">
              <span class="line-clamp-1 font-medium text-gray-800">{{ item.job_title }}</span>
              <el-badge :value="item.unread_count" :hidden="!item.unread_count" />
            </div>
            <div class="mt-1 text-xs text-gray-500">{{ item.company }} · {{ item.source_name }}</div>
            <div class="mt-3 flex items-center justify-between gap-2">
              <el-tag size="small" :type="workspaceStatusType(item.status)" effect="plain">{{ workspaceStatusText(item.status) }}</el-tag>
              <span class="text-xs text-gray-400">{{ formatTime(item.updated_at) }}</span>
            </div>
          </button>
        </div>
      </el-card>

      <el-card v-if="workspace" class="border-0" shadow="never">
        <template #header>
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="text-lg font-semibold text-gray-800">{{ workspace.job_title }}</h2>
                <el-tag :type="workspaceStatusType(workspace.status)">{{ workspaceStatusText(workspace.status) }}</el-tag>
              </div>
              <div class="mt-1 text-sm text-gray-500">{{ workspace.company }} · {{ workspace.source_name }} · {{ workspace.hr_name || '等待获取 HR 信息' }}</div>
            </div>
            <el-button :icon="TopRight" :disabled="!workspace.source_url" @click="openWorkspaceSource">第三方原站</el-button>
          </div>
        </template>

        <el-alert
          v-if="workspace.platform_login_status !== 'logged_in'"
          title="第三方登录已失效，所有 Agent 自动化操作已暂停。请先由你本人重新登录。"
          type="error"
          show-icon
          :closable="false"
          class="mb-5"
        />

        <el-progress :percentage="workspace.progress || 0" :status="workspace.status === 'failed' ? 'exception' : undefined" class="mb-5" />

        <el-tabs v-model="activeTab">
          <el-tab-pane label="执行概况" name="overview">
            <div class="grid gap-5 xl:grid-cols-2">
              <div class="rounded-xl border border-gray-100 p-5">
                <div class="mb-4 font-medium text-gray-700">自动化控制</div>
                <el-radio-group v-model="workspaceMode" @change="applyWorkspaceModeDefaults">
                  <el-radio value="full_auto">AI 全自动</el-radio>
                  <el-radio value="assisted">AI 辅助确认</el-radio>
                  <el-radio value="manual">用户手动</el-radio>
                </el-radio-group>
                <div class="mt-4 grid gap-2 text-sm">
                  <el-checkbox v-model="workspacePermissions.auto_apply" :disabled="workspaceMode === 'manual'">自动投递</el-checkbox>
                  <el-checkbox v-model="workspacePermissions.auto_greeting" :disabled="workspaceMode === 'manual'">自动招呼</el-checkbox>
                  <el-checkbox v-model="workspacePermissions.auto_reply" :disabled="workspaceMode !== 'full_auto'">自动回复</el-checkbox>
                  <el-checkbox v-model="workspacePermissions.auto_schedule_interview" :disabled="workspaceMode !== 'full_auto'">自动协调面试</el-checkbox>
                </div>
                <el-button type="primary" plain class="mt-4" :loading="workspaceUpdating" :disabled="workspace.platform_login_status !== 'logged_in'" @click="saveWorkspaceMode">保存模式</el-button>
              </div>

              <div class="rounded-xl border border-gray-100 p-5">
                <div class="mb-4 font-medium text-gray-700">Agent 操作</div>
                <div class="grid gap-3 sm:grid-cols-2">
                  <el-button type="warning" plain :loading="workspaceUpdating" @click="controlWorkspace('pause')">暂停 Agent</el-button>
                  <el-button type="success" plain :loading="workspaceUpdating" :disabled="workspace.platform_login_status !== 'logged_in'" @click="controlWorkspace('resume')">继续执行</el-button>
                  <el-button type="primary" plain :loading="workspaceUpdating" @click="controlWorkspace('take_over')">人工接管</el-button>
                  <el-button type="danger" plain :loading="workspaceUpdating" @click="controlWorkspace('terminate')">终止任务</el-button>
                </div>
              <div class="mt-5 rounded-lg bg-gray-50 p-4 text-sm text-gray-600">
                当前步骤：{{ workspace.current_step || '等待执行' }}
              </div>
              <div v-if="deliveryEvidence" class="mt-4 rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-800">
                <div class="font-medium">投递简历证据</div>
                <div class="mt-2">版本：{{ deliveryResumeVersion }}</div>
                <div v-if="deliveryEvidence.file_name" class="mt-1">文件：{{ deliveryEvidence.file_name }}</div>
                <div v-if="deliveryEvidence.file_sha256" class="mt-1 break-all text-xs">SHA-256：{{ deliveryEvidence.file_sha256 }}</div>
                <div class="mt-1">
                  核验状态：{{ deliveryEvidence.resume_verified ? '平台已使用所选文件完成投递' : '平台历史申请，无法反向核验当时简历版本' }}
                </div>
              </div>
              </div>
            </div>

            <div v-if="workspace.pending_actions?.length" class="mt-5 space-y-3">
              <div
                v-for="action in workspace.pending_actions"
                :key="action.id"
                class="rounded-xl border border-amber-200 bg-amber-50 p-4"
              >
                <div class="font-medium text-amber-900">{{ actionTitle(action.action_type) }}</div>
                <div class="mt-2 whitespace-pre-wrap text-sm leading-6 text-amber-800">{{ action.content }}</div>
                <div v-if="action.reason" class="mt-2 text-xs text-amber-700">{{ action.reason }}</div>
                <div class="mt-3 flex gap-2">
                  <el-button size="small" type="primary" @click="confirmPendingAction(action.id, true)">确认执行</el-button>
                  <el-button size="small" @click="confirmPendingAction(action.id, false)">拒绝</el-button>
                </div>
              </div>
            </div>

            <div v-if="workspace.interview" class="mt-5 rounded-xl border border-indigo-100 bg-indigo-50 p-5">
              <div class="font-medium text-indigo-800">面试安排</div>
              <div class="mt-2 text-sm text-indigo-700">{{ formatTime(workspace.interview.scheduled_at) }} · {{ workspace.interview.interview_type || '待确认形式' }}</div>
              <div v-if="workspace.interview.location" class="mt-1 text-sm text-indigo-700">{{ workspace.interview.location }}</div>
              <el-link
                v-if="workspace.interview.meeting_url"
                class="mt-1"
                type="primary"
                :href="workspace.interview.meeting_url"
                target="_blank"
              >
                打开面试会议链接
              </el-link>
              <div v-if="workspace.interview.missing_fields?.length" class="mt-2 text-xs text-amber-700">
                待补充：{{ workspace.interview.missing_fields.join('、') }}
              </div>
              <el-button
                v-if="!workspace.interview.scheduled_at || workspace.interview.missing_fields?.length"
                class="mt-3"
                size="small"
                type="primary"
                plain
                @click="openInterviewDialog"
              >
                补充面试安排
              </el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane :label="`HR 沟通${unreadLabel}`" name="messages">
            <div
              class="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border px-4 py-3 text-sm"
              :class="['failed', 'login_expired', 'network_denied'].includes(workspace.sync_status || '')
                ? 'border-red-200 bg-red-50 text-red-700'
                : 'border-gray-100 bg-gray-50 text-gray-600'"
            >
              <div>
                平台同步：{{ syncStatusText }}
                <span v-if="workspace.last_synced_at"> · {{ formatTime(workspace.last_synced_at) }}</span>
                <span v-if="workspace.platform_snapshot?.thread_available"> · 58微聊已连接</span>
                <span v-if="workspace.platform_snapshot?.message_node_count !== undefined">
                  · 平台消息 {{ workspace.platform_snapshot.message_node_count }} 条
                </span>
                <div v-if="workspace.sync_error" class="mt-1 text-xs">{{ workspace.sync_error }}</div>
              </div>
              <el-button
                :icon="Refresh"
                :loading="messageSyncing"
                :disabled="workspace.sync_status === 'syncing'"
                @click="syncMessages(true)"
              >
                {{ workspace.sync_status === 'network_denied' ? '网络恢复后重试' : '同步平台消息' }}
              </el-button>
            </div>
            <div class="message-panel rounded-xl bg-gray-50 p-5">
              <div v-if="!messages.length" class="py-16 text-center text-sm text-gray-400">暂未同步到 HR 消息</div>
              <div v-else class="space-y-4">
                <div v-for="message in messages" :key="message.id" class="flex" :class="message.sender_type === 'hr' ? 'justify-start' : 'justify-end'">
                  <div class="max-w-[78%]">
                    <div class="mb-1 text-xs text-gray-400">{{ senderText(message.sender_type) }} · {{ formatTime(message.sent_at) }}</div>
                    <div class="rounded-2xl px-4 py-3 text-sm leading-6" :class="message.sender_type === 'hr' ? 'border bg-white text-gray-700' : 'bg-indigo-600 text-white'">
                      {{ message.content }}
                    </div>
                    <div v-if="message.requires_confirmation && message.action_id" class="mt-2 flex gap-2">
                      <el-button size="small" type="primary" @click="confirmPendingAction(message.action_id, true)">确认发送</el-button>
                      <el-button size="small" @click="confirmPendingAction(message.action_id, false)">拒绝</el-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="suggestions.length" class="mt-4 rounded-xl border border-indigo-100 p-4">
              <div class="mb-3 flex items-center justify-between gap-3 text-sm font-medium text-gray-700">
                <span>AI 回复建议</span>
                <span v-if="suggestionKnowledgeSource" class="text-xs font-normal text-gray-400">
                  知识依据：{{ suggestionKnowledgeSource }}
                </span>
              </div>
              <button v-for="(item, index) in suggestions" :key="item.id || index" type="button" class="mb-2 block w-full rounded-lg bg-indigo-50 p-3 text-left text-sm text-gray-700 hover:bg-indigo-100" @click="messageInput = item.content">
                {{ item.content }}
              </button>
            </div>

            <div class="mt-4 flex gap-3">
              <el-input v-model="messageInput" type="textarea" :rows="3" maxlength="1000" show-word-limit placeholder="输入要发送给 HR 的内容；手动模式下由你确认发送" />
              <div class="flex w-36 flex-col gap-2">
                <el-button :icon="MagicStick" :loading="suggestionLoading" @click="generateSuggestions">AI 建议</el-button>
                <el-button type="primary" :loading="messageSending" :disabled="!messageInput.trim() || workspace.platform_login_status !== 'logged_in'" @click="sendMessage">手动发送</el-button>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="操作日志" name="logs">
            <el-timeline v-if="logs.length">
              <el-timeline-item v-for="item in logs" :key="item.id" :timestamp="formatTime(item.created_at)" :type="logType(item.status)">
                <div class="font-medium text-gray-700">{{ item.action }}</div>
                <div class="mt-1 text-sm text-gray-500">{{ item.description }}</div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无 Agent 操作日志" />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <el-dialog v-model="interviewDialogVisible" title="补充并确认面试安排" width="520px">
      <el-form label-position="top">
        <el-form-item label="面试时间" required>
          <el-date-picker
            v-model="interviewForm.scheduled_at"
            type="datetime"
            placeholder="选择面试日期和时间"
            class="w-full"
          />
        </el-form-item>
        <el-form-item label="面试形式" required>
          <el-input v-model="interviewForm.interview_type" placeholder="例如：视频面试、现场面试" />
        </el-form-item>
        <el-form-item label="地点或说明">
          <el-input v-model="interviewForm.location" placeholder="线下面试地址或线上会议说明" />
        </el-form-item>
        <el-form-item label="会议链接">
          <el-input v-model="interviewForm.meeting_url" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="发送给 HR 的确认内容" required>
          <el-input v-model="interviewForm.reply_content" type="textarea" :rows="3" maxlength="1000" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="interviewDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="interviewSubmitting" @click="submitInterview">生成待确认安排</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MagicStick, Refresh, TopRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { hrApi } from '@/api/hr'
import { jobApi } from '@/api/job'
import { useHrAutomationStore } from '@/stores/hrAutomation'
import type { Job } from '@/types'
import type {
  HrAutomationMode,
  HrAutomationPermissions,
  HrAutomationPreflight,
  HrConversationMessage,
  HrOperationLog,
  HrReplySuggestion,
  HrWorkspace,
  HrWorkspaceStatus,
  HrWorkspaceSummary,
  HrWorkspaceControlParams,
} from '@/api/types/hr'
import type { JobResumeSource } from '@/api/types/job'

const route = useRoute()
const router = useRouter()
const hrStore = useHrAutomationStore()

const initialLoading = ref(false)
const creatingWorkspace = ref(false)
const workspaceUpdating = ref(false)
const messageSending = ref(false)
const suggestionLoading = ref(false)
const messageSyncing = ref(false)
const interviewDialogVisible = ref(false)
const interviewSubmitting = ref(false)
const workspaces = ref<HrWorkspaceSummary[]>([])
const selectedWorkspaceId = ref<number | null>(null)
const workspace = ref<HrWorkspace | null>(null)
const messages = ref<HrConversationMessage[]>([])
const logs = ref<HrOperationLog[]>([])
const suggestions = ref<HrReplySuggestion[]>([])
const candidateJob = ref<Job | null>(null)
const preflight = ref<HrAutomationPreflight | null>(null)
const activeTab = ref('overview')
const messageInput = ref('')
const suggestionKnowledgeSource = ref('')
const manualLoginAcknowledged = ref(false)
const setupMode = ref<HrAutomationMode>('assisted')
const setupPermissions = reactive<HrAutomationPermissions>(modePermissions('assisted'))
const workspaceMode = ref<HrAutomationMode>('assisted')
const workspacePermissions = reactive<HrAutomationPermissions>(modePermissions('assisted'))
const interviewForm = reactive({
  scheduled_at: null as Date | null,
  interview_type: '视频面试',
  location: '',
  meeting_url: '',
  reply_content: '您好，这个时间我可以参加，请确认面试安排，谢谢。',
})

const queryJobId = computed(() => toPositiveNumber(route.query.job_id))
const querySource = computed(() => String(route.query.source || ''))
const queryResumeId = computed(() => toPositiveNumber(route.query.resume_id))
const queryResumeSource = computed<JobResumeSource>(() => route.query.resume_source === 'optimized' ? 'optimized' : 'original')
const queryOptimizationId = computed(() => toPositiveNumber(route.query.resume_optimization_id))

const canCreateWorkspace = computed(() => Boolean(
  candidateJob.value
  && preflight.value?.can_start
  && preflight.value.manual_login_verified
  && manualLoginAcknowledged.value
  && queryResumeId.value,
))

const candidateResumeText = computed(() => queryResumeSource.value === 'optimized'
  ? `优化简历 #${queryOptimizationId.value || '-'}`
  : `原始简历 #${queryResumeId.value || '-'}`)

const candidateSalary = computed(() => {
  if (!candidateJob.value) return '薪资面议'
  const min = formatSalary(candidateJob.value.salary_min)
  const max = formatSalary(candidateJob.value.salary_max)
  return min && max ? `${min}-${max}` : min || max || '薪资面议'
})

const unreadLabel = computed(() => workspace.value?.unread_count ? `（${workspace.value.unread_count}）` : '')
const syncStatusText = computed(() => {
  const labels: Record<string, string> = {
    never: '尚未同步',
    syncing: '同步中',
    success: '正常',
    failed: '同步失败',
    login_expired: '登录已失效',
    network_denied: '运行环境无法访问58',
  }
  return labels[workspace.value?.sync_status || 'never'] || '未知'
})
const deliveryEvidence = computed<Record<string, unknown> | null>(() => {
  const action = [...(workspace.value?.actions || [])]
    .reverse()
    .find((item) => item.action_type === 'submit_application' && item.status === 'success')
  const evidence = action?.payload?.resume_delivery
  return evidence && typeof evidence === 'object'
    ? evidence as Record<string, unknown>
    : null
})
const deliveryResumeVersion = computed(() => {
  const evidence = deliveryEvidence.value
  if (!evidence) return '-'
  return evidence.resume_source === 'optimized'
    ? `优化简历 #${evidence.resume_optimization_id || '-'}`
    : `原始简历 #${evidence.resume_id || '-'}`
})

let activityTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  void refreshPage()
  activityTimer = setInterval(() => { void refreshWorkspaceActivity() }, 15000)
})

onBeforeUnmount(() => {
  if (activityTimer) clearInterval(activityTimer)
})

async function refreshPage() {
  initialLoading.value = true
  try {
    await Promise.all([loadWorkspaces(), hrStore.loadOverview(true), loadCandidate()])
  } finally {
    initialLoading.value = false
  }
}

async function loadCandidate() {
  if (!queryJobId.value || !querySource.value) {
    candidateJob.value = null
    preflight.value = null
    return
  }
  try {
    const [jobResponse, preflightResponse] = await Promise.all([
      jobApi.getDetail(queryJobId.value),
      hrApi.checkPreflight({ job_id: queryJobId.value, source: querySource.value }),
    ])
    candidateJob.value = jobResponse.data
    preflight.value = preflightResponse.data
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载待投递岗位失败'))
  }
}

async function loadWorkspaces() {
  try {
    const response = await hrApi.getWorkspaces({ page: 1, page_size: 100 })
    workspaces.value = response.data.items || []
    const queryWorkspaceId = toPositiveNumber(route.query.workspace_id)
    const targetId = queryWorkspaceId || selectedWorkspaceId.value || workspaces.value[0]?.id
    if (targetId) await selectWorkspace(targetId)
  } catch (error: unknown) {
    workspaces.value = []
    if (!queryJobId.value) ElMessage.error(getErrorMessage(error, '加载投递工作区失败'))
  }
}

async function selectWorkspace(id: number) {
  selectedWorkspaceId.value = id
  try {
    const [workspaceResponse, messageResponse, logResponse] = await Promise.all([
      hrApi.getWorkspace(id),
      hrApi.getMessages(id),
      hrApi.getLogs(id),
    ])
    workspace.value = workspaceResponse.data
    messages.value = messageResponse.data.items || []
    logs.value = logResponse.data.items || []
    workspaceMode.value = workspace.value.automation_mode
    Object.assign(workspacePermissions, workspace.value.permissions)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载工作区详情失败'))
  }
}

async function createWorkspace() {
  if (!candidateJob.value || !queryJobId.value || !queryResumeId.value || !canCreateWorkspace.value) return
  creatingWorkspace.value = true
  try {
    const latestPreflight = await hrApi.checkPreflight({ job_id: queryJobId.value, source: querySource.value })
    preflight.value = latestPreflight.data
    if (!latestPreflight.data.can_start || !latestPreflight.data.manual_login_verified) {
      ElMessage.error(latestPreflight.data.reason || '第三方平台登录已失效，请由你本人重新登录后再试')
      return
    }
    const response = await hrApi.createWorkspace({
      job_id: queryJobId.value,
      source: querySource.value,
      resume_id: queryResumeId.value,
      resume_source: queryResumeSource.value,
      resume_optimization_id: queryOptimizationId.value || undefined,
      automation_mode: setupMode.value,
      permissions: { ...setupPermissions },
      manual_login_confirmed: true,
    })
    hrStore.markWorkspaceCreated()
    candidateJob.value = null
    preflight.value = null
    manualLoginAcknowledged.value = false
    await router.replace({ path: '/hr', query: { workspace_id: String(response.data.id) } })
    await loadWorkspaces()
    ElMessage.success('投递工作区已创建，Agent 将按你的授权范围执行')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '创建投递工作区失败'))
  } finally {
    creatingWorkspace.value = false
  }
}

function applyModeDefaults(value: string | number | boolean | undefined) {
  Object.assign(setupPermissions, modePermissions(value as HrAutomationMode))
}

function applyWorkspaceModeDefaults(value: string | number | boolean | undefined) {
  Object.assign(workspacePermissions, modePermissions(value as HrAutomationMode))
}

async function saveWorkspaceMode() {
  if (!workspace.value) return
  workspaceUpdating.value = true
  try {
    const response = await hrApi.updateMode(workspace.value.id, {
      automation_mode: workspaceMode.value,
      permissions: { ...workspacePermissions },
    })
    workspace.value = response.data
    ElMessage.success('自动化模式已保存')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '保存自动化模式失败'))
  } finally {
    workspaceUpdating.value = false
  }
}

async function controlWorkspace(action: HrWorkspaceControlParams['action']) {
  if (!workspace.value) return
  if (action === 'terminate') {
    try {
      await ElMessageBox.confirm('终止后 Agent 将不再操作第三方平台，确定继续吗？', '终止自动化任务', { type: 'warning' })
    } catch {
      return
    }
  }
  workspaceUpdating.value = true
  try {
    const response = await hrApi.controlWorkspace(workspace.value.id, { action })
    workspace.value = response.data
    await hrStore.loadOverview(true)
    ElMessage.success({ pause: 'Agent 已暂停', resume: 'Agent 已继续执行', terminate: '任务已终止', take_over: '已切换为人工接管' }[action])
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '操作失败'))
  } finally {
    workspaceUpdating.value = false
  }
}

async function generateSuggestions() {
  if (!workspace.value) return
  suggestionLoading.value = true
  try {
    const response = await hrApi.getSuggestions(workspace.value.id)
    suggestions.value = response.data.items || []
    suggestionKnowledgeSource.value = response.data.retrieval_source === 'qdrant_vector'
      ? '向量知识库'
      : response.data.retrieval_source
        ? '本地知识库'
        : ''
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '生成回复建议失败'))
  } finally {
    suggestionLoading.value = false
  }
}

async function sendMessage() {
  if (!workspace.value || !messageInput.value.trim()) return
  messageSending.value = true
  try {
    const response = await hrApi.sendMessage(workspace.value.id, { content: messageInput.value.trim(), send_mode: 'manual' })
    messages.value.push(response.data.message)
    messageInput.value = ''
    suggestions.value = []
    ElMessage.success(response.data.waiting_confirmation ? '消息等待你的再次确认' : '消息已进入平台发送流程')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '发送消息失败'))
  } finally {
    messageSending.value = false
  }
}

async function syncMessages(showResult = false) {
  if (!workspace.value || messageSyncing.value || workspace.value.platform_login_status !== 'logged_in') return
  messageSyncing.value = true
  try {
    const response = await hrApi.syncMessages(workspace.value.id)
    workspace.value.sync_status = response.data.sync_status || workspace.value.sync_status
    workspace.value.sync_error = response.data.sync_error || null
    workspace.value.last_synced_at = response.data.last_synced_at || workspace.value.last_synced_at
    workspace.value.platform_snapshot = response.data.platform_snapshot || workspace.value.platform_snapshot
    const newMessages = response.data.new_messages || 0
    if (response.data.sync_skipped) {
      if (showResult) ElMessage.info('已有同步任务正在执行，请稍后查看')
      return
    }
    if (newMessages > 0) {
      if (showResult) {
        const actionMessages: Partial<Record<
          NonNullable<typeof response.data.automation_action>,
          string
        >> = {
          reply_queued: '已同步 HR 新消息，AI 回复已进入发送流程',
          reply_confirmation_required: '已同步 HR 新消息，AI 回复需要你确认',
          interview_confirmation_required: '检测到面试邀请，请确认面试安排',
        }
        const actionMessage = response.data.automation_action
          ? actionMessages[response.data.automation_action]
          : undefined
        ElMessage.success(actionMessage || `已同步 ${newMessages} 条 HR 新消息`)
      }
      await selectWorkspace(workspace.value.id)
      await hrStore.loadOverview(true)
    } else if (showResult) {
      ElMessage.info('当前没有新的 HR 消息')
    }
  } catch (error: unknown) {
    if (showResult) ElMessage.error(getErrorMessage(error, '同步平台消息失败'))
  } finally {
    messageSyncing.value = false
  }
}

async function refreshWorkspaceActivity() {
  if (!workspace.value || initialLoading.value || workspaceUpdating.value) return
  const workspaceId = workspace.value.id
  if (
    ['applied', 'communicating', 'interview_pending', 'interview_scheduled'].includes(workspace.value.status)
    && workspace.value.platform_login_status === 'logged_in'
  ) {
    await syncMessages(false)
  }
  if (selectedWorkspaceId.value === workspaceId) {
    await selectWorkspace(workspaceId)
  }
}

function openInterviewDialog() {
  const current = workspace.value?.interview
  interviewForm.scheduled_at = current?.scheduled_at ? new Date(current.scheduled_at) : null
  interviewForm.interview_type = current?.interview_type || '视频面试'
  interviewForm.location = current?.location || ''
  interviewForm.meeting_url = current?.meeting_url || ''
  interviewForm.reply_content = current?.suggested_reply || '您好，这个时间我可以参加，请确认面试安排，谢谢。'
  interviewDialogVisible.value = true
}

async function submitInterview() {
  if (!workspace.value || !interviewForm.scheduled_at || !interviewForm.interview_type.trim() || !interviewForm.reply_content.trim()) {
    ElMessage.warning('请填写面试时间、形式和确认内容')
    return
  }
  const normalizedType = interviewForm.interview_type.toLowerCase().replace(/\s+/g, '')
  if (['视频', '线上', '在线', '远程', 'online'].some((item) => normalizedType.includes(item)) && !interviewForm.meeting_url.trim()) {
    ElMessage.warning('线上或视频面试必须填写会议链接')
    return
  }
  if (['现场', '线下', '到店', '面谈', 'onsite'].some((item) => normalizedType.includes(item)) && !interviewForm.location.trim()) {
    ElMessage.warning('线下或现场面试必须填写地点')
    return
  }
  interviewSubmitting.value = true
  try {
    await hrApi.createInterview(workspace.value.id, {
      scheduled_at: interviewForm.scheduled_at.toISOString(),
      timezone: 'Asia/Shanghai',
      interview_type: interviewForm.interview_type.trim(),
      location: interviewForm.location.trim() || undefined,
      meeting_url: interviewForm.meeting_url.trim() || undefined,
      reply_content: interviewForm.reply_content.trim(),
    })
    interviewDialogVisible.value = false
    await selectWorkspace(workspace.value.id)
    ElMessage.success('面试安排已生成，请在待确认操作中确认发送')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '创建面试安排失败'))
  } finally {
    interviewSubmitting.value = false
  }
}

async function confirmPendingAction(actionId: number, approved: boolean) {
  if (!workspace.value) return
  try {
    await hrApi.confirmAction(workspace.value.id, actionId, { approved })
    await selectWorkspace(workspace.value.id)
    ElMessage.success(approved ? '已确认执行' : '已拒绝该操作')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '确认操作失败'))
  }
}

function cancelCandidate() {
  candidateJob.value = null
  preflight.value = null
  void router.replace('/hr')
}

function openCandidateSource() {
  const url = candidateJob.value?.source_url || candidateJob.value?.url
  if (url) window.open(url, '_blank', 'noopener,noreferrer')
}

function openWorkspaceSource() {
  if (workspace.value?.source_url) window.open(workspace.value.source_url, '_blank', 'noopener,noreferrer')
}

function modePermissions(mode: HrAutomationMode): HrAutomationPermissions {
  if (mode === 'full_auto') return { auto_apply: true, auto_greeting: true, auto_reply: true, auto_schedule_interview: true }
  if (mode === 'assisted') return { auto_apply: true, auto_greeting: true, auto_reply: false, auto_schedule_interview: false }
  return { auto_apply: false, auto_greeting: false, auto_reply: false, auto_schedule_interview: false }
}

function actionTitle(actionType: string) {
  return ({
    submit_application: '确认投递简历',
    send_message: '确认发送消息',
    schedule_interview: '确认面试安排',
  } as Record<string, string>)[actionType] || '待确认操作'
}

function workspaceStatusText(status: HrWorkspaceStatus) {
  return ({ draft: '待开始', applying: '投递中', applied: '已投递', communicating: '沟通中', interview_pending: '待确认面试', interview_scheduled: '已约面试', paused: '已暂停', completed: '已完成', failed: '失败', cancelled: '已终止' } as Record<HrWorkspaceStatus, string>)[status]
}

function workspaceStatusType(status: HrWorkspaceStatus) {
  if (['applied', 'communicating', 'interview_scheduled', 'completed'].includes(status)) return 'success'
  if (['failed', 'cancelled'].includes(status)) return 'danger'
  if (status === 'paused' || status === 'interview_pending') return 'warning'
  return 'primary'
}

function senderText(sender: HrConversationMessage['sender_type']) {
  return { hr: 'HR', user: '我', ai: 'AI 助手', system: '系统' }[sender]
}

function logType(status: HrOperationLog['status']) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'waiting_confirmation') return 'warning'
  return 'primary'
}

function formatSalary(value?: number) {
  if (!value) return ''
  return `${value >= 1000 ? Math.round(value / 1000) : value}k`
}

function formatTime(value?: string | null) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN')
}

function toPositiveNumber(value: unknown) {
  const normalized = Array.isArray(value) ? value[0] : value
  const number = Number(normalized || 0)
  return Number.isInteger(number) && number > 0 ? number : 0
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error && typeof error === 'object') {
    const response = (error as { response?: { data?: { detail?: unknown; message?: unknown } } }).response
    if (typeof response?.data?.detail === 'string') return response.data.detail
    if (typeof response?.data?.message === 'string') return response.data.message
    if (typeof (error as { message?: unknown }).message === 'string') return String((error as { message: string }).message)
  }
  return fallback
}
</script>

<style scoped>
.mode-group :deep(.el-radio-button__inner) {
  min-width: 112px;
}

.workspace-item {
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.workspace-item:hover,
.workspace-item.active {
  border-left: 3px solid #4f46e5;
  background: #eef2ff;
}

.message-panel {
  min-height: 360px;
  max-height: 520px;
  overflow-y: auto;
}
</style>
