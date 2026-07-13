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
  (error) => {
    // If the error is from our mock interceptor, return the mock data
    if (error.__mock) {
      return Promise.resolve(error.data)
    }
    if (error.response?.status === 401) {
      storage.remove(TOKEN_KEY)
      window.location.href = '/login'
    }
    ElMessage.error(error.response?.data?.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request