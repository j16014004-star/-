# AI Career Agent 后端 API 接口文档

> 版本：1.0  
> 最后更新：2026-07-13  
> 基础路径：`/api`  
> 认证方式：Bearer Token（`Authorization: Bearer <token>`）

---

## 目录

- [一、通用说明](#一通用说明)
- [二、用户认证模块](#二用户认证模块)
- [三、简历管理模块](#三简历管理模块)
- [四、职业规划模块](#四职业规划模块)
- [五、岗位推荐模块](#五岗位推荐模块)
- [六、AI聊天助手模块](#六ai聊天助手模块)
- [七、Agent任务模块](#七agent任务模块)
- [八、HR沟通模块](#八hr沟通模块)
- [九、AI面试模块](#九ai面试模块)

---

## 一、通用说明

### 1.1 认证

所有需要认证的接口，需在请求头中携带 Token：

```
Authorization: Bearer <token>
```

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
| 401 | 未认证/Token过期 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 二、用户认证模块

### 2.1 用户登录

**POST** `/auth/login`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

**请求示例：**

```json
{
  "username": "zhangsan",
  "password": "123456"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "username": "zhangsan",
      "email": "zhangsan@example.com",
      "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan"
    }
  }
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| data.token | string | JWT Token，用于后续认证 |
| data.user.id | number | 用户ID |
| data.user.username | string | 用户名 |
| data.user.email | string | 邮箱 |
| data.user.avatar | string | 头像URL |

---

### 2.2 用户注册

**POST** `/auth/register`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 是 | 用户名（2-20字符） |
| email | string | 是 | 邮箱 |
| password | string | 是 | 密码（至少6字符） |

**请求示例：**

```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "123456"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "注册成功",
  "data": null
}
```

---

### 2.3 获取用户信息

**GET** `/auth/userinfo`

**请求参数：** 无

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=zhangsan",
    "phone": "138****8888",
    "created_at": "2025-01-15T08:00:00.000Z"
  }
}
```

**响应字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| data.id | number | 用户ID |
| data.username | string | 用户名 |
| data.email | string | 邮箱 |
| data.avatar | string | 头像URL |
| data.phone | string | 手机号 |
| data.created_at | string | 注册时间（ISO 8601） |

---

### 2.4 更新用户资料

**PUT** `/auth/profile`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 用户名 |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 手机号 |
| avatar | string | 否 | 头像URL |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "avatar": "...",
    "phone": "138****8888",
    "created_at": "2025-01-15T08:00:00.000Z"
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

---

## 三、简历管理模块

### 3.1 获取简历列表

**GET** `/resumes`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认1 |
| page_size | number | 否 | 每页数量，默认10 |

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
          "suggestions": ["补充Webpack构建优化经验"],
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

**Resume 对象字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 简历ID |
| title | string | 简历标题 |
| file_type | string | 文件类型（pdf/word/text） |
| file_url | string | 文件下载URL |
| file_size | number | 文件大小（字节） |
| score | number | AI评分（0-100） |
| status | string | 状态（pending/analyzing/completed/failed） |
| analysis | object | AI分析结果 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

---

### 3.2 获取简历详情

**GET** `/resumes/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 简历ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
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
      "suggestions": ["补充Webpack构建优化经验"],
      "missing_keywords": ["Webpack", "CI/CD"],
      "format_score": 90,
      "content_score": 82,
      "relevance_score": 88
    },
    "created_at": "2026-06-28T10:30:00.000Z",
    "updated_at": "2026-07-10T14:20:00.000Z"
  }
}
```

---

### 3.3 上传简历

**POST** `/resumes/upload`

**Content-Type:** `multipart/form-data`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 简历文件（PDF/DOC/DOCX） |
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

---

### 3.4 删除简历

**DELETE** `/resumes/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 简历ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

### 3.5 AI分析简历

**POST** `/resumes/:id/analyze`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 简历ID |

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
    "missing_keywords": ["TypeScript高级类型", "前端性能监控"],
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

### 3.6 AI优化简历

**POST** `/resumes/:id/optimize`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 简历ID |

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target_position | string | 否 | 目标岗位 |
| requirements | string | 否 | 岗位要求 |

**请求示例：**

```json
{
  "target_position": "高级前端工程师",
  "requirements": "3年以上经验，精通Vue3和TypeScript"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "优化完成",
  "data": {
    "original": "负责公司前端项目的开发与维护，使用Vue.js框架进行页面开发。",
    "optimized": "主导公司核心前端项目的架构设计与开发，基于Vue3 + TypeScript技术栈实现模块化开发，通过自定义Hook封装复用逻辑使代码复用率提升40%。",
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

**ResumeOptimizeResult 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| original | string | 原始简历内容 |
| optimized | string | 优化后简历内容 |
| changes | array | 修改详情列表 |
| changes[].section | string | 修改所属章节 |
| changes[].original | string | 修改前内容 |
| changes[].optimized | string | 修改后内容 |
| changes[].reason | string | 修改原因 |

---

## 四、职业规划模块

### 4.1 生成职业规划

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
      "description": "使用Vue3开发的管理后台",
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
      "全栈开发工程师（Node.js方向）",
      "前端架构师"
    ],
    "learning_path": [
      {
        "stage": "基础巩固阶段（1-2个月）",
        "skills": ["TypeScript深入（泛型、装饰器、条件类型）", "设计模式在前端的应用"],
        "duration": "1-2个月",
        "resources": ["TypeScript官方文档", "《JavaScript设计模式》"]
      }
    ],
    "skill_suggestions": [
      "深入学习TypeScript高级类型系统",
      "掌握一种后端语言（Node.js/Python/Go）"
    ],
    "career_direction": "根据您的Vue.js、TypeScript、Node.js技能背景和当前市场趋势，推荐发展方向为...",
    "market_analysis": "2026年前端开发市场呈现以下趋势：1）AI辅助编程普及..."
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

## 五、岗位推荐模块

### 5.1 获取推荐岗位

**GET** `/jobs/recommendations`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认1 |
| page_size | number | 否 | 每页数量，默认10 |
| keywords | string | 否 | 搜索关键词 |
| city | string | 否 | 城市筛选 |
| salary_min | number | 否 | 最低薪资（元） |
| salary_max | number | 否 | 最高薪资（元） |

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
        "match_reasons": ["技能匹配度92%", "Vue3经验高度契合"],
        "source": "BOSS直聘",
        "url": "https://www.zhipin.com/job/1",
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
| id | number | 岗位ID |
| company | string | 公司名称 |
| company_logo | string | 公司Logo URL |
| title | string | 岗位名称 |
| salary_min | number | 最低薪资（元） |
| salary_max | number | 最高薪资（元） |
| city | string | 城市 |
| experience_required | string | 经验要求 |
| education_required | string | 学历要求 |
| skills | string[] | 技能要求 |
| description | string | 岗位描述 |
| match_score | number | AI匹配度（0-100） |
| match_reasons | string[] | 匹配原因 |
| source | string | 来源平台 |
| url | string | 原始链接 |
| created_at | string | 发布时间 |

---

### 5.2 获取岗位详情

**GET** `/jobs/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 岗位ID |

**响应示例：** 同5.1中的单个Job对象。

---

## 六、AI聊天助手模块

### 6.1 获取会话列表

**GET** `/chat/sessions`

**请求参数：** 无

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

### 6.2 获取会话消息

**GET** `/chat/sessions/:id/messages`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 会话ID |

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

### 6.3 发送消息

**POST** `/chat/send`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | number | 否 | 会话ID，不传则创建新会话 |
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
    "content": "好的，我将根据STAR原则为您优化...",
    "created_at": "2026-07-13T14:30:05.000Z"
  }
}
```

---

### 6.4 删除会话

**DELETE** `/chat/sessions/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 会话ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

## 七、Agent任务模块

### 7.1 获取任务列表

**GET** `/agent/tasks`

**请求参数：** 无

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
| id | number | 任务ID |
| type | string | 任务类型（search/filter/apply/track） |
| status | string | 任务状态（pending/running/completed/failed/paused） |
| progress | number | 进度（0-100） |
| config | object | 任务配置 |
| logs | array | 执行日志 |
| applications | array | 投递记录 |

---

### 7.2 获取任务详情

**GET** `/agent/tasks/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 任务ID |

**响应示例：** 同7.1中的单个AgentTask对象。

---

### 7.3 创建任务

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
    "config": {...},
    "logs": [],
    "applications": [],
    "created_at": "2026-07-13T10:00:00.000Z",
    "updated_at": "2026-07-13T10:00:00.000Z"
  }
}
```

---

### 7.4 启动任务

**POST** `/agent/tasks/:id/start`

**响应示例：** 返回更新后的AgentTask对象，status变为"running"。

---

### 7.5 暂停任务

**POST** `/agent/tasks/:id/pause`

**响应示例：** 返回更新后的AgentTask对象，status变为"paused"。

---

### 7.6 停止任务

**POST** `/agent/tasks/:id/stop`

**响应示例：** 返回更新后的AgentTask对象，status变为"failed"。

---

### 7.7 删除任务

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

## 八、HR沟通模块

### 8.1 获取HR消息列表

**GET** `/hr/messages`

**请求参数：** 无

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "company": "字节跳动",
      "hr_name": "张女士",
      "content": "您好，我们在BOSS直聘上看到了您的简历...",
      "reply_suggestion": "您好张女士，感谢您的邀请！",
      "status": "pending",
      "created_at": "2026-07-13T09:00:00.000Z"
    }
  ]
}
```

**HRMessage 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 消息ID |
| company | string | 公司名称 |
| hr_name | string | HR姓名 |
| content | string | 消息内容 |
| reply_suggestion | string | AI建议的回复 |
| status | string | 状态（pending/replied/archived） |
| created_at | string | 发送时间 |

---

### 8.2 获取回复建议

**GET** `/hr/messages/:id/suggestions`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 消息ID |

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "suggestions": [
      "您好，感谢您的邀请！我对这个岗位非常感兴趣。",
      "感谢联系！我很感兴趣。是否能先了解一下团队的技术栈？"
    ]
  }
}
```

---

### 8.3 回复HR消息

**POST** `/hr/reply`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message_id | number | 是 | 消息ID |
| content | string | 是 | 回复内容 |

**请求示例：**

```json
{
  "message_id": 1,
  "content": "您好，感谢您的邀请！我对这个岗位非常感兴趣。"
}
```

**响应示例：**

```json
{
  "code": 200,
  "message": "回复成功",
  "data": null
}
```

---

### 8.4 归档消息

**POST** `/hr/messages/:id/archive`

**响应示例：**

```json
{
  "code": 200,
  "message": "归档成功",
  "data": null
}
```

---

## 九、AI面试模块

### 9.1 获取面试列表

**GET** `/interviews`

**请求参数：** 无

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
      "questions": [...],
      "score": 85,
      "report": {...},
      "created_at": "2026-07-12T10:00:00.000Z"
    }
  ]
}
```

---

### 9.2 获取面试详情

**GET** `/interviews/:id`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 面试ID |

**响应示例：** 返回完整的Interview对象。

**Interview 字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 面试ID |
| title | string | 面试标题 |
| status | string | 状态（pending/in_progress/completed） |
| position | string | 目标岗位 |
| company | string | 目标公司 |
| questions | array | 面试题目列表 |
| score | number | 综合评分 |
| report | object | 面试报告 |
| created_at | string | 创建时间 |

---

### 9.3 创建面试

**POST** `/interviews`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| position | string | 是 | 目标岗位 |
| company | string | 否 | 目标公司 |
| question_types | string[] | 否 | 题目类型（technical/behavioral/project/general） |
| question_count | number | 否 | 题目数量（3-10） |

**请求示例：**

```json
{
  "position": "前端开发工程师",
  "company": "字节跳动",
  "question_types": ["technical", "behavioral"],
  "question_count": 5
}
```

**响应示例：** 返回创建的Interview对象。

---

### 9.4 开始面试

**POST** `/interviews/:id/start`

**响应示例：** 返回更新后的Interview对象，status变为"in_progress"。

---

### 9.5 获取下一题

**GET** `/interviews/:id/next-question`

**响应示例：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "type": "technical",
    "question": "什么是虚拟DOM？Vue3中是如何优化虚拟DOM性能的？",
    "tips": "可以手写一个简单的Diff算法来展示理解深度。"
  }
}
```

---

### 9.6 提交答案

**POST** `/interviews/:id/answer`

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question_id | number | 是 | 题目ID |
| answer | string | 是 | 用户答案 |
| duration | number | 是 | 答题时长（秒） |

**请求示例：**

```json
{
  "question_id": 1,
  "answer": "Vue3使用Proxy替代了Vue2的Object.defineProperty...",
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
    "question": "请解释Vue3的响应式原理",
    "answer": "Vue3使用Proxy...",
    "score": 85,
    "feedback": "回答完整，涵盖了Proxy对比defineProperty的核心优势。",
    "tips": "面试时可以从Vue2的局限性切入。",
    "duration": 180
  }
}
```

---

### 9.7 结束面试

**POST** `/interviews/:id/finish`

**响应示例：** 返回完整的Interview对象，包含report。

---

### 9.8 获取面试报告

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
    "questions": [...],
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

### 9.9 删除面试

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

## FastAPI 实现参考

### 项目结构建议

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy 模型
│   │   ├── user.py
│   │   ├── resume.py
│   │   ├── job.py
│   │   ├── chat.py
│   │   ├── agent.py
│   │   ├── hr.py
│   │   └── interview.py
│   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── user.py
│   │   ├── resume.py
│   │   ├── ...
│   ├── api/                 # 路由
│   │   ├── auth.py
│   │   ├── resume.py
│   │   ├── career.py
│   │   ├── job.py
│   │   ├── chat.py
│   │   ├── agent.py
│   │   ├── hr.py
│   │   └── interview.py
│   ├── services/            # 业务逻辑
│   │   ├── auth_service.py
│   │   ├── ai_service.py    # LLM 调用
│   │   └── ...
│   └── utils/               # 工具函数
├── requirements.txt
└── .env
```

### 依赖库

```txt
fastapi>=0.100.0
uvicorn>=0.23.0
sqlalchemy>=2.0.0
alembic>=1.11.0
pydantic>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
httpx>=0.24.0
openai>=1.0.0
langchain>=0.0.300
```

### 示例路由

```python
# app/api/resume.py
from fastapi import APIRouter, Depends, UploadFile, File
from app.schemas.resume import ResumeResponse, ResumeAnalysisResponse

router = APIRouter(prefix="/resumes", tags=["简历管理"])

@router.get("/", response_model=PaginatedResponse[ResumeResponse])
async def get_resumes(
    page: int = 1,
    page_size: int = 10,
    current_user = Depends(get_current_user)
):
    """获取简历列表"""
    ...

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    title: str = None,
    current_user = Depends(get_current_user)
):
    """上传简历"""
    ...

@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    resume_id: int,
    current_user = Depends(get_current_user)
):
    """AI分析简历"""
    ...
```

---

## 附录

### 状态枚举值

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

**HR Message Status:**
- `pending` - 待回复
- `replied` - 已回复
- `archived` - 已归档

**Interview Status:**
- `pending` - 待开始
- `in_progress` - 进行中
- `completed` - 已完成

---

*文档结束*
