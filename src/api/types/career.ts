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
