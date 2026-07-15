<template>
  <div class="resume-detail-view p-6 bg-gray-50 min-h-screen">
    <!-- Page Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <el-button text @click="$router.push('/resume')">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div>
          <h1 class="text-2xl font-bold text-gray-800">{{ resume.title }}</h1>
          <p class="text-sm text-gray-500">上传于 {{ resume.uploadDate }}</p>
        </div>
      </div>
    </div>

    <el-row :gutter="24">
      <!-- Left Panel: Resume Content -->
      <el-col :xs="24" :lg="12" class="mb-6">
        <el-card class="border-0" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <span class="font-semibold text-gray-800">简历内容</span>
              <el-tag :type="resume.fileType === 'pdf' ? 'danger' : 'primary'" size="small">
                {{ resume.fileType.toUpperCase() }}
              </el-tag>
            </div>
          </template>

          <div class="space-y-6">
            <!-- Basic Info -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><User /></el-icon> 基本信息
              </h3>
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="姓名">{{ resumeContent.name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="电话">{{ resumeContent.phone || '-' }}</el-descriptions-item>
                <el-descriptions-item label="邮箱">{{ resumeContent.email || '-' }}</el-descriptions-item>
                <el-descriptions-item label="工作经验">{{ resumeContent.experience || '-' }}</el-descriptions-item>
                <el-descriptions-item label="最高学历">{{ resumeContent.education || '-' }}</el-descriptions-item>
                <el-descriptions-item label="现居城市">{{ resumeContent.city || '-' }}</el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- Extracted Text -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3">提取文本</h3>
              <el-empty v-if="!extractedText" description="暂无提取文本" :image-size="80" />
              <pre
                v-else
                class="max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-lg bg-gray-50 p-4 text-sm leading-6 text-gray-600"
              >{{ extractedText }}</pre>
            </div>

            <!-- Text Chunks -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3">文本分块</h3>
              <el-empty v-if="chunks.length === 0" description="暂无文本分块" :image-size="80" />
              <el-collapse v-else>
                <el-collapse-item
                  v-for="chunk in chunks"
                  :key="chunk.index"
                  :name="String(chunk.index)"
                >
                  <template #title>
                    <span>分块 {{ chunk.index }}</span>
                    <span v-if="chunk.metadata?.page" class="ml-2 text-xs text-gray-400">
                      第 {{ chunk.metadata.page }} 页
                    </span>
                  </template>
                  <pre class="whitespace-pre-wrap break-words rounded bg-gray-50 p-3 text-sm text-gray-600">{{ chunk.text }}</pre>
                </el-collapse-item>
              </el-collapse>
            </div>

            <!-- Education -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><School /></el-icon> 教育背景
              </h3>
              <el-empty v-if="resumeContent.educationList.length === 0" description="暂无教育背景" :image-size="80" />
              <el-timeline v-else>
                <el-timeline-item
                  v-for="edu in resumeContent.educationList"
                  :key="edu.school"
                  :timestamp="edu.period"
                  placement="top"
                >
                  <div class="font-medium">{{ edu.school }}</div>
                  <div class="text-sm text-gray-500">{{ edu.major }} | {{ edu.degree }}</div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- Work Experience -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><Briefcase /></el-icon> 工作经历
              </h3>
              <el-empty v-if="resumeContent.workList.length === 0" description="暂无工作经历" :image-size="80" />
              <el-timeline v-else>
                <el-timeline-item
                  v-for="work in resumeContent.workList"
                  :key="work.company"
                  :timestamp="work.period"
                  placement="top"
                >
                  <div class="font-medium">{{ work.company }}</div>
                  <div class="text-sm text-gray-500">{{ work.position }}</div>
                  <div class="text-sm text-gray-500 mt-1">{{ work.description }}</div>
                </el-timeline-item>
              </el-timeline>
            </div>

            <!-- Skills -->
            <div>
              <h3 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <el-icon><Coin /></el-icon> 技能标签
              </h3>
              <el-empty v-if="resumeContent.skills.length === 0" description="暂无技能标签" :image-size="80" />
              <div v-else class="flex flex-wrap gap-2">
                <el-tag
                  v-for="skill in resumeContent.skills"
                  :key="skill"
                  effect="plain"
                  round
                >
                  {{ skill }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Right Panel: AI Optimization -->
      <el-col :xs="24" :lg="12" class="mb-6">
        <div class="text-center py-20">
          <el-card class="optimization-entry-card border-0" shadow="hover">
            <div class="optimization-icon mx-auto mb-5">
              <el-icon><MagicStick /></el-icon>
            </div>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">让 AI 帮你优化简历</h3>
            <p class="text-gray-500 mb-7">
              {{ canOptimize ? '根据简历内容生成更清晰、更有竞争力的表达' : '简历解析完成后即可使用 AI 优化' }}
            </p>
            <el-button
              class="optimization-button"
              type="primary"
              size="large"
              :icon="MagicStick"
              :disabled="!canOptimize"
              @click="handleOptimize()"
            >
              AI优化简历
            </el-button>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, User, School, Briefcase, Coin, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { resumeApi } from '@/api/resume'

const route = useRoute()
const router = useRouter()
const resumeId = Number(route.params.id) || 1
const isLoading = ref(true)

interface EducationItem {
  school: string
  major?: string
  degree?: string
  period?: string
}

interface WorkItem {
  company: string
  position?: string
  description?: string
  period?: string
}

interface ResumeContentState {
  name: string
  phone: string
  email: string
  experience: string
  education: string
  city: string
  educationList: EducationItem[]
  workList: WorkItem[]
  skills: string[]
}

interface TextChunk {
  index: number
  text: string
  metadata?: Record<string, string | number | boolean | null>
}

interface RawTextChunk {
  index?: number
  chunk_index?: number
  text?: string
  content?: string
  chunk_text?: string
  page_content?: string
  raw_text?: string
  metadata?: Record<string, string | number | boolean | null>
}

interface ApiResumeContent extends Record<string, unknown> {
  name?: string
  full_name?: string
  phone?: string
  phone_number?: string
  mobile?: string
  email?: string
  experience?: string
  work_experience?: string
  years_of_experience?: string
  education?: string
  highest_education?: string
  degree?: string
  city?: string
  current_city?: string
  expected_city?: string
  location?: string
  education_list?: EducationItem[]
  educationList?: EducationItem[]
  educations?: EducationItem[]
  education_background?: EducationItem[]
  work_list?: WorkItem[]
  workList?: WorkItem[]
  work_experiences?: WorkItem[]
  experiences?: WorkItem[]
  skills?: string[]
  skill_tags?: string[]
  skillTags?: string[]
}

const resume = ref({
  id: resumeId,
  title: '',
  fileType: 'pdf',
  uploadDate: '',
  status: 'pending'
})

const resumeContent = ref({
  name: '',
  phone: '',
  email: '',
  experience: '',
  education: '',
  city: '',
  educationList: [] as EducationItem[],
  workList: [] as WorkItem[],
  skills: [] as string[]
} satisfies ResumeContentState)

const extractedText = ref('')
const chunks = ref<TextChunk[]>([])
const canOptimize = computed(() => resume.value.status === 'completed' && Boolean(extractedText.value.trim()))

const normalizeText = (text: string) => text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')

const getSection = (text: string, startLabel: string, endLabels: string[]) => {
  const start = text.indexOf(startLabel)
  if (start === -1) return ''
  const bodyStart = start + startLabel.length
  const end = endLabels
    .map((label) => text.indexOf(label, bodyStart))
    .filter((index) => index !== -1)
    .sort((a, b) => a - b)[0]
  return text.slice(bodyStart, end ?? text.length).trim()
}

const findDegree = (text: string) => {
  const degrees = ['博士', '硕士', '本科', '大专', '专科', '高中']
  return degrees.find((degree) => text.includes(degree)) || ''
}

const getMonthIndex = (value: string) => {
  const match = value.match(/(\d{4})[./](\d{1,2})/)
  if (!match) return null
  return Number(match[1]) * 12 + Number(match[2])
}

const estimateExperience = (text: string) => {
  const ranges = [...text.matchAll(/(\d{4}[./]\d{1,2})\s*[–—-]\s*(\d{4}[./]\d{1,2})/g)]
  const months = ranges.reduce((total, range) => {
    const start = getMonthIndex(range[1])
    const end = getMonthIndex(range[2])
    if (start === null || end === null || end < start) return total
    return total + end - start + 1
  }, 0)
  if (!months) return ''
  if (months < 12) return `约${months}个月`
  const years = Math.round((months / 12) * 10) / 10
  return `约${years}年`
}

const parseEducationList = (text: string): EducationItem[] => {
  const section = getSection(text, '教育背景', ['资格证书', '技能标签', '工作经历'])
  const result: EducationItem[] = []
  section
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const match = line.match(/^(.+?)\s*[|｜]\s*(.+?)\s*[|｜]\s*(\d{4}[./]\d{1,2}\s*[–—-]\s*\d{4}[./]\d{1,2})/)
      if (!match) return
      const degree = findDegree(match[2])
      result.push({
        school: match[1].trim(),
        major: match[2].replace(/[（(].*?[）)]/g, '').trim(),
        degree,
        period: match[3].trim()
      })
    })
  return result
}

const parseWorkList = (text: string): WorkItem[] => {
  const section = getSection(text, '工作经历', ['教育背景', '资格证书', '技能标签'])
  const lines = section.split('\n').map((line) => line.trim()).filter(Boolean)
  const result: WorkItem[] = []
  let current: WorkItem | null = null

  lines.forEach((line) => {
    const match = line.match(/^(.+?)\s*[|｜]\s*(.+?)\s*[（(]([^)）]+)[）)]/)
    if (match) {
      current = {
        company: match[1].trim(),
        position: match[2].trim(),
        period: match[3].trim(),
        description: ''
      }
      result.push(current)
      return
    }

    if (current && /^[•\-]/.test(line)) {
      const item = line.replace(/^[•\-\s]+/, '').trim()
      current.description = current.description ? `${current.description}\n${item}` : item
    }
  })

  return result
}

