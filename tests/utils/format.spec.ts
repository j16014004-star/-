import { describe, it, expect } from 'vitest'
import { formatFileSize, formatSalary, formatDate, formatDateTime, timeAgo, getScoreColor, getScoreLevel } from '@/utils/format'

describe('format 工具函数', () => {
  describe('formatFileSize', () => {
    it('0 字节返回 0 B', () => {
      expect(formatFileSize(0)).toBe('0 B')
    })

    it('正确格式化字节为 KB', () => {
      expect(formatFileSize(1024)).toBe('1 KB')
    })

    it('正确格式化字节为 MB', () => {
      expect(formatFileSize(1048576)).toBe('1 MB')
    })

    it('正确格式化字节为 GB', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB')
    })

    it('正确格式化小数值', () => {
      expect(formatFileSize(1536)).toBe('1.5 KB')
    })
  })

  describe('formatSalary', () => {
    it('格式化千位薪资为 k 格式', () => {
      expect(formatSalary(30000, 50000)).toBe('30k-50k')
    })

    it('格式化小于1000的薪资', () => {
      expect(formatSalary(500, 800)).toBe('500-800')
    })
  })

  describe('formatDate', () => {
    it('格式化日期为中文格式', () => {
      const result = formatDate('2026-07-13T10:00:00.000Z')
      expect(result).toContain('2026')
    })
  })

  describe('formatDateTime', () => {
    it('格式化日期时间为中文格式', () => {
      const result = formatDateTime('2026-07-13T10:00:00.000Z')
      expect(result).toContain('2026')
    })
  })

  describe('timeAgo', () => {
    it('返回"刚刚"当时间在1分钟内', () => {
      const now = new Date().toISOString()
      expect(timeAgo(now)).toBe('刚刚')
    })

    it('返回"x分钟前"当时间在1小时内', () => {
      const past = new Date(Date.now() - 5 * 60 * 1000).toISOString()
      expect(timeAgo(past)).toBe('5分钟前')
    })

    it('返回"x小时前"当时间在24小时内', () => {
      const past = new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString()
      expect(timeAgo(past)).toBe('3小时前')
    })

    it('返回"x天前"当时间在30天内', () => {
      const past = new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
      expect(timeAgo(past)).toBe('5天前')
    })
  })

  describe('getScoreColor', () => {
    it('80分及以上返回绿色', () => {
      expect(getScoreColor(80)).toBe('#10b981')
      expect(getScoreColor(100)).toBe('#10b981')
    })

    it('60-79分返回黄色', () => {
      expect(getScoreColor(60)).toBe('#f59e0b')
      expect(getScoreColor(79)).toBe('#f59e0b')
    })

    it('60分以下返回红色', () => {
      expect(getScoreColor(0)).toBe('#ef4444')
      expect(getScoreColor(59)).toBe('#ef4444')
    })
  })

  describe('getScoreLevel', () => {
    it('90分及以上返回"优秀"', () => {
      expect(getScoreLevel(90)).toBe('优秀')
      expect(getScoreLevel(100)).toBe('优秀')
    })

    it('80-89分返回"良好"', () => {
      expect(getScoreLevel(80)).toBe('良好')
      expect(getScoreLevel(89)).toBe('良好')
    })

    it('60-79分返回"一般"', () => {
      expect(getScoreLevel(60)).toBe('一般')
      expect(getScoreLevel(79)).toBe('一般')
    })

    it('60分以下返回"需要改进"', () => {
      expect(getScoreLevel(0)).toBe('需要改进')
      expect(getScoreLevel(59)).toBe('需要改进')
    })
  })
})