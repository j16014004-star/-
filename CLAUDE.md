# AI Career Agent - 项目记忆文件

> **最后更新**: 2026-07-13  
> **维护者**: Claude AI Assistant  
> **用途**: 快速恢复项目上下文，指导后续开发

---

## 📋 项目介绍

### 项目背景
AI Career Agent 是一个智能求职助手平台的前端项目，旨在为求职者提供 AI 驱动的职业发展服务，包括简历分析优化、岗位匹配推荐、AI 模拟面试、职业规划等功能。

### 项目目标
- 构建一个现代化、响应式的单页应用（SPA）
- 提供完整的用户交互体验
- 实现前后端分离架构（当前仅前端，使用 Mock 数据）
- 支持未来与后端 API 的无缝集成

### 核心价值
- **智能化**: 利用 AI 技术提供简历分析、岗位匹配、面试训练等功能
- **个性化**: 根据用户技能和偏好提供定制化的职业规划建议
- **便捷性**: 一站式求职服务平台，简化求职流程

---

## 🛠️ 技术栈

### 核心框架
- **Vue 3.5.39** - 渐进式 JavaScript 框架
- **TypeScript 6.0.2** - 类型安全的 JavaScript 超集
- **Vite 8.1.1** - 下一代前端构建工具

### UI 与样式
- **Element Plus 2.14.3** - Vue 3 组件库
- **Tailwind CSS 4.3.2** - 实用优先的 CSS 框架
- **@element-plus/icons-vue 2.3.2** - Element Plus 图标库

### 状态管理与路由
- **Pinia 3.0.4** - Vue 3 官方状态管理库
- **Vue Router 4.6.4** - Vue 3 官方路由管理器

### 网络请求
- **Axios 1.18.1** - 基于 Promise 的 HTTP 客户端

### 测试工具
- **Vitest 4.1.10** - Vite 原生测试框架
- **@vue/test-utils 2.4.11** - Vue 组件测试工具
- **jsdom 29.1.1** - DOM 模拟环境

### 开发工具
- **@vitejs/plugin-vue 6.0.7** - Vite Vue 插件
- **@tailwindcss/vite 4.3.2** - Tailwind CSS Vite 插件
- **vue-tsc 3.3.5** - Vue TypeScript 类型检查

---

## 📁 项目结构

