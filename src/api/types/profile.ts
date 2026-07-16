export interface ProfileInfo {
  id: number
  username: string
  email: string
  phone?: string | null
  avatar?: string | null
  status: 'active' | 'inactive'
  email_verified: boolean
  phone_verified: boolean
  two_factor_enabled: boolean
  created_at: string
  last_login_at?: string | null
}

export interface ProfileUpdateParams {
  username: string
}

export interface AvatarUploadResult {
  avatar_url: string
}

export interface ChangePasswordParams {
  current_password: string
  new_password: string
}

export interface ChangePasswordResult { requires_relogin: boolean }

export interface TwoFactorSetupResult {
  secret: string
  qr_code_data_url: string
  recovery_codes?: string[]
}
export interface TwoFactorSetupParams { password: string }

export interface TwoFactorEnableParams {
  code: string
}

export interface TwoFactorDisableParams {
  password: string
  code: string
}

export interface TwoFactorStatusResult {
  enabled: boolean
  recovery_codes?: string[]
}

export interface LoginLogItem {
  id: number
  login_time: string
  ip_address?: string | null
  location?: string | null
  device?: string | null
  browser?: string | null
  operating_system?: string | null
  status: 'success' | 'failed'
}

export interface ProfilePreferences {
  email_notifications: boolean
  push_notifications: boolean
  ai_report_notifications: boolean
}

export type ProfilePreferencesUpdateParams = Partial<ProfilePreferences>

export interface DeleteAccountParams {
  password: string
  confirmation: '确认删除'
  code?: string
}
