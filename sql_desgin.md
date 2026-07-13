# 用户注册登录模块 - 数据库设计

## 一、设计思想

### 1. 核心需求
- 用户注册（邮箱/手机号）
- 用户登录（密码登录）
- JWT Token 认证
- 密码安全存储
- 登录状态管理
- 安全审计日志

### 2. 设计原则
- **安全第一**：密码 bcrypt 加密，token 加密存储
- **多设备支持**：一个用户可以同时在多个设备登录
- **可扩展性**：预留第三方登录字段
- **审计追踪**：记录登录日志，便于安全分析

### 3. 表结构设计

#### 核心表：
1. **users** - 用户主表（存储用户基本信息，含角色和逻辑删除）
2. **refresh_tokens** - 刷新令牌表（仅管理 refresh token，access token 不持久化）
3. **verification_codes** - 验证码表（注册/找回密码）
4. **login_logs** - 登录日志表（安全审计，含登录地点）

### 4. 技术选型
- **数据库**：MySQL 8.0+
- **密码加密**：bcrypt（cost factor = 12）
- **Token**：JWT（HS256 算法）
- **字符集**：utf8mb4（支持 emoji）

---

## 二、数据表设计

### 1. users - 用户表

**用途**：存储用户基本信息和认证数据

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) | NO | - | 用户名，唯一 |
| email | VARCHAR(100) | YES | NULL | 邮箱，唯一 |
| phone | VARCHAR(20) | YES | NULL | 手机号，唯一 |
| password_hash | VARCHAR(255) | NO | - | bcrypt 加密后的密码 |
| avatar | VARCHAR(500) | YES | NULL | 头像 URL |
| role | VARCHAR(20) | NO | 'user' | 角色：user/super_admin |
| status | VARCHAR(20) | NO | 'active' | 状态：active/inactive/banned |
| email_verified | BOOLEAN | NO | FALSE | 邮箱是否验证 |
| phone_verified | BOOLEAN | NO | FALSE | 手机是否验证 |
| last_login_at | TIMESTAMP | YES | NULL | 最后登录时间 |
| last_login_ip | VARCHAR(45) | YES | NULL | 最后登录 IP |
| is_deleted | BOOLEAN | NO | FALSE | 是否已删除（逻辑删除） |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | YES | NULL | 软删除时间 |

**索引设计**：
- PRIMARY KEY (id)
- UNIQUE (username)
- UNIQUE (email)
- UNIQUE (phone)
- INDEX (status)
- INDEX (role)
- INDEX (is_deleted)
- INDEX (created_at)

**设计说明**：
- username、email、phone 三个字段都是唯一的，用户可以选择任意一种方式注册
- password_hash 使用 bcrypt 加密，不可逆
- role 字段用于权限控制，默认 'user'，超级管理员为 'super_admin'
- status 字段支持禁用用户
- email_verified 和 phone_verified 用于标识验证状态
- last_login_at 和 last_login_ip 记录最后登录信息
- is_deleted 用于逻辑删除，避免物理删除导致关联数据问题
- deleted_at 记录删除时间，配合 is_deleted 使用

---

### 2. refresh_tokens - 刷新令牌表

**用途**：仅管理 refresh token，access token 不持久化存储（仅在内存中签发）

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| refresh_token | VARCHAR(500) | NO | - | 刷新令牌（唯一） |
| device_name | VARCHAR(100) | YES | NULL | 设备名称（如 "Chrome - Windows"） |
| device_info | VARCHAR(200) | YES | NULL | 设备详细信息（User-Agent） |
| ip_address | VARCHAR(45) | YES | NULL | 登录 IP |
| expires_at | TIMESTAMP | NO | - | 过期时间 |
| last_used_at | TIMESTAMP | YES | NULL | 最后使用时间 |
| is_active | BOOLEAN | NO | TRUE | 是否有效 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引设计**：
- PRIMARY KEY (id)
- UNIQUE (refresh_token)
- INDEX (user_id, is_active)
- INDEX (expires_at)
- INDEX (created_at)

**设计说明**：
- 仅存储 refresh_token，access_token 不持久化（每次请求时动态签发）
- 一个用户可以有多个 refresh_token（多设备登录）
- device_name 记录设备名称，便于用户查看和管理登录设备
- expires_at 用于自动清理过期 token
- is_active 支持手动注销某个设备的登录

---

### 3. verification_codes - 验证码表

