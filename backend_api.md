# AI Career Agent 后端 API 接口文档

> 版本：2.0
> 最后更新：2026-07-13
> 基础路径：`/api`
> 认证方式：Bearer Token（`Authorization: Bearer <token>`）
> 技术栈：FastAPI + LangChain + JWT + SQLAlchemy + MySQL + 向量数据库（Pinecone/Milvus/Chroma）

---

## 目录

- [一、通用说明](#一通用说明)
- [二、用户认证模块](#二用户认证模块)
- [三、用户资料模块](#三用户资料模块)
- [四、简历管理模块](#四简历管理模块)
- [五、职业规划模块](#五职业规划模块)
- [六、岗位推荐模块](#六岗位推荐模块)
- [七、AI聊天助手模块](#七ai聊天助手模块)
- [八、Agent 任务模块](#八agent-任务模块)
- [九、HR AI Agent 沟通中心](#九hr-ai-agent-沟通中心)
- [十、AI面试模块](#十ai面试模块)
- [十一、爬虫系统模块](#十一爬虫系统模块)
- [十二、向量知识库模块](#十二向量知识库模块)
- [十三、平台账号管理模块](#十三平台账号管理模块)
- [十四、WebSocket 实时通信](#十四websocket-实时通信)

---

## 一、通用说明

### 1.1 认证

所有需要认证的接口，需在请求头中携带 Token：

```
Authorization: Bearer <token>
```

Token 通过 `/auth/login` 或 `/auth/register` 获取。

### 1.2 响应格式

所有接口返回统一格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | number | 状态码，200 表示成功 |
| message | string | 响应消息 |
| data | any | 响应数据 |

### 1.3 分页参数

分页接口支持以下查询参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | number | 1 | 当前页码 |
| page_size | number | 10 | 每页数量 |

### 1.4 分页响应格式

```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

### 1.5 错误码

| code | 说明 |
|------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 / Token 过期 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如用户名已存在） |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |

### 1.6 时间格式

所有时间字段使用 ISO 8601 格式：`2026-07-13T14:30:00.000Z`

---

## 二、用户认证模块

> 对应数据表：`users`, `user_tokens`, `verification_codes`, `login_logs`

### 2.1 用户注册

**POST** `/auth/register`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（2-20字符，唯一） |
| email | string | 是 | 邮箱（唯一） |
| password | string | 是 | 密码（至少6字符，bcrypt 加密存储） |
| verification_code | string | 否 | 邮箱验证码 |

**请求示例：**

```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "Test123456",
  "verification_code": "123456"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com"
  }
}
```

**业务逻辑：**
1. 校验用户名/邮箱唯一性
2. bcrypt 加密密码（cost factor = 12）
3. 如开启邮箱验证，校验验证码
4. 创建用户记录
5. 记录登录日志

---

### 2.2 用户登录

**POST** `/auth/login`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 / 邮箱 / 手机号 |
| password | string | 是 | 密码 |

**请求示例：**

```json
{
  "username": "zhangsan",
  "password": "Test123456"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "zhangsan",
      "email": "zhangsan@example.com",
      "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan",
      "phone": null,
      "status": "active"
    }
  }
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| data.access_token | string | JWT 访问令牌（有效期 2 小时） |
| data.refresh_token | string | 刷新令牌（有效期 7 天） |
| data.expires_in | number | access_token 过期时间（秒） |
| data.user | object | 用户基本信息 |

**业务逻辑：**
1. 支持用户名 / 邮箱 / 手机号登录
2. bcrypt 验证密码
3. 检查账号状态（active / inactive / banned）
4. 密码错误 5 次锁定账号 15 分钟
5. 生成 access_token + refresh_token，存入 `user_tokens` 表
6. 记录登录日志到 `login_logs` 表
7. 更新 `users.last_login_at` 和 `users.last_login_ip`

---

### 2.3 刷新 Token

**POST** `/auth/refresh`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 7200
  }
}
```

**业务逻辑：**
1. 验证 refresh_token 有效性
2. 检查是否过期
3. 生成新的 access_token
4. 更新 `user_tokens.last_used_at`

---

### 2.4 获取用户信息

**GET** `/auth/userinfo`

**请求参数：** 无（通过 Token 获取当前用户）

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "phone": "138****8888",
    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan",
    "status": "active",
    "email_verified": true,
    "phone_verified": false,
    "created_at": "2026-01-15T08:00:00.000Z",
    "last_login_at": "2026-07-13T14:30:00.000Z"
  }
}
```

---

### 2.5 用户登出

**POST** `/auth/logout`

**请求参数：** 无

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": null
}
```

**业务逻辑：**
1. 将当前 Token 在 `user_tokens` 表中标记为 `is_active = false`
2. 清除 Token 记录

---

### 2.6 发送验证码

**POST** `/auth/send-code`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 目标邮箱 |
| type | string | 是 | 类型：`register` / `reset_password` |

**请求示例：**

```json
{
  "email": "zhangsan@example.com",
  "type": "register"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "验证码已发送",
  "data": null
}
```

**业务逻辑：**
1. 生成 6 位随机验证码
2. 存入 `verification_codes` 表（5 分钟过期）
3. 发送邮件（SMTP / 第三方邮件服务）
4. 同一邮箱 60 秒内不可重复发送

---

### 2.7 登出所有设备

**POST** `/auth/logout-all`

**请求参数：** 无

**响应示例：**

```json
{
  "code": 200,
  "message": "已登出所有设备",
  "data": {
    "revoked_count": 3
  }
}
```

**业务逻辑：**
1. 将当前用户所有 `user_tokens` 记录标记为 `is_active = false`
2. 返回被注销的设备数量

---

### 2.8 获取登录设备列表

**GET** `/auth/devices`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "device_info": "Chrome / Windows 10",
      "ip_address": "192.168.1.100",
      "is_current": true,
      "last_used_at": "2026-07-13T14:30:00.000Z",
      "created_at": "2026-07-10T08:00:00.000Z"
    },
    {
      "id": 2,
      "device_info": "Safari / macOS",
      "ip_address": "192.168.1.101",
      "is_current": false,
      "last_used_at": "2026-07-12T10:00:00.000Z",
      "created_at": "2026-07-11T09:00:00.000Z"
    }
  ]
}
```

---

### 2.9 注销指定设备

**DELETE** `/auth/devices/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 设备 Token 记录 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "已注销该设备",
  "data": null
}
```

---

## 三、用户资料模块

> 对应数据表：`users`

### 3.1 更新用户资料

**PUT** `/auth/profile`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 用户名 |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 手机号 |
| avatar | string | 否 | 头像 URL |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "phone": "13812348888",
    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan",
    "status": "active",
    "email_verified": true,
    "phone_verified": false,
    "created_at": "2026-01-15T08:00:00.000Z",
    "last_login_at": "2026-07-13T14:30:00.000Z"
  }
}
```

---

### 3.2 更新自动化偏好

**PUT** `/auth/preferences`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| auto_apply_enabled | boolean | 否 | 是否开启自动投递 |
| auto_communicate_enabled | boolean | 否 | 是否开启 AI 自动沟通 |
| preferred_salary_min | number | 否 | 期望最低薪资（元） |
| preferred_salary_max | number | 否 | 期望最高薪资（元） |
| preferred_cities | string[] | 否 | 期望城市列表 |
| preferred_skills | string[] | 否 | 技能标签列表 |
| preferred_positions | string[] | 否 | 期望岗位列表 |

**请求示例：**

```json
{
  "auto_apply_enabled": true,
  "auto_communicate_enabled": true,
  "preferred_salary_min": 20000,
  "preferred_salary_max": 50000,
  "preferred_cities": ["北京", "上海", "杭州"],
  "preferred_skills": ["Vue3", "TypeScript", "Node.js"],
  "preferred_positions": ["前端开发工程师", "全栈工程师"]
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "auto_apply_enabled": true,
    "auto_communicate_enabled": true,
    "preferred_salary_min": 20000,
    "preferred_salary_max": 50000,
    "preferred_cities": ["北京", "上海", "杭州"],
    "preferred_skills": ["Vue3", "TypeScript", "Node.js"],
    "preferred_positions": ["前端开发工程师", "全栈工程师"]
  }
}
```

---

### 3.3 上传头像

**POST** `/auth/avatar`

**Content-Type:** `multipart/form-data`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 头像图片（JPG/PNG，最大 5MB） |

**响应示例：**

```json
{
  "code": 200,
  "message": "头像上传成功",
  "data": {
    "avatar_url": "/uploads/avatars/user_1_1720000000.jpg"
  }
}
```

---

## 四、简历管理模块

> 对应数据表：`resumes`, `resume_analyses`

### 4.1 获取简历列表

**GET** `/resumes`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认 1 |
| page_size | number | 否 | 每页数量，默认 10 |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "前端开发工程师简历",
        "file_type": "pdf",
        "file_url": "/resumes/resume_1.pdf",
        "file_size": 245760,
        "score": 85,
        "status": "completed",
        "analysis": {
          "score": 85,
          "strengths": ["技术栈匹配度高", "项目经验丰富"],
          "weaknesses": ["缺少性能优化描述"],
          "suggestions": ["补充 Webpack 构建优化经验"],
          "missing_keywords": ["Webpack", "CI/CD"],
          "format_score": 90,
          "content_score": 82,
          "relevance_score": 88
        },
        "created_at": "2026-06-28T10:30:00.000Z",
        "updated_at": "2026-07-10T14:20:00.000Z"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 10
  }
}
```

---

### 4.2 获取简历详情

**GET** `/resumes/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 简历 ID |

**响应示例：** 同 4.1 中单个 Resume 对象（包含 analysis 详情）。

---

### 4.3 上传简历

**POST** `/resumes/upload`

**Content-Type:** `multipart/form-data`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 简历文件（PDF / DOC / DOCX，最大 10MB） |
| title | string | 否 | 简历标题 |

**响应示例：**

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "id": 10,
    "title": "前端工程师_张三",
    "file_type": "pdf",
    "file_url": "/resumes/resume_10.pdf",
    "file_size": 150000,
    "score": null,
    "status": "pending",
    "analysis": null,
    "created_at": "2026-07-13T10:00:00.000Z",
    "updated_at": "2026-07-13T10:00:00.000Z"
  }
}
```

**业务逻辑：**
1. 保存文件到存储（本地 / OSS）
2. 创建 `resumes` 记录，状态为 `pending`
3. 触发异步 AI 分析任务

---

### 4.4 删除简历

**DELETE** `/resumes/:id`

**响应示例：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 4.5 AI 分析简历

**POST** `/resumes/:id/analyze`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 简历 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "分析完成",
  "data": {
    "score": 82,
    "strengths": ["技术栈覆盖面广", "项目经验与岗位匹配度高"],
    "weaknesses": ["工作经历时间线有断档", "部分技能描述过于简略"],
    "suggestions": [
      "补充近期的技术学习经历填补时间断档",
      "对核心技能增加具体的使用年限和熟练度描述"
    ],
    "missing_keywords": ["TypeScript 高级类型", "前端性能监控"],
    "format_score": 88,
    "content_score": 78,
    "relevance_score": 85
  }
}
```

**ResumeAnalysis 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| score | number | 综合评分（0-100） |
| strengths | string[] | 优势列表 |
| weaknesses | string[] | 劣势列表 |
| suggestions | string[] | 改进建议 |
| missing_keywords | string[] | 缺失关键词 |
| format_score | number | 格式评分（0-100） |
| content_score | number | 内容评分（0-100） |
| relevance_score | number | 匹配度评分（0-100） |

---

### 4.6 AI 优化简历

**POST** `/resumes/:id/optimize`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 简历 ID |

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target_position | string | 否 | 目标岗位 |
| requirements | string | 否 | 岗位要求描述 |

**请求示例：**

```json
{
  "target_position": "高级前端工程师",
  "requirements": "3年以上经验，精通 Vue3 和 TypeScript"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "优化完成",
  "data": {
    "original": "负责公司前端项目的开发与维护，使用 Vue.js 框架进行页面开发。",
    "optimized": "主导公司核心前端项目的架构设计与开发，基于 Vue3 + TypeScript 技术栈实现模块化开发，通过自定义 Hook 封装复用逻辑使代码复用率提升 40%。",
    "changes": [
      {
        "section": "工作经历",
        "original": "负责公司前端项目的开发与维护",
        "optimized": "主导公司核心前端项目的架构设计与开发",
        "reason": "使用'主导'、'核心'等强动词替代'负责'，体现主动性"
      }
    ]
  }
}
```

---

## 五、职业规划模块

> 对应数据表：`career_plans`

### 5.1 生成职业规划

**POST** `/career/plan`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| education | string | 是 | 教育背景 |
| skills | string[] | 是 | 技能标签列表 |
| experience | string | 是 | 工作经历描述 |
| projects | array | 否 | 项目经验列表 |

**请求示例：**

```json
{
  "education": "本科",
  "skills": ["Vue.js", "TypeScript", "Node.js"],
  "experience": "3年前端开发经验，主要负责电商平台前端开发",
  "projects": [
    {
      "name": "电商后台管理系统",
      "description": "使用 Vue3 开发的管理后台",
      "role": "前端负责人"
    }
  ]
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "recommended_positions": [
      "高级前端开发工程师",
      "全栈开发工程师（Node.js 方向）",
      "前端架构师"
    ],
    "learning_path": [
      {
        "stage": "基础巩固阶段",
        "skills": ["TypeScript 深入（泛型、装饰器、条件类型）", "设计模式在前端的应用"],
        "duration": "1-2个月",
        "resources": ["TypeScript 官方文档", "《JavaScript 设计模式》"]
      }
    ],
    "skill_suggestions": [
      "深入学习 TypeScript 高级类型系统",
      "掌握一种后端语言（Node.js / Python / Go）"
    ],
    "career_direction": "根据您的 Vue.js、TypeScript、Node.js 技能背景和当前市场趋势，推荐发展方向为...",
    "market_analysis": "2026 年前端开发市场呈现以下趋势：1）AI 辅助编程普及..."
  }
}
```

**CareerPlan 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| recommended_positions | string[] | 推荐岗位列表 |
| learning_path | array | 学习路线 |
| learning_path[].stage | string | 阶段名称 |
| learning_path[].skills | string[] | 需学习技能 |
| learning_path[].duration | string | 预计时长 |
| learning_path[].resources | string[] | 推荐学习资源 |
| skill_suggestions | string[] | 技能提升建议 |
| career_direction | string | 职业方向描述 |
| market_analysis | string | 市场分析 |

---

## 六、岗位推荐模块

> 对应数据表：`jobs`, `job_sources`（爬虫来源），`job_applications`

### 6.1 获取推荐岗位

**GET** `/jobs/recommendations`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认 1 |
| page_size | number | 否 | 每页数量，默认 10 |
| keywords | string | 否 | 搜索关键词 |
| city | string | 否 | 城市筛选 |
| salary_min | number | 否 | 最低薪资（元） |
| salary_max | number | 否 | 最高薪资（元） |
| source | string | 否 | 来源平台筛选（boss / lagou / liepin） |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "company": "字节跳动",
        "company_logo": "https://img.bosszhipin.com/logo/byte.png",
        "title": "高级前端开发工程师",
        "salary_min": 30000,
        "salary_max": 60000,
        "city": "北京",
        "experience_required": "3-5年",
        "education_required": "本科及以上",
        "skills": ["Vue3", "TypeScript", "Webpack", "Node.js"],
        "description": "负责抖音电商平台前端架构设计与开发...",
        "match_score": 92,
        "match_reasons": ["技能匹配度 92%", "Vue3 经验高度契合"],
        "source": "boss",
        "source_name": "BOSS直聘",
        "source_url": "https://www.zhipin.com/job/1",
        "is_active": true,
        "crawl_time": "2026-07-13T08:00:00.000Z",
        "created_at": "2026-07-10T10:00:00.000Z"
      }
    ],
    "total": 8,
    "page": 1,
    "page_size": 10
  }
}
```

**Job 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 岗位 ID |
| company | string | 公司名称 |
| company_logo | string | 公司 Logo URL |
| title | string | 岗位名称 |
| salary_min | number | 最低薪资（元） |
| salary_max | number | 最高薪资（元） |
| city | string | 城市 |
| experience_required | string | 经验要求 |
| education_required | string | 学历要求 |
| skills | string[] | 技能要求标签 |
| description | string | 岗位描述 |
| match_score | number | AI 匹配度（0-100） |
| match_reasons | string[] | 匹配原因 |
| source | string | 来源平台标识（boss / lagou / liepin） |
| source_name | string | 来源平台名称 |
| source_url | string | 原始链接 |
| is_active | boolean | 岗位是否仍有效 |
| crawl_time | string | 爬取时间 |
| created_at | string | 入库时间 |

---

### 6.2 获取岗位详情

**GET** `/jobs/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 岗位 ID |

**响应示例：** 同 6.1 中单个 Job 对象。

---

### 6.3 申请岗位

**POST** `/jobs/:id/apply`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| resume_id | number | 是 | 使用的简历 ID |
| cover_letter | string | 否 | 自荐信 |

**响应示例：**

```json
{
  "code": 200,
  "message": "投递成功",
  "data": {
    "id": 1,
    "job_id": 1,
    "resume_id": 1,
    "status": "pending",
    "apply_type": "manual",
    "applied_at": "2026-07-13T14:30:00.000Z"
  }
}
```

**业务逻辑：**
1. 创建 `job_applications` 记录
2. `apply_type` 为 `manual`（手动投递）
3. 如由 AI Agent 自动投递，`apply_type` 为 `auto`，同时记录 `agent_task_id`

---

## 七、AI聊天助手模块

> 对应数据表：`chat_sessions`, `chat_messages`

### 7.1 获取会话列表

**GET** `/chat/sessions`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "简历优化咨询",
      "messages": [
        {
          "id": "m1",
          "role": "user",
          "content": "请帮我优化简历中的项目描述",
          "created_at": "2026-07-12T14:30:00.000Z"
        },
        {
          "id": "m2",
          "role": "assistant",
          "content": "好的，请将您的项目描述发送给我...",
          "created_at": "2026-07-12T14:30:05.000Z"
        }
      ],
      "created_at": "2026-07-12T14:30:00.000Z",
      "updated_at": "2026-07-12T14:35:00.000Z"
    }
  ]
}
```

---

### 7.2 获取会话消息

**GET** `/chat/sessions/:id/messages`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 会话 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "m1",
      "role": "user",
      "content": "请帮我优化简历中的项目描述",
      "created_at": "2026-07-12T14:30:00.000Z"
    }
  ]
}
```

---

### 7.3 发送消息

**POST** `/chat/send`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | number | 否 | 会话 ID，不传则创建新会话 |
| message | string | 是 | 用户消息内容 |

**请求示例：**

```json
{
  "session_id": 1,
  "message": "请帮我优化简历中的项目描述"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "msg_1234567890",
    "role": "assistant",
    "content": "好的，我将根据 STAR 原则为您优化...",
    "created_at": "2026-07-13T14:30:05.000Z"
  }
}
```

---

### 7.4 流式发送消息（SSE）

**GET** `/chat/send/stream`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | number | 否 | 会话 ID |
| message | string | 是 | 用户消息（URL 编码） |
| token | string | 是 | JWT Token（作为查询参数传递，SSE 不支持自定义 Header） |

**响应格式：** Server-Sent Events (SSE)

```
data: {"content": "好的", "done": false}

