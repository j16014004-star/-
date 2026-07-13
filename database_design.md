# AI Career Agent 数据库设计文档

## 一、业务分析

### 核心业务流程
用户注册/登录 → 上传简历 → AI分析优化 → 职业规划 → **爬虫抓取岗位** → **AI自动投递** → **AI自动沟通** → AI面试 → 向量知识库

### 系统架构
- **后端技术栈**: FastAPI + LangChain + JWT + Agent智能 + 爬虫技术
- **AI能力**: 自动投递简历、自动寻找岗位、自动与HR沟通
- **向量数据库**: 存储面试答案、职业规划、专业知识（用于RAG检索）
- **爬虫系统**: 从Boss直聘等招聘网站抓取岗位数据
- **Agent系统**: AI托管与HR沟通、自动投递

### 核心实体
1. **用户** - 求职者基本信息、认证信息、偏好设置
2. **简历** - 用户上传的简历文件及AI分析结果
3. **岗位** - **从招聘网站爬取的职位信息**
4. **爬虫系统** - 招聘源配置、爬虫任务、抓取日志
5. **申请** - 投递记录（手动/AI自动投递）
6. **AI Agent** - 智能体任务、自动沟通、自动投递
7. **面试** - AI模拟面试会话、问题、回答、报告
8. **聊天** - 用户与AI助手的对话会话和消息
9. **职业规划** - AI生成的职业发展建议
10. **知识库** - **向量数据库存储的专业知识（面试答案、职业规划等）**
11. **HR消息** - **AI与HR的沟通记录（自动托管）**

---

## 二、ER关系图

```
Users (1) ──< (N) Resumes
Users (1) ──< (N) Applications
Users (1) ──< (N) Interviews
Users (1) ──< (N) ChatSessions
Users (1) ──< (N) CareerPlans
Users (1) ──< (N) AgentTasks
Users (1) ──< (N) HRConversations
Users (1) ──< (N) PlatformAccounts (招聘平台账号)

Resumes (1) ──< (1) ResumeAnalyses
Interviews (1) ──< (N) InterviewQuestions
Interviews (1) ──< (0..1) InterviewReports
ChatSessions (1) ──< (N) ChatMessages
AgentTasks (1) ──< (N) AgentLogs
AgentTasks (1) ──< (N) AgentActions (自动投递/沟通动作)
Jobs (1) ──< (N) Applications
JobSources (1) ──< (N) CrawlTasks (爬虫源 → 爬虫任务)
CrawlTasks (1) ──< (N) CrawlLogs
KnowledgeDocuments (1) ──< (N) KnowledgeChunks (文档 → 分块)
HRConversations (1) ──< (N) HRMessages (会话 → 消息)
```

### 关键关系说明
- **Jobs** 数据来自爬虫系统，通过 `job_source_id` 关联来源
- **Applications** 区分手动投递和AI自动投递
- **AgentTasks** 控制AI自动投递和沟通行为
- **KnowledgeDocuments/Chunks** 用于RAG向量检索
- **HRConversations** 是AI与HR在招聘平台的对话记录

---

## 三、表设计清单

### 1. users - 用户表
**用途**: 存储用户基本信息、认证数据和自动化偏好

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| username | VARCHAR(50) | NO | - | 用户名，唯一 |
| email | VARCHAR(100) | NO | - | 邮箱，唯一 |
| password_hash | VARCHAR(255) | NO | - | 加密后的密码 |
| phone | VARCHAR(20) | YES | NULL | 手机号 |
| avatar | VARCHAR(500) | YES | NULL | 头像URL |
| role | VARCHAR(20) | NO | 'job_seeker' | 角色：job_seeker/hr/admin |
| status | VARCHAR(20) | NO | 'active' | 状态：active/inactive/banned |
| **auto_apply_enabled** | BOOLEAN | NO | FALSE | 是否启用AI自动投递 |
| **auto_communicate_enabled** | BOOLEAN | NO | FALSE | 是否启用AI自动沟通 |
| **preferred_salary_min** | INT | YES | NULL | 期望最低薪资 |
| **preferred_salary_max** | INT | YES | NULL | 期望最高薪资 |
| **preferred_cities** | JSON | YES | NULL | 期望城市列表 |
| **preferred_skills** | JSON | YES | NULL | 技能偏好 |
| last_login_at | TIMESTAMP | YES | NULL | 最后登录时间 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | YES | NULL | 软删除时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (username)
- UNIQUE (email)
- INDEX (status, created_at)