```
ai-career-agent/
├── index.html                      # 入口 HTML
├── package.json                    # 项目依赖配置
├── vite.config.ts                  # Vite 配置文件
├── vitest.config.ts                # Vitest 测试配置
├── tsconfig.json                   # TypeScript 配置
├── tsconfig.node.json              # Node.js TypeScript 配置
├── env.d.ts                        # 环境变量类型定义
│
├── public/                         # 静态资源
│   └── favicon.svg
│
├── src/
│   ├── main.ts                     # 应用入口文件
│   ├── App.vue                     # 根组件
│   │
│   ├── api/                        # API 请求层（待实现）
│   │   ├── index.ts                # Axios 实例配置
│   │   ├── auth.ts                 # 认证 API
│   │   ├── resume.ts               # 简历 API
│   │   ├── career.ts               # 职业规划 API
│   │   ├── job.ts                  # 岗位推荐 API
│   │   ├── chat.ts                 # AI 助手 API
│   │   ├── agent.ts                # Agent 任务 API
│   │   ├── hr.ts                   # HR 沟通 API
│   │   ├── interview.ts            # AI 面试 API
│   │   └── types/                  # API 类型定义
│   │
│   ├── assets/                     # 静态资源
│   │   └── styles/
│   │       └── index.css           # 全局样式 + Tailwind 指令
│   │
│   ├── components/                 # 组件库
│   │   ├── layout/                 # 布局组件
│   │   │   ├── AppLayout.vue       # 主布局（侧边栏 + 顶栏 + 内容区）
│   │   │   ├── AppSidebar.vue      # 左侧导航菜单
│   │   │   ├── AppHeader.vue       # 顶部导航栏
│   │   │   └── AppBreadcrumb.vue   # 面包屑导航
│   │   │
│   │   ├── common/                 # 通用组件
│   │   │   ├── PageHeader.vue      # 页面标题
│   │   │   ├── StatCard.vue        # 统计卡片
│   │   │   ├── StatusTag.vue       # 状态标签
│   │   │   ├── EmptyState.vue      # 空状态
│   │   │   └── LoadingOverlay.vue  # 加载遮罩
│   │   │
│   │   └── business/               # 业务组件
│   │       ├── ResumeCard.vue      # 简历卡片
│   │       ├── JobCard.vue         # 岗位卡片
│   │       ├── ScoreRing.vue       # 评分环
│   │       ├── ChatBubble.vue      # 聊天气泡
│   │       ├── StreamingText.vue   # 流式文本
│   │       └── MatchBadge.vue      # 匹配度徽章
│   │
│   ├── composables/                # 组合式函数
│   │   ├── useAuth.ts              # 认证逻辑
│   │   ├── usePagination.ts        # 分页逻辑
│   │   ├── useSSE.ts               # Server-Sent Events
│   │   └── useUpload.ts            # 文件上传
│   │
│   ├── mock/                       # Mock 数据系统
│   │   ├── index.ts                # Mock 拦截器核心
│   │   ├── auth.ts                 # 认证 Mock
│   │   ├── resume.ts               # 简历 Mock
│   │   ├── career.ts               # 职业规划 Mock
│   │   ├── job.ts                  # 岗位推荐 Mock
│   │   ├── chat.ts                 # AI 助手 Mock
│   │   ├── agent.ts                # Agent 任务 Mock
│   │   ├── hr.ts                   # HR 沟通 Mock
│   │   └── interview.ts            # AI 面试 Mock
│   │
│   ├── router/                     # 路由配置
│   │   └── index.ts                # 路由定义与守卫
│   │
│   ├── stores/                     # Pinia 状态管理
│   │   ├── app.ts                  # 全局 UI 状态
│   │   ├── user.ts                 # 用户信息
│   │   ├── resume.ts               # 简历数据
│   │   └── chat.ts                 # 聊天记录
│   │
│   ├── types/                      # TypeScript 类型定义
│   │   └── index.ts                # 全局类型
│   │
│   ├── utils/                      # 工具函数
│   │   ├── request.ts              # HTTP 请求封装
│   │   ├── storage.ts              # 本地存储封装
│   │   └── format.ts               # 格式化工具
│   │
│   └── views/                      # 页面视图
│       ├── auth/                   # 认证页面
│       │   ├── LoginView.vue       # 登录
│       │   └── RegisterView.vue    # 注册
│       │
│       ├── dashboard/              # 首页
│       │   └── DashboardView.vue   # 仪表盘
│       │
│       ├── resume/                 # 简历管理
│       │   ├── ResumeListView.vue      # 简历列表
│       │   ├── ResumeUploadView.vue    # 上传简历
│       │   ├── ResumeDetailView.vue    # 简历详情
│       │   └── ResumeOptimizeView.vue  # AI 优化
│       │
│       ├── career/                 # 职业规划
│       │   └── CareerPlanView.vue
│       │
│       ├── job/                    # 岗位推荐
│       │   └── JobListView.vue
│       │
│       ├── chat/                   # AI 助手
│       │   └── ChatAssistantView.vue
│       │
│       ├── agent/                  # Agent 任务中心
│       │   └── AgentTaskView.vue
│       │
│       ├── hr/                     # HR 沟通助手
│       │   └── HrChatView.vue
│       │
│       ├── interview/              # AI 面试
│       │   ├── InterviewLobbyView.vue   # 面试大厅
│       │   ├── InterviewRoomView.vue    # 面试房间
│       │   └── InterviewReportView.vue  # 面试报告
│       │
│       └── profile/                # 个人中心
│           └── ProfileView.vue
│
└── tests/                          # 测试文件
    ├── setup.ts                    # 测试环境配置
    ├── utils/                      # 工具函数测试
    ├── stores/                     # 状态管理测试
    ├── composables/                # 组合式函数测试
    ├── components/                 # 组件测试
    └── router.spec.ts              # 路由测试
```

---

## 🗄️ 数据库设计

> **状态**: 待实现  
> **说明**: 当前项目使用 Mock 数据，数据库设计需根据后端 API 确定

### 预期数据表
1. **users** - 用户信息
2. **resumes** - 简历数据
3. **resume_analyses** - 简历分析结果
4. **career_plans** - 职业规划
5. **jobs** - 岗位信息
6. **job_applications** - 岗位申请
7. **chat_sessions** - 聊天会话
8. **chat_messages** - 聊天消息
9. **agent_tasks** - Agent 任务
10. **interviews** - 面试记录
11. **interview_questions** - 面试问题
12. **hr_messages** - HR 沟通消息

