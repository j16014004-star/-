// Simple mock system for development mode.
// Each mock module registers handlers that return realistic data.
// The API layer detects the mock interceptor error and resolves the data.

import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios'

interface MockHandler {
  method: string
  url: string
  handler: (params?: any) => any
}

const handlers: MockHandler[] = []

export function registerMock(method: string, url: string, handler: (params?: any) => any) {
  handlers.push({ method: method.toUpperCase(), url, handler })
}

export function setupMock(axiosInstance: AxiosInstance) {
  axiosInstance.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    // Only intercept in development mode
    if (!import.meta.env.DEV) {
      return config
    }

    const method = (config.method || 'get').toUpperCase()
    let url = config.url || ''

    // Strip baseURL if present
    const baseURL = axiosInstance.defaults.baseURL || ''
    if (url.startsWith(baseURL)) {
      url = url.slice(baseURL.length)
    }

    // Find matching handler
    const match = handlers.find((h) => {
      if (h.method !== method) return false
      // Support simple wildcard matching: /resumes/:id matches /resumes/1
      const hParts = h.url.split('/')
      const uParts = url.split('/')
      if (hParts.length !== uParts.length) return false
      return hParts.every((part, i) => part.startsWith(':') || part === uParts[i])
    })

    if (match) {
      // Extract params from URL for wildcard routes
      const params: Record<string, string> = {}
      const hParts = match.url.split('/')
      const uParts = url.split('/')
      hParts.forEach((part, i) => {
        if (part.startsWith(':')) {
          params[part.slice(1)] = uParts[i]
        }
      })

      // Merge URL params, query params, and body data
      const queryParams = config.params || {}
      let bodyData: any
      try {
        bodyData = config.data ? JSON.parse(config.data) : {}
      } catch {
        bodyData = config.data || {}
      }
      const mergedParams = { ...queryParams, ...bodyData, ...params }

      // Simulate network delay
      await new Promise((r) => setTimeout(r, 300 + Math.random() * 500))

      const result = match.handler(mergedParams)

      // Throw a special error that the response interceptor catches
      throw {
        __mock: true,
        data: {
          code: 200,
          message: 'success',
          data: result,
        },
      }
    }

    return config
  })
}

export async function useMock<T>(mockData: T, delay = 500): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, delay))
  return mockData
}