---

### 2. resumes - 简历表
**用途**: 存储用户上传的简历文件信息

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| title | VARCHAR(200) | NO | - | 简历标题 |
| file_type | VARCHAR(10) | NO | - | 文件类型：pdf/word/text |
| file_url | VARCHAR(500) | YES | NULL | 文件存储URL |
| file_size | INT | YES | NULL | 文件大小（字节） |
| status | VARCHAR(20) | NO | 'pending' | 状态：pending/analyzing/completed/failed |
| overall_score | INT | YES | NULL | AI综合评分（0-100） |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | YES | NULL | 软删除时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, status)
- INDEX (created_at)

---

### 3. resume_analyses - 简历分析结果表
**用途**: 存储AI对简历的详细分析结果

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| resume_id | BIGINT | NO | - | 外键：resumes.id |
| score | INT | NO | - | 综合评分 |
| format_score | INT | NO | - | 格式评分 |
| content_score | INT | NO | - | 内容评分 |
| relevance_score | INT | NO | - | 相关性评分 |
| strengths | JSON | NO | - | 优势列表 |
| weaknesses | JSON | NO | - | 劣势列表 |
| suggestions | JSON | NO | - | 改进建议 |
| missing_keywords | JSON | NO | - | 缺失关键词 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (resume_id)

---

### 4. resume_optimizations - 简历优化记录表
**用途**: 存储AI对简历的优化建议

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| resume_id | BIGINT | NO | - | 外键：resumes.id |
| original_text | TEXT | NO | - | 原文 |
| optimized_text | TEXT | NO | - | 优化后文本 |
| changes | JSON | NO | - | 修改详情（数组） |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (resume_id)

---

### 5. jobs - 岗位表
**用途**: 存储从招聘网站爬取的职位信息

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| **job_source_id** | BIGINT | NO | - | 外键：job_sources.id（来源网站） |
| **external_id** | VARCHAR(100) | YES | NULL | 招聘网站的原始职位ID |
| **source_url** | VARCHAR(500) | NO | - | 职位原始链接 |
| company | VARCHAR(100) | NO | - | 公司名称 |
| company_logo | VARCHAR(500) | YES | NULL | 公司Logo URL |
| title | VARCHAR(200) | NO | - | 职位标题 |
| salary_min | INT | NO | - | 最低薪资（元/月） |
| salary_max | INT | NO | - | 最高薪资（元/月） |
| city | VARCHAR(50) | NO | - | 工作城市 |
| experience_required | VARCHAR(50) | NO | - | 经验要求 |
| education_required | VARCHAR(50) | NO | - | 学历要求 |
| skills | JSON | NO | - | 技能要求（数组） |
| description | TEXT | NO | - | 职位描述 |
| **company_size** | VARCHAR(50) | YES | NULL | 公司规模 |
| **company_industry** | VARCHAR(100) | YES | NULL | 公司行业 |
| **benefits** | JSON | YES | NULL | 福利待遇 |
| source | VARCHAR(50) | NO | - | 来源：boss/zhipin/liepin/lagou |
| **crawl_time** | TIMESTAMP | NO | CURRENT_TIMESTAMP | 爬取时间 |
| **is_active** | BOOLEAN | NO | TRUE | 职位是否仍然有效 |
| status | VARCHAR(20) | NO | 'active' | 状态：active/closed/expired |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (job_source_id, status)
- INDEX (city, status)
- INDEX (salary_min, salary_max)
- INDEX (crawl_time)
- INDEX (is_active)
- FULLTEXT (title, description)
- UNIQUE (external_id, source) - 防止重复爬取同一职位

---

### 6. applications - 申请记录表
**用途**: 存储用户申请职位的记录（手动/AI自动投递）

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| job_id | BIGINT | NO | - | 外键：jobs.id |
| resume_id | BIGINT | YES | NULL | 外键：resumes.id（使用的简历） |
| **apply_type** | VARCHAR(20) | NO | 'manual' | 投递方式：manual/auto |
| **agent_task_id** | BIGINT | YES | NULL | 外键：agent_tasks.id（AI投递时关联） |
| status | VARCHAR(20) | NO | 'submitted' | 状态：submitted/viewed/interviewing/rejected/accepted |
| **ai_message** | TEXT | YES | NULL | AI自动发送的求职信/消息 |
| **platform_response** | TEXT | YES | NULL | 平台/HR的回复 |
| applied_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 申请时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (user_id, job_id, apply_type)
- INDEX (user_id, status)
- INDEX (job_id)
- INDEX (apply_type, created_at)
- INDEX (agent_task_id)