---

## ✅ 已完成模块

### 1. 项目基础架构 ✅
- [x] Vite + Vue 3 + TypeScript 项目初始化
- [x] 所有依赖安装与配置
- [x] Tailwind CSS 集成
- [x] Element Plus 集成
- [x] TypeScript 类型检查配置

### 2. 路由系统 ✅
- [x] 完整的路由配置（15+ 页面）
- [x] 路由守卫（认证检查）
- [x] 路由懒加载
- [x] 嵌套路由支持
- [x] 404 页面重定向

**路由列表**:
| 路径 | 页面 | 认证要求 |
|------|------|----------|
| `/login` | 登录页 | 否 |
| `/register` | 注册页 | 否 |
| `/` | 仪表盘 | 是 |
| `/resume` | 简历列表 | 是 |
| `/resume/upload` | 上传简历 | 是 |
| `/resume/detail/:id` | 简历详情 | 是 |
| `/resume/optimize/:id` | AI 优化 | 是 |
| `/career` | 职业规划 | 是 |
| `/jobs` | 岗位推荐 | 是 |
| `/chat` | AI 助手 | 是 |
| `/agent` | Agent 任务 | 是 |
| `/hr` | HR 助手 | 是 |
| `/interview` | 面试大厅 | 是 |
| `/interview/lobby` | 面试大厅 | 是 |
| `/interview/:id` | 面试房间 | 是 |
| `/interview/report/:id` | 面试报告 | 是 |
| `/profile` | 个人中心 | 是 |

### 3. 布局组件 ✅
- [x] **AppLayout** - 主布局框架
- [x] **AppSidebar** - 可折叠侧边栏菜单
- [x] **AppHeader** - 顶部导航栏（面包屑 + 用户信息）
- [x] 响应式设计支持

### 4. 认证页面 ✅
- [x] **LoginView** - 登录页面
  - 表单验证
  - 模拟登录逻辑
  - Token 存储
  - 跳转逻辑
- [x] **RegisterView** - 注册页面
  - 表单验证
  - 密码确认
  - 模拟注册逻辑

### 5. 仪表盘 ✅
- [x] **DashboardView** - 首页仪表盘
  - 欢迎信息（显示用户名）
  - 统计数据卡片（简历数、面试次数、匹配岗位、AI 对话）
  - 快捷操作入口
  - 最近动态列表
  - 即将到来的面试

### 6. 功能页面（UI 完成，功能待完善）
- [x] **ResumeListView** - 简历列表（Mock 数据）
- [x] **ResumeUploadView** - 简历上传（UI 完成）
- [x] **ResumeDetailView** - 简历详情（Mock 数据）
- [x] **ResumeOptimizeView** - AI 优化（Mock 数据）
- [x] **CareerPlanView** - 职业规划（Mock 数据）
- [x] **JobListView** - 岗位推荐（Mock 数据）
- [x] **ChatAssistantView** - AI 助手（模拟流式对话）
- [x] **AgentTaskView** - Agent 任务中心（Mock 数据）
- [x] **HrChatView** - HR 沟通助手（Mock 数据）
- [x] **InterviewLobbyView** - 面试大厅（Mock 数据）
- [x] **InterviewRoomView** - 面试房间（UI 完成）
- [x] **InterviewReportView** - 面试报告（Mock 数据）
- [x] **ProfileView** - 个人中心（UI 完成）

### 7. Mock 数据系统 ✅
- [x] Axios 请求拦截器实现
- [x] 延迟模拟（300-800ms）
- [x] 通配符路由匹配
- [x] 参数提取与合并
- [x] 完整的 Mock 数据模块（9 个模块）

### 8. 状态管理 ✅
- [x] **useAppStore** - 全局 UI 状态（侧边栏折叠、用户信息）
- [x] **useUserStore** - 用户认证状态
- [x] **useResumeStore** - 简历数据管理
- [x] **useChatStore** - 聊天记录管理

### 9. 工具函数 ✅
- [x] **request.ts** - Axios 实例封装（请求/响应拦截器）
- [x] **storage.ts** - LocalStorage 封装（类型安全）
- [x] **format.ts** - 格式化工具（日期、文件大小等）