data: {"content": "，我将", "done": false}

data: {"content": "根据 STAR 原则", "done": false}

data: {"content": "", "done": true, "message_id": "msg_xxx"}
```

**业务逻辑：**
1. 通过 LangChain 调用 LLM
2. 流式返回 AI 回复的文本片段
3. `done: true` 表示回复结束，返回完整消息 ID
4. 消息完成后自动保存到 `chat_messages` 表

---

### 7.5 删除会话

**DELETE** `/chat/sessions/:id`

**响应示例：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

**业务逻辑：** 级联删除 `chat_sessions` 和关联的 `chat_messages` 记录。

---

## 八、Agent 任务模块

> 对应数据表：`agent_tasks`, `agent_actions`

### 8.1 获取任务列表

**GET** `/agent/tasks`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "type": "search",
      "status": "running",
      "progress": 65,
      "config": {
        "keywords": "前端开发 北京",
        "salary_range": [25000, 50000],
        "cities": ["北京"]
      },
      "logs": [
        {
          "id": 1,
          "message": "开始搜索任务：前端开发 北京",
          "level": "info",
          "created_at": "2026-07-13T09:00:00.000Z"
        }
      ],
      "applications": [
        {
          "id": 1,
          "company": "字节跳动",
          "position": "高级前端开发工程师",
          "status": "viewed",
          "submitted_at": "2026-07-13T09:05:00.000Z"
        }
      ],
      "created_at": "2026-07-13T09:00:00.000Z",
      "updated_at": "2026-07-13T09:06:30.000Z"
    }
  ]
}
```

