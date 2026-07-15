export interface ResumeOptimizeParams {
  resume_id: number
  optimization_type: 'general' | 'target_role'
  target_role?: string
  optimization_focus: Array<'work_experience' | 'project_experience' | 'skills' | 'ats' | 'all'>
  style: 'professional' | 'technical' | 'management' | 'graduate'
  preserve_structure: boolean
}

export interface ResumeOptimizationContentParams {
  resume_id: number
  optimization_id: number
  optimized_content: string
}

export interface ResumeOptimizationAiPreviewParams extends ResumeOptimizationContentParams {
  confirmation_questions: string[]
  feedback?: string
}

export interface ResumeOptimizationManualConfirmItem {
  question: string
  answer: string
}

export interface ResumeOptimizationManualPreviewParams extends ResumeOptimizationContentParams {
  confirmations: ResumeOptimizationManualConfirmItem[]
}

export interface ResumeOptimizationConfirmationPreview {
  preview_id?: string
  added_content: string
  optimized_content: string
  summary: string
  resolved_questions: string[]
  remaining_questions: string[]
  change_items: Array<{
    section: string
    original: string
    optimized: string
    reason: string
    evidence?: string
    requires_confirmation?: boolean
  }>
  has_changes: boolean
}

export interface ResumeOptimizationConfirmationAction {
  type: 'ai' | 'manual' | 'dismiss'
  title: string
  questions: string[]
  added_content?: string
  summary?: string
  feedback?: string
  created_at: string
}

export interface ResumeOptimizationSaveParams extends ResumeOptimizationContentParams {
  confirmation_actions: ResumeOptimizationConfirmationAction[]
  change_items: ResumeOptimizationConfirmationPreview['change_items']
  confirmation_questions: string[]
}

export interface ResumeOptimizationDismissConfirmParams {
  resume_id: number
  optimization_id: number
  confirmation_questions: string[]
}
