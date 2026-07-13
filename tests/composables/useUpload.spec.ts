import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useUpload } from '@/composables/useUpload'

// Mock Element Plus ElMessage
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}))

describe('useUpload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('初始状态', () => {
    const { uploading, uploadProgress } = useUpload()
    expect(uploading.value).toBe(false)
    expect(uploadProgress.value).toBe(0)
  })

  it('upload 成功后返回结果', async () => {
    const { upload } = useUpload()
    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    const uploadFn = vi.fn().mockResolvedValue({ id: 1, title: 'test' })

    const promise = upload(mockFile, uploadFn)
    vi.advanceTimersByTime(500)
    const result = await promise

    expect(uploadFn).toHaveBeenCalledWith(mockFile)
    expect(result).toEqual({ id: 1, title: 'test' })
  })

  it('upload 失败时抛出错误', async () => {
    const { upload } = useUpload()
    const mockFile = new File(['content'], 'test.pdf')
    const uploadFn = vi.fn().mockRejectedValue(new Error('上传失败'))

    await expect(upload(mockFile, uploadFn)).rejects.toThrow('上传失败')
  })
})