**AgentTask 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 任务 ID |
| type | string | 任务类型：`search`（搜索）/ `filter`（筛选）/ `apply`（自动投递）/ `track`（追踪） |
| status | string | 状态：`pending` / `running` / `completed` / `failed` / `paused` |
| progress | number | 进度（0-100） |
| config | object | 任务配置参数 |
| logs | array | 执行日志 |
| applications | array | 投递记录 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

---

### 8.2 获取任务详情

**GET** `/agent/tasks/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 任务 ID |

**响应示例：** 同 8.1 中单个 AgentTask 对象。

---

### 8.3 创建任务

**POST** `/agent/tasks`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 任务类型 |
| config | object | 是 | 任务配置 |

**请求示例：**

```json
{
  "type": "search",
  "config": {
    "keywords": "前端开发",
    "cities": ["北京", "上海"],
    "salary_range": [20000, 50000]
  }
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": 10,
    "type": "search",
    "status": "pending",
    "progress": 0,
    "config": {
      "keywords": "前端开发",
      "cities": ["北京", "上海"],
      "salary_range": [20000, 50000]
    },
    "logs": [],
    "applications": [],
    "created_at": "2026-07-13T10:00:00.000Z",
    "updated_at": "2026-07-13T10:00:00.000Z"
  }
}
```

---

### 8.4 启动任务

**POST** `/agent/tasks/:id/start`

**响应示例：** 返回更新后的 AgentTask 对象，status 变为 `running`。

---

### 8.5 暂停任务

**POST** `/agent/tasks/:id/pause`

**响应示例：** 返回更新后的 AgentTask 对象，status 变为 `paused`。

---

### 8.6 停止任务

**POST** `/agent/tasks/:id/stop`

**响应示例：** 返回更新后的 AgentTask 对象，status 变为 `failed`。

---

### 8.7 删除任务

**DELETE** `/agent/tasks/:id`

**响应示例：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 8.8 获取 Agent 操作日志

**GET** `/agent/tasks/:id/actions`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 任务 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "task_id": 1,
      "action_type": "auto_apply",
      "target_type": "job",
      "target_id": 5,
      "status": "success",
      "detail": {
        "company": "字节跳动",
        "position": "前端开发工程师"
      },
      "error_message": null,
      "created_at": "2026-07-13T09:05:00.000Z"
    }
  ]
}
```

