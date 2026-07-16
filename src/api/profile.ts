import type { AxiosProgressEvent, AxiosResponse } from 'axios'
import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types'
import type {
  AvatarUploadResult,
  ChangePasswordParams,
  ChangePasswordResult,
  DeleteAccountParams,
  LoginLogItem,
  ProfileInfo,
  ProfilePreferences,
  ProfilePreferencesUpdateParams,
  ProfileUpdateParams,
  TwoFactorDisableParams,
  TwoFactorEnableParams,
  TwoFactorSetupResult,
  TwoFactorSetupParams,
  TwoFactorStatusResult,
} from './types/profile'

type ApiPromise<T> = Promise<ApiResponse<T>>

function asApiPromise<T>(promise: Promise<AxiosResponse<ApiResponse<T>>>): ApiPromise<T> {
  return promise as unknown as ApiPromise<T>
}

export const profileApi = {
  getProfile() {
    return asApiPromise(request.get<ApiResponse<ProfileInfo>>('/auth/userinfo'))
  },

  updateProfile(params: ProfileUpdateParams) {
    return asApiPromise(request.put<ApiResponse<ProfileInfo>>('/auth/profile', params))
  },

  uploadAvatar(file: File, onProgress?: (percentage: number) => void) {
    const form = new FormData()
    form.append('file', file)
    return asApiPromise(
      request.post<ApiResponse<AvatarUploadResult>>('/auth/avatar', form, {
        onUploadProgress: (event: AxiosProgressEvent) => {
          if (!event.total) return
          onProgress?.(Math.min(99, Math.round((event.loaded / event.total) * 100)))
        },
      }),
    )
  },

  removeAvatar() {
    return asApiPromise(request.delete<ApiResponse<null>>('/auth/avatar'))
  },

  changePassword(params: ChangePasswordParams) {
    return asApiPromise(request.put<ApiResponse<ChangePasswordResult>>('/auth/password', params))
  },

  setupTwoFactor(params: TwoFactorSetupParams) {
    return asApiPromise(request.post<ApiResponse<TwoFactorSetupResult>>('/auth/two-factor/setup', params))
  },

  enableTwoFactor(params: TwoFactorEnableParams) {
    return asApiPromise(request.post<ApiResponse<TwoFactorStatusResult>>('/auth/two-factor/enable', params))
  },

  disableTwoFactor(params: TwoFactorDisableParams) {
    return asApiPromise(request.post<ApiResponse<TwoFactorStatusResult>>('/auth/two-factor/disable', params))
  },

  getLoginLogs(page = 1, pageSize = 20) {
    return asApiPromise(
      request.get<ApiResponse<PaginatedData<LoginLogItem>>>('/auth/login-logs', {
        params: { page, page_size: pageSize },
      }),
    )
  },

  getPreferences() {
    return asApiPromise(request.get<ApiResponse<ProfilePreferences>>('/auth/preferences'))
  },

  updatePreferences(params: ProfilePreferencesUpdateParams) {
    return asApiPromise(request.put<ApiResponse<ProfilePreferences>>('/auth/preferences', params))
  },

  deleteAccount(params: DeleteAccountParams) {
    return asApiPromise(
      request.delete<ApiResponse<null>>('/auth/account', { data: params }),
    )
  },
}
