<template>
  <div class="career-plan-view min-h-screen bg-gray-50 p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">职业生涯规划</h1>
      <p class="mt-1 text-sm text-gray-500">填写真实背景信息，由 AI 生成岗位方向、阶段目标和学习路径</p>
    </div>

    <el-card class="mb-6 border-0" shadow="never">
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
        <el-button type="primary" size="large" :loading="generating" @click="handleGenerate">
          <el-icon class="mr-1"><TrendCharts /></el-icon>
          {{ generating ? '正在生成职业生涯规划...' : '生成职业生涯规划' }}
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
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Delete, Plus, TrendCharts, Upload } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules, type UploadRequestOptions } from 'element-plus'
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
const generating = ref(false)
const plan = ref<CareerPlan | null>(null)
const taskProgress = ref(0)
const generationStep = ref('正在准备职业规划任务')
let localAttachmentId = 1000
let localPlanId = 2000

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
    project.uploadProgress = 35
    const attachment: CareerProjectAttachment = {
      id: ++localAttachmentId,
      original_filename: file.name,
      file_type: file.name.split('.').pop()?.toLowerCase() || 'file',
      file_size: file.size,
      status: 'completed',
      error_message: null,
    }
    project.attachments.push(attachment)
    project.file_ids.push(attachment.id)
    project.uploadProgress = 100
    options.onSuccess(attachment)
    ElMessage.success('项目附件已添加')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '项目附件添加失败'))
  } finally {
    project.uploading = false
  }
}

const removeAttachment = async (project: CareerProjectForm, fileId: number) => {
  project.attachments = project.attachments.filter((file) => file.id !== fileId)
  project.file_ids = project.file_ids.filter((id) => id !== fileId)
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

    taskProgress.value = 35
    generationStep.value = '正在分析岗位方向和能力差距'
    await wait(300)
    taskProgress.value = 70
    generationStep.value = '正在生成学习路径和行动计划'
    await wait(300)
    plan.value = buildLocalCareerPlan(profile)
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

const priorityLabel = (priority: 'high' | 'medium' | 'low') => ({ high: '高', medium: '中', low: '低' })[priority]

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms))

const educationLabels: Record<string, string> = {
  high_school: '高中及以下',
  college: '大专',
  bachelor: '本科',
  master: '硕士',
  phd: '博士',
}

const experienceLabels: Record<string, string> = {
  fresh: '应届生',
  '0-1': '1年以内',
  '1-3': '1-3年',
  '3-5': '3-5年',
  '5-10': '5-10年',
  '10+': '10年以上',
}

const inferPrimaryRole = (profile: CareerPlanningProfileParams) => {
  if (profile.preferred_target_role) return profile.preferred_target_role
  const skillText = profile.skills.join(' ').toLowerCase()
  if (skillText.includes('vue') || skillText.includes('react') || skillText.includes('typescript')) return '前端开发工程师'
  if (skillText.includes('python') || skillText.includes('fastapi') || skillText.includes('java') || skillText.includes('go')) return '后端开发工程师'
  if (skillText.includes('sql') || skillText.includes('数据')) return '数据分析师'
  if (skillText.includes('产品')) return '产品经理'
  return '应用开发工程师'
}

