import { registerMock } from './index'

export function setupInterviewMock() {
  // Get interview list
  registerMock('get', '/interviews', () => {
    return [
      {
        id: 1,
        title: '字节跳动前端模拟面试',
        status: 'completed',
        position: '高级前端开发工程师',
        company: '字节跳动',
        questions: [
          {
            id: 1,
            type: 'technical',
            question: '请解释Vue3的响应式原理，与Vue2相比有哪些改进？',
            answer: 'Vue3使用Proxy替代了Vue2的Object.defineProperty。Proxy可以直接代理整个对象，而不需要递归遍历所有属性。Vue3的响应式系统通过reactive()和ref()两个核心API实现。reactive()使用Proxy拦截对象的get、set等操作，在get时收集依赖（track），在set时触发更新（trigger）。ref()则通过一个包含value属性的对象来实现基本数据类型的响应式。\n\n主要改进：\n1. 支持Map、Set等新数据类型\n2. 懒递归，只有访问时才深层代理，性能更好\n3. 更好的数组支持\n4. 依赖追踪更精确，避免不必要的重渲染',
            score: 85,
            feedback: '回答完整，涵盖了Proxy对比defineProperty的核心优势，以及响应式的工作原理。建议补充computed和watch的实现机制。',
            tips: '面试时可以从"Vue2的局限性"切入，然后自然引出Vue3的改进。',
            duration: 180,
          },
          {
            id: 2,
            type: 'technical',
            question: '什么是虚拟DOM？Vue3中是如何优化虚拟DOM性能的？',
            answer: '虚拟DOM是用JavaScript对象来表示真实DOM树的一种数据结构。当状态变化时，通过对比新旧虚拟DOM的差异（Diff算法），计算出最小的DOM操作来更新视图。\n\nVue3的优化：\n1. PatchFlag：编译时标记动态节点，跳过静态内容对比\n2. Block Tree：将模板结构树拍平，只对比动态节点\n3. Fragment支持：模板支持多个根节点\n4. Suspense：异步组件的挂起状态管理\n5. 静态提升：将静态节点提升到渲染函数体外',
            score: 80,
            feedback: '基本概念清晰，Vue3的优化点回答全面。可以深入说明PatchFlag的具体类型和优化效果。',
            tips: '可以手写一个简单的Diff算法来展示理解深度。',
            duration: 200,
          },
          {
            id: 3,
            type: 'behavioral',
            question: '请描述一次你处理过的技术债务或遗留系统的经历。',
            answer: '在上一家公司，我接手了一个使用jQuery + Backbone.js的老项目，代码耦合度高，维护困难。我采取了渐进式重构策略：\n1. 先引入Vue2作为新功能的开发框架\n2. 使用微前端方案（qiankun）将老项目作为子应用逐步迁移\n3. 制定代码规范，引入ESLint和Prettier\n4. 建立自动化测试，保证重构不影响现有功能\n经过6个月，成功将80%的模块迁移到Vue3 + TypeScript技术栈。',
            score: 90,
            feedback: 'STAR原则运用得当，展示了技术能力和项目管理能力。',
            tips: '重点强调"渐进式"策略，体现风险控制意识。',
            duration: 240,
          },
        ],
        score: 85,
        report: {
          overall_score: 85,
          dimension_scores: {
            technical: 82,
            behavioral: 90,
            communication: 88,
            logic: 85,
          },
          strengths: ['技术原理理解深入', '有大型项目重构经验', '回答问题条理清晰'],
          weaknesses: ['部分前沿技术了解不够', '系统设计方面经验偏少'],
          suggestions: [
            '深入学习浏览器渲染原理和性能优化',
            '补充系统设计相关知识',
            '多参与技术分享提升表达能力',
          ],
          summary: '面试表现整体优秀，技术基础扎实，有丰富的项目实战经验。建议重点加强系统设计能力和前沿技术的跟进，为架构师方向做准备。',
        },
        created_at: '2026-07-12T10:00:00.000Z',
      },
      {
        id: 2,
        title: '美团前端技术面试',
        status: 'completed',
        position: '资深前端开发工程师',
        company: '美团',
        questions: [
          {
            id: 4,
            type: 'technical',
            question: '前端性能优化有哪些手段？如何评估优化效果？',
            answer: '前端性能优化手段：\n1. 加载优化：CDN、懒加载、代码分割、预加载\n2. 渲染优化：减少重排重绘、使用虚拟滚动、Web Worker\n3. 资源优化：图片压缩、Tree Shaking、代码压缩\n4. 缓存优化：HTTP缓存、Service Worker、本地缓存\n5. 网络优化：HTTP/2、SSR、预连接\n\n评估指标：FCP、LCP、FID、CLS、TTI、TBT。使用Lighthouse、Web Vitals等工具测量。',
            score: 75,
            feedback: '覆盖面广，但深度不够。建议深入说明一个具体优化案例，附带量化数据。',
            tips: '准备一个真实的性能优化案例，包含优化前后的数据对比。',
            duration: 160,
          },
          {
            id: 5,
            type: 'project',
            question: '请介绍一个你最满意的项目，你在其中承担了什么角色？',
            answer: '我主导开发了公司的低代码平台，担任技术负责人。项目从0到1搭建，支持拖拽生成中后台页面。我负责技术选型（Vue3 + Element Plus + Formily）、架构设计、核心模块开发和技术团队管理。平台上线后，开发效率提升60%，被5个业务线采用。',
            score: 88,
            feedback: '项目描述清晰，突出了个人贡献和量化成果。',
            tips: '准备项目架构图可以更直观展示设计能力。',
            duration: 200,
          },
        ],
        score: 82,
        report: {
          overall_score: 82,
          dimension_scores: {
            technical: 78,
            behavioral: 85,
            communication: 85,
            logic: 80,
          },
          strengths: ['项目经验丰富', '有技术管理经验', '沟通表达流畅'],
          weaknesses: ['性能优化系统性不足', '部分基础概念需要更深入'],
          suggestions: [
            '深入学习Chrome DevTools的各项性能分析工具',
            '补充计算机基础（网络协议、数据结构）',
            '培养技术方案设计和文档能力',
          ],
          summary: '面试表现良好，项目经验和管理能力是亮点。建议加强技术深度和系统性思维的训练。',
        },
        created_at: '2026-07-10T14:00:00.000Z',
      },
      {
        id: 3,
        title: '日常模拟面试练习',
        status: 'in_progress',
        position: '前端开发工程师',
        company: undefined,
        questions: [
          {
            id: 6,
            type: 'technical',
            question: '请解释TypeScript中的泛型约束（Generic Constraints）及其应用场景。',
            answer: undefined,
            score: undefined,
            feedback: undefined,
            tips: '可以从extends关键字、keyof操作符、条件类型三个层面回答。再举一个实际项目中封装API请求类型的例子。',
            duration: undefined,
          },
        ],
        score: undefined,
        report: undefined,
        created_at: '2026-07-13T08:00:00.000Z',
      },
    ]
  })

  // Get interview detail
  registerMock('get', '/interviews/:id', (params: any) => {
    const id = parseInt(params.id)
    return {
      id,
      title: id === 1 ? '字节跳动前端模拟面试' : '日常模拟面试练习',
      status: id === 1 ? 'completed' : 'in_progress',
      position: '高级前端开发工程师',
      company: id === 1 ? '字节跳动' : undefined,
      questions: [
        {
          id: 1,
          type: 'technical',
          question: '请解释Vue3的响应式原理，与Vue2相比有哪些改进？',
          answer: id === 1 ? 'Vue3使用Proxy替代了Vue2的Object.defineProperty...' : undefined,
          score: id === 1 ? 85 : undefined,
          feedback: id === 1 ? '回答完整，建议补充computed和watch的实现机制。' : undefined,
          tips: '从"Vue2的局限性"切入，自然引出Vue3的改进。',
          duration: id === 1 ? 180 : undefined,
        },
      ],
      score: id === 1 ? 85 : undefined,
      report: id === 1 ? {
        overall_score: 85,
        dimension_scores: { technical: 82, behavioral: 90, communication: 88, logic: 85 },
        strengths: ['技术原理理解深入'],
        weaknesses: ['系统设计方面经验偏少'],
        suggestions: ['深入学习浏览器渲染原理和性能优化'],
        summary: '面试表现整体优秀。',
      } : undefined,
      created_at: '2026-07-12T10:00:00.000Z',
    }
  })

  // Create interview
  registerMock('post', '/interviews', (params: any) => {
    return {
      id: Math.floor(Math.random() * 100) + 10,
      title: params.position + '模拟面试',
      status: 'pending',
      position: params.position || '前端开发工程师',
      company: params.company,
      questions: [],
      score: undefined,
      report: undefined,
      created_at: new Date().toISOString(),
    }
  })

  // Start interview
  registerMock('post', '/interviews/:id/start', () => {
    return {
      id: 3,
      title: '日常模拟面试练习',
      status: 'in_progress',
      position: '前端开发工程师',
      questions: [
        {
          id: 1,
          type: 'technical',
          question: '请解释TypeScript中的泛型约束及其应用场景。',
          tips: '从extends、keyof、条件类型三个层面回答。',
        },
      ],
      score: undefined,
      report: undefined,
      created_at: '2026-07-13T08:00:00.000Z',
    }
  })

  // Get next question
  registerMock('get', '/interviews/:id/next-question', () => {
    return {
      id: Math.floor(Math.random() * 100) + 10,
      type: 'technical',
      question: '请描述浏览器从输入URL到页面展示的完整过程。',
      tips: '从DNS解析、TCP连接、HTTP请求、浏览器解析渲染几个阶段回答。',
    }
  })

  // Submit answer
  registerMock('post', '/interviews/:id/answer', (params: any) => {
    return {
      id: parseInt(params.question_id) || 1,
      type: 'technical',
      question: '请解释Vue3的响应式原理',
      answer: params.answer || '用户提交的答案',
      score: Math.floor(Math.random() * 30) + 70,
      feedback: '回答基本正确，建议更深入地阐述实现细节和性能优化点。',
      tips: '可以结合源码层面进行更深入的解释。',
      duration: params.duration || 120,
    }
  })

  // Finish interview
  registerMock('post', '/interviews/:id/finish', () => {
    return {
      id: 3,
      title: '日常模拟面试练习',
      status: 'completed',
      position: '前端开发工程师',
      questions: [
        { id: 1, type: 'technical', question: '问题1', answer: '答案1', score: 85, feedback: '很好', duration: 120 },
        { id: 2, type: 'technical', question: '问题2', answer: '答案2', score: 75, feedback: '不错', duration: 150 },
      ],
      score: 80,
      report: {
        overall_score: 80,
        dimension_scores: { technical: 78, behavioral: 85, communication: 80, logic: 82 },
        strengths: ['技术基础扎实', '回答有条理'],
        weaknesses: ['对前沿技术关注不够', '深度有待提升'],
        suggestions: [
          '系统学习浏览器原理',
          '关注前端社区最新动态',
          '多进行实际项目练习',
        ],
        summary: '整体表现中等偏上，有进一步提升空间。',
      },
      created_at: '2026-07-13T08:00:00.000Z',
    }
  })

  // Get report
  registerMock('get', '/interviews/:id/report', (params: any) => {
    const id = parseInt(params.id)
    const scores: Record<number, any> = {
      1: {
        id: 1,
        title: '字节跳动前端模拟面试',
        status: 'completed',
        position: '高级前端开发工程师',
        company: '字节跳动',
        questions: [
          { id: 1, type: 'technical', question: 'Vue3响应式原理', answer: '...', score: 85, duration: 180 },
          { id: 2, type: 'technical', question: '虚拟DOM优化', answer: '...', score: 80, duration: 200 },
          { id: 3, type: 'behavioral', question: '处理技术债务的经历', answer: '...', score: 90, duration: 240 },
        ],
        score: 85,
        report: {
          overall_score: 85,
          dimension_scores: { technical: 82, behavioral: 90, communication: 88, logic: 85 },
          strengths: ['技术原理理解深入', '有大型项目重构经验', '回答问题条理清晰'],
          weaknesses: ['部分前沿技术了解不够', '系统设计方面经验偏少'],
          suggestions: ['深入学习浏览器渲染原理和性能优化', '补充系统设计相关知识'],
          summary: '面试表现整体优秀，技术基础扎实。',
        },
        created_at: '2026-07-12T10:00:00.000Z',
      },
      2: {
        id: 2,
        title: '美团前端技术面试',
        status: 'completed',
        position: '资深前端开发工程师',
        company: '美团',
        questions: [
          { id: 4, type: 'technical', question: '前端性能优化手段', answer: '...', score: 75, duration: 160 },
          { id: 5, type: 'project', question: '介绍最满意的项目', answer: '...', score: 88, duration: 200 },
        ],
        score: 82,
        report: {
          overall_score: 82,
          dimension_scores: { technical: 78, behavioral: 85, communication: 85, logic: 80 },
          strengths: ['项目经验丰富', '有技术管理经验', '沟通表达流畅'],
          weaknesses: ['性能优化系统性不足', '部分基础概念需要更深入'],
          suggestions: ['深入学习Chrome DevTools性能分析工具', '补充计算机基础'],
          summary: '面试表现良好，项目经验和管理能力是亮点。',
        },
        created_at: '2026-07-10T14:00:00.000Z',
      },
    }
    return scores[id] || scores[1]
  })

  // Delete interview
  registerMock('delete', '/interviews/:id', () => {
    return null
  })
}