const parseSkills = (text: string) => {
  const skillKeywords = [
    'Office', 'Java', 'Python', '数据结构', '数据库', '信息系统', '数据处理',
    '文档编写', '需求文档', '项目计划', '项目协调', '风险跟踪', '物流信息系统',
    '英语四级', '英语六级', 'CET-4', 'CET-6'
  ]
  return [...new Set(skillKeywords.filter((skill) => text.includes(skill)))]
}

const getNestedRecord = (value: unknown): Record<string, unknown> | undefined => {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : undefined
}

const getStringField = (source: Record<string, unknown> | undefined, keys: string[]) => {
  if (!source) return ''
  for (const key of keys) {
    const value = source[key]
    if (typeof value === 'string' && value.trim()) {
      return value.trim()
    }
    if (typeof value === 'number') {
      return String(value)
    }
  }
  return ''
}

const getArrayField = <T>(source: Record<string, unknown> | undefined, keys: string[]) => {
  if (!source) return [] as T[]
  for (const key of keys) {
    const value = source[key]
    if (Array.isArray(value) && value.length > 0) {
      return value as T[]
    }
  }
  return [] as T[]
}

const normalizeEducationItem = (item: EducationItem | Record<string, unknown>): EducationItem => {
  const source = item as Record<string, unknown>
  return {
    school: getStringField(source, ['school', 'university', 'college', 'name']) || '未知学校',
    major: getStringField(source, ['major', 'profession', 'field']),
    degree: getStringField(source, ['degree', 'education', 'level']),
    period: getStringField(source, ['period', 'time', 'date_range', 'duration'])
  }
}

