import type { AITask, AITaskType } from '@/api/types/ai'
import type {
  CareerPlan,
  CareerPlanningProfile,
  CareerPlanningProfileParams,
  CareerProjectAttachment,
} from '@/api/types/career'
import type { ResumeOptimizeResult } from '@/types'
import { registerMock } from './index'

interface StoredTask {
  task: AITask
  createdAt: number
}

const tasks = new Map<string, StoredTask>()
const optimizations = new Map<number, ResumeOptimizeResult>()
const profiles = new Map<number, CareerPlanningProfile>()
const plans = new Map<number, CareerPlan>()

let optimizationId = 200
let profileId = 300
let projectFileId = 400
let planId = 500

const createTaskId = () => `mock-${Date.now()}-${Math.random().toString(16).slice(2)}`

const createTask = (taskType: AITaskType, resultId: number): AITask => {
  const task: AITask = {
    task_id: createTaskId(),
    task_type: taskType,
    status: 'pending',
    progress: 5,
    result_id: resultId,
    error_message: null,
    poll_after_seconds: 1,
  }
  tasks.set(task.task_id, { task, createdAt: Date.now() })
  return task
}

const getTaskSnapshot = (stored: StoredTask): AITask => {
  const elapsed = Date.now() - stored.createdAt
  if (elapsed >= 2400) return { ...stored.task, status: 'success', progress: 100 }
  if (elapsed >= 1800) return { ...stored.task, status: 'saving', progress: 88 }
  if (elapsed >= 1200) return { ...stored.task, status: 'validating', progress: 72 }
  if (elapsed >= 600) return { ...stored.task, status: 'generating', progress: 45 }
  return { ...stored.task, status: 'preparing', progress: 18 }
}

const buildOptimization = (): ResumeOptimizeResult => ({
  id: ++optimizationId,
  optimization_summary: '本次优化重点是明确职责、补充技术方法，并将无法确认的信息保留为确认问题。',
  original: '负责后端接口开发和数据库维护，完成相关功能。',
  optimized: '参与后端服务开发，基于 FastAPI 完成业务接口与数据校验，并使用 SQLAlchemy 维护数据访问流程。',
  optimized_content: '参与后端服务开发，基于 FastAPI 完成业务接口与数据校验，并使用 SQLAlchemy 维护数据访问流程。',
  score_improvement: 82,
  change_items: [
    {
      section: '工作经历',
      original: '负责后端接口开发和数据库维护，完成相关功能。',
      optimized: '参与后端服务开发，基于 FastAPI 完成业务接口与数据校验，并使用 SQLAlchemy 维护数据访问流程。',
      reason: '补充具体技术和工作动作，让经历更清晰。',
      evidence: '来源于原简历中的后端接口和数据库相关描述。',
      requires_confirmation: false,
    },
  ],
  confirmation_questions: ['是否有可以公开说明的接口数量、性能提升或业务效果？'],
  created_at: new Date().toISOString(),
})

