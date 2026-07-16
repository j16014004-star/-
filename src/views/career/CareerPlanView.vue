<template>
  <div class="career-plan-view min-h-screen bg-gray-50 p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">职业生涯规划</h1>
      <p class="mt-1 text-sm text-gray-500">填写真实背景信息，由 AI 生成岗位方向、阶段目标和学习路径</p>
    </div>

    <el-card v-if="restoringPlan" class="mb-6 border-0 py-16 text-center" shadow="never">
      <el-icon class="is-loading text-4xl text-indigo-500"><TrendCharts /></el-icon>
      <div class="mt-4 text-sm text-gray-500">正在加载你已确认的职业规划...</div>
    </el-card>

    <el-card v-if="!restoringPlan && planDecisionStatus !== 'accepted'" class="mb-6 border-0" shadow="never">
      <template #header>
        <div>
          <div class="font-semibold text-gray-800">个人背景信息</div>
          <div class="mt-1 text-xs text-gray-400">带 * 的信息用于生成个性化规划，请尽量如实填写</div>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="教育背景" prop="education">
              <el-select v-model="form.education" placeholder="请选择学历" class="w-full">
                <el-option label="高中及以下" value="high_school" />
                <el-option label="大专" value="college" />
                <el-option label="本科" value="bachelor" />
                <el-option label="硕士" value="master" />
                <el-option label="博士" value="phd" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="工作年限" prop="experience">
              <el-select v-model="form.experience" placeholder="请选择工作年限" class="w-full">
                <el-option label="应届生" value="fresh" />
                <el-option label="1年以内" value="0-1" />
                <el-option label="1-3年" value="1-3" />
                <el-option label="3-5年" value="3-5" />
                <el-option label="5-10年" value="5-10" />
                <el-option label="10年以上" value="10+" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="技能标签" prop="skills">
          <el-select
            v-model="form.skills"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            :max-collapse-tags="6"
            placeholder="可从下拉框选择，也可以输入自定义技能后按回车"
            class="w-full"
          >
            <el-option v-for="skill in skillOptions" :key="skill" :label="skill" :value="skill" />
          </el-select>
          <div class="mt-1 text-xs text-gray-400">最多建议填写 20 个与职业发展相关的技能</div>
        </el-form-item>

        <el-form-item label="工作经历描述" prop="workDescription">
          <el-input
            v-model="form.workDescription"
            type="textarea"
            :rows="5"
            maxlength="5000"
            show-word-limit
            placeholder="描述你的主要工作内容和职责..."
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="每周可投入学习时间" prop="weeklyLearningHours">
              <el-select v-model="form.weeklyLearningHours" class="w-full">
                <el-option label="每周 3 小时" :value="3" />
                <el-option label="每周 5 小时" :value="5" />
                <el-option label="每周 8 小时" :value="8" />
                <el-option label="每周 10 小时" :value="10" />
                <el-option label="每周 15 小时" :value="15" />
                <el-option label="每周 20 小时" :value="20" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="12">
            <el-form-item label="期望岗位方向（可选）">
              <el-input v-model="form.preferredTargetRole" maxlength="100" placeholder="例如：后端开发工程师；留空则由 AI 推荐" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="项目经验（可添加多个）">
          <div class="w-full space-y-4">
            <div
              v-for="(project, index) in form.projects"
              :key="project.clientId"
              class="rounded-xl border border-gray-200 bg-gray-50 p-4"
            >
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-semibold text-gray-700">项目 {{ index + 1 }}</span>
                <el-button
                  v-if="form.projects.length > 1"
                  text
                  type="danger"
                  size="small"
                  :disabled="project.uploading"
                  @click="removeProject(index)"
                >
                  <el-icon><Delete /></el-icon>
                  删除项目
                </el-button>
              </div>

              <el-row :gutter="16">
                <el-col :xs="24" :md="12">
                  <el-input v-model="project.name" maxlength="200" placeholder="项目名称" />
                </el-col>
                <el-col :xs="24" :md="12" class="mt-3 md:mt-0">
                  <el-input v-model="project.role" maxlength="200" placeholder="你在项目中的角色" />
                </el-col>
              </el-row>

              <el-input
                v-model="project.description"
                type="textarea"
                :rows="3"
                maxlength="3000"
                show-word-limit
                placeholder="项目描述、主要职责和你的贡献..."
                class="mt-3"
              />

              <div class="mt-3 flex flex-wrap items-center gap-3">
                <el-upload
                  :show-file-list="false"
                  :http-request="getProjectUploadHandler(index)"
                  accept=".pdf,.docx,.txt"
                  :disabled="project.uploading || project.attachments.length >= 3"
                >
                  <el-button :loading="project.uploading" :icon="Upload" plain>
                    {{ project.uploading ? `上传中 ${project.uploadProgress}%` : '上传项目' }}
                  </el-button>
                </el-upload>
                <span class="text-xs text-gray-400">支持 PDF、DOCX、TXT；每个项目最多 3 个附件</span>
              </div>

              <div v-if="project.attachments.length" class="mt-3 space-y-2">
                <div
                  v-for="file in project.attachments"
                  :key="file.id"
                  class="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2"
                >
                  <div class="min-w-0">
                    <div class="truncate text-sm text-gray-700">{{ file.original_filename }}</div>
                    <div class="text-xs text-gray-400">{{ formatFileSize(file.file_size) }} · {{ file.status === 'completed' ? '已完成文本提取' : file.status }}</div>
                  </div>
                  <el-button text type="danger" size="small" @click="removeAttachment(project, file.id)">删除</el-button>
                </div>
              </div>
            </div>

            <el-button type="primary" plain :icon="Plus" @click="addProject">添加项目</el-button>
          </div>
        </el-form-item>
      </el-form>

      <div class="mt-8 flex justify-center">
        <el-button type="primary" size="large" :loading="generating || restoringPlan" :disabled="restoringPlan" @click="handleGenerate">
          <el-icon class="mr-1"><TrendCharts /></el-icon>
          {{ restoringPlan ? '正在加载已确认规划...' : generating ? '正在生成职业生涯规划...' : '生成职业生涯规划' }}
        </el-button>
      </div>
    </el-card>

    <el-card v-if="generating" class="mb-6 border-0 text-center py-12" shadow="never">
      <div class="mb-4 text-5xl animate-pulse">🧠</div>
      <h3 class="mb-2 text-lg font-semibold text-gray-700">{{ taskStatusText }}</h3>
      <p class="mb-4 text-sm text-gray-500">正在根据你的背景生成岗位方向、能力差距和学习路径</p>
      <el-progress :percentage="taskProgress" :stroke-width="8" class="mx-auto max-w-xl" />
    </el-card>

    <template v-if="plan">
      <el-card class="mb-6 border-0 bg-gradient-to-r from-indigo-50 to-purple-50" shadow="never">
        <template #header><span class="font-semibold text-indigo-800">职业画像总结</span></template>
        <div class="text-sm leading-7 text-gray-700">{{ plan.career_profile_summary.summary }}</div>
        <div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <div class="text-xs text-gray-400">当前阶段</div>
            <div class="mt-1 font-medium text-gray-700">{{ plan.career_profile_summary.current_stage }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-400">核心优势</div>
            <div class="mt-2 flex flex-wrap gap-1">
              <el-tag v-for="item in plan.career_profile_summary.core_strengths" :key="item" size="small">{{ item }}</el-tag>
            </div>
          </div>
          <div>
            <div class="text-xs text-gray-400">主要短板</div>
            <div class="mt-2 text-sm text-gray-600">{{ plan.career_profile_summary.main_weaknesses.join('、') }}</div>
          </div>
        </div>
      </el-card>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header><span class="font-semibold">AI 岗位方向推荐</span></template>
        <el-alert
          title="以下是 AI 根据你提供的信息生成的职业方向建议，不是实时招聘岗位，也不代表具体企业正在招聘。"
          type="info"
          :closable="false"
          show-icon
          class="mb-4"
        />
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div v-for="role in plan.recommended_roles" :key="role.role_name" class="rounded-xl border border-indigo-100 p-4">
            <div class="flex items-center justify-between gap-3">
              <div class="font-semibold text-gray-800">{{ role.role_name }}</div>
              <el-tag type="primary">匹配度 {{ role.match_score }}%</el-tag>
            </div>
            <p class="mt-2 text-sm leading-6 text-gray-600">{{ role.recommendation_reason }}</p>
            <div class="mt-3 text-xs text-gray-500"><b>已具备：</b>{{ role.matched_capabilities.join('、') }}</div>
            <div class="mt-1 text-xs text-gray-500"><b>待提升：</b>{{ role.missing_capabilities.join('、') }}</div>
            <div class="mt-1 text-xs text-gray-500"><b>下一步：</b>{{ role.next_actions.join('；') }}</div>
          </div>
        </div>
      </el-card>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header><span class="font-semibold">短中长期职业目标</span></template>
        <el-row :gutter="18">
          <el-col v-for="group in goalGroups" :key="group.title" :xs="24" :md="8" class="mb-4 md:mb-0">
            <div class="h-full rounded-xl bg-gray-50 p-4">
              <div class="mb-3 font-medium" :class="group.color">{{ group.title }}</div>
              <ul class="space-y-2 text-sm leading-6 text-gray-600">
                <li v-for="item in group.items" :key="item">• {{ item }}</li>
              </ul>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header><span class="font-semibold">能力差距</span></template>
        <el-table :data="plan.skill_gap_analysis" stripe>
          <el-table-column prop="skill" label="能力" min-width="130" />
          <el-table-column prop="current_level" label="当前水平" min-width="120" />
          <el-table-column prop="target_level" label="目标水平" min-width="180" />
          <el-table-column label="优先级" width="100">
            <template #default="{ row }">
              <el-tag :type="row.priority === 'high' ? 'danger' : row.priority === 'medium' ? 'warning' : 'info'">
                {{ priorityLabel(row.priority) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="原因" min-width="220" />
        </el-table>
      </el-card>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold">学习路径</span>
            <span class="text-xs text-gray-400">{{ plan.learning_path.total_weeks }} 周 · 每周 {{ plan.learning_path.hours_per_week }} 小时</span>
          </div>
        </template>
        <el-timeline>
          <el-timeline-item v-for="stage in plan.learning_path.stages" :key="stage.stage" :timestamp="stage.duration" placement="top">
            <div class="rounded-xl border border-gray-100 bg-gray-50 p-4">
              <div class="font-semibold text-gray-800">{{ stage.stage }}</div>
              <div class="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div><div class="text-xs font-medium text-gray-400">学习任务</div><ul class="mt-1 text-sm leading-6 text-gray-600"><li v-for="item in stage.tasks" :key="item">• {{ item }}</li></ul></div>
                <div><div class="text-xs font-medium text-gray-400">实践任务</div><ul class="mt-1 text-sm leading-6 text-gray-600"><li v-for="item in stage.practice_tasks" :key="item">• {{ item }}</li></ul></div>
                <div><div class="text-xs font-medium text-gray-400">阶段产出</div><ul class="mt-1 text-sm leading-6 text-gray-600"><li v-for="item in stage.deliverables" :key="item">• {{ item }}</li></ul></div>
                <div><div class="text-xs font-medium text-gray-400">验收标准</div><ul class="mt-1 text-sm leading-6 text-gray-600"><li v-for="item in stage.acceptance_criteria" :key="item">• {{ item }}</li></ul></div>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <el-row :gutter="20">
        <el-col :xs="24" :lg="12" class="mb-6">
          <el-card class="h-full border-0" shadow="never">
            <template #header><span class="font-semibold">行动计划</span></template>
            <div class="space-y-4 text-sm text-gray-600">
              <div><b>本周：</b>{{ plan.action_plan.this_week.join('；') }}</div>
              <div><b>本月：</b>{{ plan.action_plan.this_month.join('；') }}</div>
              <div><b>项目建议：</b>{{ plan.action_plan.portfolio_projects.join('；') }}</div>
              <div><b>简历行动：</b>{{ plan.action_plan.resume_actions.join('；') }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="12" class="mb-6">
          <el-card class="h-full border-0" shadow="never">
            <template #header><span class="font-semibold text-orange-600">风险与备选路线</span></template>
            <div class="space-y-4 text-sm text-gray-600">
              <div><b>主要风险：</b>{{ plan.risks_and_alternatives.risks.join('；') }}</div>
              <div><b>需要确认：</b>{{ plan.risks_and_alternatives.assumptions_to_confirm.join('；') }}</div>
              <div><b>备选岗位：</b>{{ plan.risks_and_alternatives.alternative_roles.join('、') }}</div>
              <div><b>调整建议：</b>{{ plan.risks_and_alternatives.adjustment_advice.join('；') }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-card class="mb-6 border-0 plan-decision-card" shadow="never">
        <template #header>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div class="font-semibold text-gray-800">确认职业规划</div>
              <div class="mt-1 text-xs text-gray-500">确认后会生成可执行的学习与求职打卡任务</div>
            </div>
            <el-tag v-if="planDecisionStatus === 'accepted'" type="success" effect="dark">已采纳</el-tag>
            <el-tag v-else-if="planDecisionStatus === 'regenerating'" type="warning">正在重新生成</el-tag>
            <el-tag v-else type="info">等待确认</el-tag>
          </div>
        </template>

        <el-alert
          v-if="planDecisionStatus === 'accepted'"
          title="这份计划已正式启用，你可以前往“计划执行打卡”查看今天和本周需要完成的任务。"
          type="success"
          :closable="false"
          show-icon
        />
        <p v-else class="text-sm leading-7 text-gray-600">
          请先确认岗位方向、学习强度和阶段目标是否适合你。若不满意，请具体说明问题，AI 会结合你的反馈重新生成完整计划。
        </p>

        <div class="mt-5 flex flex-wrap gap-3">
          <el-button
            v-if="planDecisionStatus !== 'accepted'"
            type="success"
            size="large"
            :loading="decisionSubmitting"
            @click="handleAcceptPlan"
          >
            <el-icon class="mr-1"><CircleCheck /></el-icon>
            确认采用并开始执行
          </el-button>
          <el-button
            v-if="planDecisionStatus !== 'accepted'"
            size="large"
            :disabled="decisionSubmitting || generating"
            @click="feedbackDialogVisible = true"
          >
            <el-icon class="mr-1"><Refresh /></el-icon>
            不满意，反馈后重新生成
          </el-button>
          <el-button v-else type="primary" size="large" @click="router.push('/career/check-in')">
            前往计划执行打卡
          </el-button>
        </div>
      </el-card>
    </template>

    <el-dialog v-model="feedbackDialogVisible" title="告诉 AI 这份计划哪里不合适" width="min(620px, 92vw)" destroy-on-close>
      <el-alert
        title="反馈越具体，重新生成的计划越符合你的实际情况。"
        type="info"
        :closable="false"
        class="mb-4"
      />
      <div class="mb-4">
        <div class="mb-2 text-sm font-medium text-gray-700">希望重点调整（可多选）</div>
        <el-checkbox-group v-model="regenerateFocusAreas">
          <el-checkbox-button label="target_role">岗位方向</el-checkbox-button>
          <el-checkbox-button label="learning_intensity">学习强度</el-checkbox-button>
          <el-checkbox-button label="learning_path">学习路径</el-checkbox-button>
          <el-checkbox-button label="project_tasks">项目任务</el-checkbox-button>
          <el-checkbox-button label="job_search">求职安排</el-checkbox-button>
        </el-checkbox-group>
      </div>
      <el-input
        v-model="regenerateFeedback"
        type="textarea"
        :rows="6"
        maxlength="1000"
        show-word-limit
        placeholder="例如：每周只有 5 小时，当前计划任务太多；希望先强化 FastAPI 和数据库，再学习部署；暂时不考虑数据分析岗位。"
      />
      <template #footer>
        <el-button :disabled="decisionSubmitting" @click="feedbackDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="decisionSubmitting" @click="handleRegeneratePlan">
          提交反馈并重新生成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CircleCheck, Delete, Plus, Refresh, TrendCharts, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadRequestOptions } from 'element-plus'
import { careerApi } from '@/api/career'
import { aiApi } from '@/api/ai'
import type { AITask } from '@/api/types/ai'
import type { CareerPlan, CareerPlanningProfileParams, CareerProjectAttachment, CareerProjectInput } from '@/api/types/career'

interface CareerProjectForm extends CareerProjectInput {
  clientId: string
  attachments: CareerProjectAttachment[]
  uploading: boolean
  uploadProgress: number
}

interface CareerFormState {
  education: string
  experience: string
  skills: string[]
  workDescription: string
  weeklyLearningHours: number
  preferredTargetRole: string
  projects: CareerProjectForm[]
}

const createProject = (): CareerProjectForm => ({
  clientId: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  name: '',
  description: '',
  role: '',
  file_ids: [],
  attachments: [],
  uploading: false,
  uploadProgress: 0,
})

const formRef = ref<FormInstance>()
const router = useRouter()
const generating = ref(false)
const restoringPlan = ref(true)
const plan = ref<CareerPlan | null>(null)
const taskProgress = ref(0)
const generationStep = ref('正在准备职业规划任务')
const planDecisionStatus = ref<'draft' | 'accepted' | 'regenerating'>('draft')
const decisionSubmitting = ref(false)
const feedbackDialogVisible = ref(false)
const regenerateFeedback = ref('')
const regenerateFocusAreas = ref<string[]>([])

const skillOptions = [
  '沟通表达', '团队协作', '项目管理', 'Office', '数据分析', 'SQL', 'Python', 'Java',
  'Go', 'FastAPI', 'Vue.js', 'React', 'TypeScript', 'Node.js', 'Docker', 'Linux', '产品设计',
]

const form = reactive<CareerFormState>({
  education: '',
  experience: '',
  skills: [],
  workDescription: '',
  weeklyLearningHours: 8,
  preferredTargetRole: '',
  projects: [createProject()],
})

const rules: FormRules<CareerFormState> = {
  education: [{ required: true, message: '请选择教育背景', trigger: 'change' }],
  experience: [{ required: true, message: '请选择工作年限', trigger: 'change' }],
  skills: [{ type: 'array', required: true, min: 1, message: '请至少填写一个技能标签', trigger: 'change' }],
  workDescription: [{ required: true, message: '请描述主要工作内容和职责', trigger: 'blur' }],
  weeklyLearningHours: [{ required: true, message: '请选择每周可投入时间', trigger: 'change' }],
}

const taskStatusText = computed(() => generationStep.value)

const goalGroups = computed(() => plan.value ? [
  { title: '短期目标（0-3个月）', items: plan.value.career_goals.short_term, color: 'text-green-600' },
  { title: '中期目标（3-12个月）', items: plan.value.career_goals.medium_term, color: 'text-blue-600' },
  { title: '长期目标（1-3年）', items: plan.value.career_goals.long_term, color: 'text-purple-600' },
] : [])

const addProject = () => form.projects.push(createProject())

const removeProject = (index: number) => {
  if (form.projects[index]?.uploading) return
  form.projects.splice(index, 1)
}

const getProjectUploadHandler = (index: number) => (options: UploadRequestOptions) => {
  void handleProjectUpload(index, options)
}

const handleProjectUpload = async (index: number, options: UploadRequestOptions) => {
  const project = form.projects[index]
  if (!project) return
  if (project.attachments.length >= 3) {
    ElMessage.warning('每个项目最多上传 3 个附件')
    return
  }

  project.uploading = true
  project.uploadProgress = 0
  try {
    const file = options.file
    const response = await careerApi.uploadProjectFile(file, (percentage) => {
      project.uploadProgress = percentage
    })
    const attachment = response.data
    project.attachments.push(attachment)
    project.file_ids.push(attachment.id)
    project.uploadProgress = 100
    options.onSuccess(attachment)
    ElMessage.success('项目附件上传成功')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '项目附件上传失败'))
  } finally {
    project.uploading = false
  }
}

const removeAttachment = async (project: CareerProjectForm, fileId: number) => {
  try {
    await careerApi.deleteProjectFile(fileId)
    project.attachments = project.attachments.filter((file) => file.id !== fileId)
    project.file_ids = project.file_ids.filter((id) => id !== fileId)
    ElMessage.success('项目附件已删除')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '项目附件删除失败'))
  }
}

