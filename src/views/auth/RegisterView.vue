<template>
  <div class="register-page min-h-screen flex">
    <!-- Left decorative panel -->
    <div class="register-left hidden lg:flex lg:w-1/2 relative overflow-hidden items-center justify-center">
      <div class="absolute inset-0 bg-gradient-to-br from-emerald-600 via-teal-700 to-cyan-800"></div>
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-10 right-10 w-72 h-72 bg-white rounded-full blur-3xl"></div>
        <div class="absolute bottom-20 left-20 w-96 h-96 bg-emerald-300 rounded-full blur-3xl"></div>
      </div>
      <div class="relative z-10 text-center px-12">
        <div class="text-6xl mb-6">&#x1F680;</div>
        <h1 class="text-4xl font-bold text-white mb-4">开启你的职业之旅</h1>
        <p class="text-xl text-emerald-200 mb-8">注册即享AI智能职业服务</p>
        <div class="grid grid-cols-2 gap-4 max-w-md mx-auto">
          <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center">
            <div class="text-2xl mb-1">&#x1F4C4;</div>
            <div class="text-white font-medium">简历分析</div>
          </div>
          <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center">
            <div class="text-2xl mb-1">&#x1F3AF;</div>
            <div class="text-white font-medium">岗位匹配</div>
          </div>
          <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center">
            <div class="text-2xl mb-1">&#x1F4AC;</div>
            <div class="text-white font-medium">面试训练</div>
          </div>
          <div class="bg-white/10 backdrop-blur-sm rounded-xl p-4 text-center">
            <div class="text-2xl mb-1">&#x1F9D1;&#x200D;&#x1F4BB;</div>
            <div class="text-white font-medium">职业规划</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right register form panel -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
      <div class="w-full max-w-md">
        <div class="text-center mb-8 lg:hidden">
          <div class="text-4xl mb-2">&#x1F680;</div>
          <h1 class="text-2xl font-bold text-gray-800">AI Career Agent</h1>
          <p class="text-gray-500">创建您的账号</p>
        </div>

        <el-card class="w-full shadow-xl border-0" body-style="padding: 40px">
          <h2 class="text-2xl font-bold text-gray-800 mb-2">创建账号</h2>
          <p class="text-gray-500 mb-8">填写以下信息完成注册</p>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            size="large"
            label-position="top"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="form.email"
                placeholder="请输入邮箱地址"
                :prefix-icon="Message"
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

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
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
                @click="handleRegister"
              >
                {{ loading ? '注册中...' : '注册' }}
              </el-button>
            </el-form-item>
          </el-form>

          <div class="text-center mt-6">
            <span class="text-gray-500">已有账号？</span>
            <router-link to="/login" class="text-blue-600 hover:text-blue-700 font-medium ml-1">
              立即登录
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
import { User, Message, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validatePass = (_rule: any, value: string, callback: any) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在2-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true

  // Simulate API call
  setTimeout(() => {
    ElMessage.success({
      message: '注册成功！请登录您的账号',
      duration: 2000
    })

    loading.value = false
    router.push('/login')
  }, 1500)
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
}

.register-left {
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
  box-shadow: 0 0 0 1px #10b981 inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #10b981 inset;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #10b981, #14b8a6);
  border: none;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #059669, #0d9488);
}
</style>