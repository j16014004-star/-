import request from '@/utils/request'
import type { LoginRequest, RegisterRequest, LoginResponse, RefreshTokenResponse } from './types/auth'
import type { ApiResponse, UserInfo } from '@/types'

export const authApi = {
  login(data: LoginRequest) {
    return request.post<ApiResponse<LoginResponse>>('/auth/login', data)
  },

  register(data: RegisterRequest) {
    return request.post<ApiResponse<null>>('/auth/register', data)
  },

  refresh(refreshToken: string) {
    return request.post<ApiResponse<RefreshTokenResponse>>('/auth/refresh', {
      refresh_token: refreshToken
    })
  },

  getUserInfo() {
    return request.get<ApiResponse<UserInfo>>('/auth/userinfo')
  },

  updateProfile(data: Partial<UserInfo>) {
    return request.put<ApiResponse<UserInfo>>('/auth/profile', data)
  },

  logout() {
    return request.post<ApiResponse<null>>('/auth/logout')
  },
}