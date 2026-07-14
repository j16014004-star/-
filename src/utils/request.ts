import axios from 'axios'
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { storage, TOKEN_KEY } from './storage'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 刷新锁：防止多个请求同时刷新 token
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

// 添加刷新订阅者
const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb)
}

// 通知所有订阅者 token 已刷新
const onTokenRefreshed = (newToken: string) => {
  refreshSubscribers.forEach(cb => cb(newToken))
  refreshSubscribers = []
}

// Request interceptor - inject token
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.get<string>(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    // Mock delay in development
    if (import.meta.env.DEV && response.config.url?.startsWith('/mock/')) {
      return data
    }
    if (data.code !== 0 && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  async (error) => {
    // If the error is from our mock interceptor, return the mock data
    if (error.__mock) {
      return Promise.resolve(error.data)
    }

    const originalRequest = error.config

    // 401 错误处理：尝试刷新 token
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 如果是刷新 token 的请求本身失败，直接跳转到登录
      if (originalRequest.url?.includes('/auth/refresh')) {
        storage.remove(TOKEN_KEY)
        storage.remove('refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 检查是否有 refresh_token
      const refreshToken = storage.get<string>('refresh_token')
      if (!refreshToken) {
        storage.remove(TOKEN_KEY)
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 如果正在刷新，将请求加入队列
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            resolve(request(originalRequest))
          })
        })
      }

      // 开始刷新
      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        })

        const { access_token } = response.data.data
        storage.set(TOKEN_KEY, access_token)

        // 通知所有等待的请求
        onTokenRefreshed(access_token)
        isRefreshing = false

        // 重试原请求
        originalRequest.headers.Authorization = `Bearer ${access_token}`
        return request(originalRequest)
      } catch (refreshError) {
        isRefreshing = false
        refreshSubscribers = []
        storage.remove(TOKEN_KEY)
        storage.remove('refresh_token')
        ElMessage.error('登录已过期，请重新登录')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    ElMessage.error(error.response?.data?.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request