const validateProjects = () => {
  for (const [index, project] of form.projects.entries()) {
    const hasContent = Boolean(project.name.trim() || project.description.trim() || project.role.trim() || project.file_ids.length)
    if (!hasContent) continue
    if (!project.name.trim() || !project.description.trim() || !project.role.trim()) {
      ElMessage.warning(`请完整填写项目 ${index + 1} 的名称、描述和你的角色`)
      return false
    }
    if (project.uploading) {
      ElMessage.warning(`项目 ${index + 1} 的附件仍在上传，请稍后提交`)
      return false
    }
  }
  return true
}

const handleGenerate = async () => {
  if (!formRef.value || generating.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid || !validateProjects()) return
  if (form.skills.length > 20) {
    ElMessage.warning('技能标签最多填写 20 个')
    return
  }

  generating.value = true
  taskProgress.value = 5
  generationStep.value = '正在整理职业背景信息'
  plan.value = null
  planDecisionStatus.value = 'draft'
  try {
    const projects = form.projects
      .filter((project) => project.name.trim() || project.description.trim() || project.role.trim() || project.file_ids.length)
      .map((project) => ({
        name: project.name.trim(),
        description: project.description.trim(),
        role: project.role.trim(),
        file_ids: project.file_ids,
      }))

    const profile: CareerPlanningProfileParams = {
      education: form.education,
      experience: form.experience,
      skills: form.skills.map((skill) => skill.trim()).filter(Boolean),
      work_description: form.workDescription.trim(),
      weekly_learning_hours: form.weeklyLearningHours,
      preferred_target_role: form.preferredTargetRole.trim() || undefined,
      projects,
    }

    taskProgress.value = 15
    generationStep.value = '正在创建职业规划档案'
    const profileResponse = await careerApi.createProfile(profile)

    taskProgress.value = 25
    generationStep.value = '正在启动 AI 职业规划任务'
    const planTaskResponse = await careerApi.createPlan({
      profile_id: profileResponse.data.id,
      preferred_target_role: profile.preferred_target_role,
    })

    const finishedTask = await pollCareerPlanTask(planTaskResponse.data.task_id)
    const planId = finishedTask.result_id || planTaskResponse.data.plan_id
    if (!planId) throw new Error('职业规划任务完成但未返回规划 ID')

    taskProgress.value = 95
    generationStep.value = '正在加载职业规划结果'
    const planResponse = await careerApi.getPlan(planId)
    plan.value = planResponse.data
    taskProgress.value = 100
    generationStep.value = '职业规划已生成'
    ElMessage.success('职业生涯规划已生成')
  } catch (error: unknown) {
    taskProgress.value = 0
    generationStep.value = '职业规划生成失败'
    ElMessage.error(getErrorMessage(error, '生成职业生涯规划失败，请稍后重试'))
  } finally {
    generating.value = false
  }
}

