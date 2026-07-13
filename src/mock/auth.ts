import { registerMock } from './index'

export function setupAuthMock() {
  // Login - accept any username/password
  registerMock('post', '/auth/login', (params: any) => {
    const { username } = params
    return {
      token: 'mock_token_' + Date.now(),
      user: {
        id: 1,
        username: username || 'career_user',
        email: username ? `${username}@example.com` : 'user@example.com',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + (username || 'default'),
      },
    }
  })

  // Register
  registerMock('post', '/auth/register', () => {
    return null
  })

  // Get user info
  registerMock('get', '/auth/userinfo', () => {
    return {
      id: 1,
      username: 'career_user',
      email: 'career_user@example.com',
      avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=career_user',
      phone: '138****8888',
      created_at: '2025-01-15T08:00:00.000Z',
    }
  })

  // Update profile
  registerMock('put', '/auth/profile', (params: any) => {
    return {
      id: 1,
      username: params.username || 'career_user',
      email: params.email || 'career_user@example.com',
      avatar: params.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=career_user',
      phone: params.phone || '138****8888',
      created_at: '2025-01-15T08:00:00.000Z',
    }
  })

  // Logout
  registerMock('post', '/auth/logout', () => {
    return null
  })
}