### 10. 测试体系 ✅
- [x] Vitest 配置完成
- [x] jsdom 测试环境
- [x] Element Plus 全局注册
- [x] **98 个测试用例全部通过**

**测试覆盖**:
- 工具函数测试（format、storage）
- 状态管理测试（app、user、resume、chat stores）
- 组合式函数测试（useAuth、usePagination、useSSE、useUpload）
- 组件测试（ScoreRing、EmptyState）
- 路由测试（路由守卫、路由配置）

### 11. 开发环境 ✅
- [x] 开发服务器配置（端口 3000）
- [x] 热更新支持
- [x] 路径别名（`@` → `/src`）
- [x] API 代理配置（`/api` → `http://localhost:8000`）

---

## 🚦 当前开发状态

### 整体进度
- **前端框架**: ✅ 100% 完成
- **页面 UI**: ✅ 90% 完成（所有页面 UI 已实现）
- **Mock 数据**: ✅ 100% 完成
- **真实 API 集成**: ⏳ 0%（待后端完成）
- **测试覆盖**: ✅ 核心模块已覆盖

### 当前运行状态
- **开发服务器**: ✅ 运行中（http://localhost:3000）
- **端口**: 3000
- **状态**: 正常运行
- **测试**: 98/98 通过

### 最近修复
1. ✅ **Content-Type 响应头问题** - 移除错误的全局 headers 配置
2. ✅ **Emoji 显示问题** - 将 HTML 实体替换为实际字符
3. ✅ **中文乱码问题** - 依赖 HTML meta charset 标签
4. ✅ **端口占用问题** - 清理残留进程

---

## 🐛 当前 Bug

> **状态**: 无已知 Bug  
> **最后检查**: 2026-07-13

### 已解决的 Bug
1. **页面无法加载** - Content-Type 配置错误导致 JS 不执行
2. **Emoji 显示为文字** - Vue 插值转义 HTML 实体
3. **中文乱码** - 响应头 charset 配置问题
4. **端口占用** - 开发服务器残留进程

### 潜在问题（需关注）
1. **Mock 初始化时序** - 异步加载可能在路由守卫之后完成
   - **影响**: 如果用户已登录，首次加载可能触发 API 请求失败
   - **当前状态**: 未发现实际问题，但存在理论风险
   - **建议**: 如需修复，可将 Mock 初始化改为同步等待

2. **localStorage 数据清理** - 用户登出后数据残留
   - **影响**: 无
   - **当前状态**: 正常行为，Token 会在登出时清除

---

## 📝 待开发功能

### 高优先级
1. **后端 API 集成**
   - [ ] 替换 Mock 数据为真实 API
   - [ ] 实现 API 错误处理
   - [ ] 添加加载状态管理
   - [ ] 实现请求重试机制

2. **文件上传功能**
   - [ ] 简历文件上传（PDF/Word）
   - [ ] 头像上传
   - [ ] 上传进度显示
   - [ ] 文件类型验证

3. **实时通信**
   - [ ] SSE (Server-Sent Events) 实现
   - [ ] AI 对话流式输出
   - [ ] 实时通知系统

### 中优先级
4. **数据库设计**
   - [ ] 设计数据库 Schema
   - [ ] 编写数据库迁移脚本
   - [ ] 实现数据模型

5. **用户认证完善**
   - [ ] Token 刷新机制
   - [ ] 记住登录状态
   - [ ] 多设备登录管理

6. **性能优化**
   - [ ] 路由懒加载优化
   - [ ] 组件按需加载
   - [ ] 图片懒加载
   - [ ] 虚拟滚动（长列表）

### 低优先级
7. **高级功能**
   - [ ] 简历模板选择
   - [ ] 多语言支持
   - [ ] 主题切换（深色模式）
   - [ ] PWA 支持

8. **部署准备**
   - [ ] 生产环境配置
   - [ ] 环境变量管理
   - [ ] 构建优化
   - [ ] CDN 配置

---

## 📏 编码规范