const handleAcceptPlan = async () => {
  if (!plan.value || decisionSubmitting.value) return
  try {
    await ElMessageBox.confirm(
      '确认后，系统会按照这份职业规划生成每日和每周执行任务。',
      '确认采用当前计划',
      { confirmButtonText: '确认采用', cancelButtonText: '再看看', type: 'success' },
    )
    decisionSubmitting.value = true
    await careerApi.acceptPlan(plan.value.id)
    planDecisionStatus.value = 'accepted'
    ElMessage.success('计划已采用，执行打卡任务已生成')
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(getErrorMessage(error, '确认计划失败，请稍后重试'))
  } finally {
    decisionSubmitting.value = false
  }
}

const handleRegeneratePlan = async () => {
  if (!plan.value || decisionSubmitting.value) return
  const feedback = regenerateFeedback.value.trim()
  if (feedback.length < 10) {
    ElMessage.warning('请至少填写 10 个字，具体说明计划哪里不合适')
    return
  }

  decisionSubmitting.value = true
  planDecisionStatus.value = 'regenerating'
  taskProgress.value = 10
  generationStep.value = '正在提交你的调整意见'
  try {
    const response = await careerApi.regeneratePlan(plan.value.id, {
      feedback,
      focus_areas: regenerateFocusAreas.value.length ? regenerateFocusAreas.value : undefined,
    })
    feedbackDialogVisible.value = false
    generating.value = true
    const finishedTask = await pollCareerPlanTask(response.data.task_id)
    const newPlanId = finishedTask.result_id || response.data.plan_id
    if (!newPlanId) throw new Error('重新生成完成但未返回新的规划 ID')

    generationStep.value = '正在加载调整后的职业规划'
    const planResponse = await careerApi.getPlan(newPlanId)
    plan.value = planResponse.data
    planDecisionStatus.value = 'draft'
    taskProgress.value = 100
    regenerateFeedback.value = ''
    regenerateFocusAreas.value = []
    ElMessage.success('AI 已根据你的反馈重新生成职业规划，请再次确认')
  } catch (error: unknown) {
    planDecisionStatus.value = 'draft'
    taskProgress.value = 0
    ElMessage.error(getErrorMessage(error, '重新生成职业规划失败，请稍后重试'))
  } finally {
    generating.value = false
    decisionSubmitting.value = false
  }
}