**AgentAction 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 操作 ID |
| task_id | number | 所属任务 ID |
| action_type | string | 操作类型：`auto_apply` / `auto_communicate` / `crawl` / `analyze` |
| target_type | string | 目标类型：`job` / `conversation` / `resume` |
| target_id | number | 目标 ID |
| status | string | 操作状态：`success` / `failed` |
| detail | object | 操作详情 |
| error_message | string | 错误信息（失败时） |
| created_at | string | 操作时间 |

---

## 九、HR AI Agent 沟通中心

> 对应数据表：`hr_conversations`, `hr_messages`
>
> **重要说明：** HR 模块已从简单的消息通知系统升级为 **AI Agent 沟通中心**。核心概念：
> - 系统从 Boss直聘 等平台爬取 HR 聊天记录
> - AI Agent 自动回复 HR 消息
> - 用户可在本系统中监控和管理所有 AI 托管的对话
> - 支持 AI 托管 / 手动接管切换

### 9.1 获取对话列表

**GET** `/hr/conversations`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filter | string | 否 | 筛选：`all`（全部）/ `active`（AI 托管中）/ `paused`（已暂停） |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "hr_name": "李经理",
      "hr_title": "HRBP",
      "company": "阿里巴巴",
      "platform_name": "boss",
      "ai_managed": true,
      "unread_count": 2,
      "last_message_at": "2026-07-13T14:30:00.000Z",
      "boss_conversation_url": "https://www.zhipin.com/web/geek/chat?uid=xxx1",
      "created_at": "2026-07-10T08:00:00.000Z",
      "updated_at": "2026-07-13T14:30:00.000Z"
    },
    {
      "id": 2,
      "hr_name": "王HR",
      "hr_title": "招聘专员",
      "company": "字节跳动",
      "platform_name": "boss",
      "ai_managed": true,
      "unread_count": 0,
      "last_message_at": "2026-07-13T11:20:00.000Z",
      "boss_conversation_url": "https://www.zhipin.com/web/geek/chat?uid=xxx2",
      "created_at": "2026-07-11T09:00:00.000Z",
      "updated_at": "2026-07-13T11:20:00.000Z"
    }
  ]
}
```

**Conversation 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 对话 ID |
| hr_name | string | HR 姓名 |
| hr_title | string | HR 职位 |
| company | string | 公司名称 |
| platform_name | string | 来源平台（boss / lagou / liepin） |
| ai_managed | boolean | 是否由 AI 托管 |
| unread_count | number | 未读消息数 |
| last_message_at | string | 最后消息时间 |
| boss_conversation_url | string | Boss直聘 原始对话链接 |
| created_at | string | 对话创建时间 |
| updated_at | string | 对话更新时间 |

---

### 9.2 获取对话消息

**GET** `/hr/conversations/:id/messages`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 对话 ID |

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认 1 |
| page_size | number | 否 | 每页数量，默认 50 |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "conversation_id": 1,
        "sender_type": "hr",
        "content": "您好，我们查看了您的简历，觉得您非常符合我们前端开发工程师的岗位要求。请问您下周有空来参加面试吗？",
        "is_ai_generated": false,
        "status": "read",
        "sent_at": "2026-07-13T14:25:00.000Z"
      },
      {
        "id": 2,
        "conversation_id": 1,
        "sender_type": "user",
        "content": "您好，非常感谢贵公司的认可！我对这个岗位很感兴趣。请问面试的具体形式是什么？是线上还是线下？",
        "is_ai_generated": true,
        "status": "read",
        "sent_at": "2026-07-13T14:28:00.000Z"
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 50
  }
}
```

**Message 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 消息 ID |
| conversation_id | number | 所属对话 ID |
| sender_type | string | 发送方：`hr` / `user` |
| content | string | 消息内容 |
| is_ai_generated | boolean | 是否由 AI 生成（用户发送但 AI 代写） |
| status | string | 消息状态：`sending` / `sent` / `read` / `failed` |
| sent_at | string | 发送时间 |

---

### 9.3 切换 AI 托管状态

**PUT** `/hr/conversations/:id/ai-managed`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 对话 ID |

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ai_managed | boolean | 是 | 是否启用 AI 托管 |

**请求示例：**

```json
{
  "ai_managed": true
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "AI 托管已启用",
  "data": {
    "id": 1,
    "ai_managed": true
  }
}
```

---

### 9.4 暂停 AI（单个对话）

**POST** `/hr/conversations/:id/pause-ai`

**响应示例：**

```json
{
  "code": 200,
  "message": "AI 已暂停，需手动回复",
  "data": {
    "id": 1,
    "ai_managed": false
  }
}
```

---

### 9.5 恢复 AI（单个对话）

**POST** `/hr/conversations/:id/resume-ai`

**响应示例：**

```json
{
  "code": 200,
  "message": "AI 已恢复自动回复",
  "data": {
    "id": 1,
    "ai_managed": true
  }
}
```

---

