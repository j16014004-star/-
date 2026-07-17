import type { JobResumeSource } from './job'

export type HrAutomationMode = 'full_auto' | 'assisted' | 'manual'
export type HrWorkspaceStatus =
  | 'draft'
  | 'applying'
  | 'applied'
  | 'communicating'
  | 'interview_pending'
  | 'interview_scheduled'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled'

export interface HrAutomationPermissions {
  auto_apply: boolean
  auto_greeting: boolean
  auto_reply: boolean
  auto_schedule_interview: boolean
}

export interface HrAutomationOverview {
  total_workspaces: number
  active_workspaces: number
  unread_messages: number
  pending_confirmations: number
  upcoming_interviews: number
}

export interface HrAutomationPreflightParams {
  job_id: number
  source: string
}

export interface HrAutomationPreflight {
  source: string
  source_name: string
  platform_login_status: 'logged_in' | 'not_logged_in' | 'expired' | 'failed' | 'unknown'
  manual_login_verified: boolean
  can_start: boolean
  reason?: string | null
  already_applied?: boolean
  next_action?: 'start_application' | 'resume_communication'
  workspace_id?: number | null
  checked_at: string
}

export interface CreateHrWorkspaceParams {
  job_id: number
  source: string
  resume_id: number
  resume_source: JobResumeSource
  resume_optimization_id?: number
  automation_mode: HrAutomationMode
  permissions: HrAutomationPermissions
  manual_login_confirmed: true
}

export interface HrWorkspaceSummary {
  id: number
  job_id: number
  job_title: string
  company: string
  city?: string
  salary?: string
  source: string
  source_name: string
  source_url?: string | null
  hr_name?: string | null
  status: HrWorkspaceStatus
  automation_mode: HrAutomationMode
  platform_login_status: HrAutomationPreflight['platform_login_status']
  unread_count: number
  pending_confirmation_count: number
  last_message?: string | null
  last_message_at?: string | null
  sync_status?: 'never' | 'syncing' | 'success' | 'failed' | 'login_expired' | 'network_denied'
  sync_error?: string | null
  last_synced_at?: string | null
  platform_snapshot?: {
    source?: string
    application_status?: string
    thread_inline?: boolean
    selector_used?: string | null
    message_node_count?: number
    received_message_count?: number
    conversation_id?: string | null
    conversation_label?: string | null
    thread_available?: boolean
  } | null
  created_at: string
  updated_at: string
}

export interface HrWorkspace extends HrWorkspaceSummary {
  resume_id: number
  resume_source: JobResumeSource
  resume_optimization_id?: number | null
  permissions: HrAutomationPermissions
  progress: number
  current_step?: string | null
  error_message?: string | null
  interview?: HrInterviewSchedule | null
  actions?: HrPendingAction[]
  pending_actions?: HrPendingAction[]
}

export interface HrWorkspaceList {
  items: HrWorkspaceSummary[]
  total: number
}

export interface HrConversationMessage {
  id: number
  workspace_id: number
  action_id?: number | null
  sender_type: 'hr' | 'user' | 'ai' | 'system'
  content: string
  status: 'pending_confirmation' | 'sending' | 'sent' | 'read' | 'failed'
  is_ai_generated: boolean
  requires_confirmation: boolean
  sent_at?: string | null
  created_at?: string
}

export interface HrPendingAction {
  id: number
  action_type: 'submit_application' | 'send_message' | 'schedule_interview' | string
  status: 'waiting_confirmation' | 'pending' | 'executing' | 'success' | 'failed' | 'rejected'
  content: string
  reason?: string | null
  payload?: Record<string, unknown> | null
  requires_confirmation: boolean
  error_message?: string | null
  created_at: string
}

export interface HrMessageSendResult {
  message: HrConversationMessage
  action_id: number
  waiting_confirmation: boolean
}

export interface HrMessageSyncResult {
  new_messages: number
  unread_count: number
  platform_login_status: HrAutomationPreflight['platform_login_status']
  sync_status?: HrWorkspaceSummary['sync_status']
  sync_error?: string | null
  last_synced_at?: string | null
  platform_snapshot?: HrWorkspaceSummary['platform_snapshot']
  automation_action?:
    | 'reply_queued'
    | 'reply_confirmation_required'
    | 'interview_confirmation_required'
    | null
  action_id?: number
  interview_detected?: boolean
  sync_skipped?: boolean
}

export interface HrReplySuggestion {
  id?: string
  content: string
  reason?: string
}

export interface HrReplySuggestionResult {
  items: HrReplySuggestion[]
  ai_task_id: string
  retrieval_source?: 'qdrant_vector' | 'local_keyword' | 'local_keyword_fallback' | string
  retrieval_error?: string | null
  retrieved_chunks?: Array<{
    chunk_id: string
    source_file: string
    section: string
    score: number
  }>
}

export interface HrOperationLog {
  id: number
  action: string
  description: string
  status: 'pending' | 'success' | 'failed' | 'waiting_confirmation'
  created_at: string
}

export interface HrInterviewSchedule {
  id: number
  action_id?: number | null
  status: 'proposed' | 'scheduled' | 'rejected' | 'failed' | 'cancelled'
  scheduled_at?: string | null
  end_at?: string | null
  timezone?: string
  interview_type?: string | null
  location?: string | null
  meeting_url?: string | null
  contact_name?: string | null
  evidence?: string | null
  missing_fields?: string[]
  suggested_reply?: string | null
  requires_confirmation: boolean
}

export interface HrInterviewDetectionResult {
  detected: boolean
  interview?: HrInterviewSchedule | null
  action_id?: number | null
  ai_task_id?: string
  reused?: boolean
}

export interface HrInterviewList {
  items: HrInterviewSchedule[]
  total: number
}

export interface HrInterviewCreateParams {
  scheduled_at: string
  end_at?: string
  timezone?: string
  interview_type: string
  location?: string
  meeting_url?: string
  contact_name?: string
  reply_content: string
}

export interface UpdateHrWorkspaceModeParams {
  automation_mode: HrAutomationMode
  permissions: HrAutomationPermissions
}

export interface SendHrMessageParams {
  content: string
  send_mode: 'manual' | 'ai_suggestion'
}

export interface HrWorkspaceControlParams {
  action: 'pause' | 'resume' | 'terminate' | 'take_over'
}

export interface ConfirmHrActionParams {
  approved: boolean
  note?: string
}
