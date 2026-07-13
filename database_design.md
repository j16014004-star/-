# AI Career Agent 数据库设计文档

## 一、业务分析

### 核心业务流程
用户注册/登录 → 上传简历 → AI分析优化 → 职业规划 → 岗位推荐 → 申请职位 → AI面试 → HR沟通

### 核心实体
1. **用户** - 求职者基本信息、认证信息
2. **简历** - 用户上传的简历文件及AI分析结果
3. **岗位** - 推荐的职位信息
4. **申请** - 用户申请的岗位记录
5. **面试** - AI模拟面试会话、问题、回答、报告
6. **聊天** - 用户与AI助手的对话会话和消息
7. **职业规划** - AI生成的职业发展建议
8. **Agent任务** - 自动化求职任务及执行日志
9. **HR消息** - 与HR的沟通记录

---

## 二、ER关系图

```
Users (1) ──< (N) Resumes
Users (1) ──< (N) Applications
Users (1) ──< (N) Interviews
Users (1) ──< (N) ChatSessions
Users (1) ──< (N) CareerPlans
Users (1) ──< (N) AgentTasks
Users (1) ──< (N) HRMessages

Resumes (1) ──< (1) ResumeAnalyses
Interviews (1) ──< (N) InterviewQuestions
Interviews (1) ──< (0..1) InterviewReports
ChatSessions (1) ──< (N) ChatMessages
AgentTasks (1) ──< (N) AgentLogs
Jobs (1) ──< (N) Applications
```

---

## 三、表设计清单

### 1. users - 用户表
**用途**: 存储用户基本信息和认证数据

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
**用途**: 存储推荐的职位信息

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
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
| source | VARCHAR(50) | YES | NULL | 来源：BOSS直聘/拉勾网等 |
| url | VARCHAR(500) | YES | NULL | 原始链接 |
| status | VARCHAR(20) | NO | 'active' | 状态：active/closed |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (city, status)
- INDEX (salary_min, salary_max)
- FULLTEXT (title, description)

---

### 6. applications - 申请记录表
**用途**: 存储用户申请职位的记录

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| job_id | BIGINT | NO | - | 外键：jobs.id |
| resume_id | BIGINT | YES | NULL | 外键：resumes.id（使用的简历） |
| status | VARCHAR(20) | NO | 'submitted' | 状态：submitted/viewed/interviewing/rejected/accepted |
| applied_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 申请时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- UNIQUE (user_id, job_id)
- INDEX (user_id, status)
- INDEX (job_id)

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

### 8. interviews - 面试表
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

### 9. interview_questions - 面试问题表
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

### 10. interview_reports - 面试报告表
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

### 11. chat_sessions - 聊天会话表
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

### 12. chat_messages - 聊天消息表
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

### 13. career_plans - 职业规划表
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

### 14. agent_tasks - Agent任务表
**用途**: 存储自动化求职任务

| 字段 | 类型 | 空 | 默认值 | 说明 |
|------|------|-----|--------|------|
| id | BIGINT | NO | AUTO_INCREMENT | 主键 |
| user_id | BIGINT | NO | - | 外键：users.id |
| type | VARCHAR(20) | NO | - | 类型：search/filter/apply/track |
| status | VARCHAR(20) | NO | 'pending' | 状态：pending/running/completed/failed/paused |
| progress | INT | NO | 0 | 进度（0-100） |
| config | JSON | NO | - | 任务配置 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- PRIMARY KEY (id)
- INDEX (user_id, status)
- INDEX (type, status)

---

### 15. agent_logs - Agent任务日志表
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

### 17. user_activities - 用户活动日志表
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
- 使用 bcrypt 加密存储，cost factor = 12
- 密码字段：`password_hash VARCHAR(255)`

### 2. 敏感数据
- 手机号：`phone` 字段，展示时脱敏（138****8888）
- 头像URL：存储在OSS，定期清理过期文件

### 3. 软删除
- 所有核心表支持软删除（`deleted_at` 字段）
- 查询时过滤：`WHERE deleted_at IS NULL`

### 4. 审计日志
- `user_activities` 表记录关键操作
- 不可删除，仅用于审计

### 5. 数据备份
- 每日全量备份
- 实时binlog增量备份

---

## 五、性能优化

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

---

## 六、设计说明

### 反范式说明
1. **job_matches 表**：冗余存储 `match_score`，避免每次查询都计算
2. **resumes.overall_score**：冗余存储分析分数，提升列表查询性能
3. **interviews.overall_score**：冗余存储面试分数，避免JOIN查询

### 扩展性考虑
1. **JSON字段**：`skills`, `strengths` 等使用JSON，便于结构变化
2. **预留字段**：`metadata` 字段用于存储未来扩展数据
3. **模块化设计**：表之间松耦合，便于独立扩展

---

## 七、调用数据库Agent

在需要时使用以下命令调用数据库架构师agent：

```
请使用数据库架构师agent帮我：
1. 生成完整的SQL建表语句
2. 优化某个表的索引设计
3. 分析查询性能瓶颈
4. 设计数据迁移方案
```

agent位置：`.claude/agents/database-architect.md`