### 9.6 人工接管对话

**POST** `/hr/conversations/:id/takeover`

**响应示例：**

```json
{
  "code": 200,
  "message": "已切换到手动模式",
  "data": {
    "id": 1,
    "ai_managed": false
  }
}
```

**业务逻辑：**
1. 将对话的 `ai_managed` 设为 `false`
2. 记录接管日志
3. 停止 AI 自动回复该对话

---

### 9.7 生成 AI 回复建议

**POST** `/hr/conversations/:id/generate-reply`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| context | string | 否 | 额外上下文信息 |

**请求示例：**

```json
{
  "context": "我对这个岗位非常感兴趣，想了解更多信息"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "suggestions": [
      "您好，非常感谢贵公司的认可！我对这个岗位很感兴趣。请问面试的具体形式是什么？是线上还是线下？",
      "感谢您的联系！我很乐意参加面试。请问需要准备哪些材料？我会提前做好准备。",
      "您好！我对贵公司的技术栈和团队文化很感兴趣。能否介绍一下团队的工作氛围和技术方向？"
    ]
  }
}
```

**业务逻辑：**
1. 获取该对话的最近消息上下文
2. 结合用户的简历信息和偏好设置
3. 通过 LangChain 调用 LLM 生成 3 条候选回复
4. 返回建议列表供用户选择

---

### 9.8 发送消息（手动回复）

**POST** `/hr/conversations/:id/messages`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 对话 ID |

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 消息内容 |
| is_ai_generated | boolean | 否 | 是否使用 AI 生成的建议（默认 false） |

**请求示例：**

```json
{
  "content": "您好，非常感谢贵公司的认可！我对这个岗位很感兴趣。",
  "is_ai_generated": true
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "消息已发送",
  "data": {
    "id": 10,
    "conversation_id": 1,
    "sender_type": "user",
    "content": "您好，非常感谢贵公司的认可！我对这个岗位很感兴趣。",
    "is_ai_generated": true,
    "status": "sent",
    "sent_at": "2026-07-13T14:35:00.000Z"
  }
}
```

**业务逻辑：**
1. 保存消息到 `hr_messages` 表
2. 同步消息到 Boss直聘 平台（通过爬虫模块的自动化接口）
3. 更新对话的 `last_message_at`

---

### 9.9 标记消息已读

**POST** `/hr/conversations/:id/read`

**响应示例：**

```json
{
  "code": 200,
  "message": "已标记为已读",
  "data": null
}
```

**业务逻辑：** 将该对话所有未读消息标记为 `read`，对话的 `unread_count` 归零。

---

### 9.10 获取对话统计

**GET** `/hr/conversations/:id/stats`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_messages": 15,
    "ai_reply_count": 10,
    "hr_message_count": 5,
    "unread_count": 2,
    "ai_managed_days": 5,
    "avg_response_time_seconds": 45
  }
}
```

---

### 9.11 全局 AI 沟通设置

**PUT** `/hr/settings`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| global_ai_enabled | boolean | 否 | 全局 AI 自动回复开关 |
| response_style | string | 否 | 回复风格：`professional` / `friendly` / `concise` |
| max_auto_replies_per_day | number | 否 | 每日最大自动回复数 |
| keywords_trigger_reply | string[] | 否 | 触发自动回复的关键词 |
| keywords_block_reply | string[] | 否 | 阻止自动回复的关键词 |

**请求示例：**

```json
{
  "global_ai_enabled": true,
  "response_style": "professional",
  "max_auto_replies_per_day": 50,
  "keywords_trigger_reply": ["面试", "薪资", "岗位"],
  "keywords_block_reply": ["已读", "暂不考虑"]
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "设置已更新",
  "data": {
    "global_ai_enabled": true,
    "response_style": "professional",
    "max_auto_replies_per_day": 50,
    "keywords_trigger_reply": ["面试", "薪资", "岗位"],
    "keywords_block_reply": ["已读", "暂不考虑"]
  }
}
```

---

### 9.12 获取全局统计

**GET** `/hr/stats`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_conversations": 12,
    "ai_managed_count": 8,
    "manual_count": 4,
    "total_unread": 5,
    "today_new_messages": 10,
    "today_ai_replies": 8,
    "total_ai_replies": 150
  }
}
```

---

## 十、AI面试模块

> 对应数据表：`interviews`, `interview_questions`

### 10.1 获取面试列表

**GET** `/interviews`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "字节跳动前端模拟面试",
      "status": "completed",
      "position": "高级前端开发工程师",
      "company": "字节跳动",
      "score": 85,
      "created_at": "2026-07-12T10:00:00.000Z"
    }
  ]
}
```

---

### 10.2 获取面试详情

**GET** `/interviews/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 面试 ID |

**Interview 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 面试 ID |
| title | string | 面试标题 |
| status | string | 状态：`pending` / `in_progress` / `completed` |
| position | string | 目标岗位 |
| company | string | 目标公司 |
| questions | array | 面试题目列表 |
| score | number | 综合评分 |
| report | object | 面试报告 |
| created_at | string | 创建时间 |

---

### 10.3 创建面试

**POST** `/interviews`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| position | string | 是 | 目标岗位 |
| company | string | 否 | 目标公司 |
| question_types | string[] | 否 | 题目类型：`technical` / `behavioral` / `project` / `general` |
| question_count | number | 否 | 题目数量（3-10，默认 5） |

**请求示例：**

```json
{
  "position": "前端开发工程师",
  "company": "字节跳动",
  "question_types": ["technical", "behavioral"],
  "question_count": 5
}
```

**响应示例：** 返回创建的 Interview 对象。

**业务逻辑：**
1. 创建 `interviews` 记录
2. 通过 LangChain 调用 LLM 根据岗位和公司生成面试题
3. 将题目存入 `interview_questions` 表
4. 返回完整面试对象

---

### 10.4 开始面试

**POST** `/interviews/:id/start`

**响应示例：** 返回更新后的 Interview 对象，status 变为 `in_progress`。

---

### 10.5 获取下一题

**GET** `/interviews/:id/next-question`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "type": "technical",
    "question": "什么是虚拟 DOM？Vue3 中是如何优化虚拟 DOM 性能的？",
    "tips": "可以手写一个简单的 Diff 算法来展示理解深度。"
  }
}
```

---

### 10.6 提交答案

**POST** `/interviews/:id/answer`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question_id | number | 是 | 题目 ID |
| answer | string | 是 | 用户答案 |
| duration | number | 是 | 答题时长（秒） |

**请求示例：**

```json
{
  "question_id": 1,
  "answer": "Vue3 使用 Proxy 替代了 Vue2 的 Object.defineProperty...",
  "duration": 180
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "type": "technical",
    "question": "请解释 Vue3 的响应式原理",
    "answer": "Vue3 使用 Proxy...",
    "score": 85,
    "feedback": "回答完整，涵盖了 Proxy 对比 defineProperty 的核心优势。",
    "tips": "面试时可以从 Vue2 的局限性切入。",
    "duration": 180
  }
}
```

**业务逻辑：**
1. 保存答案到 `interview_questions` 表
2. 通过 LangChain 调用 LLM 评分并生成反馈
3. 返回单题评分和反馈

---

### 10.7 结束面试

**POST** `/interviews/:id/finish`

**响应示例：** 返回完整的 Interview 对象，包含 report。

**业务逻辑：**
1. 汇总所有题目评分
2. 通过 LLM 生成综合面试报告
3. 更新面试状态为 `completed`

---

### 10.8 获取面试报告

**GET** `/interviews/:id/report`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "字节跳动前端模拟面试",
    "status": "completed",
    "position": "高级前端开发工程师",
    "company": "字节跳动",
    "score": 85,
    "report": {
      "overall_score": 85,
      "dimension_scores": {
        "technical": 82,
        "behavioral": 90,
        "communication": 88,
        "logic": 85
      },
      "strengths": ["技术原理理解深入", "有大型项目重构经验"],
      "weaknesses": ["部分前沿技术了解不够"],
      "suggestions": ["深入学习浏览器渲染原理和性能优化"],
      "summary": "面试表现整体优秀，技术基础扎实。"
    },
    "created_at": "2026-07-12T10:00:00.000Z"
  }
}
```

