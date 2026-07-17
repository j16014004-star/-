import type { AIStartTaskResult } from './ai'

export interface CareerProjectAttachment {
  id: number
  original_filename: string
  file_type: string
  file_size: number
  status: 'uploaded' | 'processing' | 'completed' | 'failed'
  error_message?: string | null
}

export interface CareerProjectInput {
  name: string
  description: string
  role: string
  file_ids: number[]
}

export interface CareerPlanningProfileParams {
  education: string
  experience: string
  skills: string[]
  work_description: string
  weekly_learning_hours: number
  preferred_target_role?: string
  projects: CareerProjectInput[]
}

export interface CareerPlanningProfile extends CareerPlanningProfileParams {
  id: number
  created_at: string
  updated_at: string
}

export interface RecommendedRole {
  role_name: string
  match_score: number
  priority: number
  recommendation_reason: string
  matched_capabilities: string[]
  missing_capabilities: string[]
  suitable_industries: string[]
  next_actions: string[]
  is_long_term_direction: boolean
}

export interface CareerGoalGroup {
  short_term: string[]
  medium_term: string[]
  long_term: string[]
}

export interface SkillGapItem {
  skill: string
  priority: 'high' | 'medium' | 'low'
  current_level: string
  target_level: string
  reason: string
}

export interface LearningStage {
  stage: string
  duration: string
  goals: string[]
  topics: string[]
  tasks: string[]
  practice_tasks: string[]
  deliverables: string[]
  acceptance_criteria: string[]
}

export interface CareerPlan {
  id: number
  profile_id: number
  status?: 'processing' | 'completed' | 'accepted' | 'failed'
  accepted_at?: string | null
  previous_plan_id?: number | null
  career_profile_summary: {
    current_stage: string
    core_strengths: string[]
    transferable_skills: string[]
    main_weaknesses: string[]
    summary: string
  }
  recommended_roles: RecommendedRole[]
  career_goals: CareerGoalGroup
  skill_gap_analysis: SkillGapItem[]
  learning_path: {
    total_weeks: number
    hours_per_week: number
    stages: LearningStage[]
  }
  action_plan: {
    this_week: string[]
    this_month: string[]
    portfolio_projects: string[]
    resume_actions: string[]
    review_points: string[]
  }
  risks_and_alternatives: {
    risks: string[]
    assumptions_to_confirm: string[]
    alternative_roles: string[]
    adjustment_advice: string[]
  }
  created_at: string
}

export interface CareerPlanCreateParams {
  profile_id: number
  preferred_target_role?: string
  plan_months?: number
}

export interface CareerPlanStartResult extends AIStartTaskResult {
  plan_id: number
}

export interface CareerPlanAcceptResult {
  plan_id: number
  status: 'accepted'
  accepted_at: string
  execution_plan_id: number
}

export interface CareerPlanRegenerateParams {
  feedback: string
  focus_areas?: string[]
}

export interface CareerPlanRegenerateResult extends AIStartTaskResult {
  plan_id: number
  previous_plan_id: number
}

export type CareerCheckinTaskStatus = 'pending' | 'completed' | 'skipped'

export interface CareerCheckinTask {
  id: number
  execution_plan_id: number
  title: string
  description?: string | null
  task_type: 'learning' | 'practice' | 'deliverable' | 'job_search' | 'review'
  stage: string
  week_no: number
  planned_date?: string | null
  is_required: boolean
  status: CareerCheckinTaskStatus
  checkin_note?: string | null
  checked_in_at?: string | null
  is_advanced?: boolean
  original_planned_date?: string | null
  advanced_at?: string | null
}

export interface CareerCheckinRecord {
  id: number
  task_id: number
  task_title: string
  status: CareerCheckinTaskStatus
  note?: string | null
  checked_in_at: string
}

export interface CareerExecutionOverview {
  id: number
  career_plan_id: number
  status: 'active' | 'paused' | 'completed'
  start_date: string
  end_date?: string | null
  current_week: number
  current_stage: string
  total_tasks: number
  completed_tasks: number
  progress_percent: number
  current_streak: number
  longest_streak: number
  today_tasks: CareerCheckinTask[]
  week_tasks: CareerCheckinTask[]
  all_tasks: CareerCheckinTask[]
  recent_checkins: CareerCheckinRecord[]
  today_completed?: boolean
  can_advance?: boolean
  next_task_available?: boolean
  ahead_task_count?: number
  ahead_days?: number
  stage_progress?: number
  assessment_ready?: boolean
  current_stage_status?: CareerStageStatus
  active_assessment_id?: number | null
}

export interface CareerTaskCheckinParams {
  status: 'completed' | 'pending' | 'skipped'
  note?: string
}

export interface CareerTaskQuestionParams {
  question: string
}

export interface CareerTaskQuestionStartResult extends AIStartTaskResult {
  question_id: number
  task_id: string
}

export interface CareerTaskQuestion {
  id: number
  execution_task_id: number
  question: string
  answer?: string | null
  status: 'pending' | 'answering' | 'answered' | 'failed'
  error_message?: string | null
  created_at: string
  answered_at?: string | null
}

export type CareerStageStatus =
  | 'in_progress'
  | 'ready_for_assessment'
  | 'assessing'
  | 'passed'
  | 'needs_improvement'

export interface CareerAdvanceResult {
  overview: CareerExecutionOverview
  advanced_task: CareerCheckinTask
}

export interface CareerCompleteAllResult {
  completed_count: number
  overview: CareerExecutionOverview
}

export type CareerAssessmentQuestionType =
  | 'single_choice'
  | 'multiple_choice'
  | 'short_answer'
  | 'code'

export interface CareerAssessmentOption {
  key: string
  label: string
}

export interface CareerAssessmentQuestion {
  id: number
  question_type: CareerAssessmentQuestionType
  title: string
  description?: string | null
  options?: CareerAssessmentOption[]
  points: number
  code_language?: string | null
}

export interface CareerStageAssessment {
  id: number
  execution_plan_id: number
  stage: string
  status: 'generating' | 'ready' | 'submitted' | 'evaluating' | 'passed' | 'needs_improvement' | 'failed'
  passing_score: number
  time_limit_minutes?: number | null
  questions: CareerAssessmentQuestion[]
  ai_task_id?: string | null
  created_at: string
}

export interface CareerAssessmentStartResult extends AIStartTaskResult {
  assessment_id: number
}

export interface CareerAssessmentAnswer {
  question_id: number
  answer: string | string[]
}

export interface CareerAssessmentSubmitParams {
  answers: CareerAssessmentAnswer[]
}

export interface CareerAssessmentSubmitResult extends AIStartTaskResult {
  assessment_id: number
}

export interface CareerAssessmentQuestionResult {
  question_id: number
  score: number
  max_score: number
  is_correct?: boolean | null
  user_answer: string | string[]
  reference_answer?: string | string[] | null
  feedback: string
}

export interface CareerAssessmentResult {
  assessment_id: number
  execution_plan_id: number
  stage: string
  status: 'passed' | 'needs_improvement'
  score: number
  passing_score: number
  passed: boolean
  summary: string
  strengths: string[]
  weaknesses: string[]
  improvement_advice: string[]
  question_results: CareerAssessmentQuestionResult[]
  remediation_available: boolean
  evaluated_at: string
}
