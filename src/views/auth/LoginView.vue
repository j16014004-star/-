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
        <div class="brand-royal-stage mx-auto mb-8" aria-label="哈基米AI 网站标志">
          <div class="royal-glow"></div>
          <div class="crown">♛</div>
          <div class="cat cat-left">ฅ</div>
          <div class="cat cat-right">ฅ</div>
          <div class="cat cat-bottom-left">🐱</div>
          <div class="cat cat-bottom-right">🐱</div>
          <img class="brand-hero-logo" src="/hakimi-logo.png" alt="哈基米AI" />
        </div>
        <h1 class="text-5xl font-black text-white mb-5 tracking-wide">哈基米AI</h1>
        <p class="text-2xl font-bold text-blue-100 mb-3">全自动找工作一站式自动化服务</p>
        <p class="text-base text-blue-100 mb-9">做简历、投岗位、约面试、聊 HR、定职业规划，AI 全程帮你跑</p>
        <div class="feature-list space-y-4 text-left text-blue-50 max-w-lg mx-auto">
          <div class="feature-item">
            <span class="feature-badge">简历</span>
            <span>AI 做简历、优化简历，突出你的岗位竞争力</span>
          </div>
          <div class="feature-item">
            <span class="feature-badge">投递</span>
            <span>AI 帮你筛岗位、匹配岗位，并自动投递简历</span>
          </div>
          <div class="feature-item">
            <span class="feature-badge">面试</span>
            <span>AI 帮你约面试、做面试训练，提前准备高频问题</span>
          </div>
          <div class="feature-item">
            <span class="feature-badge">HR</span>
            <span>AI 辅助和 HR 沟通，跟进进度、表达意向、争取机会</span>
          </div>
          <div class="feature-item">
            <span class="feature-badge">规划</span>
            <span>AI 定职业规划，帮你找到长期发展路线</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Right login form panel -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
      <div class="w-full max-w-md">
        <div class="text-center mb-8 lg:hidden">
          <img class="brand-mobile-logo mx-auto mb-3" src="/hakimi-logo.png" alt="哈基米AI" />
          <h1 class="text-2xl font-bold text-gray-800">哈基米AI</h1>
          <p class="text-gray-500">全自动找工作一站式自动化服务</p>
        </div>

        <el-card class="w-full shadow-xl border-0" body-style="padding: 40px">
          <h2 class="text-2xl font-bold text-gray-800 mb-2">{{ twoFactorToken ? '两步验证' : '欢迎回来' }}</h2>
          <p class="text-gray-500 mb-8">{{ twoFactorToken ? '请输入身份验证器动态码或恢复码' : '登录您的账号以继续' }}</p>

          <el-form
            v-if="!twoFactorToken"
            ref="formRef"
            :model="form"
            :rules="rules"
            size="large"
            label-position="top"
            @keyup.enter="handleLogin"
          >
            <el-form-item label="用户名 / 邮箱 / 手机号" prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名、邮箱或手机号"
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

          <el-form v-else size="large" label-position="top" @keyup.enter="handleTwoFactorLogin">
            <el-form-item label="验证码">
              <el-input v-model="twoFactorCode" maxlength="12" autocomplete="one-time-code" placeholder="6 位动态码或恢复码" />
            </el-form-item>
            <el-button type="primary" class="w-full" :loading="loading" @click="handleTwoFactorLogin">验证并登录</el-button>
            <el-button class="w-full mt-3" @click="cancelTwoFactor">返回账号登录</el-button>
          </el-form>

          <div class="text-center mt-6">
            <span class="text-gray-500">还没有账号？</span>
            <router-link to="/register" class="text-blue-600 hover:text-blue-700 font-medium ml-1">
              立即注册
            </router-link>
          </div>
        </el-card>

        <p class="text-center text-gray-400 text-sm mt-8">
          &copy; 2026 哈基米AI. All rights reserved.
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
const twoFactorToken = ref('')
const twoFactorCode = ref('')

