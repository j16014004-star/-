import { describe, it, expect } from 'vitest'
import router from '@/router'

describe('Router 配置', () => {
  it('包含登录路由', () => {
    const route = router.getRoutes().find((r) => r.path === '/login')
    expect(route).toBeDefined()
    expect(route?.name).toBe('login')
  })

  it('登录路由不需要认证', () => {
    const route = router.getRoutes().find((r) => r.path === '/login')
    expect(route?.meta?.requiresAuth).toBe(false)
  })

  it('包含注册路由', () => {
    const route = router.getRoutes().find((r) => r.path === '/register')
    expect(route).toBeDefined()
    expect(route?.name).toBe('register')
  })

  it('包含 Dashboard 路由', () => {
    const routes = router.getRoutes()
    const dashboard = routes.find((r) => r.name === 'dashboard')
    expect(dashboard).toBeDefined()
  })

  it('包含所有主要业务路由名称', () => {
    const routeNames = router.getRoutes().map((r) => r.name as string)
    const expected = ['login', 'register', 'dashboard', 'resume-list', 'resume-upload', 'resume-detail', 'resume-optimize', 'career', 'jobs', 'chat', 'agent', 'hr', 'interview', 'interview-room', 'interview-report', 'profile']
    expected.forEach((name) => {
      expect(routeNames).toContain(name)
    })
  })

  it('未匹配路由重定向到首页', () => {
    const notFound = router.getRoutes().find((r) => r.name === 'not-found')
    expect(notFound).toBeDefined()
    expect(notFound?.redirect).toBe('/')
  })

  it('简历详情路由包含 :id 参数', () => {
    const route = router.getRoutes().find((r) => r.name === 'resume-detail')
    expect(route?.path).toContain(':id')
  })

  it('面试房间路由包含 :id 参数', () => {
    const route = router.getRoutes().find((r) => r.name === 'interview-room')
    expect(route?.path).toContain(':id')
  })

  it('面试报告路由包含 :id 参数', () => {
    const route = router.getRoutes().find((r) => r.name === 'interview-report')
    expect(route?.path).toContain(':id')
  })

  it('路由总数 >= 16', () => {
    // Vue Router 会为每个子路由生成扁平化记录
    const routeNames = router.getRoutes().map((r) => r.name as string).filter(Boolean)
    expect(routeNames.length).toBeGreaterThanOrEqual(16)
  })
})