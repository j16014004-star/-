import { describe, it, expect, beforeEach } from 'vitest'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'

describe('storage 工具函数', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('set 和 get', () => {
    it('存储和获取字符串', () => {
      storage.set('key', 'value')
      expect(storage.get('key')).toBe('value')
    })

    it('存储和获取对象', () => {
      const obj = { name: '张三', age: 25 }
      storage.set('user', obj)
      expect(storage.get('user')).toEqual(obj)
    })

    it('存储和获取数组', () => {
      const arr = [1, 2, 3]
      storage.set('numbers', arr)
      expect(storage.get<number[]>('numbers')).toEqual(arr)
    })

    it('存储和获取 null', () => {
      storage.set('null', null)
      expect(storage.get('null')).toBe(null)
    })

    it('存储和获取布尔值', () => {
      storage.set('flag', true)
      expect(storage.get('flag')).toBe(true)
    })

    it('获取不存在的 key 返回 null', () => {
      expect(storage.get('nonexistent')).toBe(null)
    })
  })

  describe('remove', () => {
    it('删除指定 key', () => {
      storage.set('key', 'value')
      storage.remove('key')
      expect(storage.get('key')).toBe(null)
    })

    it('删除不存在的 key 不报错', () => {
      expect(() => storage.remove('nonexistent')).not.toThrow()
    })
  })

  describe('clear', () => {
    it('清空所有存储', () => {
      storage.set('key1', 'value1')
      storage.set('key2', 'value2')
      storage.clear()
      expect(storage.get('key1')).toBe(null)
      expect(storage.get('key2')).toBe(null)
    })
  })

  describe('常量', () => {
    it('TOKEN_KEY 正确', () => {
      expect(TOKEN_KEY).toBe('ai_career_token')
    })

    it('USER_KEY 正确', () => {
      expect(USER_KEY).toBe('ai_career_user')
    })
  })
})