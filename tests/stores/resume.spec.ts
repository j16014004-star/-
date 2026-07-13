import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useResumeStore } from '@/stores/resume'

describe('useResumeStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始状态', () => {
    const store = useResumeStore()
    expect(store.resumes).toEqual([])
    expect(store.currentResume).toBe(null)
    expect(store.loading).toBe(false)
    expect(store.analyzing).toBe(false)
  })

  it('setResumes 设置简历列表', () => {
    const store = useResumeStore()
    const resumes = [
      { id: 1, title: '简历1', file_type: 'pdf', status: 'completed', created_at: '2026-01-01', updated_at: '2026-01-01' },
      { id: 2, title: '简历2', file_type: 'word', status: 'pending', created_at: '2026-01-02', updated_at: '2026-01-02' },
    ] as any[]
    store.setResumes(resumes)
    expect(store.resumes.length).toBe(2)
  })

  it('addResume 添加到列表开头', () => {
    const store = useResumeStore()
    store.resumes = [{ id: 1, title: '简历1' } as any]
    store.addResume({ id: 2, title: '简历2' } as any)
    expect(store.resumes[0].id).toBe(2)
    expect(store.resumes.length).toBe(2)
  })

  it('removeResume 删除指定简历', () => {
    const store = useResumeStore()
    store.resumes = [
      { id: 1, title: '简历1' } as any,
      { id: 2, title: '简历2' } as any,
    ]
    store.removeResume(1)
    expect(store.resumes.length).toBe(1)
    expect(store.resumes[0].id).toBe(2)
  })

  it('setCurrent 设置当前简历', () => {
    const store = useResumeStore()
    const resume = { id: 1, title: '简历1' } as any
    store.setCurrent(resume)
    expect(store.currentResume).toEqual(resume)
    store.setCurrent(null)
    expect(store.currentResume).toBe(null)
  })

  it('updateAnalysis 更新简历分析', () => {
    const store = useResumeStore()
    const resume = { id: 1, title: '简历1', status: 'pending' } as any
    store.resumes = [resume]
    store.currentResume = { ...resume }

    const analysis = {
      score: 85,
      strengths: ['优势1'],
      weaknesses: ['劣势1'],
      suggestions: ['建议1'],
      missing_keywords: [],
      format_score: 80,
      content_score: 90,
      relevance_score: 85,
    }

    store.updateAnalysis(1, analysis)

    expect(store.resumes[0].status).toBe('completed')
    expect(store.resumes[0].score).toBe(85)
    expect(store.currentResume?.status).toBe('completed')
    expect(store.currentResume?.score).toBe(85)
  })
})