export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  verification_code?: string
}

export interface AuthenticatedLoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: {
    id: number
    username: string
    email: string
    avatar?: string
    phone?: string | null
    status: string
  }
}

export interface TwoFactorRequiredResponse {
  requires_two_factor: true
  two_factor_token: string
  expires_in: number
}

export type LoginResponse = AuthenticatedLoginResponse | TwoFactorRequiredResponse

export interface TwoFactorLoginRequest {
  two_factor_token: string
  code: string
}

// 刷新 Token 响应
export interface RefreshTokenResponse {
  access_token: string
  expires_in: number
}
