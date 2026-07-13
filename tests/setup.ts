import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

// 全局注册 Element Plus 用于组件测试
config.global.plugins.push(ElementPlus)