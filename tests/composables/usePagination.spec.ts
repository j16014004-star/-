import { describe, it, expect } from 'vitest'
import { usePagination } from '@/composables/usePagination'

describe('usePagination', () => {
  it('初始默认值', () => {
    const { page, pageSize, total } = usePagination()
    expect(page.value).toBe(1)
    expect(pageSize.value).toBe(10)
    expect(total.value).toBe(0)
  })

  it('自定义默认 pageSize', () => {
    const { pageSize } = usePagination(20)
    expect(pageSize.value).toBe(20)
  })

  it('onPageChange 更新页码', () => {
    const { page, onPageChange } = usePagination()
    onPageChange(5)
    expect(page.value).toBe(5)
  })

  it('onSizeChange 更新 pageSize 并重置页码', () => {
    const { page, pageSize, onSizeChange, onPageChange } = usePagination()
    onPageChange(3)
    expect(page.value).toBe(3)
    onSizeChange(20)
    expect(pageSize.value).toBe(20)
    expect(page.value).toBe(1)
  })

  it('pagination 计算属性正确', () => {
    const { pagination, onPageChange } = usePagination()
    expect(pagination.value).toEqual({ page: 1, page_size: 10, total: 0 })
    onPageChange(5)
    expect(pagination.value.page).toBe(5)
  })
})