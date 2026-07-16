// ============ API Response Wrapper ============
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// ============ Pagination ============
export interface PaginationParams {
  page: number
  page_size: number
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ============ User ============
export interface UserInfo {
  id: number
  username: string
  email: string
  avatar?: string
  phone?: string
  status?: string
  email_verified?: boolean
  phone_verified?: boolean
  created_at: string
  last_login_at?: string
}

// ============ Resume ============
export interface Resume {
  id: number
  title: string
  file_type: 'pdf' | 'doc' | 'docx'
  file_url?: string
  file_size?: number
  score?: number | null
  status: 'pending' | 'processing' | 'analyzing' | 'completed' | 'failed'
  created_at: string
  updated_at: string
  extracted_text?: string
  chunks?: ResumeTextChunk[]
  structured_data?: ResumeContent
  content?: ResumeContent
  recommendation_refresh?: {
    status: string
    task_id?: string | null
    message: string
  } | null
}

export interface ResumeTextChunk {
  id?: number
  index?: number
  chunk_index?: number
  text?: string
  content?: string
  char_count?: number
  created_at?: string
  metadata?: Record<string, string | number | boolean | null>
}

export interface ResumeContent {
  name?: string
  phone?: string
  email?: string
  experience?: string
  education?: string
  city?: string
  education_list?: ResumeEducation[]
  work_list?: ResumeWorkExperience[]
  skills?: string[]
  raw_text?: string
}

export interface ResumeEducation {
  school: string
  major?: string
  degree?: string
  period?: string
}

export interface ResumeWorkExperience {
  company: string
  position?: string
  description?: string
  period?: string
}

export interface ResumeOptimizeResult {
  id?: number
  resume_id?: number
  title?: string
  saved_at?: string | null
  is_saved?: boolean
  optimization_summary?: string
  original?: string
  optimized?: string
  optimized_content?: string
  score_improvement?: number | null
  changes?: OptimizeChange[]
  change_items: OptimizeChange[]
  confirmation_questions: string[]
  confirmation_actions?: Array<{
    type: 'ai' | 'manual' | 'dismiss'
    title: string
    questions: string[]
    added_content?: string
    summary?: string
    feedback?: string
    created_at: string
  }>
  created_at?: string
}

export interface OptimizeChange {
  section: string
  original: string
  optimized: string
  reason: string
  evidence?: string
  evidence_source?: 'original_resume' | 'user_confirmation' | 'knowledge_base'
  requires_confirmation?: boolean
}

// ============ Career ============
export interface CareerPlan {
  recommended_positions: string[]
  learning_path: LearningPathItem[]
  skill_suggestions: string[]
  career_direction: string
  market_analysis: string
}

export interface LearningPathItem {
  stage: string
  skills: string[]
  duration: string
  resources: string[]
}

// ============ Job ============
export interface Job {
  id: number
  company: string
  company_logo?: string
  title: string
  salary_min: number
  salary_max: number
  city: string
  experience_required: string
  education_required: string
  skills: string[]
  description: string
  match_score: number
  match_reasons: string[]
  source?: string
  source_name?: string
  source_url?: string
  url?: string
  is_active?: boolean
  crawl_time?: string
  created_at: string
}

// ============ Chat ============
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

export interface ChatSession {
  id: number
  title: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
}

// ============ Agent ============
export type AgentTaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'paused'
export type AgentTaskType = 'search' | 'filter' | 'apply' | 'track'

export interface AgentTask {
  id: number
  type: AgentTaskType
  status: AgentTaskStatus
  progress: number
  config: Record<string, any>
  logs: AgentLog[]
  applications: Application[]
  created_at: string
  updated_at: string
}

export interface AgentLog {
  id: number
  message: string
  level: 'info' | 'warn' | 'error'
  created_at: string
}

export interface Application {
  id: number
  company: string
  position: string
  status: 'submitted' | 'viewed' | 'interviewing' | 'rejected' | 'accepted'
  submitted_at: string
}

// ============ HR ============
export interface HRMessage {
  id: number
  company: string
  hr_name: string
  content: string
  reply_suggestion?: string
  status: 'pending' | 'replied' | 'archived'
  created_at: string
}

// ============ Interview ============
export type QuestionType = 'technical' | 'behavioral' | 'project' | 'general'

export interface Interview {
  id: number
  title: string
  status: 'pending' | 'in_progress' | 'completed'
  position: string
  company?: string
  questions: InterviewQuestion[]
  score?: number
  report?: InterviewReport
  created_at: string
}

export interface InterviewQuestion {
  id: number
  type: QuestionType
  question: string
  answer?: string
  score?: number
  feedback?: string
  tips?: string
  duration?: number
}

export interface InterviewReport {
  overall_score: number
  dimension_scores: {
    technical: number
    behavioral: number
    communication: number
    logic: number
  }
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  summary: string
}

// ============ Menu ============
export interface MenuItem {
  index: string
  title: string
  icon?: string
  path?: string
  children?: MenuItem[]
}

// ============ Dashboard ============
export interface DashboardStats {
  resume_count: number
  interview_count: number
  job_matches: number
  chat_sessions: number
  recent_activities: ActivityItem[]
  upcoming_interviews: Interview[]
}

export interface ActivityItem {
  id: number
  type: string
  content: string
  time: string
}


