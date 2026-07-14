# 刷新 Token 流程接口文档

## 概述

本文档描述了 AI Career Agent 前端的 Token 刷新机制，包括自动刷新流程、错误处理和最佳实践。

---

## 1. 接口定义

### 1.1 刷新 Token 接口

**请求方式**: POST  
**请求路径**: `/api/auth/refresh`

**请求参数**:
```json
{
  "refresh_token": "string"  // 必填，刷新令牌
}
```

**响应格式**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "string",  // 新的访问令牌
    "expires_in": 7200         // 过期时间（秒）
  }
}
```

**类型定义**:
```typescript
export interface RefreshTokenResponse {
  access_token: string
  expires_in: number
}
```

---

## 2. Token 存储

### 2.1 存储位置

所有 Token 存储在 `localStorage` 中：

| Key | 说明 | 过期时间 |
|-----|------|----------|
| `ai_career_token` | 访问令牌（access_token） | 2 小时 |
| `refresh_token` | 刷新令牌（refresh_token） | 7 天 |

### 2.2 存储时机

**登录成功后**:
```typescript
localStorage.setItem('token', response.data.access_token)
localStorage.setItem('refresh_token', response.data.refresh_token)
localStorage.setItem('user', JSON.stringify(response.data.user))
```

**退出登录时**:
```typescript
localStorage.removeItem('token')
localStorage.removeItem('refresh_token')
localStorage.removeItem('user')
```

---

## 3. 自动刷新流程

### 3.1 流程图

```
请求发起
  ↓
请求拦截器注入 access_token
  ↓
发送请求
  ↓
响应拦截器处理
  ├─ 成功 → 返回数据
  └─ 401 错误 → 检查是否可刷新
                  ↓
            检查 refresh_token 是否存在
                  ↓
            调用 /auth/refresh 接口
                  ↓
            ├─ 成功 → 更新 access_token
            │        → 重试原请求
            │        → 返回数据
            │
            └─ 失败 → 清除所有 Token
                     → 跳转登录页
