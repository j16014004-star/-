<template>
  <div class="login-page min-h-screen flex">
    <!-- Left decorative panel -->
    <div class="login-left hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center">
      <div class="absolute inset-0 bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800"></div>
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-10 left-10 w-72 h-72 bg-white rounded-full blur-3xl"></div>
        <div class="absolute bottom-20 right-20 w-96 h-96 bg-blue-300 rounded-full blur-3xl"></div>
      </div>
      <div class="relative z-10 text-center px-12">
        <div class="text-6xl mb-6">&#x1F916;</div>
        <h1 class="text-4xl font-bold text-white mb-4">AI Career Agent</h1>
        <p class="text-xl text-blue-200 mb-8">智能职业发展助手</p>
        <div class="space-y-4 text-left text-blue-100 max-w-md mx-auto">
          <div class="flex items-center gap-3">
            <el-tag class="flex-shrink-0" color="rgba(255,255,255,0.2)">AI</el-tag>
            <span>智能简历分析与优化</span>
          </div>
          <div class="flex items-center gap-3">
            <el-tag class="flex-shrink-0" color="rgba(255,255,255,0.2)">&#x1F3AF;</el-tag>
            <span>精准岗位匹配推荐</span>
          </div>
          <div class="flex items-center gap-3">
            <el-tag class="flex-shrink-0" color="rgba(255,255,255,0.2)">&#x1F4AC;</el-tag>
            <span>AI模拟面试训练</span>
          </div>
          <div class="flex items-center gap-3">
            <el-tag class="flex-shrink-0" color="rgba(255,255,255,0.2)">&#x1F4CB;</el-tag>
            <span>个性化职业规划</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Right login form panel -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
      <div class="w-full max-w-md">
        <div class="text-center mb-8 lg:hidden">
          <div class="text-4xl mb-2">&#x1F916;</div>
          <h1 class="text-2xl font-bold text-gray-800">AI Career Agent</h1>
          <p class="text-gray-500">智能职业发展助手</p>
        </div>

        <el-card class="w-full shadow-xl border-0" body-style="padding: 40px">
          <h2 class="text-2xl font-bold text-gray-800 mb-2">欢迎回来</h2>
          <p class="text-gray-500 mb-8">登录您的账号以继续</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            size="large"
            label-position="top"
            @keyup.enter="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="w-full"
                :loading="loading"
                @click="handleLogin"
              >
                {{ loading ? '登录中...' : '登录' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div class="text-center mt-6">
            <span class="text-gray-500">还没有账号？</span>
            <router-link to="/register" class="text-blue-600 hover:text-blue-700 font-medium ml-1">
              立即注册
            </router-link>
          </div>
        </el-card>

        <p class="text-center text-gray-400 text-sm mt-8">
          &copy; 2026 AI Career Agent. All rights reserved.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在2-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true

  try {
    // 调用后端登录 API
    const response = await authApi.login({
      username: form.username,
      password: form.password
    })

    // 保存 token 和用户信息到 localStorage
    storage.set(TOKEN_KEY, response.data.access_token)
    storage.set('refresh_token', response.data.refresh_token)
    storage.set('token_type', response.data.token_type)
    storage.set('expires_in', response.data.expires_in)
    storage.set('token_expires_at', Date.now() + response.data.expires_in * 1000)
    storage.set(USER_KEY, response.data.user)

    ElMessage.success({
      message: `欢迎回来，${form.username}！`,
      duration: 2000
    })

    router.push('/')
  } catch (error: any) {
    const status = error.response?.status
    const message = error.response?.data?.message

    switch (status) {
      case 401:
        ElMessage.error('用户名或密码错误')
        break
      case 403:
        ElMessage.error('账号已被禁用，请联系管理员')
        break
      case 404:
        ElMessage.error('用户不存在')
        break
      case 429:
        ElMessage.error('请求过于频繁，请稍后再试')
        break
      default:
        ElMessage.error(message || '登录失败，请检查网络连接')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
}

.login-left {
  min-height: 100vh;
}

:deep(.el-card) {
  border-radius: 16px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  padding-bottom: 4px;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px #e5e7eb inset;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #3b82f6 inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #3b82f6 inset;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  border: none;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
}
</style>