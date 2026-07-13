export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email: string
}

export interface LoginResponse {
  token: string
  user: {
    id: number
    username: string
    email: string
    avatar?: string
  }
}