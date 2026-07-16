export type AITaskStatus =
  | 'pending'
  | 'preparing'
  | 'generating'
  | 'validating'
  | 'saving'
  | 'success'
  | 'failed'
  | 'cancelled'

export type AITaskType =
  | 'resume_optimization'
  | 'career_plan'
  | 'career_plan_question'
  | 'career_stage_assessment'
  | 'career_stage_assessment_evaluation'

export interface AITask {
  task_id: string
  task_type: AITaskType
  status: AITaskStatus
  progress: number
  result_id: number | null
  error_message: string | null
  poll_after_seconds: number
}

export interface AIStartTaskResult {
  task_id: string
  status: AITaskStatus
  result_id?: number | null
  poll_after_seconds: number
}