### Vue 组件规范
```vue
<!-- 1. 使用 <script setup> 语法 -->
<script setup lang="ts">
// 2. 导入顺序：Vue → 第三方库 → 内部模块 → 类型
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import type { UserInfo } from '@/types'

// 3. Props 定义（使用 TypeScript）
const props = defineProps<{
  title: string
  count?: number
}>()

// 4. Emits 定义
const emit = defineEmits<{
  update: [value: string]
  delete: [id: number]
}>()

// 5. 响应式数据
const loading = ref(false)
const dataList = ref<UserInfo[]>([])

// 6. 计算属性
const isEmpty = computed(() => dataList.value.length === 0)

// 7. 方法定义
function handleSubmit() {
  // ...
}

// 8. 生命周期钩子
onMounted(() => {
  // ...
})
</script>

<!-- 9. 模板使用 Element Plus 组件 -->
<template>
  <div class="component-name">
    <!-- 内容 -->
  </div>
</template>

<!-- 10. 样式使用 scoped -->
<style scoped>
.component-name {
  /* 样式 */
}
</style>
```

### TypeScript 规范
```typescript
// 1. 接口命名使用 PascalCase
interface UserInfo {
  id: number
  username: string
  email: string
}

// 2. 类型命名使用 PascalCase
type UserStatus = 'active' | 'inactive' | 'pending'

// 3. 函数参数和返回值使用类型注解
function getUserById(id: number): UserInfo | null {
  // ...
}

// 4. 避免使用 any，使用 unknown 或具体类型
function processData(data: unknown) {
  if (typeof data === 'object' && data !== null) {
    // 类型守卫
  }
}

// 5. 枚举使用 const enum
const enum TaskStatus {
  Pending = 'pending',
  Running = 'running',
  Completed = 'completed',
}
```

### CSS 规范
```css
/* 1. 使用 Tailwind CSS 工具类优先 */
<div class="flex items-center gap-4 p-6 bg-white rounded-xl shadow-sm">

/* 2. 自定义样式使用 BEM 命名 */
.block-name {
  /* 块样式 */
}
.block-name__element {
  /* 元素样式 */
}
.block-name--modifier {
  /* 修饰符样式 */
}

/* 3. 使用 CSS 变量 */
:root {
  --primary-color: #4f46e5;
  --success-color: #10b981;
}

/* 4. 避免使用 !important，除非覆盖第三方库 */
.el-card {
  border-radius: 12px !important;
}
```

### 命名规范
- **文件名**: PascalCase（组件）或 camelCase（工具函数）
- **组件名**: PascalCase（如 `UserProfile.vue`）
- **变量/函数**: camelCase（如 `userName`, `handleSubmit`）
- **常量**: UPPER_SNAKE_CASE（如 `API_BASE_URL`）
- **类型/接口**: PascalCase（如 `UserInfo`, `ApiResponse`）
- **CSS 类**: kebab-case（如 `user-profile`）

### 目录组织
- **按功能模块**组织，而非按文件类型
- **组件**放在 `components/` 目录
- **页面**放在 `views/` 目录
- **工具函数**放在 `utils/` 目录
- **类型定义**放在 `types/` 目录

---

## 👨‍💻 我的开发习惯

### 工作流程偏好
1. **先分析后修改**
   - 遇到问题时，先排查原因，不要立即修改代码
   - 输出：错误原因、影响文件、修复方案
   - 确认后再实施修改

2. **保持代码稳定**
   - 不要重构现有代码
   - 不要修改不相关的功能
   - 只修复明确的问题

3. **清晰的沟通**
   - 修改前说明要做什么
   - 修改后说明改了什么
   - 提供验证方法

### 代码偏好
- **TypeScript**: 所有代码必须使用 TypeScript
- **Composition API**: 使用 `<script setup>` 语法
- **Element Plus**: 优先使用 Element Plus 组件
- **Tailwind CSS**: 优先使用 Tailwind 工具类
- **类型安全**: 避免使用 `any`，使用明确的类型定义

### 项目规范要求
- **不破坏现有功能**: 任何修改不能导致现有功能失效
- **测试覆盖**: 重要功能必须有测试
- **代码注释**: 复杂逻辑必须添加注释
- **错误处理**: 所有异步操作必须有错误处理

### 希望 Claude 如何协助
1. **主动发现问题**
   - 不仅修复当前问题，还要发现潜在问题
   - 提供改进建议

2. **详细的解释**
   - 解释为什么这样修改
   - 解释技术原理

3. **谨慎的修改**
   - 最小化修改范围
   - 不引入不必要的变更

