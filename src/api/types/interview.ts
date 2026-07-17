export type InterviewSourceType = 'applied' | 'intention' | 'custom'
export type InterviewDifficulty = 'junior' | 'middle' | 'senior'
export type InterviewQuestionType = 'technical' | 'project' | 'behavioral' | 'scenario'

export interface AppliedJobOption {
  application_id: number
  job_id: number
  title: string
  company: string
  description?: string
  resume_id: number
  resume_source: 'original' | 'optimized'
  resume_optimization_id?: number
}

export interface ResumeOption {
  id: number
  title: string
  updated_at?: string
}

export interface OptimizedResumeOption {
  id: number
  resume_id: number
  title: string
  target_role?: string
  saved_at?: string
}

export interface InterviewOptions {
  applied_jobs: AppliedJobOption[]
  resumes: ResumeOption[]
  optimized_resumes: OptimizedResumeOption[]
  supported_domains: Array<{ value: string; label: string }>
}

export interface InterviewCreateParams {
  source_type: InterviewSourceType
  job_id?: number
  resume_id?: number
  resume_source?: 'original' | 'optimized'
  resume_optimization_id?: number
  title?: string
  target_role?: string
  company?: string
  job_description?: string
  difficulty: InterviewDifficulty
  question_types: InterviewQuestionType[]
  question_count: number
}

export interface InterviewAnswerParams {
  question_id: number
  answer: string
  duration_seconds: number
}

export interface InterviewQuestion {
  id: number
  order_no: number
  question_type: InterviewQuestionType
  type: InterviewQuestionType
  question: string
  difficulty: InterviewDifficulty
  status: 'pending' | 'answered'
  duration_minutes: number
  answer?: string
  duration_seconds?: number
  score?: number
  dimension_scores?: Record<string, number>
  matched_points?: string[]
  missing_points?: string[]
  feedback?: string
  follow_up_question?: string
}

export interface InterviewItem {
  id: number
  title: string
  source_type: InterviewSourceType
  job_id?: number
  resume_id?: number
  target_role: string
  position: string
  company?: string
  domain: 'python_backend' | 'secretary_studies'
  difficulty: InterviewDifficulty
  question_types: InterviewQuestionType[]
  question_count: number
  status: 'pending' | 'in_progress' | 'completed'
  current_question_order: number
  overall_score?: number
  score?: number
  created_at: string
  started_at?: string
  completed_at?: string
  questions?: InterviewQuestion[]
}

export interface AnswerSubmitResult {
  evaluation: {
    question_id: number
    score: number
    dimension_scores: Record<string, number>
    matched_points: string[]
    missing_points: string[]
    feedback: string
    follow_up_question?: string
  }
  next_question?: InterviewQuestion
  answered_count: number
  total_questions: number
}

export interface InterviewReport {
  id: number
  overall_score: number
  dimension_scores: Record<string, number>
  summary: string
  strengths: string[]
  weaknesses: string[]
  improvement_plan_7_days: string[]
  improvement_plan_30_days: string[]
}

export interface QuestionBankItem {
  id: number
  weakness: string
  question_type: InterviewQuestionType
  question: string
  difficulty: InterviewDifficulty
  reference_points: string[]
}

export interface InterviewReportDetail extends InterviewItem {
  questions: InterviewQuestion[]
  report: InterviewReport
  question_bank: QuestionBankItem[]
}
