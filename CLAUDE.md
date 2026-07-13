# AI Career Agent - 项目记忆文件

> **最后更新**: 2026-07-13  
> **用途**: 快速恢复项目上下文

---

## 📋 项目简介

AI Career Agent 是智能求职助手平台前端，提供简历分析优化、岗位匹配推荐、AI 模拟面试、职业规划等功能。

**技术栈**: Vue 3 + TypeScript + Vite + Element Plus + Tailwind CSS 4 + Pinia  
**后端计划**: FastAPI + LangChain + JWT + MySQL + Vector DB

---

## 🚦 当前状态

- **前端框架**: ✅ 100% 完成
- **页面 UI**: ✅ 100% 完成（所有页面）
- **Mock 数据**: ✅ 100% 完成
- **测试**: ✅ 98/98 通过
- **开发服务器**: ✅ 端口 3000

### 最近完成
1. ✅ sql_desgin.md 数据库设计修改（users 增加 role/is_deleted，refresh_tokens 重构，login_logs 增加 login_location）
2. ✅ backend_api.md v2.0（14 个模块）
3. ✅ HrChatView.vue 重写为 AI Agent 沟通中心
4. ✅ database_design.md（25 张表）

### 未提交文件（不要自动 commit）
- sql_desgin.md、backend_api.md、database_design.md、HrChatView.vue

---

## 📁 项目结构

```
ai-career-agent/
├── src/
│   ├── api/              # API 请求层（auth, resume, career, job, chat, agent, hr, interview）
│   ├── components/       # 组件库（layout/, common/, business/）
│   ├── composables/      # 组合式函数（useAuth, usePagination, useSSE, useUpload）
│   ├── mock/             # Mock 数据系统（9 个模块）
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态管理（app, user, resume, chat）
│   ├── types/            # TypeScript 类型定义
│   ├── utils/            # 工具函数（request, storage, format）
│   └── views/            # 页面视图（auth, dashboard, resume, career, job, chat, agent, hr, interview, profile）
└── tests/                # 测试文件（98 个用例）
```

---

## 📏 核心规则

### 协作规则（必须遵守）
1. **不要自动 git commit** - 除非用户明确要求
2. **保持数据库结构简单** - 不要随意增加新表或重新设计
3. **使用中文** - 所有沟通使用中文
4. **修改前先分析** - 先排查原因，确认后再修改
5. **最小化修改** - 不要重构不相关的代码

### 代码规范
- TypeScript + Composition API (`<script setup>`)
- Element Plus + Tailwind CSS
- 避免 `any`，使用明确类型
- 复杂逻辑必须有注释
- 所有异步操作必须有错误处理

### 命令
- 启动: `npm run dev`（端口 3000）
- 测试: `npm run test`
- `/remember` - 读取 CLAUDE.md 恢复上下文

---

## 🐛 已知问题

**当前状态**: 无已知 Bug

**潜在风险**:
- Mock 初始化时序：异步加载可能在路由守卫之后完成（未发现实际问题）
- localStorage 数据残留：用户登出后数据残留（无影响）

---

## 📝 待开发功能

### 高优先级
1. 后端 API 集成（替换 Mock 数据）
2. 文件上传功能（简历、头像）
3. 实时通信（SSE、WebSocket）

### 中优先级
4. 数据库实现（Schema、迁移脚本）
5. 用户认证完善（Token 刷新、多设备管理）
6. 性能优化（懒加载、虚拟滚动）

---

## 🗄️ 数据库设计

### 用户认证模块（sql_desgin.md）
- **users** - 用户主表（含 role、is_deleted 逻辑删除）
- **refresh_tokens** - 刷新令牌表（仅存储 refresh token，access token 不持久化）
- **verification_codes** - 验证码表
- **login_logs** - 登录日志表（含 login_location）

### 完整设计（database_design.md）
25 张表，覆盖所有业务模块

### API 文档（backend_api.md）
14 个模块的完整 API 设计

---

## 💡 重要决策

1. **Mock 数据系统** - 前端独立开发，未来切换到真实 API
2. **Element Plus** - 官方维护，组件丰富
3. **Tailwind CSS** - 开发速度快，样式一致性好
4. **Vitest** - Vite 原生支持，速度快
5. **不重构现有代码** - 保持稳定性，只修复 Bug

---

**维护说明**: 此文件由 Claude AI Assistant 维护，每次重要变更后更新。
