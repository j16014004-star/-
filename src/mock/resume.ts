import { registerMock } from './index'

export function setupResumeMock() {
  // Get resume list
  registerMock('get', '/resumes', (params: any) => {
    const page = params?.page || 1
    const pageSize = params?.page_size || 10
    const items = [
      {
        id: 1,
        title: '前端开发工程师简历',
        file_type: 'pdf',
        file_url: '/mock/resumes/resume_1.pdf',
        file_size: 245760,
        score: 85,
        status: 'completed',
        analysis: {
          score: 85,
          strengths: ['技术栈匹配度高', '项目经验丰富', '有大型项目架构经验'],
          weaknesses: ['缺少性能优化相关描述', '团队协作经历描述不足'],
          suggestions: ['补充Webpack/Vite构建优化经验', '增加跨团队协作案例', '突出性能优化成果'],
          missing_keywords: ['Webpack', 'CI/CD', 'Docker', '性能优化'],
          format_score: 90,
          content_score: 82,
          relevance_score: 88,
        },
        created_at: '2026-06-28T10:30:00.000Z',
        updated_at: '2026-07-10T14:20:00.000Z',
      },
      {
        id: 2,
        title: '全栈开发简历',
        file_type: 'pdf',
        file_url: '/mock/resumes/resume_2.pdf',
        file_size: 312576,
        score: 72,
        status: 'completed',
        analysis: {
          score: 72,
          strengths: ['后端技术扎实', '数据库设计能力好'],
          weaknesses: ['前端技能描述较浅', '项目成果量化不足'],
          suggestions: ['补充前端框架深度使用经验', '用量化数据支撑项目成果', '增加系统设计案例'],
          missing_keywords: ['Vue3', 'TypeScript', '微服务', 'Redis'],
          format_score: 85,
          content_score: 68,
          relevance_score: 75,
        },
        created_at: '2026-06-25T09:15:00.000Z',
        updated_at: '2026-07-08T11:45:00.000Z',
      },
      {
        id: 3,
        title: 'Java后端开发简历',
        file_type: 'word',
        file_size: 198656,
        score: 68,
        status: 'completed',
        analysis: {
          score: 68,
          strengths: ['Java基础扎实', 'Spring框架熟练'],
          weaknesses: ['项目经历偏传统', '缺少微服务实践经验'],
          suggestions: ['补充Spring Cloud微服务项目', '增加高并发处理经验', '补充容器化部署经验'],
          missing_keywords: ['Spring Cloud', 'Kubernetes', 'Docker', '消息队列'],
          format_score: 75,
          content_score: 65,
          relevance_score: 70,
        },
        created_at: '2026-06-20T16:00:00.000Z',
        updated_at: '2026-07-05T09:30:00.000Z',
      },
      {
        id: 4,
        title: '数据分析师简历',
        file_type: 'pdf',
        file_size: 180224,
        score: 90,
        status: 'completed',
        analysis: {
          score: 90,
          strengths: ['数据分析方法论完整', '可视化能力突出', '业务理解深入'],
          weaknesses: ['机器学习项目偏少', '大数据工具经验不足'],
          suggestions: ['补充机器学习模型实战经验', '增加Spark/Flink使用经验', '突出业务驱动分析案例'],
          missing_keywords: ['Spark', 'Flink', 'TensorFlow', 'AB测试'],
          format_score: 95,
          content_score: 88,
          relevance_score: 92,
        },
        created_at: '2026-06-18T13:00:00.000Z',
        updated_at: '2026-07-12T16:10:00.000Z',
      },
      {
        id: 5,
        title: '产品经理简历',
        file_type: 'pdf',
        file_size: 220160,
        score: 78,
        status: 'completed',
        analysis: {
          score: 78,
          strengths: ['产品方法论扎实', '跨部门协作经验丰富'],
          weaknesses: ['数据驱动决策描述不足', '技术理解深度不够'],
          suggestions: ['补充数据驱动产品决策案例', '增加与研发团队协作细节', '突出产品上线后数据提升'],
          missing_keywords: ['PRD', '用户研究', 'AARRR', '数据分析'],
          format_score: 82,
          content_score: 76,
          relevance_score: 80,
        },
        created_at: '2026-06-15T11:20:00.000Z',
        updated_at: '2026-07-01T08:00:00.000Z',
      },
    ]
    return {
      items: items.slice(0, pageSize),
      total: items.length,
      page,
      page_size: pageSize,
    }
  })

  // Get resume detail
  registerMock('get', '/resumes/:id', (params: any) => {
    const id = parseInt(params.id)
    return {
      id,
      title: id === 1 ? '前端开发工程师简历' : '全栈开发简历',
      file_type: 'pdf',
      file_url: '/mock/resumes/resume_' + id + '.pdf',
      file_size: 245760 + id * 10000,
      score: 85 - id * 5,
      status: 'completed',
      analysis: {
        score: 85 - id * 5,
        strengths: ['技术栈匹配度高', '项目经验丰富'],
        weaknesses: ['缺少性能优化描述', '团队协作描述不足'],
        suggestions: ['补充构建优化经验', '增加协作案例'],
        missing_keywords: ['Webpack', 'CI/CD', 'Docker'],
        format_score: 90,
        content_score: 80,
        relevance_score: 85,
      },
      created_at: '2026-06-28T10:30:00.000Z',
      updated_at: '2026-07-10T14:20:00.000Z',
      extracted_text: '张三\n前端工程师\n\n具备 Vue 3、TypeScript 和 Vite 项目开发经验。\n负责企业管理系统的前端开发与性能优化。',
      chunks: [
        {
          index: 1,
          text: '张三\n前端工程师\n具备 Vue 3、TypeScript 和 Vite 项目开发经验。',
          metadata: { page: 1 },
        },
        {
          index: 2,
          text: '负责企业管理系统的前端开发与性能优化，与后端协作完成接口联调。',
          metadata: { page: 1 },
        },
      ],
    }
  })

  // Upload resume
  registerMock('post', '/resumes/upload', (params: any) => {
    return {
      id: Math.floor(Math.random() * 1000) + 10,
      title: params.title || '新上传简历',
      file_type: 'pdf',
      file_url: '/mock/resumes/new_resume.pdf',
      file_size: 150000,
      score: null,
      status: 'pending',
      analysis: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  })

  // Download resume
  registerMock('get', '/resumes/:id/download', (params: any) => {
    return {
      filename: `resume_${params.id}.pdf`,
    }
  })

  // Delete resume
  registerMock('delete', '/resumes/:id', () => {
    return null
  })

  // Analyze resume
  registerMock('post', '/resumes/:id/analyze', () => {
    return {
      score: 82,
      strengths: ['技术栈覆盖面广', '项目经验与岗位匹配度高', '有开源项目贡献经历'],
      weaknesses: ['工作经历时间线有断档', '部分技能描述过于简略'],
      suggestions: [
        '补充近期的技术学习经历填补时间断档',
        '对核心技能增加具体的使用年限和熟练度描述',
        '增加项目成果的量化指标（性能提升百分比、用户增长数等）',
      ],
      missing_keywords: ['TypeScript高级类型', '前端性能监控', '单元测试覆盖', 'GraphQL'],
      format_score: 88,
      content_score: 78,
      relevance_score: 85,
    }
  })

  // Optimize resume
  registerMock('post', '/resumes/:id/optimize', () => {
    return {
      original: '负责公司前端项目的开发与维护，使用Vue.js框架进行页面开发，与后端配合完成接口联调。',
      optimized: '主导公司核心前端项目的架构设计与开发，基于Vue3 + TypeScript技术栈实现模块化开发，通过自定义Hook封装复用逻辑使代码复用率提升40%；优化Webpack构建配置，将打包体积缩减35%，加载速度提升50%。',
      changes: [
        {
          section: '工作经历',
          original: '负责公司前端项目的开发与维护',
          optimized: '主导公司核心前端项目的架构设计与开发',
          reason: '使用"主导"、"核心"等强动词替代"负责"，体现主动性；增加"架构设计"突显技术深度',
        },
        {
          section: '技术实现',
          original: '使用Vue.js框架进行页面开发',
          optimized: '基于Vue3 + TypeScript技术栈实现模块化开发，通过自定义Hook封装复用逻辑使代码复用率提升40%',
          reason: '具体化技术栈版本，增加量化成果（代码复用率提升40%）',
        },
        {
          section: '性能优化',
          original: '与后端配合完成接口联调',
          optimized: '优化Webpack构建配置，将打包体积缩减35%，加载速度提升50%',
          reason: '将常规协作描述替换为更具竞争力的性能优化成果，提供具体数据支撑',
        },
      ],
    }
  })
}
