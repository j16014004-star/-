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
    import('./mock/resume').then(({ setupResumeMock }) => setupResumeMock())
    import('./mock/career').then(({ setupCareerMock }) => setupCareerMock())
    import('./mock/job').then(({ setupJobMock }) => setupJobMock())
    import('./mock/chat').then(({ setupChatMock }) => setupChatMock())
    import('./mock/agent').then(({ setupAgentMock }) => setupAgentMock())
    import('./mock/hr').then(({ setupHRMock }) => setupHRMock())
    import('./mock/interview').then(({ setupInterviewMock }) => setupInterviewMock())
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