const form = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 100, message: '账号长度在 2～100 个字符', trigger: 'blur' }
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

    if ('requires_two_factor' in response.data) {
      twoFactorToken.value = response.data.two_factor_token
      twoFactorCode.value = ''
      return
    }

    completeLogin(response.data)
  } catch (error: any) {
    handleLoginError(error)
  } finally {
    loading.value = false
  }
}

const completeLogin = (data: import('@/api/types/auth').AuthenticatedLoginResponse) => {
    storage.set(TOKEN_KEY, data.access_token)
    storage.set('refresh_token', data.refresh_token)
    storage.set('token_type', data.token_type)
    storage.set('expires_in', data.expires_in)
    storage.set('token_expires_at', Date.now() + data.expires_in * 1000)
    storage.set(USER_KEY, data.user)

    ElMessage.success({
      message: `欢迎回来，${form.username}！`,
      duration: 2000
    })

    router.push('/')
}

const handleLoginError = (error: any) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message

    switch (status) {
      case 401:
        ElMessage.error(twoFactorToken.value ? '动态验证码或恢复码错误' : '用户名或密码错误')
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
}

const handleTwoFactorLogin = async () => {
  if (!twoFactorCode.value.trim()) return ElMessage.warning('请输入验证码')
  loading.value = true
  try {
    const response = await authApi.verifyTwoFactor({ two_factor_token: twoFactorToken.value, code: twoFactorCode.value.trim() })
    completeLogin(response.data)
  } catch (error: any) {
    handleLoginError(error)
  } finally {
    loading.value = false
  }
}

const cancelTwoFactor = () => {
  twoFactorToken.value = ''
  twoFactorCode.value = ''
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
}

.login-left {
  min-height: 100vh;
}

.brand-royal-stage {
  position: relative;
  width: 278px;
  height: 218px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.royal-glow {
  position: absolute;
  width: 220px;
  height: 220px;
  border-radius: 999px;
  background:
    radial-gradient(circle, rgba(255, 244, 179, 0.95) 0%, rgba(250, 204, 21, 0.36) 34%, rgba(129, 140, 248, 0) 70%);
  filter: blur(2px);
  animation: royalPulse 3s ease-in-out infinite;
}

.brand-hero-logo {
  position: relative;
  z-index: 3;
  width: 176px;
  height: 176px;
  border: 4px solid rgba(255, 255, 255, 0.72);
  border-radius: 42px;
  object-fit: cover;
  box-shadow:
    0 30px 70px rgba(15, 23, 42, 0.42),
    0 0 0 10px rgba(255, 255, 255, 0.12),
    0 0 46px rgba(250, 204, 21, 0.34);
}

.crown {
  position: absolute;
  top: -18px;
  z-index: 4;
  color: #fde68a;
  font-size: 64px;
  line-height: 1;
  text-shadow:
    0 8px 18px rgba(15, 23, 42, 0.34),
    0 0 18px rgba(253, 230, 138, 0.65);
}

.cat {
  position: absolute;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 54px;
  border: 1px solid rgba(255, 255, 255, 0.32);
  border-radius: 18px;
  color: #fff7ed;
  font-size: 34px;
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(10px);
}

.cat-left {
  left: 0;
  top: 82px;
  transform: rotate(18deg);
}

.cat-right {
  right: 0;
  top: 82px;
  transform: scaleX(-1) rotate(18deg);
}

.cat-bottom-left {
  left: 22px;
  bottom: 2px;
  z-index: 5;
  width: 66px;
  height: 66px;
  font-size: 40px;
  transform: rotate(-10deg);
}

.cat-bottom-right {
  right: 22px;
  bottom: 2px;
  z-index: 5;
  width: 66px;
  height: 66px;
  font-size: 40px;
  transform: rotate(10deg);
}

@keyframes royalPulse {
  0%, 100% {
    transform: scale(0.96);
    opacity: 0.78;
  }
  50% {
    transform: scale(1.05);
    opacity: 1;
  }
}

.brand-mobile-logo {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  object-fit: cover;
}

.feature-list {
  font-size: 17px;
  font-weight: 650;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
}

.feature-badge {
  display: inline-flex;
  min-width: 46px;
  height: 30px;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  color: #ffffff;
  font-size: 14px;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.14);
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