**InterviewReport 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| overall_score | number | 综合评分（0-100） |
| dimension_scores | object | 维度评分 |
| dimension_scores.technical | number | 技术深度评分 |
| dimension_scores.behavioral | number | 行为表现评分 |
| dimension_scores.communication | number | 沟通表达评分 |
| dimension_scores.logic | number | 逻辑思维评分 |
| strengths | string[] | 优势列表 |
| weaknesses | string[] | 待提升点 |
| suggestions | string[] | 改进建议 |
| summary | string | 总结 |

---

### 10.9 删除面试

**DELETE** `/interviews/:id`

**响应示例：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

## 十一、爬虫系统模块

> 对应数据表：`job_sources`, `crawl_tasks`, `crawl_logs`
>
> **说明：** 爬虫系统负责从 Boss直聘、拉勾网、猎聘网等平台爬取岗位数据，是岗位推荐模块的数据来源。

### 11.1 获取数据源列表

**GET** `/crawler/sources`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "BOSS直聘",
      "code": "boss",
      "base_url": "https://www.zhipin.com",
      "is_enabled": true,
      "crawl_interval_minutes": 60,
      "last_crawl_at": "2026-07-13T08:00:00.000Z",
      "total_jobs_crawled": 1500,
      "created_at": "2026-07-01T00:00:00.000Z"
    }
  ]
}
```

**JobSource 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 数据源 ID |
| name | string | 平台名称 |
| code | string | 平台标识（boss / lagou / liepin） |
| base_url | string | 平台基础 URL |
| is_enabled | boolean | 是否启用 |
| crawl_interval_minutes | number | 爬取间隔（分钟） |
| last_crawl_at | string | 最后爬取时间 |
| total_jobs_crawled | number | 累计爬取岗位数 |

---

### 11.2 创建爬虫任务

**POST** `/crawler/tasks`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| source_id | number | 是 | 数据源 ID |
| keywords | string | 是 | 搜索关键词 |
| cities | string[] | 否 | 城市列表 |
| max_pages | number | 否 | 最大爬取页数（默认 10） |

**请求示例：**

```json
{
  "source_id": 1,
  "keywords": "前端开发工程师",
  "cities": ["北京", "上海"],
  "max_pages": 20
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "爬虫任务已创建",
  "data": {
    "id": 5,
    "source_id": 1,
    "status": "pending",
    "keywords": "前端开发工程师",
    "cities": ["北京", "上海"],
    "max_pages": 20,
    "jobs_found": 0,
    "jobs_saved": 0,
    "created_at": "2026-07-13T10:00:00.000Z"
  }
}
```

---

### 11.3 获取爬虫任务列表

**GET** `/crawler/tasks`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码 |
| page_size | number | 否 | 每页数量 |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 5,
        "source_id": 1,
        "source_name": "BOSS直聘",
        "status": "running",
        "keywords": "前端开发工程师",
        "cities": ["北京", "上海"],
        "max_pages": 20,
        "current_page": 8,
        "jobs_found": 200,
        "jobs_saved": 180,
        "error_message": null,
        "started_at": "2026-07-13T10:00:00.000Z",
        "completed_at": null,
        "created_at": "2026-07-13T10:00:00.000Z"
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 10
  }
}
```

---

### 11.4 获取爬虫任务详情

**GET** `/crawler/tasks/:id`

**响应示例：** 同 11.3 中单个任务对象。

---

### 11.5 启动爬虫任务

**POST** `/crawler/tasks/:id/start`

**响应示例：** 返回更新后的任务对象，status 变为 `running`。

---

### 11.6 停止爬虫任务

**POST** `/crawler/tasks/:id/stop`

**响应示例：** 返回更新后的任务对象，status 变为 `stopped`。

---

### 11.7 获取爬虫日志

**GET** `/crawler/tasks/:id/logs`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 爬虫任务 ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "task_id": 5,
      "level": "info",
      "message": "开始爬取 BOSS直聘：前端开发工程师 北京",
      "created_at": "2026-07-13T10:00:00.000Z"
    },
    {
      "id": 2,
      "task_id": 5,
      "level": "info",
      "message": "第 1 页爬取完成，发现 25 个岗位",
      "created_at": "2026-07-13T10:01:30.000Z"
    },
    {
      "id": 3,
      "task_id": 5,
      "level": "warning",
      "message": "第 5 页请求频率过高，等待 30 秒",
      "created_at": "2026-07-13T10:06:00.000Z"
    }
  ]
}
```

**CrawlLog 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 日志 ID |
| task_id | number | 所属任务 ID |
| level | string | 日志级别：`info` / `warning` / `error` |
| message | string | 日志内容 |
| created_at | string | 日志时间 |

---

## 十二、向量知识库模块

> 对应数据表：`knowledge_documents`, `knowledge_chunks`
>
> **说明：** 知识库为 RAG（检索增强生成）提供数据支持。文档被切分为 chunks 后存入向量数据库（Pinecone / Milvus / Chroma），用于 AI 面试回答生成、HR 沟通回复、职业规划建议等场景。

### 12.1 获取文档列表

**GET** `/knowledge/documents`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码 |
| page_size | number | 否 | 每页数量 |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "前端面试知识库",
        "description": "包含 Vue、React、TypeScript 等前端面试常见问题与答案",
        "category": "interview",
        "file_type": "pdf",
        "file_size": 5242880,
        "chunk_count": 156,
        "status": "processed",
        "created_at": "2026-07-01T10:00:00.000Z",
        "updated_at": "2026-07-01T10:05:00.000Z"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 10
  }
}
```

**KnowledgeDocument 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 文档 ID |
| title | string | 文档标题 |
| description | string | 文档描述 |
| category | string | 分类：`interview` / `career` / `technical` / `general` |
| file_type | string | 文件类型 |
| file_size | number | 文件大小（字节） |
| chunk_count | number | 切片数量 |
| status | string | 处理状态：`pending` / `processing` / `processed` / `failed` |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

---

### 12.2 上传知识文档

**POST** `/knowledge/documents/upload`

