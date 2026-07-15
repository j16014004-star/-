import type { Job } from '@/types'

export interface JobSearchParams {
  keywords?: string
  city?: string
  salary_min?: number
  salary_max?: number
  source?: string
  page?: number
  page_size?: number
}

export interface JobApplyParams {
  resume_id: number
  cover_letter?: string
}

export interface JobApplication {
  id: number
  job_id: number
  resume_id: number
  status: 'pending' | 'submitted' | 'viewed' | 'interviewing' | 'rejected' | 'accepted'
  apply_type: 'manual' | 'auto'
  applied_at: string
  agent_task_id?: number | null
}

export type JobPlatformLoginStatus = 'not_logged_in' | 'logged_in' | 'expired' | 'unknown'

export interface JobPlatform {
  source: string
  name: string
  enabled: boolean
  login_required: boolean
  login_status: JobPlatformLoginStatus
}

export interface JobPlatformList {
  items: JobPlatform[]
}

export interface StartPlatformLoginParams {
  source: string
  resume_id: number
}

export type PlatformLoginSessionStatus = 'waiting_login' | 'logged_in' | 'expired' | 'failed'

export interface PlatformLoginSession {
  login_session_id: string
  source: string
  source_name: string
  status: PlatformLoginSessionStatus
  login_url?: string
  expires_in?: number
}

export interface PlatformLoginStatus {
  login_session_id: string
  source: string
  status: PlatformLoginSessionStatus
  is_authenticated: boolean
  message?: string
}

export interface StartRecommendationParams {
  resume_id: number
  source: string
  login_session_id: string
  limit?: number
}

export type JobRecommendTaskStatus = 'pending' | 'crawling' | 'matching' | 'success' | 'failed' | 'need_login'

export interface JobRecommendTask {
  task_id: string
  status: JobRecommendTaskStatus
  progress?: number
  source: string
  source_name?: string
  resume_id: number
  extracted_skills?: string[]
  total_found?: number
  total_saved?: number
  total_matched?: number
  message?: string
  error_message?: string | null
  started_at?: string
  finished_at?: string | null
}

export interface JobRecommendResultParams {
  page?: number
  page_size?: number
}

export interface JobRecommendResults {
  task_id: string
  resume_id: number
  source: string
  source_name?: string
  extracted_skills?: string[]
  items: Job[]
  total: number
  page: number
  page_size: number
}
