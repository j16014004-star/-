import { registerMock } from './index'

export function setupAgentMock() {
  // Get agent tasks
  registerMock('get', '/agent/tasks', () => {
    return [
      {
        id: 1,
        type: 'search',
        status: 'running',
        progress: 65,
        config: {
          keywords: '前端开发 北京',
          salary_range: [25000, 50000],
          cities: ['北京'],
          auto_apply: false,
          schedule: '每天 09:00',
        },
        logs: [
          { id: 1, message: '开始搜索任务：前端开发 北京', level: 'info', created_at: '2026-07-13T09:00:00.000Z' },
          { id: 2, message: '已扫描 BOSS直聘 第1页', level: 'info', created_at: '2026-07-13T09:01:00.000Z' },
          { id: 3, message: '找到15个匹配职位', level: 'info', created_at: '2026-07-13T09:02:00.000Z' },
          { id: 4, message: '正在筛选高匹配度职位...', level: 'info', created_at: '2026-07-13T09:02:30.000Z' },
          { id: 5, message: '已筛选出8个优质职位，匹配度>80%', level: 'info', created_at: '2026-07-13T09:03:00.000Z' },
        ],
        applications: [
          { id: 1, company: '字节跳动', position: '高级前端开发工程师', status: 'viewed', submitted_at: '2026-07-13T09:05:00.000Z' },
          { id: 2, company: '美团', position: '资深前端开发工程师', status: 'submitted', submitted_at: '2026-07-13T09:06:00.000Z' },
          { id: 3, company: '京东', position: '资深前端工程师（交易方向）', status: 'submitted', submitted_at: '2026-07-13T09:06:30.000Z' },
        ],
        created_at: '2026-07-13T09:00:00.000Z',
        updated_at: '2026-07-13T09:06:30.000Z',
      },
      {
        id: 2,
        type: 'filter',
        status: 'completed',
        progress: 100,
        config: {
          min_match_score: 70,
          exclude_companies: [],
          preferred_industries: ['互联网', '科技'],
          keywords_include: ['Vue3', 'TypeScript'],
          keywords_exclude: ['React'],
        },
        logs: [
          { id: 6, message: '筛选任务启动', level: 'info', created_at: '2026-07-12T14:00:00.000Z' },
          { id: 7, message: '正在分析120个职位...', level: 'info', created_at: '2026-07-12T14:00:05.000Z' },
          { id: 8, message: '按技能要求过滤：Vue3, TypeScript', level: 'info', created_at: '2026-07-12T14:00:10.000Z' },
          { id: 9, message: '过滤完成，共匹配22个职位', level: 'info', created_at: '2026-07-12T14:00:30.000Z' },
          { id: 10, message: '按匹配度排序完成', level: 'info', created_at: '2026-07-12T14:01:00.000Z' },
        ],
        applications: [],
        created_at: '2026-07-12T14:00:00.000Z',
        updated_at: '2026-07-12T14:01:00.000Z',
      },
      {
        id: 3,
        type: 'track',
        status: 'running',
        progress: 30,
        config: {
          application_ids: [1, 2, 3],
          check_interval_minutes: 30,
          notify_on_change: true,
        },
        logs: [
          { id: 11, message: '跟踪任务启动，监控3个申请', level: 'info', created_at: '2026-07-13T09:10:00.000Z' },
          { id: 12, message: '字节跳动 前端开发工程师: 状态更新为 "简历被查看"', level: 'info', created_at: '2026-07-13T09:30:00.000Z' },
          { id: 13, message: '下次检查时间: 10:00', level: 'info', created_at: '2026-07-13T09:30:01.000Z' },
        ],
        applications: [
          { id: 1, company: '字节跳动', position: '高级前端开发工程师', status: 'viewed', submitted_at: '2026-07-12T10:00:00.000Z' },
          { id: 2, company: '美团', position: '资深前端开发工程师', status: 'submitted', submitted_at: '2026-07-12T11:00:00.000Z' },
          { id: 3, company: '京东', position: '资深前端工程师（交易方向）', status: 'submitted', submitted_at: '2026-07-12T11:30:00.000Z' },
        ],
        created_at: '2026-07-13T09:10:00.000Z',
        updated_at: '2026-07-13T09:30:01.000Z',
      },
    ]
  })

  // Get task detail
  registerMock('get', '/agent/tasks/:id', (params: any) => {
    const id = parseInt(params.id)
    return {
      id,
      type: 'search',
      status: 'running',
      progress: 65,
      config: {
        keywords: '前端开发 北京',
        salary_range: [25000, 50000],
        cities: ['北京'],
        auto_apply: false,
        schedule: '每天 09:00',
      },
      logs: [
        { id: 1, message: '开始搜索任务', level: 'info', created_at: '2026-07-13T09:00:00.000Z' },
        { id: 2, message: '已扫描平台第1页', level: 'info', created_at: '2026-07-13T09:01:00.000Z' },
        { id: 3, message: '找到15个匹配职位', level: 'info', created_at: '2026-07-13T09:02:00.000Z' },
      ],
      applications: [
        { id: 1, company: '字节跳动', position: '高级前端开发工程师', status: 'viewed', submitted_at: '2026-07-13T09:05:00.000Z' },
        { id: 2, company: '美团', position: '资深前端开发工程师', status: 'submitted', submitted_at: '2026-07-13T09:06:00.000Z' },
      ],
      created_at: '2026-07-13T09:00:00.000Z',
      updated_at: '2026-07-13T09:06:30.000Z',
    }
  })

  // Create task
  registerMock('post', '/agent/tasks', (params: any) => {
    return {
      id: Math.floor(Math.random() * 100) + 10,
      type: params.type || 'search',
      status: 'pending',
      progress: 0,
      config: params.config || {},
      logs: [],
      applications: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  })

  // Start task
  registerMock('post', '/agent/tasks/:id/start', () => {
    return { id: 1, type: 'search', status: 'running', progress: 0, config: {}, logs: [], applications: [], created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
  })

  // Pause task
  registerMock('post', '/agent/tasks/:id/pause', () => {
    return { id: 1, type: 'search', status: 'paused', progress: 50, config: {}, logs: [], applications: [], created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
  })

  // Stop task
  registerMock('post', '/agent/tasks/:id/stop', () => {
    return { id: 1, type: 'search', status: 'failed', progress: 65, config: {}, logs: [], applications: [], created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
  })

  // Delete task
  registerMock('delete', '/agent/tasks/:id', () => {
    return null
  })
}