**用途**：存储注册/找回密码的验证码

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| target | VARCHAR(100) | NO | - | 目标（邮箱/手机号） |
| code | VARCHAR(10) | NO | - | 验证码 |
| type | VARCHAR(20) | NO | - | 类型：register/reset_password |
| used | BOOLEAN | NO | FALSE | 是否已使用 |
| expires_at | TIMESTAMP | NO | - | 过期时间 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引设计**：
- PRIMARY KEY (id)
- INDEX (target, type, used)
- INDEX (expires_at)
- INDEX (created_at)

**设计说明**：
- 验证码 6 位数字，5 分钟过期
- used 字段防止重复使用
- type 区分不同用途（注册/找回密码）

---

### 4. login_logs - 登录日志表

**用途**：记录用户登录行为，用于安全审计

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | YES | NULL | 外键：users.id（登录成功时有值） |
| login_type | VARCHAR(20) | NO | - | 类型：password/sms/third_party |
| identifier | VARCHAR(100) | NO | - | 登录标识（用户名/邮箱/手机） |
| ip_address | VARCHAR(45) | NO | - | 登录 IP |
| login_location | VARCHAR(200) | YES | NULL | 登录地点（如 "北京市"） |
| user_agent | VARCHAR(500) | YES | NULL | 浏览器 User-Agent |
| status | VARCHAR(20) | NO | - | 状态：success/failed |
| fail_reason | VARCHAR(200) | YES | NULL | 失败原因 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 登录时间 |

**索引设计**：
- PRIMARY KEY (id)
- INDEX (user_id, created_at)
- INDEX (identifier, status)
- INDEX (created_at)
- INDEX (ip_address)

**设计说明**：
- 记录所有登录尝试（成功和失败）
- login_location 记录登录地点，便于检测异地登录
- 用于安全分析（异常登录检测）
- fail_reason 记录失败原因（密码错误/账号禁用等）

---

## 三、SQL 建表语句