**Content-Type:** `multipart/form-data`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 知识文档（PDF / TXT / MD / DOCX） |
| title | string | 否 | 文档标题 |
| description | string | 否 | 文档描述 |
| category | string | 否 | 分类 |

**响应示例：**

```json
{
  "code": 200,
  "message": "文档上传成功，正在处理",
  "data": {
    "id": 6,
    "title": "Vue3 最佳实践",
    "status": "processing",
    "created_at": "2026-07-13T10:00:00.000Z"
  }
}
```

**业务逻辑：**
1. 保存文件
2. 创建 `knowledge_documents` 记录，状态为 `processing`
3. 异步处理：文本提取 -> 文档切片 -> 向量化 -> 存入向量数据库
4. 处理完成后更新状态为 `processed`

---

### 12.3 删除知识文档

**DELETE** `/knowledge/documents/:id`

**业务逻辑：** 同时删除 `knowledge_documents` 记录和向量数据库中对应的向量。

---

### 12.4 知识库搜索（RAG 检索）

**POST** `/knowledge/search`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索查询 |
| top_k | number | 否 | 返回结果数量（默认 5） |
| category | string | 否 | 限定分类搜索 |

**请求示例：**

```json
{
  "query": "Vue3 组合式 API 和选项式 API 的区别",
  "top_k": 3,
  "category": "interview"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "chunk_id": "vec_001",
      "document_id": 1,
      "document_title": "前端面试知识库",
      "content": "Vue3 组合式 API（Composition API）相比选项式 API（Options API）的主要优势在于...",
      "score": 0.95,
      "metadata": {
        "page": 12,
        "section": "Vue3 核心概念"
      }
    }
  ]
}
```

**业务逻辑：**
1. 将 query 通过 Embedding 模型转为向量
2. 在向量数据库中执行近似最近邻搜索（ANN）
3. 返回相似度最高的 chunks
4. 结果用于 RAG 增强 LLM 回答

---

## 十三、平台账号管理模块

> 对应数据表：`platform_accounts`
>
> **说明：** 管理用户在 Boss直聘 等求职平台的加密账号信息，用于 AI Agent 自动化操作。

### 13.1 获取平台账号列表

**GET** `/platform/accounts`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "platform_name": "BOSS直聘",
      "platform_code": "boss",
      "account_identifier": "138****8888",
      "is_active": true,
      "last_sync_at": "2026-07-13T08:00:00.000Z",
      "created_at": "2026-07-01T00:00:00.000Z"
    }
  ]
}
```

**注意：** 出于安全考虑，账号密码等敏感信息不会在列表中返回。

---

### 13.2 添加平台账号

**POST** `/platform/accounts`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform_code | string | 是 | 平台标识（boss / lagou / liepin） |
| username | string | 是 | 平台账号（手机号/邮箱） |
| password | string | 是 | 平台密码（加密存储） |
| cookie | string | 否 | 平台 Cookie（可选，用于免登录） |

**请求示例：**

```json
{
  "platform_code": "boss",
  "username": "13812348888",
  "password": "platform_password"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "账号添加成功",
  "data": {
    "id": 2,
    "platform_code": "boss",
    "account_identifier": "138****8888",
    "is_active": true,
    "created_at": "2026-07-13T10:00:00.000Z"
  }
}
```

**业务逻辑：**
1. 使用 AES-256 加密密码和 Cookie
2. 存入 `platform_accounts` 表
3. 验证账号登录是否有效

---

### 13.3 更新平台账号

**PUT** `/platform/accounts/:id`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 平台账号 |
| password | string | 否 | 平台密码 |
| cookie | string | 否 | 平台 Cookie |
| is_active | boolean | 否 | 是否启用 |

---

### 13.4 删除平台账号

**DELETE** `/platform/accounts/:id`

---

### 13.5 同步平台数据

**POST** `/platform/accounts/:id/sync`

**响应示例：**

```json
{
  "code": 200,
  "message": "同步任务已启动",
  "data": {
    "task_id": 10,
    "status": "running"
  }
}
```

**业务逻辑：**
1. 使用存储的加密凭证登录目标平台
2. 爬取该账号的聊天记录、投递状态等数据
3. 同步到本地 `hr_conversations` 和 `hr_messages` 表

---

## 十四、WebSocket 实时通信

> 用于 HR AI Agent 沟通中心的实时消息推送

### 14.1 HR 消息实时推送

**WebSocket** `ws://<host>/ws/hr/messages`

**连接参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | JWT Token（通过 query param 传递） |

**连接示例：**

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/hr/messages?token=${jwtToken}`)
```

**服务端推送消息格式：**

```json
{
  "type": "new_message",
  "data": {
    "conversation_id": 1,
    "message": {
      "id": 11,
      "conversation_id": 1,
      "sender_type": "hr",
      "content": "您好，请问您考虑得怎么样了？",
      "is_ai_generated": false,
      "status": "sent",
      "sent_at": "2026-07-13T15:00:00.000Z"
    }
  }
}
```

**消息类型：**

| type | 说明 |
|------|------|
| `new_message` | 收到新的 HR 消息 |
| `ai_reply_sent` | AI 已自动回复 |
| `conversation_updated` | 对话状态更新（如 AI 托管状态变化） |
| `unread_count_updated` | 未读消息数变化 |
| `sync_status` | 平台同步状态更新 |

**客户端可发送的消息：**

```json
{
  "type": "subscribe",
  "data": {
    "conversation_ids": [1, 2, 3]
  }
}
```

```json
{
  "type": "mark_read",
  "data": {
    "conversation_id": 1
  }
}
```

---

### 14.2 Agent 任务状态推送

**WebSocket** `ws://<host>/ws/agent/tasks`

**连接参数：** 同上

**服务端推送消息格式：**

```json
{
  "type": "task_progress",
  "data": {
    "task_id": 1,
    "status": "running",
    "progress": 75,
    "latest_log": {
      "message": "已投递 15 个岗位",
      "level": "info",
      "created_at": "2026-07-13T10:30:00.000Z"
    }
  }
}
```

---

## FastAPI 实现参考

