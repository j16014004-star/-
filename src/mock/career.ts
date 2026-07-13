import { registerMock } from './index'

export function setupCareerMock() {
  registerMock('post', '/career/plan', (params: any) => {
    const skills = params?.skills || ['Vue.js', 'TypeScript']
    return {
      recommended_positions: [
        '高级前端开发工程师',
        '全栈开发工程师（Node.js方向）',
        '前端架构师',
        '技术团队负责人（前端方向）',
      ],
      learning_path: [
        {
          stage: '基础巩固阶段（1-2个月）',
          skills: ['TypeScript深入（泛型、装饰器、条件类型）', '设计模式在前端的应用', '浏览器渲染原理与性能优化'],
          duration: '1-2个月',
          resources: [
            'TypeScript官方文档',
            '《JavaScript设计模式》',
            'Chrome DevTools Performance文档',
            'MDN Web性能优化指南',
          ],
        },
        {
          stage: '进阶提升阶段（2-3个月）',
          skills: ['Vue3源码阅读与理解', '前端工程化（Webpack/Vite插件开发）', 'Node.js全栈开发', '前端测试体系（Vitest、Cypress）'],
          duration: '2-3个月',
          resources: [
            'Vue.js官方设计文档',
            'Vite插件开发指南',
            'Node.js官方教程',
            'Vitest官方文档',
          ],
        },
        {
          stage: '高阶拓展阶段（3-4个月）',
          skills: ['微前端架构（Module Federation）', 'Serverless架构实践', 'CI/CD流水线搭建', 'WebAssembly入门'],
          duration: '3-4个月',
          resources: [
            'Module Federation官方示例',
            '阿里云Serverless实践指南',
            'GitHub Actions文档',
            'WebAssembly官方文档',
          ],
        },
        {
          stage: '架构师准备阶段（2-3个月）',
          skills: ['系统架构设计能力', '技术团队管理', '跨部门协作与沟通', '技术方案评审与决策'],
          duration: '2-3个月',
          resources: [
            '《架构整洁之道》',
            '《卓有成效的管理者》',
            '《系统设计面试》',
            '技术管理相关博客与播客',
          ],
        },
      ],
      skill_suggestions: [
        '深入学习TypeScript高级类型系统',
        '掌握一种后端语言（Node.js/Python/Go）',
        '了解容器化技术（Docker + Kubernetes）',
        '学习云服务部署（阿里云/AWS）',
        '培养技术文档写作和方案设计能力',
      ],
      career_direction: `根据您的${skills.join('、')}技能背景和当前市场趋势，推荐发展方向为：高级前端开发工程师 → 前端架构师/全栈架构师。当前互联网行业对"T型人才"需求旺盛，即在前端领域有深度同时在后端或工程化方向有广度。保持技术深度的同时，逐步扩展技术广度，特别是在Node.js后端开发和云原生技术方面。`,
      market_analysis: '2026年前端开发市场呈现以下趋势：1）AI辅助编程普及，初级前端岗位需求下降，高级岗位薪资持续上涨；2）全栈能力成为中高级岗位标配，特别是Node.js全栈方向；3）大前端概念深化，小程序、跨端开发、微前端需求稳定增长；4）性能优化和用户体验专精方向人才稀缺；5）具备工程化能力和团队管理经验的前端架构师平均年薪已达60-80万。建议重点关注全栈能力和工程化方向。',
    }
  })
}