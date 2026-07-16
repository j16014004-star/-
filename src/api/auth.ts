import request from '@/utils/request'
import type { AxiosResponse } from 'axios'
import type { AuthenticatedLoginResponse, LoginRequest, RegisterRequest, LoginResponse, RefreshTokenResponse, TwoFactorLoginRequest } from './types/auth'
import type { ApiResponse, UserInfo } from '@/types'

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): Promise<ApiResponse<T>> {
  return promise as unknown as Promise<ApiResponse<T>>
}

export const authApi = {
  login(data: LoginRequest) {
    return asApiPromise(request.post<ApiResponse<LoginResponse>>('/auth/login', data))
  },

  verifyTwoFactor(data: TwoFactorLoginRequest) {
    return asApiPromise(request.post<ApiResponse<AuthenticatedLoginResponse>>('/auth/login/two-factor', data))
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
