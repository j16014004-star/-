import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EmptyState from '@/components/common/EmptyState.vue'

describe('EmptyState', () => {
  it('使用默认消息渲染', () => {
    const wrapper = mount(EmptyState)
    expect(wrapper.text()).toContain('暂无数据')
  })

  it('使用自定义消息', () => {
    const wrapper = mount(EmptyState, {
      props: { message: '没有找到简历' },
    })
    expect(wrapper.text()).toContain('没有找到简历')
  })
})