const buildCareerPlan = (profile: CareerPlanningProfile): CareerPlan => ({
  id: ++planId,
  profile_id: profile.id,
  career_profile_summary: {
    current_stage: profile.experience === 'fresh' ? '职业起步阶段' : '能力提升与方向聚焦阶段',
    core_strengths: profile.skills.slice(0, 4),
    transferable_skills: ['学习能力', '问题分析', '项目协作'],
    main_weaknesses: ['目标岗位能力证据不足', '需要形成可展示的项目成果'],
    summary: '当前背景具备继续深耕技术岗位的基础，建议先确定一个主方向，再通过项目和阶段复盘积累岗位能力证据。',
  },
  recommended_roles: [
    {
      role_name: profile.preferred_target_role || '应用开发工程师',
      match_score: 84,
      priority: 1,
      recommendation_reason: '现有技能与项目经历能够支撑应用开发方向的继续成长。',
      matched_capabilities: profile.skills.slice(0, 4),
      missing_capabilities: ['系统化测试', '项目成果表达'],
      suitable_industries: ['企业服务', '互联网产品', 'AI应用'],
      next_actions: ['选择一个真实业务问题完成作品项目', '根据目标岗位优化简历'],
      is_long_term_direction: true,
    },
    {
      role_name: '技术支持与解决方案工程师',
      match_score: 72,
      priority: 2,
      recommendation_reason: '技术基础和沟通协作能力可以迁移到解决方案方向。',
      matched_capabilities: ['问题分析', '文档整理'],
      missing_capabilities: ['客户沟通案例', '方案演示能力'],
      suitable_industries: ['软件服务', '云服务'],
      next_actions: ['练习技术方案讲解', '整理项目问题排查案例'],
      is_long_term_direction: false,
    },
  ],
  career_goals: {
    short_term: ['确定主目标岗位', '完成一份目标岗位能力清单', '优化一版针对性简历'],
    medium_term: ['完成一个可展示项目', '补齐测试和部署能力', '进行至少两次模拟面试'],
    long_term: ['能够独立负责完整业务模块', '形成稳定的技术方向和作品集'],
  },
  skill_gap_analysis: [
    { skill: '自动化测试', priority: 'high', current_level: '待补充', target_level: '能够编写核心业务测试', reason: '这是保证项目质量的重要能力。' },
    { skill: '项目成果表达', priority: 'high', current_level: '基础', target_level: '能够用证据说明个人贡献', reason: '直接影响简历和面试说服力。' },
  ],
  learning_path: {
    total_weeks: 12,
    hours_per_week: profile.weekly_learning_hours,
    stages: [
      {
        stage: '方向确认与基础补齐',
        duration: '第1-3周',
        goals: ['确定目标岗位', '补齐核心基础'],
        topics: ['岗位能力拆解', '核心技术复习'],
        tasks: ['整理技能清单', '完成基础练习'],
        practice_tasks: ['为现有项目补充测试'],
        deliverables: ['目标岗位能力表', '基础练习记录'],
        acceptance_criteria: ['能够解释目标岗位的核心职责', '完成至少一组可运行测试'],
      },
      {
        stage: '作品项目建设',
        duration: '第4-8周',
        goals: ['完成可展示项目'],
        topics: ['需求拆解', '接口设计', '部署与文档'],
        tasks: ['制定迭代计划', '完成核心功能'],
        practice_tasks: ['部署演示版本', '编写项目说明'],
        deliverables: ['可运行项目', '项目说明文档'],
        acceptance_criteria: ['项目可以独立运行', '能够清晰说明个人贡献'],
      },
      {
        stage: '求职准备与复盘',
        duration: '第9-12周',
        goals: ['形成求职材料和面试能力'],
        topics: ['简历优化', '项目表达', '模拟面试'],
        tasks: ['完成目标岗位简历', '准备项目问答'],
        practice_tasks: ['完成两次模拟面试'],
        deliverables: ['优化简历', '面试复盘记录'],
        acceptance_criteria: ['能够在5分钟内讲清核心项目', '完成一轮计划复盘'],
      },
    ],
  },
  action_plan: {
    this_week: ['选择一个主目标岗位', '整理已有技能和项目证据'],
    this_month: ['完成能力差距清单', '启动作品项目'],
    portfolio_projects: ['围绕真实业务问题完成一个可部署项目'],
    resume_actions: ['补充项目角色和成果', '按目标岗位调整技能顺序'],
    review_points: ['第4周复盘方向', '第8周检查项目成果', '第12周复盘求职准备'],
  },
  risks_and_alternatives: {
    risks: ['学习目标过多导致主线不清晰'],
    assumptions_to_confirm: ['每周是否能稳定投入计划时间'],
    alternative_roles: ['技术支持工程师', '解决方案工程师'],
    adjustment_advice: ['如果连续两周无法完成任务，应减少并行学习主题。'],
  },
  created_at: new Date().toISOString(),
})

export function setupAIMock() {
  registerMock('get', '/ai/tasks/:taskId', (params: Record<string, unknown>) => {
    const stored = tasks.get(String(params.taskId || ''))
    if (!stored) throw new Error('AI 任务不存在')
    return getTaskSnapshot(stored)
  })

  registerMock('post', '/resumes/:id/optimizations', () => {
    const result = buildOptimization()
    optimizations.set(result.id || 0, result)
    const task = createTask('resume_optimization', result.id || 0)
    return { task_id: task.task_id, status: task.status, result_id: task.result_id, poll_after_seconds: 1 }
  })

  registerMock('get', '/resumes/:id/optimizations/:optimizationId', (params: Record<string, unknown>) => {
    return optimizations.get(Number(params.optimizationId)) || buildOptimization()
  })

  registerMock('post', '/career-plans/project-files/upload', (params: Record<string, unknown>) => {
    const file = params.file instanceof File ? params.file : null
    const attachment: CareerProjectAttachment = {
      id: ++projectFileId,
      original_filename: file?.name || '项目说明.txt',
      file_type: (file?.name.split('.').pop() || 'txt').toLowerCase(),
      file_size: file?.size || 0,
      status: 'completed',
      error_message: null,
    }
    return attachment
  })

  registerMock('delete', '/career-plans/project-files/:fileId', () => null)

  registerMock('post', '/career-planning/profiles', (params: Record<string, unknown>) => {
    const payload = params as unknown as CareerPlanningProfileParams
    const now = new Date().toISOString()
    const profile: CareerPlanningProfile = {
      ...payload,
      id: ++profileId,
      created_at: now,
      updated_at: now,
    }
    profiles.set(profile.id, profile)
    return profile
  })

  registerMock('post', '/career-plans', (params: Record<string, unknown>) => {
    const profile = profiles.get(Number(params.profile_id))
    if (!profile) throw new Error('职业规划档案不存在')
    const plan = buildCareerPlan(profile)
    plans.set(plan.id, plan)
    const task = createTask('career_plan', plan.id)
    return {
      task_id: task.task_id,
      status: task.status,
      result_id: plan.id,
      plan_id: plan.id,
      poll_after_seconds: 1,
    }
  })

  registerMock('get', '/career-plans/:planId', (params: Record<string, unknown>) => {
    const plan = plans.get(Number(params.planId))
    if (!plan) throw new Error('职业规划不存在')
    return plan
  })
}