---

### 7. job_matches - 岗位匹配记录表
**用途**: 存储AI计算的用户与岗位匹配度

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| job_id | BIGINT | NO | - | 外键：jobs.id |
| match_score | INT | NO | - | 匹配分数（0-100） |
| match_reasons | JSON | NO | - | 匹配原因（数组） |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (user_id, job_id)
- INDEX (user_id, match_score DESC)

---

### 8. job_sources - 招聘源配置表
**用途**: 配置招聘网站的爬虫源信息

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| name | VARCHAR(50) | NO | - | 来源名称：Boss直聘/猎聘/拉勾 |
| domain | VARCHAR(100) | NO | - | 域名：zhipin.com/liepin.com |
| base_url | VARCHAR(200) | NO | - | 基础URL |
| **crawl_config** | JSON | NO | - | 爬虫配置（选择器、规则等） |
| **is_enabled** | BOOLEAN | NO | TRUE | 是否启用 |
| **last_crawl_at** | TIMESTAMP | YES | NULL | 最后爬取时间 |
| **crawl_interval** | INT | NO | 3600 | 爬取间隔（秒） |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (domain)
- INDEX (is_enabled)

---

### 9. crawl_tasks - 爬虫任务表
**用途**: 记录爬虫任务的执行状态

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| job_source_id | BIGINT | NO | - | 外键：job_sources.id |
| **task_type** | VARCHAR(20) | NO | - | 类型：full/incremental |
| status | VARCHAR(20) | NO | 'pending' | 状态：pending/running/completed/failed |
| **total_count** | INT | YES | 0 | 计划抓取数量 |
| **success_count** | INT | YES | 0 | 成功数量 |
| **failed_count** | INT | YES | 0 | 失败数量 |
| **error_message** | TEXT | YES | NULL | 错误信息 |
| started_at | TIMESTAMP | YES | NULL | 开始时间 |
| completed_at | TIMESTAMP | YES | NULL | 完成时间 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (job_source_id, status)
- INDEX (created_at)

---

### 10. interviews - 面试表
**用途**: 存储AI模拟面试会话

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| title | VARCHAR(200) | NO | - | 面试标题 |
| position | VARCHAR(100) | NO | - | 应聘职位 |
| company | VARCHAR(100) | YES | NULL | 公司名称 |
| status | VARCHAR(20) | NO | 'pending' | 状态：pending/in_progress/completed |
| overall_score | INT | YES | NULL | 综合评分 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | YES | NULL | 软删除时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, status)
- INDEX (created_at)

---

### 11. interview_questions - 面试问题表
**用途**: 存储面试中的问题和回答

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| interview_id | BIGINT | NO | - | 外键：interviews.id |
| type | VARCHAR(20) | NO | - | 类型：technical/behavioral/project/general |
| question | TEXT | NO | - | 问题内容 |
| answer | TEXT | YES | NULL | 用户回答 |
| score | INT | YES | NULL | 评分 |
| feedback | TEXT | YES | NULL | AI反馈 |
| tips | TEXT | YES | NULL | 回答提示 |
| duration | INT | YES | NULL | 答题时长（秒） |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (interview_id)

---

### 12. interview_reports - 面试报告表
**用途**: 存储AI生成的面试评估报告

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| interview_id | BIGINT | NO | - | 外键：interviews.id |
| overall_score | INT | NO | - | 综合评分 |
| dimension_scores | JSON | NO | - | 维度评分（technical/behavioral/communication/logic） |
| strengths | JSON | NO | - | 优势列表 |
| weaknesses | JSON | NO | - | 劣势列表 |
| suggestions | JSON | NO | - | 改进建议 |
| summary | TEXT | NO | - | 总结 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (interview_id)

---

### 13. chat_sessions - 聊天会话表
**用途**: 存储用户与AI助手的对话会话

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| title | VARCHAR(200) | NO | - | 会话标题 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | YES | NULL | 软删除时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, updated_at DESC)

---