const normalizeWorkItem = (item: WorkItem | Record<string, unknown>): WorkItem => {
  const source = item as Record<string, unknown>
  const responsibilities = source.description || source.responsibilities || source.duties
  return {
    company: getStringField(source, ['company', 'company_name', 'name']) || '未知公司',
    position: getStringField(source, ['position', 'job_title', 'title', 'role']),
    period: getStringField(source, ['period', 'time', 'date_range', 'duration']),
    description: Array.isArray(responsibilities)
      ? responsibilities.join('\n')
      : getStringField(source, ['description', 'responsibilities', 'duties'])
  }
}

const parseResumeText = (text: string): ResumeContentState => {
  const normalized = normalizeText(text)
  const lines = normalized.split('\n').map((line) => line.trim()).filter(Boolean)
  const firstContentLine = lines.find((line) =>
    !line.includes('|') &&
    !line.includes('电话') &&
    !line.includes('邮箱') &&
    !line.includes('---') &&
    !['个人优势', '工作经历', '教育背景', '资格证书'].includes(line)
  )
  const educationList = parseEducationList(normalized)
  const workList = parseWorkList(normalized)

  return {
    name: firstContentLine || '',
    phone: normalized.match(/(?:电话[:：]\s*)?(1[3-9]\d{9})/)?.[1] || '',
    email: normalized.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/)?.[0] || '',
    experience: estimateExperience(getSection(normalized, '工作经历', ['教育背景', '资格证书'])) || '',
    education: educationList[0]?.degree || findDegree(normalized),
    city: normalized.match(/(?:期望城市|现居城市)[:：]\s*([^|\s]+)/)?.[1] || '',
    educationList,
    workList,
    skills: parseSkills(normalized)
  }
}