4. **完整的测试**
   - 修改后运行测试
   - 确保没有破坏现有功能

---

## 🤝 Claude 开发协作规则

### 修改代码前
1. **读取相关文件** - 理解现有代码结构
2. **分析问题** - 确定问题根因
3. **提出方案** - 说明修改内容和影响
4. **等待确认** - 获得用户同意后再修改

### 修改代码时
1. **最小化修改** - 只修改必要的部分
2. **保持风格** - 遵循现有代码风格
3. **添加注释** - 解释复杂逻辑
4. **类型安全** - 使用 TypeScript 类型

### 修改代码后
1. **运行测试** - 确保测试通过
2. **验证功能** - 手动测试相关功能
3. **清理代码** - 移除调试代码
4. **更新文档** - 如有必要更新文档

### 沟通原则
1. **先说结论** - 先说明结果，再解释原因
2. **使用中文** - 所有说明使用中文
3. **提供选项** - 如果有多种方案，提供选择
4. **承认错误** - 如果修改导致问题，立即承认并修复

### 禁止行为
- ❌ 不要未经允许修改代码
- ❌ 不要重构不相关的代码
- ❌ 不要引入新的依赖（除非必要）
- ❌ 不要删除现有功能
- ❌ 不要使用 `any` 类型
- ❌ 不要忽略错误处理
- ❌ 不要硬编码魔法数字

---

## 📚 历史问题记录

### 2026-07-13: Content-Type 响应头问题
**问题**: 浏览器无法加载页面，显示空白  
**原因**: `vite.config.ts` 中配置了全局 `headers: { 'Content-Type': 'text/html; charset=utf-8' }`，导致所有文件（包括 JS/CSS）都被标记为 HTML，浏览器不执行 JavaScript  
**影响文件**: `vite.config.ts`  
**修复方案**: 移除全局 headers 配置，依赖 HTML meta charset 标签  
**教训**: 不要为所有文件设置统一的 Content-Type，让 Vite 自动处理

### 2026-07-13: Emoji 显示为 HTML 实体
**问题**: 页面显示 `&#x1F44B;` 而不是 👋 emoji  
**原因**: 在 JavaScript 数据中使用 HTML 实体（如 `icon: '&#x1F44B;'`），Vue 在 `{{ }}` 插值时会转义为字面文本  
**影响文件**: `DashboardView.vue`, `AgentTaskView.vue`  
**修复方案**: 将 HTML 实体替换为实际 emoji 字符（如 `icon: '👋'`）  
**教训**: 
- 模板中可以直接使用 HTML 实体
- JavaScript 数据中必须使用实际字符

### 2026-07-13: 中文乱码问题
**问题**: 页面中文显示为乱码  
**原因**: 初期尝试通过响应头设置 charset，但配置错误  
**影响文件**: `vite.config.ts`, `index.html`  
**修复方案**: 
- 确保 `index.html` 包含 `<meta charset="UTF-8" />`
- 移除错误的响应头配置
**教训**: HTML meta 标签足以解决编码问题，不需要额外配置响应头

### 2026-07-13: 端口占用问题
**问题**: 开发服务器无法启动，端口 3000 被占用  
**原因**: 之前的开发服务器进程未正确终止  
**影响文件**: 无  
**修复方案**: 使用 `netstat` 查找占用进程，`taskkill` 强制终止  
**教训**: 停止服务器时要确保进程完全终止

### 2026-07-13: EmptyState.vue 重复 defineProps
**问题**: 编译失败 "duplicate defineProps() call"  
**原因**: 组件中有两个 `defineProps` 调用  
**影响文件**: `EmptyState.vue`  
**修复方案**: 合并为一个 `defineProps`，使用 `withDefaults`  
**教训**: 一个组件只能有一个 `defineProps`

### 2026-07-13: ScoreRing 测试无限递归
**问题**: 测试失败 "Maximum call stack size exceeded"  
**原因**: `requestAnimationFrame` 在 jsdom 中被 mock 为递归调用  
**影响文件**: `ScoreRing.spec.ts`  
**修复方案**: Mock `requestAnimationFrame` 为同步执行，只调用一次  
**教训**: 测试环境中需要正确 mock 浏览器 API

