import { registerMock } from './index'

export function setupChatMock() {
  // Get chat sessions
  registerMock('get', '/chat/sessions', () => {
    return [
      {
        id: 1,
        title: '简历优化咨询',
        messages: [
          {
            id: 'm1',
            role: 'user',
            content: '请帮我优化简历中的项目描述',
            created_at: '2026-07-12T14:30:00.000Z',
          },
          {
            id: 'm2',
            role: 'assistant',
            content: '好的，请将您的项目描述发送给我，我会根据STAR原则进行优化，突出您的个人贡献和项目成果。',
            created_at: '2026-07-12T14:30:05.000Z',
          },
        ],
        created_at: '2026-07-12T14:30:00.000Z',
        updated_at: '2026-07-12T14:35:00.000Z',
      },
      {
        id: 2,
        title: '面试准备-字节跳动',
        messages: [
          {
            id: 'm3',
            role: 'user',
            content: '我要面试字节跳动前端岗位，请帮我准备面试',
            created_at: '2026-07-11T10:00:00.000Z',
          },
          {
            id: 'm4',
            role: 'assistant',
            content: '好的！字节跳动前端面试通常包括：JavaScript基础、框架原理（Vue/React）、浏览器原理、性能优化、算法与数据结构、项目深挖等环节。请先告诉我您的技术栈和准备的岗位级别。',
            created_at: '2026-07-11T10:00:08.000Z',
          },
          {
            id: 'm5',
            role: 'user',
            content: '我主要用Vue3和TypeScript，准备面试P6级别',
            created_at: '2026-07-11T10:05:00.000Z',
          },
          {
            id: 'm6',
            role: 'assistant',
            content: '好的！针对字节P6级别（高级工程师），我将从以下几个维度帮您准备：\n\n1. **Vue3核心原理**：响应式系统、虚拟DOM、编译优化\n2. **TypeScript高级类型**：泛型约束、条件类型、映射类型\n3. **浏览器与性能**：渲染流程、事件循环、性能指标\n4. **前端工程化**：构建工具、CI/CD、代码质量\n5. **算法与数据结构**：重点准备数组、树、动态规划\n\n需要先从哪个模块开始？',
            created_at: '2026-07-11T10:05:30.000Z',
          },
        ],
        created_at: '2026-07-11T10:00:00.000Z',
        updated_at: '2026-07-11T10:10:00.000Z',
      },
      {
        id: 3,
        title: '职业发展咨询',
        messages: [
          {
            id: 'm7',
            role: 'user',
            content: '我工作3年了，感觉遇到了技术瓶颈，不知道该怎么提升',
            created_at: '2026-07-10T09:00:00.000Z',
          },
          {
            id: 'm8',
            role: 'assistant',
            content: '工作3年是一个很关键的阶段。建议从以下方面突破：\n\n1. **技术深度**：选择一个方向深入（如前端性能优化、工程化、跨端开发）\n2. **技术广度**：学习一门后端语言（Node.js/Python/Go）\n3. **架构思维**：从实现功能到设计系统\n4. **软技能**：技术方案设计、跨团队沟通\n\n您目前主要从事哪方面的工作？我可以给出更具体的建议。',
            created_at: '2026-07-10T09:00:15.000Z',
          },
        ],
        created_at: '2026-07-10T09:00:00.000Z',
        updated_at: '2026-07-10T09:05:00.000Z',
      },
      {
        id: 4,
        title: '薪资谈判咨询',
        messages: [
          {
            id: 'm9',
            role: 'user',
            content: '拿到两个offer，不知道如何选择，薪资方面怎么谈',
            created_at: '2026-07-09T15:00:00.000Z',
          },
          {
            id: 'm10',
            role: 'assistant',
            content: '恭喜！关于Offer选择和薪资谈判，以下是一些建议：\n\n**Offer选择考虑因素：**\n1. 成长空间 > 薪资（尤其3-5年阶段）\n2. 业务前景和技术栈匹配度\n3. 团队氛围和管理风格\n4. 综合福利（股票期权、培训机会等）\n\n**薪资谈判技巧：**\n1. 不要先报价，让HR给出区间\n2. 用另一个Offer作为杠杆\n3. 关注总包而非月薪\n4. 谈成长机会和发展空间\n\n方便分享两个Offer的基本信息吗？我帮您具体分析。',
            created_at: '2026-07-09T15:00:20.000Z',
          },
        ],
        created_at: '2026-07-09T15:00:00.000Z',
        updated_at: '2026-07-09T15:10:00.000Z',
      },
    ]
  })

  // Get messages for a session
  registerMock('get', '/chat/sessions/:id/messages', (params: any) => {
    const sessionId = parseInt(params.id)
    const sessions: Record<number, any[]> = {
      1: [
        { id: 'm1', role: 'user', content: '请帮我优化简历中的项目描述', created_at: '2026-07-12T14:30:00.000Z' },
        { id: 'm2', role: 'assistant', content: '好的，请将您的项目描述发送给我，我会根据STAR原则进行优化，突出您的个人贡献和项目成果。', created_at: '2026-07-12T14:30:05.000Z' },
      ],
      2: [
        { id: 'm3', role: 'user', content: '我要面试字节跳动前端岗位，请帮我准备面试', created_at: '2026-07-11T10:00:00.000Z' },
        { id: 'm4', role: 'assistant', content: '好的！字节跳动前端面试通常包括：JavaScript基础、框架原理（Vue/React）、浏览器原理、性能优化、算法与数据结构、项目深挖等环节。请先告诉我您的技术栈和准备的岗位级别。', created_at: '2026-07-11T10:00:08.000Z' },
        { id: 'm5', role: 'user', content: '我主要用Vue3和TypeScript，准备面试P6级别', created_at: '2026-07-11T10:05:00.000Z' },
        { id: 'm6', role: 'assistant', content: '好的！针对字节P6级别（高级工程师），我将从以下几个维度帮您准备：\n\n1. **Vue3核心原理**：响应式系统、虚拟DOM、编译优化\n2. **TypeScript高级类型**：泛型约束、条件类型、映射类型\n3. **浏览器与性能**：渲染流程、事件循环、性能指标\n4. **前端工程化**：构建工具、CI/CD、代码质量\n5. **算法与数据结构**：重点准备数组、树、动态规划\n\n需要先从哪个模块开始？', created_at: '2026-07-11T10:05:30.000Z' },
      ],
      3: [
        { id: 'm7', role: 'user', content: '我工作3年了，感觉遇到了技术瓶颈，不知道该怎么提升', created_at: '2026-07-10T09:00:00.000Z' },
        { id: 'm8', role: 'assistant', content: '工作3年是一个很关键的阶段。建议从以下方面突破：\n\n1. **技术深度**：选择一个方向深入（如前端性能优化、工程化、跨端开发）\n2. **技术广度**：学习一门后端语言（Node.js/Python/Go）\n3. **架构思维**：从实现功能到设计系统\n4. **软技能**：技术方案设计、跨团队沟通\n\n您目前主要从事哪方面的工作？我可以给出更具体的建议。', created_at: '2026-07-10T09:00:15.000Z' },
      ],
      4: [
        { id: 'm9', role: 'user', content: '拿到两个offer，不知道如何选择，薪资方面怎么谈', created_at: '2026-07-09T15:00:00.000Z' },
        { id: 'm10', role: 'assistant', content: '恭喜！关于Offer选择和薪资谈判，以下是一些建议：\n\n**Offer选择考虑因素：**\n1. 成长空间 > 薪资（尤其3-5年阶段）\n2. 业务前景和技术栈匹配度\n3. 团队氛围和管理风格\n4. 综合福利（股票期权、培训机会等）\n\n**薪资谈判技巧：**\n1. 不要先报价，让HR给出区间\n2. 用另一个Offer作为杠杆\n3. 关注总包而非月薪\n4. 谈成长机会和发展空间\n\n方便分享两个Offer的基本信息吗？我帮您具体分析。', created_at: '2026-07-09T15:00:20.000Z' },
      ],
    }
    return sessions[sessionId] || []
  })

  // Send message (non-streaming)
  registerMock('post', '/chat/send', (params: any) => {
    const message = params?.message || ''
    const responses: Record<string, string> = {
      default: `感谢您的提问。针对"${message}"，我建议从以下几个方面考虑：\n\n1. **明确目标**：首先需要明确您的短期和长期职业目标\n2. **分析现状**：评估当前技能水平和经验积累\n3. **制定计划**：根据差距制定具体的学习和实践计划\n4. **持续迭代**：定期复盘和调整方向\n\n如果您能提供更具体的背景信息，我可以给出更有针对性的建议。`,
      hello: '您好！我是哈基米AI，您的全自动求职帮手，可以帮您做简历、找岗位、准备面试、制定职业规划。请问有什么可以帮您的？',
      help: '我可以帮您做以下事情：\n\n1. **简历优化** - 上传简历获取分析报告和优化建议\n2. **面试准备** - 模拟面试和针对性练习\n3. **职业规划** - 生成个性化职业发展路径\n4. **职位推荐** - 根据您的背景匹配合适职位\n5. **HR沟通** - 智能回复HR消息\n\n请问您想先体验哪项服务？',
    }

    const content = responses[message.trim().toLowerCase()] || responses.default

    return {
      id: 'msg_' + Date.now(),
      role: 'assistant',
      content,
      created_at: new Date().toISOString(),
    }
  })

  // Delete session
  registerMock('delete', '/chat/sessions/:id', () => {
    return null
  })
}