const normalizeResumeContent = (content: ApiResumeContent | undefined, text: string): ResumeContentState => {
  const fallback = parseResumeText(text)
  const basicInfo = getNestedRecord(content?.basic_info)
  const profile = getNestedRecord(content?.profile)
  const educationList = getArrayField<EducationItem>(content, [
    'education_list', 'educationList', 'educations', 'education_background'
  ]).map(normalizeEducationItem)
  const workList = getArrayField<WorkItem>(content, [
    'work_list', 'workList', 'work_experiences', 'experiences'
  ]).map(normalizeWorkItem)
  const skills = getArrayField<string>(content, ['skills', 'skill_tags', 'skillTags'])

  return {
    name: getStringField(content, ['name', 'full_name']) || getStringField(basicInfo, ['name', 'full_name']) || fallback.name,
    phone: getStringField(content, ['phone', 'phone_number', 'mobile']) || getStringField(basicInfo, ['phone', 'phone_number', 'mobile']) || fallback.phone,
    email: getStringField(content, ['email']) || getStringField(basicInfo, ['email']) || fallback.email,
    experience: getStringField(content, ['experience', 'work_experience', 'years_of_experience']) || getStringField(profile, ['experience', 'work_experience']) || fallback.experience,
    education: getStringField(content, ['education', 'highest_education', 'degree']) || getStringField(profile, ['education', 'highest_education', 'degree']) || fallback.education,
    city: getStringField(content, ['city', 'current_city', 'expected_city', 'location']) || getStringField(profile, ['city', 'current_city', 'expected_city', 'location']) || fallback.city,
    educationList: educationList.length > 0 ? educationList : fallback.educationList,
    workList: workList.length > 0 ? workList : fallback.workList,
    skills: skills.length > 0 ? skills : fallback.skills
  }
}

const getExtractedText = (data: Record<string, unknown>) => {
  const content = getNestedRecord(data.content)
  return getStringField(data, ['extracted_text', 'raw_text', 'text', 'parsed_text']) ||
    getStringField(content, ['extracted_text', 'raw_text', 'text', 'parsed_text'])
}

const getStructuredContent = (data: Record<string, unknown>) => {
  return getNestedRecord(data.content) ||
    getNestedRecord(data.structured_content) ||
    getNestedRecord(data.structured_data) ||
    getNestedRecord(data.parsed_content) ||
    getNestedRecord(data.resume_content)
}

const buildFallbackChunks = (text: string): TextChunk[] => {
  const normalized = normalizeText(text)
  return normalized
    .split(/(?=个人优势|工作经历|教育背景|资格证书)/)
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item, index) => ({
      index: index + 1,
      text: item,
      metadata: { source: 'fallback' }
    }))
}

const normalizeChunks = (rawChunks: RawTextChunk[] | undefined, text: string): TextChunk[] => {
  if (!rawChunks?.length) {
    return buildFallbackChunks(text)
  }

  const normalized = rawChunks
    .map((chunk, index) => ({
      index: typeof chunk.index === 'number'
        ? chunk.index
        : (typeof chunk.chunk_index === 'number' ? chunk.chunk_index : index + 1),
      text: chunk.text || chunk.content || chunk.chunk_text || chunk.page_content || chunk.raw_text || '',
      metadata: chunk.metadata
    }))
    .filter((chunk) => chunk.text.trim())
  return normalized.length > 0 ? normalized : buildFallbackChunks(text)
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  const data = (error as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data
  if (typeof data?.detail === 'string') return data.detail
  return typeof data?.message === 'string' ? data.message : fallback
}

// 从后端 API 加载简历详情
onMounted(async () => {
  isLoading.value = true
  try {
    const response = await resumeApi.getDetail(resumeId)
    const data = response.data
    const rawData = data as unknown as Record<string, unknown>

    resume.value.title = data.title || '未命名简历'
    resume.value.fileType = data.file_type || 'pdf'
    resume.value.uploadDate = data.created_at?.split('T')[0] || ''
    resume.value.status = data.status || 'pending'
    extractedText.value = getExtractedText(rawData)
    chunks.value = normalizeChunks(data.chunks as RawTextChunk[] | undefined, extractedText.value)
    resumeContent.value = normalizeResumeContent(getStructuredContent(rawData), extractedText.value)

  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载简历详情失败'))
  } finally {
    isLoading.value = false
  }
})

const handleOptimize = () => {
  router.push(`/resume/optimize/${resume.value.id}`)
}
</script>

<style scoped>
.resume-detail-view :deep(.el-card) {
  border-radius: 16px;
}

:deep(.el-descriptions) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}

.optimization-entry-card {
  background: linear-gradient(145deg, #ffffff 0%, #f5f8ff 58%, #eef2ff 100%);
}

.optimization-entry-card :deep(.el-card__body) {
  padding: 52px 32px;
}

.optimization-icon {
  display: flex;
  width: 72px;
  height: 72px;
  align-items: center;
  justify-content: center;
  border-radius: 22px;
  color: #ffffff;
  font-size: 34px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 14px 30px rgba(99, 102, 241, 0.25);
}

.optimization-button {
  min-width: 180px;
  height: 46px;
  border: 0;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  box-shadow: 0 10px 22px rgba(79, 70, 229, 0.22);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.optimization-button:not(.is-disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(79, 70, 229, 0.3);
}
</style>