### 14. chat_messages - 聊天消息表
**用途**: 存储对话中的具体消息

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| session_id | BIGINT | NO | - | 外键：chat_sessions.id |
| role | VARCHAR(20) | NO | - | 角色：user/assistant/system |
| content | TEXT | NO | - | 消息内容 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (session_id, created_at)

---

### 15. career_plans - 职业规划表
**用途**: 存储AI生成的职业规划建议

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| recommended_positions | JSON | NO | - | 推荐职位列表 |
| learning_path | JSON | NO | - | 学习路径（数组） |
| skill_suggestions | JSON | NO | - | 技能建议列表 |
| career_direction | TEXT | NO | - | 职业方向说明 |
| market_analysis | TEXT | NO | - | 市场分析 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, created_at DESC)

---

### 16. agent_tasks - Agent任务表
**用途**: 存储AI自动化求职任务（自动投递、自动沟通）

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| **task_type** | VARCHAR(30) | NO | - | 类型：auto_apply/auto_communicate/job_search/resume_analyze |
| status | VARCHAR(20) | NO | 'pending' | 状态：pending/running/completed/failed/paused |
| progress | INT | NO | 0 | 进度（0-100） |
| **config** | JSON | NO | - | 任务配置（目标岗位、筛选条件等） |
| **result** | JSON | YES | NULL | 执行结果（投递数量、沟通结果等） |
| **error_message** | TEXT | YES | NULL | 错误信息 |
| started_at | TIMESTAMP | YES | NULL | 开始时间 |
| completed_at | TIMESTAMP | YES | NULL | 完成时间 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, task_type, status)
- INDEX (created_at)

---

### 17. agent_logs - Agent任务日志表
**用途**: 存储任务执行的详细日志

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| task_id | BIGINT | NO | - | 外键：agent_tasks.id |
| level | VARCHAR(10) | NO | 'info' | 级别：info/warn/error |
| message | TEXT | NO | - | 日志内容 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (task_id, created_at)

---

### 16. hr_messages - HR消息表
**用途**: 存储与HR的沟通记录

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| company | VARCHAR(100) | NO | - | 公司名称 |
| hr_name | VARCHAR(50) | NO | - | HR姓名 |
| content | TEXT | NO | - | 消息内容 |
| reply_suggestion | TEXT | YES | NULL | AI回复建议 |
| status | VARCHAR(20) | NO | 'pending' | 状态：pending/replied/archived |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, status)
- INDEX (created_at)

---

### 18. platform_accounts - 招聘平台账号表
**用途**: 存储用户在招聘平台的账号信息（用于AI自动登录和操作）

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| job_source_id | BIGINT | NO | - | 外键：job_sources.id |
| **platform_username** | VARCHAR(100) | NO | - | 平台用户名/手机号 |
| **platform_password** | VARCHAR(255) | NO | - | 加密后的密码 |
| **cookies** | TEXT | YES | NULL | 登录后的cookies（JSON） |
| **last_login_at** | TIMESTAMP | YES | NULL | 最后登录时间 |
| **is_active** | BOOLEAN | NO | TRUE | 账号是否可用 |
| **login_failed_count** | INT | NO | 0 | 登录失败次数 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (user_id, job_source_id)
- INDEX (is_active)

**安全说明**:
- 密码使用 AES-256 加密存储
- cookies 定期刷新
- 登录失败超过5次自动禁用

---

### 19. hr_conversations - HR对话会话表
**用途**: 存储AI与HR在招聘平台的对话会话

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| **job_id** | BIGINT | YES | NULL | 外键：jobs.id（关联的职位） |
| **platform_name** | VARCHAR(50) | NO | - | 平台名称：boss/liepin/lagou |
| **hr_name** | VARCHAR(50) | YES | NULL | HR姓名 |
| **hr_title** | VARCHAR(100) | YES | NULL | HR职位 |
| **company_name** | VARCHAR(100) | NO | - | 公司名称 |
| **conversation_status** | VARCHAR(20) | NO | 'active' | 状态：active/closed/archived |
| **ai_managed** | BOOLEAN | NO | TRUE | 是否AI托管 |
| **last_message_at** | TIMESTAMP | YES | NULL | 最后消息时间 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, conversation_status)
- INDEX (job_id)
- INDEX (last_message_at DESC)

---

