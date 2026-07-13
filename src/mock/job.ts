import { registerMock } from './index'

export function setupJobMock() {
  registerMock('get', '/jobs/recommendations', (params: any) => {
    const page = params?.page || 1
    const pageSize = params?.page_size || 10

    const allJobs = [
      {
        id: 1,
        company: '字节跳动',
        company_logo: 'https://img.bosszhipin.com/logo/byte.png',
        title: '高级前端开发工程师',
        salary_min: 30000,
        salary_max: 60000,
        city: '北京',
        experience_required: '3-5年',
        education_required: '本科及以上',
        skills: ['Vue3', 'TypeScript', 'Webpack', 'Node.js', '性能优化'],
        description: '负责抖音电商平台前端架构设计与开发，参与大流量高并发场景下的性能优化，推动前端工程化建设。要求有大型前端项目经验，熟悉前端性能优化手段。',
        match_score: 92,
        match_reasons: ['技能匹配度92%', 'Vue3经验高度契合', '有电商项目经验优先'],
        source: 'BOSS直聘',
        url: 'https://www.zhipin.com/job/1',
        created_at: '2026-07-10T10:00:00.000Z',
      },
      {
        id: 2,
        company: '阿里巴巴',
        company_logo: 'https://img.bosszhipin.com/logo/alibaba.png',
        title: '前端架构师',
        salary_min: 40000,
        salary_max: 70000,
        city: '杭州',
        experience_required: '5-10年',
        education_required: '本科及以上',
        skills: ['Vue3/React', 'Node.js', '微前端', 'Webpack/Vite', '架构设计'],
        description: '负责企业级中后台前端架构设计与技术规划，主导前端基础建设，制定技术标准和规范。需要有丰富的架构设计经验和技术团队指导能力。',
        match_score: 78,
        match_reasons: ['架构经验匹配', '技术栈通用', 'Node.js技能契合'],
        source: '拉勾网',
        url: 'https://www.lagou.com/job/2',
        created_at: '2026-07-09T14:30:00.000Z',
      },
      {
        id: 3,
        company: '腾讯',
        company_logo: 'https://img.bosszhipin.com/logo/tencent.png',
        title: '全栈开发工程师',
        salary_min: 25000,
        salary_max: 50000,
        city: '深圳',
        experience_required: '3-5年',
        education_required: '本科及以上',
        skills: ['TypeScript', 'Node.js', 'React', 'MongoDB', 'Docker'],
        description: '参与腾讯云产品的全栈开发，负责前后端功能设计与实现，打造高可用的云服务产品。全栈能力要求强，有云服务开发经验者优先。',
        match_score: 65,
        match_reasons: ['TypeScript技能优秀', 'Node.js基础扎实', '需补充React经验'],
        source: 'BOSS直聘',
        url: 'https://www.zhipin.com/job/3',
        created_at: '2026-07-08T09:00:00.000Z',
      },
      {
        id: 4,
        company: '美团',
        company_logo: 'https://img.bosszhipin.com/logo/meituan.png',
        title: '资深前端开发工程师',
        salary_min: 28000,
        salary_max: 55000,
        city: '北京',
        experience_required: '5-10年',
        education_required: '本科及以上',
        skills: ['Vue3', 'TypeScript', '小程序', '性能优化', '工程化'],
        description: '负责美团到店事业群前端开发，优化用户端体验和商家端效率，推动前端组件化建设。有大型C端项目经验优先。',
        match_score: 85,
        match_reasons: ['Vue3经验对口', '性能优化能力匹配', '工程化经验契合'],
        source: '猎聘',
        url: 'https://www.liepin.com/job/4',
        created_at: '2026-07-07T16:45:00.000Z',
      },
      {
        id: 5,
        company: '小红书',
        company_logo: 'https://img.bosszhipin.com/logo/redbook.png',
        title: '前端技术专家',
        salary_min: 35000,
        salary_max: 65000,
        city: '上海',
        experience_required: '5-10年',
        education_required: '本科及以上',
        skills: ['前端架构', 'Vue3/React', 'Node.js', 'SSR', 'CI/CD'],
        description: '负责小红书社区前端技术架构，提升开发效率和用户体验，探索新技术在前端的应用。需要有技术前瞻性和强烈的技术热情。',
        match_score: 70,
        match_reasons: ['架构能力扎实', '技术广度好', 'Node.js技能加分'],
        source: 'BOSS直聘',
        url: 'https://www.zhipin.com/job/5',
        created_at: '2026-07-06T11:20:00.000Z',
      },
      {
        id: 6,
        company: '百度',
        company_logo: 'https://img.bosszhipin.com/logo/baidu.png',
        title: '前端开发工程师（AI方向）',
        salary_min: 26000,
        salary_max: 48000,
        city: '北京',
        experience_required: '3-5年',
        education_required: '硕士及以上',
        skills: ['TypeScript', 'React', 'Python', 'AI产品', 'WebGL'],
        description: '参与百度AI产品的Web端开发，打造智能交互界面，探索前端与AI技术的融合。有AI产品开发经验或WebGL经验者优先。',
        match_score: 55,
        match_reasons: ['TypeScript基础好', '需补充React经验', 'AI方向需学习'],
        source: '百度招聘',
        url: 'https://talent.baidu.com/job/6',
        created_at: '2026-07-05T08:30:00.000Z',
      },
      {
        id: 7,
        company: '京东',
        company_logo: 'https://img.bosszhipin.com/logo/jd.png',
        title: '资深前端工程师（交易方向）',
        salary_min: 27000,
        salary_max: 52000,
        city: '北京',
        experience_required: '5-10年',
        education_required: '本科及以上',
        skills: ['Vue3', 'TypeScript', '高并发', '性能优化', '监控体系'],
        description: '负责京东核心交易链路前端开发，保障大促期间系统稳定性，优化用户下单转化率。有电商交易系统经验者优先。',
        match_score: 88,
        match_reasons: ['Vue3技能高度匹配', '性能优化经验对口', '技术挑战契合'],
        source: '京东招聘',
        url: 'https://zhaopin.jd.com/job/7',
        created_at: '2026-07-04T13:15:00.000Z',
      },
      {
        id: 8,
        company: '网易',
        company_logo: 'https://img.bosszhipin.com/logo/netease.png',
        title: '前端开发工程师',
        salary_min: 20000,
        salary_max: 40000,
        city: '广州',
        experience_required: '1-3年',
        education_required: '本科及以上',
        skills: ['Vue.js', 'JavaScript', 'CSS', 'Webpack', 'Git'],
        description: '参与网易有道产品线前端开发，负责功能迭代和性能优化。要求有扎实的前端基础，对用户体验有追求。',
        match_score: 60,
        match_reasons: ['Vue基础匹配', '薪资期望偏低', '更适合初级岗位'],
        source: '拉勾网',
        url: 'https://www.lagou.com/job/8',
        created_at: '2026-07-03T10:00:00.000Z',
      },
    ]

    // Filter by keywords if provided
    let filtered = allJobs
    if (params?.keywords) {
      const kw = params.keywords.toLowerCase()
      filtered = allJobs.filter(
        (j) =>
          j.title.toLowerCase().includes(kw) ||
          j.company.toLowerCase().includes(kw) ||
          j.skills.some((s) => s.toLowerCase().includes(kw))
      )
    }
    if (params?.city) {
      filtered = filtered.filter((j) => j.city.includes(params.city))
    }

    return {
      items: filtered.slice(0, pageSize),
      total: filtered.length,
      page,
      page_size: pageSize,
    }
  })

  // Get job detail
  registerMock('get', '/jobs/:id', (params: any) => {
    const id = parseInt(params.id)
    return {
      id,
      company: '字节跳动',
      company_logo: 'https://img.bosszhipin.com/logo/byte.png',
      title: '高级前端开发工程师',
      salary_min: 30000,
      salary_max: 60000,
      city: '北京',
      experience_required: '3-5年',
      education_required: '本科及以上',
      skills: ['Vue3', 'TypeScript', 'Webpack', 'Node.js', '性能优化'],
      description: '负责抖音电商平台前端架构设计与开发，参与大流量高并发场景下的性能优化，推动前端工程化建设。\n\n岗位职责：\n1. 负责电商业务前端架构设计与核心模块开发\n2. 参与前端性能优化，提升页面加载速度和交互体验\n3. 推动前端工程化建设，提升团队开发效率\n4. 参与技术方案评审和技术分享\n\n任职要求：\n1. 3年以上前端开发经验，有大型Web项目经验\n2. 精通Vue3/React等主流框架，对响应式原理有深入理解\n3. 熟悉TypeScript，有大型项目TypeScript实践经验\n4. 熟悉前端工程化工具链（Webpack、Vite、Rollup等）\n5. 有性能优化经验，熟悉浏览器渲染原理\n6. 良好的沟通能力和团队协作精神',
      match_score: 92,
      match_reasons: ['技能匹配度92%', 'Vue3经验高度契合', '有电商项目经验优先'],
      source: 'BOSS直聘',
      url: 'https://www.zhipin.com/job/' + id,
      created_at: '2026-07-10T10:00:00.000Z',
    }
  })
}