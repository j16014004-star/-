import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import ScoreRing from '@/components/business/ScoreRing.vue'

// Mock requestAnimationFrame - 立即执行以完成动画
;(global as any).requestAnimationFrame = (cb: (t: number) => void) => {
  cb(800)
  return 0
}
;(global as any).performance = { now: () => 0 }

describe('ScoreRing', () => {
  it('使用默认 props 渲染', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 85 },
    })
    await nextTick()
    expect(wrapper.find('.score-ring').exists()).toBe(true)
  })

  it('渲染 SVG 元素', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 90, size: 100, strokeWidth: 8 },
    })
    await nextTick()
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('circle').exists()).toBe(true)
  })

  it('显示分数文字', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 85 },
    })
    await nextTick()
    expect(wrapper.find('.score-text').text()).toBe('85')
  })

  it('分数 >= 80 使用绿色 stroke', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 85 },
    })
    await nextTick()
    const circles = wrapper.findAll('circle')
    expect(circles[1].attributes('stroke')).toBe('#10b981')
  })

  it('分数 60-79 使用黄色 stroke', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 70 },
    })
    await nextTick()
    const circles = wrapper.findAll('circle')
    expect(circles[1].attributes('stroke')).toBe('#f59e0b')
  })

  it('分数 < 60 使用红色 stroke', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 50 },
    })
    await nextTick()
    const circles = wrapper.findAll('circle')
    expect(circles[1].attributes('stroke')).toBe('#ef4444')
  })

  it('分数 >= 70 使用绿色文字类', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 75 },
    })
    await nextTick()
    expect(wrapper.find('.score-text').classes()).toContain('text-green-600')
  })

  it('应用自定义 size', async () => {
    const wrapper = mount(ScoreRing, {
      props: { score: 80, size: 120 },
    })
    await nextTick()
    const svg = wrapper.find('svg')
    expect(svg.attributes('width')).toBe('120')
    expect(svg.attributes('height')).toBe('120')
  })
})