### 项目结构建议

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置（环境变量、数据库连接等）
│   ├── database.py          # SQLAlchemy 数据库连接
│   ├── dependencies.py      # 依赖注入（get_current_user 等）
│   │
│   ├── models/              # SQLAlchemy ORM 模型
│   │   ├── user.py          # users, user_tokens, verification_codes, login_logs
│   │   ├── resume.py        # resumes, resume_analyses
│   │   ├── career.py        # career_plans
│   │   ├── job.py           # jobs, job_applications
│   │   ├── chat.py          # chat_sessions, chat_messages
│   │   ├── agent.py         # agent_tasks, agent_actions
│   │   ├── hr.py            # hr_conversations, hr_messages
│   │   ├── interview.py     # interviews, interview_questions
│   │   ├── crawler.py       # job_sources, crawl_tasks, crawl_logs
│   │   ├── knowledge.py     # knowledge_documents, knowledge_chunks
│   │   └── platform.py      # platform_accounts
│   │
│   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── resume.py
│   │   ├── career.py
│   │   ├── job.py
│   │   ├── chat.py
│   │   ├── agent.py
│   │   ├── hr.py
│   │   ├── interview.py
│   │   ├── crawler.py
│   │   ├── knowledge.py
│   │   └── platform.py
│   │
│   ├── api/                 # 路由（Router）
│   │   ├── auth.py          # 认证模块
│   │   ├── user.py          # 用户资料
│   │   ├── resume.py        # 简历管理
│   │   ├── career.py        # 职业规划
│   │   ├── job.py           # 岗位推荐
│   │   ├── chat.py          # AI 聊天助手
│   │   ├── agent.py         # Agent 任务
│   │   ├── hr.py            # HR 沟通中心
│   │   ├── interview.py     # AI 面试
│   │   ├── crawler.py       # 爬虫系统
│   │   ├── knowledge.py     # 向量知识库
│   │   └── platform.py      # 平台账号
│   │
│   ├── services/            # 业务逻辑层
│   │   ├── auth_service.py      # 认证逻辑
│   │   ├── ai_service.py        # LLM 调用（LangChain）
│   │   ├── crawler_service.py   # 爬虫调度
│   │   ├── vector_service.py    # 向量数据库操作
│   │   ├── rag_service.py       # RAG 检索增强
│   │   └── ...
│   │
│   ├── crawlers/            # 爬虫实现
│   │   ├── base.py          # 爬虫基类
│   │   ├── boss_spider.py   # Boss直聘爬虫
│   │   ├── lagou_spider.py  # 拉勾网爬虫
│   │   └── liepin_spider.py # 猎聘网爬虫
│   │
│   ├── ws/                  # WebSocket 处理
│   │   ├── hr_ws.py         # HR 消息实时推送
│   │   └── agent_ws.py      # Agent 任务状态推送
│   │
│   └── utils/               # 工具函数
│       ├── security.py      # 加密工具（bcrypt、AES）
│       ├── jwt_handler.py   # JWT 生成与验证
│       ├── email.py         # 邮件发送
│       └── file_storage.py  # 文件存储
│
├── requirements.txt
├── .env                     # 环境变量（不入 Git）
└── alembic/                 # 数据库迁移
    └── versions/
```

### 依赖库

```txt
# 核心框架
fastapi>=0.100.0
uvicorn>=0.23.0

# 数据库
sqlalchemy>=2.0.0
alembic>=1.11.0
aiomysql>=0.2.0
cryptography>=41.0.0

# 数据验证
pydantic>=2.0.0
email-validator>=2.0.0

# 认证
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# 文件上传
python-multipart>=0.0.6

# AI / LLM
langchain>=0.2.0
langchain-openai>=0.1.0
openai>=1.0.0
tiktoken>=0.5.0

# 向量数据库
pinecone-client>=2.0.0        # 或
# pymilvus>=2.3.0              # 或
# chromadb>=0.4.0

# HTTP 客户端
httpx>=0.24.0

# 爬虫
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# WebSocket
websockets>=11.0.0

# 任务队列
celery>=5.3.0
redis>=5.0.0

# 工具
python-dotenv>=1.0.0
loguru>=0.7.0
```

### 环境变量配置（.env）

```env
# 应用配置
APP_NAME=AI Career Agent
DEBUG=true
SECRET_KEY=your-secret-key-here

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=ai_career_agent

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret
JWT_REFRESH_SECRET_KEY=your-jwt-refresh-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 加密配置
AES_SECRET_KEY=your-aes-256-key

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# OpenAI / LLM 配置
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# 向量数据库配置
VECTOR_DB_TYPE=pinecone
PINECONE_API_KEY=xxx
PINECONE_INDEX_NAME=ai-career-agent

# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=xxx

# 文件存储
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760
```

### 示例路由

```python
# app/api/hr.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from app.schemas.hr import (
    ConversationResponse,
    MessageResponse,
    AiManagedUpdate,
    GenerateReplyRequest,
    SendMessageRequest,
)
from app.dependencies import get_current_user
from app.services.hr_service import HRService

router = APIRouter(prefix="/hr", tags=["HR 沟通中心"])

@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(
    filter: str = "all",
    current_user=Depends(get_current_user),
):
    """获取对话列表"""
    ...

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user=Depends(get_current_user),
):
    """获取对话消息"""
    ...

@router.put("/conversations/{conversation_id}/ai-managed")
async def toggle_ai_managed(
    conversation_id: int,
    body: AiManagedUpdate,
    current_user=Depends(get_current_user),
):
    """切换 AI 托管状态"""
    ...

@router.post("/conversations/{conversation_id}/generate-reply")
async def generate_reply(
    conversation_id: int,
    body: GenerateReplyRequest = None,
    current_user=Depends(get_current_user),
):
    """生成 AI 回复建议"""
    ...

@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    body: SendMessageRequest,
    current_user=Depends(get_current_user),
):
    """发送消息（手动回复）"""
    ...

# WebSocket
@router.websocket("/ws/hr/messages")
async def hr_messages_ws(websocket: WebSocket, token: str):
    """HR 消息实时推送 WebSocket"""
    await websocket.accept()
    # 验证 token
    # 管理连接
    # 推送实时消息
    ...
```

---

## 附录

### 状态枚举值

**User Status:**
- `active` - 正常
- `inactive` - 未激活
- `banned` - 已封禁

**Resume Status:**
- `pending` - 待分析
- `analyzing` - 分析中
- `completed` - 已完成
- `failed` - 分析失败

**Agent Task Status:**
- `pending` - 待执行
- `running` - 运行中
- `completed` - 已完成
- `paused` - 已暂停
- `failed` - 失败

**Interview Status:**
- `pending` - 待开始
- `in_progress` - 进行中
- `completed` - 已完成

**HR Message Status:**
- `sending` - 发送中
- `sent` - 已发送
- `read` - 已读
- `failed` - 发送失败

**Crawl Task Status:**
- `pending` - 待执行
- `running` - 运行中
- `completed` - 已完成
- `stopped` - 已停止
- `failed` - 失败

**Knowledge Document Status:**
- `pending` - 待处理
- `processing` - 处理中
- `processed` - 已处理
- `failed` - 处理失败

**Apply Type:**
- `manual` - 手动投递
- `auto` - AI 自动投递

---

### 数据库表关系概览

```
users (1) ──── (N) user_tokens
users (1) ──── (N) resumes
users (1) ──── (N) chat_sessions
users (1) ──── (N) agent_tasks
users (1) ──── (N) hr_conversations
users (1) ──── (N) interviews
users (1) ──── (N) career_plans
users (1) ──── (N) platform_accounts
users (1) ──── (N) knowledge_documents

resumes (1) ──── (1) resume_analyses
chat_sessions (1) ──── (N) chat_messages
hr_conversations (1) ──── (N) hr_messages
agent_tasks (1) ──── (N) agent_actions
interviews (1) ──── (N) interview_questions
jobs (1) ──── (N) job_applications
jobs (N) ──── (1) job_sources
knowledge_documents (1) ──── (N) knowledge_chunks
crawl_tasks (N) ──── (1) job_sources
crawl_tasks (1) ──── (N) crawl_logs
```

---

*文档结束*