### 2026-07-13: 路由守卫 Meta 继承问题
**问题**: 子路由无法访问父路由的 meta  
**原因**: Vue Router 的 meta 不会自动继承到子路由  
**影响文件**: `router.spec.ts`  
**修复方案**: 修改测试逻辑，不依赖 meta 继承  
**教训**: 路由守卫需要使用 `to.matched.some()` 检查所有匹配路由的 meta

---

## 🎯 重要决策记录

### 决策 1: 选择 Mock 数据系统而非后端 API
**时间**: 2026-07-13  
**背景**: 项目初期需要快速开发前端，后端 API 尚未完成  
**决策**: 实现完整的 Mock 数据系统，通过 Axios 拦截器模拟 API  
**理由**: 
- 前端可以独立开发和测试
- 模拟真实的 API 交互
- 未来可以轻松切换到真实 API
**影响**: 前端开发进度加快，但需要后续替换为真实 API

### 决策 2: 使用 Element Plus 而非其他 UI 库
**时间**: 2026-07-13  
**背景**: 需要选择一个 Vue 3 组件库  
**决策**: 选择 Element Plus  
**理由**: 
- 官方维护，稳定可靠
- 组件丰富，满足需求
- 文档完善，社区活跃
**影响**: 开发效率提高，组件质量有保障

### 决策 3: 使用 Tailwind CSS 而非传统 CSS
**时间**: 2026-07-13  
**背景**: 需要选择样式方案  
**决策**: 使用 Tailwind CSS 工具类  
**理由**: 
- 开发速度快
- 样式一致性好
- 不需要编写大量 CSS
**影响**: 开发效率提高，但学习成本略高

### 决策 4: 使用 Vitest 而非 Jest
**时间**: 2026-07-13  
**背景**: 需要选择测试框架  
**决策**: 选择 Vitest  
**理由**: 
- Vite 原生支持，配置简单
- 速度快
- 与 Vite 配置共享
**影响**: 测试配置简单，运行速度快

### 决策 5: 不重构现有代码
**时间**: 2026-07-13  
**背景**: 用户明确要求不要重构  
**决策**: 只修复 Bug，不重构代码  
**理由**: 
- 保持代码稳定
- 避免引入新问题
- 尊重现有代码结构
**影响**: 代码质量可能不是最优，但稳定性好

---

## 🔮 未来开发计划

### 短期（1-2 周）
1. **后端 API 集成**
   - 与后端团队协作确定 API 接口
   - 替换 Mock 数据为真实 API
   - 实现错误处理和加载状态

2. **文件上传功能**
   - 实现简历文件上传
   - 实现头像上传
   - 添加文件类型和大小验证

3. **实时通信**
   - 实现 SSE 流式输出
   - 实现实时通知

### 中期（1-2 月）
4. **性能优化**
   - 路由懒加载优化
   - 组件按需加载
   - 图片懒加载

5. **用户体验优化**
   - 添加加载动画
   - 优化错误提示
   - 添加操作确认

6. **测试完善**
   - 增加 E2E 测试
   - 提高测试覆盖率
   - 添加性能测试

### 长期（3-6 月）
7. **高级功能**
   - 简历模板选择
   - 多语言支持
   - 深色模式

8. **部署上线**
   - 生产环境配置
   - 性能监控
   - 错误追踪

---

## 📞 联系方式

- **项目负责人**: [待填写]
- **前端开发**: Claude AI Assistant
- **后端开发**: [待填写]
- **UI 设计**: [待填写]

---

## 📄 版本历史

### v1.0.0 (2026-07-13)
- ✅ 完成项目基础架构
- ✅ 完成所有页面 UI
- ✅ 完成 Mock 数据系统
- ✅ 完成测试体系（98 个测试用例）
- ✅ 修复所有已知 Bug
- ✅ 项目可以正常运行

---

## 📝 备注

1. **项目当前状态**: 前端开发基本完成，可以正常运行和演示
2. **下一步重点**: 与后端集成，替换 Mock 数据为真实 API
3. **注意事项**: 
   - 不要重构现有代码
   - 修改前先分析原因
   - 保持代码稳定性
4. **测试命令**: `npm run test` 或 `/test`
5. **启动命令**: `npm run dev`（端口 3000）

---

**文件维护说明**: 
- 此文件由 Claude AI Assistant 维护
- 每次重要变更后更新
- 用于快速恢复项目上下文
- 如有问题请联系项目负责人
