# AI Career Agent 测试文档

> 版本：1.0  
> 最后更新：2026-07-13  
> 测试框架：Vitest + jsdom + @vue/test-utils

---

## 目录

- [一、测试环境](#一测试环境)
- [二、快速开始](#二快速开始)
- [三、测试覆盖范围](#三测试覆盖范围)
- [四、测试文件结构](#四测试文件结构)
- [五、测试命令](#五测试命令)
- [六、新增测试](#六新增测试)
- [七、常见问题](#七常见问题)

---

## 一、测试环境

### 依赖列表

| 依赖 | 版本 | 说明 |
|------|------|------|
| vitest | ^4.1.10 | 测试框架 |
| jsdom | ^29.1.1 | 浏览器环境模拟 |
| @vue/test-utils | ^2.4.11 | Vue 组件测试工具 |

### 配置

```js
// vitest.config.ts
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/**/*.spec.ts'],
    setupFiles: ['tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
  resolve: {
    alias: { '@': '/src' },
  },
})
```

---

## 二、快速开始

### 运行测试

```bash
# 运行全部测试
npm test

# 等同于
npx vitest run

# 监听模式（文件变化自动重跑）
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

### 最新测试结果

```
Test Files  13 passed (13)
     Tests  98 passed (98)
   Start at  15:34:48
   Duration  14.73s
```

---

## 三、测试覆盖范围

### 3.1 工具函数 (utils) - 2 文件 / 28 测试

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `tests/utils/format.spec.ts` | 16 | `formatFileSize`, `formatSalary`, `formatDate`, `timeAgo`, `getScoreColor`, `getScoreLevel` |
| `tests/utils/storage.spec.ts` | 12 | `storage.set`, `storage.get`, `storage.remove`, `storage.clear` |

### 3.2 Pinia Store - 4 文件 / 36 测试

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `tests/stores/app.spec.ts` | 5 | sidebar 状态切换、宽度计算、退出登录 |
| `tests/stores/user.spec.ts` | 8 | 登录/登出、token 管理、用户信息更新 |
| `tests/stores/resume.spec.ts` | 7 | 简历 CRUD、分析更新 |
| `tests/stores/chat.spec.ts` | 16 | 会话管理、消息发送、流式消息处理 |

### 3.3 组合式函数 (composables) - 4 文件 / 21 测试

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `tests/composables/useAuth.spec.ts` | 4 | 登录状态、登出、更新用户信息 |
| `tests/composables/usePagination.spec.ts` | 5 | 分页状态管理、页码/页大小变化 |
| `tests/composables/useSSE.spec.ts` | 5 | 连接/关闭、消息接收、DONE 处理 |
| `tests/composables/useUpload.spec.ts` | 7 | 上传状态、进度、成功/失败 |

### 3.4 组件 (components) - 2 文件 / 11 测试

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `tests/components/ScoreRing.spec.ts` | 8 | 渲染、SVG 属性、颜色、尺寸 |
| `tests/components/EmptyState.spec.ts` | 3 | 默认消息、自定义消息 |

### 3.5 路由 (router) - 1 文件 / 9 测试

| 文件 | 测试数 | 说明 |
|------|--------|------|
| `tests/router.spec.ts` | 9 | 路由存在性、meta 属性、参数路由、路由总数 |

---

## 四、测试文件结构

```
tests/
├── setup.ts                          # 全局测试配置（Element Plus 注册）
├── utils/
│   ├── format.spec.ts                # 格式化工具测试
│   └── storage.spec.ts             # 本地存储测试
├── stores/
│   ├── app.spec.ts                  # App Store 测试
│   ├── user.spec.ts                 # User Store 测试
│   ├── resume.spec.ts               # Resume Store 测试
│   └── chat.spec.ts                 # Chat Store 测试
├── composables/
│   ├── useAuth.spec.ts              # useAuth 测试
│   ├── usePagination.spec.ts        # usePagination 测试
│   ├── useSSE.spec.ts               # useSSE 测试
│   └── useUpload.spec.ts            # useUpload 测试
├── components/
│   ├── ScoreRing.spec.ts            # ScoreRing 组件测试
│   └── EmptyState.spec.ts           # EmptyState 组件测试
└── router.spec.ts                   # 路由配置测试
```

---

## 五、测试命令

### package.json scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

### 命令详解

| 命令 | 说明 |
|------|------|
| `npm test` | 运行全部测试（一次性） |
| `npm run test:watch` | 监听模式，文件变化自动重跑 |
| `npm run test:coverage` | 运行测试并生成覆盖率报告 |
| `npx vitest run tests/utils` | 运行指定目录测试 |
| `npx vitest run -t "xxx"` | 按标题过滤测试 |

---

## 六、新增测试

### 6.1 新增 Store 测试

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useXXXStore } from '@/stores/xxx'

describe('useXXXStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('初始状态', () => {
    const store = useXXXStore()
    expect(store.someValue).toBe('default')
  })

  it('action 正确工作', () => {
    const store = useXXXStore()
    store.someAction()
    expect(store.someValue).toBe('changed')
  })
})
```

### 6.2 新增组件测试

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from '@/components/business/MyComponent.vue'

describe('MyComponent', () => {
  it('正确渲染', () => {
    const wrapper = mount(MyComponent, {
      props: { title: 'Hello' },
    })
    expect(wrapper.text()).toContain('Hello')
  })

  it('点击触发事件', async () => {
    const wrapper = mount(MyComponent)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

### 6.3 新增工具函数测试

```typescript
import { describe, it, expect } from 'vitest'
import { myUtil } from '@/utils/myUtil'

describe('myUtil', () => {
  it('正确处理输入', () => {
    expect(myUtil('input')).toBe('result')
  })

  it('抛出异常当输入无效时', () => {
    expect(() => myUtil(null as any)).toThrow()
  })
})
```

---

## 七、常见问题

### 7.1 Element Plus 组件注册

**问题：** Element Plus 组件在测试中未注册。  
**解决：** `tests/setup.ts` 已全局注册 Element Plus 插件。

```ts
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'
config.global.plugins.push(ElementPlus)
```

### 7.2 路由 meta 不继承

**问题：** 嵌套路由的 meta 属性不继承自父路由。  
**解决：** 测试时直接断言父路由的 meta 属性，子路由使用 `props` 传参测试。

### 7.3 requestAnimationFrame 无限递归

**问题：** `ScoreRing` 组件使用 `requestAnimationFrame` 动画导致测试堆栈溢出。  
**解决：** 测试文件 mock `requestAnimationFrame` 为同步执行。

```ts
(global as any).requestAnimationFrame = (cb: (t: number) => void) => {
  cb(800)
  return 0
}
(global as any).performance = { now: () => 0 }
```

### 7.4 类型检查错误

**问题：** 测试文件中 TypeScript 类型报错。  
**解决：** 确保 `vitest.config.ts` 中 `resolve.alias` 包含 `@` 指向 `/src`。

---

*文档结束*