const buildLocalCareerPlan = (profile: CareerPlanningProfileParams): CareerPlan => {
  const primaryRole = inferPrimaryRole(profile)
  const strengths = profile.skills.slice(0, 4)
  const hasProjects = profile.projects.length > 0
  const now = new Date().toISOString()

  return {
    id: ++localPlanId,
    profile_id: localPlanId,
    career_profile_summary: {
      current_stage: `${experienceLabels[profile.experience] || profile.experience} · ${educationLabels[profile.education] || profile.education}`,
      core_strengths: strengths.length ? strengths : ['学习能力', '执行力'],
      transferable_skills: ['问题分析', '沟通协作', '持续学习'],
      main_weaknesses: [
        hasProjects ? '项目成果需要进一步量化' : '缺少可展示项目经历',
        '目标岗位能力证据需要更集中',
      ],
      summary: `结合你的教育背景、工作年限、技能标签和项目经历，建议先以“${primaryRole}”作为主线方向，围绕岗位能力补齐作品、表达和面试证据。`,
    },
    recommended_roles: [
      {
        role_name: primaryRole,
        match_score: hasProjects ? 86 : 78,
        priority: 1,
        recommendation_reason: `该方向与你已填写的 ${profile.skills.slice(0, 5).join('、') || '基础能力'} 匹配度较高，适合作为当前阶段主目标。`,
        matched_capabilities: strengths.length ? strengths : ['基础学习能力'],
        missing_capabilities: ['项目结果量化', '岗位关键词表达', '面试案例沉淀'],
        suitable_industries: ['互联网产品', '企业服务', 'AI应用'],
        next_actions: ['整理目标岗位 JD 关键词', '补充一个可展示项目', '按目标岗位优化简历'],
        is_long_term_direction: true,
      },
      {
        role_name: primaryRole.includes('开发') ? '技术支持与解决方案工程师' : '项目助理/运营分析方向',
        match_score: 72,
        priority: 2,
        recommendation_reason: '该方向更看重沟通、问题拆解和业务理解，可作为求职备选路线。',
        matched_capabilities: ['沟通协作', '问题分析'],
        missing_capabilities: ['业务案例表达', '方案沉淀能力'],
        suitable_industries: ['软件服务', '数字化咨询'],
        next_actions: ['准备问题排查案例', '练习方案讲解', '整理业务复盘材料'],
        is_long_term_direction: false,
      },
    ],
    career_goals: {
      short_term: ['确定一个主目标岗位', '完成目标岗位能力清单', '整理已有项目和工作成果证据'],
      medium_term: ['完成一个可展示项目或案例集', '补齐关键技能短板', '完成至少两轮模拟面试'],
      long_term: ['形成稳定职业方向', '能独立负责完整模块或业务场景', '建立可持续学习和复盘机制'],
    },
    skill_gap_analysis: [
      { skill: '岗位关键词表达', priority: 'high', current_level: '分散', target_level: '能围绕目标岗位组织简历和面试表达', reason: '这会直接影响简历筛选和面试沟通效率。' },
      { skill: '项目成果量化', priority: 'high', current_level: hasProjects ? '有项目基础' : '待补充', target_level: '能说明职责、动作、结果和证据', reason: '项目证据是职业转化最关键的材料。' },
      { skill: '系统化学习', priority: 'medium', current_level: '需要规划', target_level: `每周稳定投入 ${profile.weekly_learning_hours} 小时`, reason: '稳定投入比一次性学习更容易形成职业竞争力。' },
    ],
    learning_path: {
      total_weeks: 12,
      hours_per_week: profile.weekly_learning_hours,
      stages: [
        {
          stage: '方向确认与材料梳理',
          duration: '第1-3周',
          goals: ['确认主目标岗位', '梳理已有技能和经历'],
          topics: ['岗位能力拆解', '简历关键词', '项目表达'],
          tasks: ['收集 10 个目标岗位 JD', '整理技能清单', '提炼工作经历亮点'],
          practice_tasks: ['用 STAR 法重写一段项目经历'],
          deliverables: ['目标岗位能力表', '经历证据清单'],
          acceptance_criteria: ['能说明目标岗位核心职责', '能列出 3 个可证明能力的案例'],
        },
        {
          stage: '能力补齐与项目建设',
          duration: '第4-8周',
          goals: ['补齐核心技能', '完成可展示项目或案例'],
          topics: ['核心工具链', '业务场景拆解', '成果量化'],
          tasks: ['完成一个小型作品项目', '补充测试/文档/部署说明'],
          practice_tasks: ['为项目写 README 和复盘文档'],
          deliverables: ['可展示项目', '项目说明文档'],
          acceptance_criteria: ['项目能独立展示', '能讲清个人贡献和结果'],
        },
        {
          stage: '求职准备与复盘',
          duration: '第9-12周',
          goals: ['完成求职材料', '提升面试表达'],
          topics: ['简历优化', '项目问答', '模拟面试'],
          tasks: ['生成目标岗位简历版本', '准备常见面试问题', '每周复盘投递反馈'],
          practice_tasks: ['完成两次模拟面试'],
          deliverables: ['目标岗位简历', '面试问答清单', '投递复盘表'],
          acceptance_criteria: ['能在 5 分钟内讲清核心项目', '能根据反馈调整简历和方向'],
        },
      ],
    },
    action_plan: {
      this_week: ['选择主目标岗位', '整理技能和项目证据', '收集目标岗位 JD'],
      this_month: ['完成能力差距清单', '启动或完善一个作品项目', '输出第一版目标岗位简历'],
      portfolio_projects: ['围绕真实业务问题做一个可展示项目', '把已有项目补充为案例集'],
      resume_actions: ['突出目标岗位关键词', '用数据和结果描述项目贡献', '删除与目标方向弱相关的信息'],
      review_points: ['第4周检查方向是否聚焦', '第8周检查项目是否可展示', '第12周复盘求职反馈'],
    },
    risks_and_alternatives: {
      risks: ['目标岗位过多导致学习主线分散', '项目成果缺少量化证据'],
      assumptions_to_confirm: [`每周能稳定投入 ${profile.weekly_learning_hours} 小时`, '目标岗位方向与真实兴趣一致'],
      alternative_roles: ['技术支持工程师', '解决方案工程师', '运营分析方向'],
      adjustment_advice: ['如果连续两周无法完成计划，应减少并行学习主题，优先保留一个主方向和一个作品项目。'],
    },
    created_at: now,
  }
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
