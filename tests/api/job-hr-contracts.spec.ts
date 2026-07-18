import { beforeEach, describe, expect, it, vi } from 'vitest'

const requestMocks = vi.hoisted(() => ({
  get: vi.fn(() => Promise.resolve({})),
  post: vi.fn(() => Promise.resolve({})),
  patch: vi.fn(() => Promise.resolve({})),
}))

vi.mock('@/utils/request', () => ({ default: requestMocks }))

import { hrApi } from '@/api/hr'
import { jobApi } from '@/api/job'

describe('岗位推荐和 HR 助手接口契约', () => {
  beforeEach(() => vi.clearAllMocks())

  it('发起平台登录时提交完整的岗位意向', async () => {
    const payload = {
      source: '58',
      resume_id: 1,
      resume_source: 'original' as const,
      target_role: 'Python后端开发工程师',
      target_city: '西安',
      force_refresh: true,
    }
    await jobApi.startPlatformLogin(payload)
    expect(requestMocks.post).toHaveBeenCalledWith('/job-platforms/login/start', payload)
  })

  it('HR 工作区列表支持请求完整分页', async () => {
    await hrApi.getWorkspaces({ status: 'communicating', page: 2, page_size: 100 })
    expect(requestMocks.get).toHaveBeenCalledWith('/hr/workspaces', {
      params: { status: 'communicating', page: 2, page_size: 100 },
    })
  })

  it('平台消息同步使用工作区同步接口', async () => {
    await hrApi.syncMessages(18)
    expect(requestMocks.post).toHaveBeenCalledWith('/hr/workspaces/18/messages/sync')
  })
})
