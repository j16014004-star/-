import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './router'
import App from './App.vue'
import './assets/styles/index.css'

// Initialize mock data in development
if (import.meta.env.DEV) {
  import('./mock/index').then(({ setupMock }) => {
    import('./utils/request').then(({ default: request }) => {
      setupMock(request)
    })
    // Auth mock disabled - using real backend API
    // import('./mock/auth').then(({ setupAuthMock }) => setupAuthMock())
    // Resume mock disabled - using real backend API for upload/delete/download/list/detail
    // import('./mock/resume').then(({ setupResumeMock }) => setupResumeMock())
    // AI Mock 默认仅在开发环境开启；后端接口完成后设置 VITE_ENABLE_AI_MOCK=false。
    if (import.meta.env.VITE_ENABLE_AI_MOCK !== 'false') {
      import('./mock/ai').then(({ setupAIMock }) => setupAIMock())
    }
    // Job mock disabled - recommendations come from backend crawler data
    // import('./mock/job').then(({ setupJobMock }) => setupJobMock())
    import('./mock/chat').then(({ setupChatMock }) => setupChatMock())
    import('./mock/agent').then(({ setupAgentMock }) => setupAgentMock())
    // HR mock disabled - job application, communication and interviews use the real backend.
    // Interview mock disabled - AI mock interviews use the real backend and vector knowledge bases.
  })
}

const app = createApp(App)

// Register all Element Plus icons globally
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: undefined })
app.mount('#app')