```

### 3.2 核心逻辑

**请求拦截器**（`src/utils/request.ts`）:
```typescript
request.interceptors.request.use(
  (config) => {
    const token = storage.get<string>(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)
```

**响应拦截器**（自动刷新逻辑）:
```typescript
request.interceptors.response.use(
  (response) => {
    // 成功处理...
  },
  async (error) => {
    const originalRequest = error.config

    // 401 错误且不是刷新请求本身
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 如果是刷新请求失败，直接跳转登录
      if (originalRequest.url?.includes('/auth/refresh')) {
        storage.remove(TOKEN_KEY)
        storage.remove('refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 检查 refresh_token 是否存在
      const refreshToken = storage.get<string>('refresh_token')
      if (!refreshToken) {
        storage.remove(TOKEN_KEY)
        window.location.href = '/login'
        return Promise.reject(error)
      }

      // 标记请求已重试，防止无限循环
      originalRequest._retry = true

      try {
        // 调用刷新接口
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        })

        const { access_token } = response.data.data
        
        // 更新存储的 token
        storage.set(TOKEN_KEY, access_token)

        // 更新原请求的 Authorization 头
        originalRequest.headers.Authorization = `Bearer ${access_token}`

        // 重试原请求
        return request(originalRequest)
      } catch (refreshError) {
        // 刷新失败，清除所有 token 并跳转登录
        storage.remove(TOKEN_KEY)
        storage.remove('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)
```

---

## 4. 并发请求处理

### 4.1 问题场景

当多个请求同时返回 401 时，如果不加控制，会导致多次刷新请求，造成资源浪费和潜在的安全问题。

### 4.2 解决方案：刷新锁机制

```typescript
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
```

### 4.3 并发处理流程

```
请求 A 返回 401
  ↓
检查 isRefreshing 锁
  ├─ false → 设置 isRefreshing = true
  │         → 发起刷新请求
  │
  └─ true  → 将请求加入订阅队列
            → 等待刷新完成

刷新成功
  ↓
更新 access_token
  ↓
通知所有订阅者
  ↓
所有等待的请求使用新 token 重试
```

---

## 5. 错误处理

### 5.1 刷新失败场景

| 场景 | 处理方式 | 用户提示 |
|------|----------|----------|
| refresh_token 不存在 | 清除 token，跳转登录 | "登录已过期，请重新登录" |
| refresh_token 已过期 | 清除 token，跳转登录 | "登录已过期，请重新登录" |
| refresh_token 无效 | 清除 token，跳转登录 | "登录已过期，请重新登录" |
| 网络错误 | 清除 token，跳转登录 | "网络错误，请检查网络连接" |

### 5.2 防护措施

1. **防止无限循环**: 使用 `_retry` 标记，确保每个请求只重试一次
2. **刷新请求豁免**: 刷新请求本身的 401 错误不触发再次刷新
3. **并发控制**: 使用刷新锁，避免多个请求同时刷新
4. **清理机制**: 刷新失败时清除所有 token，确保用户必须重新登录

---

## 6. API 方法

### 6.1 手动刷新（可选）

虽然自动刷新已在拦截器中实现，但也可以手动调用：

```typescript
import { authApi } from '@/api/auth'

const refreshToken = localStorage.getItem('refresh_token')
if (refreshToken) {
  try {
    const response = await authApi.refresh(refreshToken)
    const { access_token } = response.data
    localStorage.setItem('token', access_token)
  } catch (error) {
    // 处理刷新失败
  }
}
```

---

## 7. 安全考虑

### 7.1 Token 安全

1. **存储位置**: 使用 `localStorage`，注意 XSS 攻击防护
2. **传输方式**: 仅通过 HTTPS 传输
3. **过期时间**: 
   - access_token: 2 小时（短）
   - refresh_token: 7 天（长）
4. **刷新策略**: 仅在 access_token 过期时刷新，不主动刷新

### 7.2 后端配合

后端应实现：
1. refresh_token 的一次性使用或轮换机制
2. 刷新失败时使所有设备失效
3. 记录刷新日志，用于安全审计
4. 检测异常刷新行为

---

## 8. 测试建议

### 8.1 单元测试

```typescript
describe('Token Refresh', () => {
  test('should refresh token on 401 error', async () => {
    // 模拟 401 响应
    // 验证刷新请求被发送
    // 验证原请求被重试
  })

  test('should redirect to login if refresh fails', async () => {
    // 模拟刷新失败
    // 验证跳转到登录页
    // 验证 token 被清除
  })

  test('should handle concurrent 401 errors', async () => {
    // 模拟多个并发 401
    // 验证只发送一次刷新请求
    // 验证所有请求都被重试
  })
})
```

### 8.2 集成测试

1. 设置 access_token 为即将过期
2. 发起 API 请求
3. 验证自动刷新触发
4. 验证请求成功返回

---

## 9. 相关文件

| 文件路径 | 说明 |
|----------|------|
| `src/utils/request.ts` | HTTP 请求封装，包含自动刷新逻辑 |
| `src/api/auth.ts` | 认证 API，包含 refresh 方法 |
| `src/api/types/auth.ts` | 认证类型定义，包含 RefreshTokenResponse |
| `src/utils/storage.ts` | 存储工具，封装 localStorage 操作 |

---

## 10. 常见问题

### Q1: 为什么不使用 Axios 拦截器的队列机制？

**A**: 我们使用了自定义的订阅者模式，这样可以更灵活地控制刷新流程，并且在刷新成功后统一通知所有等待的请求。

### Q2: 如果用户关闭了浏览器，refresh_token 还在吗？

**A**: 是的，`localStorage` 中的数据会持久化，除非用户手动清除或使用无痕模式。

### Q3: 如何强制用户重新登录？

**A**: 后端可以让 refresh_token 失效，前端刷新时会返回 401，自动跳转到登录页。

### Q4: 多个标签页同时打开，Token 会冲突吗？

**A**: 不会。每个标签页有独立的内存空间，刷新锁只在单个标签页内生效。但 `localStorage` 是共享的，一个标签页刷新 token 后，其他标签页下次请求时会使用新 token。

---

## 11. 未来优化

1. **主动刷新**: 在 token 过期前 5 分钟主动刷新，避免请求中断
2. **Token 轮换**: 每次刷新返回新的 refresh_token，提高安全性
3. **离线检测**: 网络恢复后自动重试失败的请求
4. **刷新频率限制**: 前端限制刷新频率，防止滥用

---

**文档版本**: 1.0  
**最后更新**: 2026-07-14  
**维护者**: AI Career Agent 开发团队