### 20. hr_messages - HR消息表
**用途**: 存储AI与HR对话的具体消息

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| conversation_id | BIGINT | NO | - | 外键：hr_conversations.id |
| **sender_type** | VARCHAR(20) | NO | - | 发送者：hr/ai/user |
| content | TEXT | NO | - | 消息内容 |
| **ai_suggestion** | TEXT | YES | NULL | AI建议的回复（用户手动模式时） |
| **sent_at** | TIMESTAMP | NO | CURRENT_TIMESTAMP | 发送时间 |
| **read_at** | TIMESTAMP | YES | NULL | 阅读时间 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (conversation_id, sent_at)
- INDEX (sender_type)

---

### 21. knowledge_documents - 知识库文档表
**用途**: 存储知识库文档（面试答案、职业规划、专业知识）

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| **title** | VARCHAR(200) | NO | - | 文档标题 |
| **doc_type** | VARCHAR(30) | NO | - | 类型：interview_answer/career_plan/professional_knowledge/company_info |
| **content** | TEXT | NO | - | 文档内容 |
| **source** | VARCHAR(100) | YES | NULL | 来源：manual/import/crawled |
| **tags** | JSON | YES | NULL | 标签（数组） |
| **is_active** | BOOLEAN | NO | TRUE | 是否启用 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | YES | NULL | 软删除时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (doc_type, is_active)
- INDEX (created_at)
- FULLTEXT (title, content)

---

### 22. knowledge_chunks - 知识库分块表
**用途**: 存储文档分块，用于向量检索（RAG）

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| document_id | BIGINT | NO | - | 外键：knowledge_documents.id |
| **chunk_index** | INT | NO | - | 分块序号 |
| **chunk_text** | TEXT | NO | - | 分块文本内容 |
| **embedding_id** | VARCHAR(100) | YES | NULL | 向量数据库中的ID（如Pinecone/Milvus） |
| **metadata** | JSON | YES | NULL | 元数据（关键词、分类等） |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (document_id, chunk_index)
- INDEX (embedding_id)

**向量数据库说明**:
- 使用外部向量数据库（Pinecone/Milvus/Chroma）存储 embeddings
- embedding_id 关联向量数据库中的记录
- 查询时先检索向量数据库，再通过 embedding_id 获取完整分块

---

### 23. crawl_logs - 爬虫日志表
**用途**: 记录爬虫任务的详细日志

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| crawl_task_id | BIGINT | NO | - | 外键：crawl_tasks.id |
| **log_level** | VARCHAR(10) | NO | 'info' | 级别：info/warn/error |
| **message** | TEXT | NO | - | 日志内容 |
| **url** | VARCHAR(500) | YES | NULL | 爬取的URL |
| **status_code** | INT | YES | NULL | HTTP状态码 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (crawl_task_id, log_level)
- INDEX (created_at)

---

### 24. agent_actions - Agent动作记录表
**用途**: 记录AI Agent执行的具体动作（投递、沟通等）

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| agent_task_id | BIGINT | NO | - | 外键：agent_tasks.id |
| **action_type** | VARCHAR(30) | NO | - | 动作类型：apply_job/send_message/parse_response/extract_info |
| **target_type** | VARCHAR(30) | YES | NULL | 目标类型：job/conversation/resume |
| **target_id** | BIGINT | YES | NULL | 目标ID |
| **status** | VARCHAR(20) | NO | 'pending' | 状态：pending/running/success/failed |
| **input_data** | JSON | YES | NULL | 输入数据 |
| **output_data** | JSON | YES | NULL | 输出数据 |
| **error_message** | TEXT | YES | NULL | 错误信息 |
| executed_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 执行时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (agent_task_id, action_type)
- INDEX (target_type, target_id)
- INDEX (status)

---

### 25. user_activities - 用户活动日志表
**用途**: 记录用户操作，用于Dashboard展示

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| type | VARCHAR(50) | NO | - | 类型：resume_upload/interview_complete/job_apply等 |
| content | VARCHAR(500) | NO | - | 活动描述 |
| metadata | JSON | YES | NULL | 附加数据 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, created_at DESC)

---

## 四、安全设计

### 1. 密码安全
- 用户密码：bcrypt 加密，cost factor = 12
- 平台账号密码：AES-256 加密存储，定期刷新

### 2. 敏感数据
- 手机号：`phone` 字段，展示时脱敏（138****8888）
- 头像URL：存储在OSS，定期清理过期文件
- 招聘平台cookies：加密存储，设置过期时间

### 3. 平台账号安全
- `platform_accounts` 表存储加密后的平台密码
- 登录失败超过5次自动禁用账号
- cookies 定期刷新，避免失效
- 支持验证码识别（预留字段）