```sql
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_career_agent 
DEFAULT CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE ai_career_agent;

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE `users` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT 'bcrypt加密密码',
  `avatar` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
  `role` VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色：user/super_admin',
  `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态：active/inactive/banned',
  `email_verified` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '邮箱是否验证',
  `phone_verified` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '手机是否验证',
  `last_login_at` TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
  `last_login_ip` VARCHAR(45) DEFAULT NULL COMMENT '最后登录IP',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已删除（逻辑删除）',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  UNIQUE KEY `uk_phone` (`phone`),
  KEY `idx_status` (`status`),
  KEY `idx_role` (`role`),
  KEY `idx_is_deleted` (`is_deleted`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 2. 刷新令牌表（仅管理 refresh token，access token 不持久化）
-- ============================================
CREATE TABLE `refresh_tokens` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `refresh_token` VARCHAR(500) NOT NULL COMMENT '刷新令牌（唯一）',
  `device_name` VARCHAR(100) DEFAULT NULL COMMENT '设备名称（如 "Chrome - Windows"）',
  `device_info` VARCHAR(200) DEFAULT NULL COMMENT '设备详细信息（User-Agent）',
  `ip_address` VARCHAR(45) DEFAULT NULL COMMENT '登录IP',
  `expires_at` TIMESTAMP NOT NULL COMMENT '过期时间',
  `last_used_at` TIMESTAMP NULL DEFAULT NULL COMMENT '最后使用时间',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否有效',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_refresh_token` (`refresh_token`),
  KEY `idx_user_active` (`user_id`, `is_active`),
  KEY `idx_expires` (`expires_at`),
  KEY `idx_created` (`created_at`),
  CONSTRAINT `fk_tokens_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='刷新令牌表（仅管理 refresh token）';

-- ============================================
-- 3. 验证码表
-- ============================================
CREATE TABLE `verification_codes` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `target` VARCHAR(100) NOT NULL COMMENT '目标（邮箱/手机号）',
  `code` VARCHAR(10) NOT NULL COMMENT '验证码',
  `type` VARCHAR(20) NOT NULL COMMENT '类型：register/reset_password',
  `used` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已使用',
  `expires_at` TIMESTAMP NOT NULL COMMENT '过期时间',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_target_type` (`target`, `type`, `used`),
  KEY `idx_expires` (`expires_at`),
  KEY `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='验证码表';

-- ============================================
-- 4. 登录日志表
-- ============================================
CREATE TABLE `login_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT DEFAULT NULL COMMENT '用户ID（登录成功时有值）',
  `login_type` VARCHAR(20) NOT NULL COMMENT '类型：password/sms/third_party',
  `identifier` VARCHAR(100) NOT NULL COMMENT '登录标识',
  `ip_address` VARCHAR(45) NOT NULL COMMENT '登录IP',
  `login_location` VARCHAR(200) DEFAULT NULL COMMENT '登录地点（如 "北京市"）',
  `user_agent` VARCHAR(500) DEFAULT NULL COMMENT '浏览器UA',
  `status` VARCHAR(20) NOT NULL COMMENT '状态：success/failed',
  `fail_reason` VARCHAR(200) DEFAULT NULL COMMENT '失败原因',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_time` (`user_id`, `created_at`),
  KEY `idx_identifier_status` (`identifier`, `status`),
  KEY `idx_created` (`created_at`),
  KEY `idx_ip` (`ip_address`),
  CONSTRAINT `fk_logs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

-- ============================================
-- 初始化数据（可选）
-- ============================================
-- 插入测试用户（密码为：Test123456）
-- INSERT INTO `users` (`username`, `email`, `password_hash`, `status`, `email_verified`)
-- VALUES ('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TcQZJrKbxEyNvDfWuXyZvWqZqZqZ', 'active', 1);
```

---

## 四、关键设计说明

### 1. 密码加密
```javascript
// 使用 bcrypt 加密（示例）
const bcrypt = require('bcrypt');
const saltRounds = 12;

// 注册时加密
const passwordHash = await bcrypt.hash(password, saltRounds);

// 登录时验证
const isValid = await bcrypt.compare(password, user.passwordHash);
```

### 2. JWT Token 生成
```javascript
// 生成 access token（有效期 2 小时，不持久化，仅在内存中签发）
const accessToken = jwt.sign(
  { userId: user.id, username: user.username },
  process.env.JWT_SECRET,
  { expiresIn: '2h' }
);

// 生成 refresh token（有效期 7 天，持久化存储到数据库）
const refreshToken = jwt.sign(
  { userId: user.id, tokenType: 'refresh' },
  process.env.JWT_REFRESH_SECRET,
  { expiresIn: '7d' }
);

// 将 refresh token 存入 refresh_tokens 表
await db.query(
  'INSERT INTO refresh_tokens (user_id, refresh_token, device_name, device_info, ip_address, expires_at) VALUES (?, ?, ?, ?, ?, ?)',
  [user.id, refreshToken, deviceName, userAgent, ipAddress, expiresAt]
);
```

### 3. 多设备登录
- 每个设备登录都会在 refresh_tokens 表生成新的记录
- device_name 记录设备名称，便于用户查看和管理
- 用户可以查看所有登录设备，并单独注销某个设备
- access token 不持久化，每次请求时动态签发，过期后使用 refresh token 刷新

### 4. 安全策略
- 密码错误 5 次，锁定账号 15 分钟
- 验证码 5 分钟过期，只能使用一次
- 登录日志记录所有尝试
- Token 过期自动清理

### 5. 性能优化
- 所有外键和常用查询字段建立索引
- refresh_tokens 表按 expires_at 定期清理过期令牌
- 登录日志按月分区（未来扩展）
- login_location 通过 IP 地址解析获得（可使用 ip2region 库）

---

## 五、API 接口设计

### 1. 注册接口
```
POST /api/auth/register
Body: {
  "username": "string",
  "email": "string",
  "password": "string",
  "verificationCode": "string"
}
```

### 2. 登录接口
```
POST /api/auth/login
Body: {
  "username": "string",  // 或 email/phone
  "password": "string"
}
Response: {
  "accessToken": "string",      // 不持久化，仅内存中签发
  "refreshToken": "string",     // 持久化存储到 refresh_tokens 表
  "user": { ... }
}
```

### 3. 刷新 Token
```
POST /api/auth/refresh
Body: {
  "refreshToken": "string"
}
Response: {
  "accessToken": "string",      // 新的 access token（不持久化）
  "refreshToken": "string"      // 新的 refresh token（可选，更新数据库）
}
```

### 4. 登出接口
```
POST /api/auth/logout
Headers: {
  "Authorization": "Bearer {accessToken}"
}
```

### 5. 发送验证码
```
POST /api/auth/send-code
Body: {
  "email": "string",
  "type": "register"
}
```

---

## 六、后续扩展

### 预留字段
- 第三方登录：`wechat_openid`, `github_id` 等
- 用户画像：`age`, `gender`, `industry` 等
- 偏好设置：`notification_enabled`, `language` 等

### 未来优化
- Redis 缓存验证码和 token
- 登录日志按月分区
- 异地登录检测和告警
- 双因素认证（2FA）

---

## 七、数据库 Agent 调用

如需进一步调整，可以调用数据库架构师 agent：

```
请使用数据库架构师agent帮我：
1. 优化用户表的索引
2. 添加第三方登录字段
3. 设计用户画像表
```

agent 位置：`.claude/agents/database-architect.md`
