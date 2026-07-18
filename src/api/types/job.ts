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
  resume_source: JobResumeSource
  resume_optimization_id?: number
  cover_letter?: string
}

export type JobResumeSource = 'original' | 'optimized'

export interface JobApplication {
  id: number
  job_id: number
  resume_id: number
  resume_source?: JobResumeSource
  resume_optimization_id?: number | null
  status: 'pending' | 'submitted' | 'viewed' | 'interviewing' | 'rejected' | 'accepted'
  apply_type: 'manual' | 'auto' | 'agent'
  applied_at: string
  agent_task_id?: number | null
}

export type JobPlatformLoginStatus = 'not_logged_in' | 'waiting_login' | 'logged_in' | 'expired' | 'failed' | 'unknown'

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
  resume_source: JobResumeSource
  resume_optimization_id?: number
  target_role?: string
  target_city?: string
  limit?: number
  force_refresh?: boolean
}

export type PlatformLoginSessionStatus = 'waiting_login' | 'logged_in' | 'expired' | 'failed'

export interface PlatformLoginSession {
  login_session_id: string
  source: string
  source_name: string
  status: PlatformLoginSessionStatus
  login_mode: 'server_browser' | 'remote_browser'
  login_url?: string
  browser_url?: string | null
  expires_at: string
  error_message?: string | null
  recommend_task_id?: string | null
  recommend_status?: JobRecommendTaskStatus | null
  recommend_poll_after_seconds?: number | null
  poll_after_seconds: number
}

export type PlatformLoginStatus = PlatformLoginSession

export interface StartRecommendationParams {
  resume_id: number
  resume_source?: JobResumeSource
  resume_optimization_id?: number
  source: string
  login_session_id: string
  target_role?: string
  target_city?: string
  limit?: number
  force_refresh?: boolean
}

export type JobRecommendTaskStatus = 'pending' | 'crawling' | 'matching' | 'success' | 'no_results' | 'failed' | 'need_login'

export type JobRecommendFailureCode =
  | 'no_exact_results'
  | 'no_matching_jobs'
  | 'parse_failed'
  | 'crawl_failed'
  | 'network_access_denied'
  | string

export interface JobCrawlDiagnostics {
  query_count?: number
  raw_items?: number
  parsed_items?: number
  accepted_items?: number
  invalid_items?: number
  duplicate_items?: number
  no_result_queries?: number
  knowledge_retrieval?: Record<string, unknown>
  freshness?: Record<string, unknown>
  [key: string]: unknown
}

export interface JobRecommendTask {
  task_id: string
  login_session_id?: string | null
  status: JobRecommendTaskStatus
  progress?: number
  source: string
  source_name?: string
  resume_id: number
  resume_source?: JobResumeSource
  resume_optimization_id?: number | null
  target_role?: string
  target_city?: string
  extracted_skills?: string[]
  search_keywords?: string[]
  total_found?: number
  total_saved?: number
  total_matched?: number
  failure_code?: JobRecommendFailureCode | null
  error_message?: string | null
  crawl_diagnostics?: JobCrawlDiagnostics | null
  created_at?: string
  started_at?: string
  finished_at?: string | null
}

export interface CurrentJobRecommendTask {
  task: JobRecommendTask | null
}

export interface JobRecommendResultParams {
  page?: number
  page_size?: number
}

export interface JobRecommendResults {
  task_id: string
  resume_id: number
  resume_source?: JobResumeSource
  resume_optimization_id?: number | null
  source: string
  source_name?: string
  target_role?: string
  target_city?: string
  extracted_skills?: string[]
  search_keywords?: string[]
  items: Job[]
  total: number
  page: number
  page_size: number
}