### 4. 软删除
- 所有核心表支持软删除（`deleted_at` 字段）
- 查询时过滤：`WHERE deleted_at IS NULL`

### 5. 审计日志
- `user_activities` 表记录关键操作
- `agent_actions` 表记录AI自动化动作
- `crawl_logs` 表记录爬虫执行日志
- 不可删除，仅用于审计和调试

### 6. 数据备份
- 每日全量备份
- 实时binlog增量备份
- 向量数据库定期备份

### 7. API安全
- JWT token 认证
- 接口限流（防止爬虫滥用）
- 敏感操作二次验证（如启用自动投递）

---

## 五、向量数据库架构

### 1. 向量数据库选型
**推荐方案**: Pinecone / Milvus / Chroma

**存储内容**:
- 面试答案 embeddings
- 职业规划文档 embeddings
- 专业知识 embeddings
- 公司信息 embeddings

### 2. 数据流
```
KnowledgeDocuments → 分块处理 → Embedding生成 → 向量数据库存储
                                      ↓
                              embedding_id 关联
                                      ↓
                           KnowledgeChunks (MySQL)
```

### 3. RAG检索流程
```
用户提问 → 问题向量化 → 向量数据库检索 → 返回相似分块
                                           ↓
                            通过 embedding_id 获取完整内容
                                           ↓
                              组合上下文 → LLM生成回答
```

### 4. 分块策略
- 文档按段落/章节分块
- 每个分块 500-1000 tokens
- 保留上下文重叠（100-200 tokens）
- 存储元数据（标题、类型、标签）

### 5. 性能优化
- 批量生成 embeddings
- 异步写入向量数据库
- 缓存热点查询结果
- 定期清理过期/低质量分块

---

## 六、性能优化

### 1. 索引策略
- 所有外键建立索引
- 高频查询字段建立复合索引
- JSON字段不建索引，查询时在应用层过滤

### 2. 分区表（未来扩展）
- `chat_messages`：按月分区
- `user_activities`：按月分区

### 3. 缓存策略
- 用户信息：Redis缓存，TTL 1小时
- 岗位列表：Redis缓存，TTL 10分钟
- 匹配分数：Redis缓存，TTL 5分钟
- 向量检索结果：Redis缓存，TTL 15分钟
- 平台cookies：Redis缓存，实时刷新

---

## 七、设计说明

### 表统计
- **总计**: 25 张表
- **核心业务表**: 17 张（用户、简历、岗位、面试、聊天等）
- **爬虫系统表**: 4 张（job_sources, crawl_tasks, crawl_logs, platform_accounts）
- **AI Agent表**: 2 张（agent_tasks增强, agent_actions）
- **知识库表**: 2 张（knowledge_documents, knowledge_chunks）
- **HR沟通表**: 2 张（hr_conversations, hr_messages增强）

### 反范式说明
1. **job_matches 表**：冗余存储 `match_score`，避免每次查询都计算
2. **resumes.overall_score**：冗余存储分析分数，提升列表查询性能
3. **interviews.overall_score**：冗余存储面试分数，避免JOIN查询
4. **jobs 表**：冗余存储爬虫相关字段，减少关联查询

### 扩展性考虑
1. **JSON字段**：`skills`, `strengths`, `config` 等使用JSON，便于结构变化
2. **预留字段**：`metadata`, `result` 字段用于存储未来扩展数据
3. **模块化设计**：表之间松耦合，便于独立扩展
4. **向量数据库分离**：embeddings 存储在外部向量数据库，MySQL只存储关联ID

### 新增功能支持
1. **爬虫系统**: job_sources + crawl_tasks + crawl_logs
2. **AI自动投递**: agent_tasks + agent_actions + platform_accounts
3. **AI自动沟通**: hr_conversations + hr_messages + agent_actions
4. **向量知识库**: knowledge_documents + knowledge_chunks + 外部向量数据库
5. **平台账号管理**: platform_accounts（加密存储，自动登录）

---

## 八、调用数据库Agent

在需要时使用以下命令调用数据库架构师agent：

```
请使用数据库架构师agent帮我：
1. 生成完整的SQL建表语句
2. 优化某个表的索引设计
3. 分析查询性能瓶颈
4. 设计数据迁移方案
```

agent位置：`.claude/agents/database-architect.md`