const priorityLabel = (priority: 'high' | 'medium' | 'low') => ({ high: '高', medium: '中', low: '低' })[priority]

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const getTaskStepText = (task: AITask) => {
  const statusMap: Record<AITask['status'], string> = {
    pending: '职业规划任务已创建，等待 AI 处理',
    preparing: '正在整理职业背景信息',
    generating: '正在分析岗位方向和能力差距',
    validating: '正在校验职业规划内容',
    saving: '正在保存职业规划结果',
    success: '职业规划已生成',
    failed: '职业规划生成失败',
    cancelled: '职业规划任务已取消',
  }
  return statusMap[task.status]
}

const pollCareerPlanTask = async (taskId: string) => {
  let latestTask: AITask | null = null
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const response = await aiApi.getTask(taskId)
    latestTask = response.data
    taskProgress.value = Math.max(taskProgress.value, latestTask.progress || 0)
    generationStep.value = getTaskStepText(latestTask)

    if (latestTask.status === 'success') return latestTask
    if (latestTask.status === 'failed') {
      throw new Error(latestTask.error_message || '职业规划生成失败')
    }
    if (latestTask.status === 'cancelled') {
      throw new Error(latestTask.error_message || '职业规划任务已取消')
    }

    const delay = Math.min(Math.max(latestTask.poll_after_seconds || 1, 1), 5) * 1000
    await wait(delay)
  }

  throw new Error('职业规划生成超时，请稍后重试')
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  const message = (error as { response?: { data?: { message?: unknown } } })?.response?.data?.message
  return typeof message === 'string' ? message : fallback
}

const restoreAcceptedPlan = async () => {
  try {
    const executionResponse = await careerApi.getCurrentExecution()
    const planResponse = await careerApi.getPlan(executionResponse.data.career_plan_id)
    plan.value = planResponse.data
    planDecisionStatus.value = 'accepted'
    taskProgress.value = 100
    generationStep.value = '已加载当前执行中的职业规划'
  } catch (error: unknown) {
    const status = (error as { response?: { status?: number } })?.response?.status
    if (status !== 404) {
      ElMessage.error(getErrorMessage(error, '加载已确认的职业规划失败'))
    }
  } finally {
    restoringPlan.value = false
  }
}

onMounted(() => {
  void restoreAcceptedPlan()
})
</script>

<style scoped>
.career-plan-view :deep(.el-card) {
  border-radius: 16px;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}

.plan-decision-card {
  border: 1px solid #c7d2fe !important;
  background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
}
</style>
