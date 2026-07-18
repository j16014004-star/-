<template>
  <main class="auth-page">
    <section class="auth-window" aria-labelledby="login-title">
      <header class="auth-banner">
        <div class="banner-orb orb-one"></div>
        <div class="banner-orb orb-two"></div>
        <div class="brand-line">
          <img src="/hakimi-logo.png" alt="哈基米AI" class="brand-mark" />
          <div>
            <p class="brand-name">哈基米 AI 求职助手</p>
            <p class="brand-slogan">让每一次求职准备更有方向</p>
          </div>
        </div>
        <div class="banner-copy">
          <span class="banner-kicker">AI CAREER AGENT</span>
          <h1 id="login-title">欢迎回来</h1>
          <p>登录后继续管理简历、岗位推荐与面试计划</p>
        </div>
      </header>

      <div class="auth-content">
        <aside class="avatar-panel" aria-hidden="true">
          <div class="avatar-frame">
            <img src="/hakimi-logo.png" alt="" />
          </div>
          <span class="online-status"><i></i> AI 服务在线</span>
        </aside>

        <div class="form-panel">
          <el-form
            v-if="!twoFactorToken"
            ref="formRef"
            :model="form"
            :rules="rules"
            size="large"
            label-position="top"
            @keyup.enter="handleLogin"
          >
            <el-form-item label="账号" prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名 / 邮箱 / 手机号"
                :prefix-icon="User"
                autocomplete="username"
              />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                autocomplete="current-password"
                show-password
              />
            </el-form-item>

            <div class="form-options">
              <span class="secure-tip"><i></i> 安全加密登录</span>
              <router-link to="/register">注册账号</router-link>
            </div>

            <el-button type="primary" class="submit-button" :loading="loading" @click="handleLogin">
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form>

          <el-form v-else size="large" label-position="top" @keyup.enter="handleTwoFactorLogin">
            <div class="verify-heading">
              <h2>两步验证</h2>
              <p>请输入身份验证器动态码或恢复码</p>
            </div>
            <el-form-item label="验证码">
              <el-input
                v-model="twoFactorCode"
                maxlength="12"
                autocomplete="one-time-code"
                placeholder="6 位动态码或恢复码"
              />
            </el-form-item>
            <el-button type="primary" class="submit-button" :loading="loading" @click="handleTwoFactorLogin">
              验证并登录
            </el-button>
            <el-button class="back-button" @click="cancelTwoFactor">返回账号登录</el-button>
          </el-form>
        </div>
      </div>

      <footer class="auth-footer">
        <span>简历优化</span><i></i><span>岗位推荐</span><i></i><span>AI 面试</span><i></i><span>职业规划</span>
      </footer>
    </section>
    <p class="copyright">© 2026 哈基米AI · AI Career Agent</p>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock, User } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const twoFactorToken = ref('')
const twoFactorCode = ref('')

const form = reactive({ username: '', password: '' })

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 100, message: '账号长度为 2～100 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const response = await authApi.login({ username: form.username, password: form.password })
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
  ElMessage.success({ message: `欢迎回来，${form.username}！`, duration: 2000 })
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
    const response = await authApi.verifyTwoFactor({
      two_factor_token: twoFactorToken.value,
      code: twoFactorCode.value.trim(),
    })
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
.auth-page {
  min-height: 100vh;
  display: grid;
  place-content: center;
  padding: 32px 20px;
  background:
    radial-gradient(circle at 15% 18%, rgba(96, 165, 250, 0.25), transparent 28%),
    radial-gradient(circle at 88% 80%, rgba(129, 140, 248, 0.22), transparent 30%),
    linear-gradient(145deg, #eef6ff 0%, #f7f9fc 48%, #edf2ff 100%);
  color: #17233d;
}

.auth-window {
  width: min(760px, calc(100vw - 40px));
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.42);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 28px 80px rgba(30, 64, 175, 0.18), 0 4px 14px rgba(15, 23, 42, 0.08);
}

.auth-banner {
  position: relative;
  min-height: 225px;
  overflow: hidden;
  padding: 26px 38px 30px;
  color: #fff;
  background: linear-gradient(135deg, #075bb8 0%, #1688df 48%, #6bc6ee 100%);
}

.auth-banner::after {
  content: '';
  position: absolute;
  left: -8%;
  right: -8%;
  bottom: -68px;
  height: 112px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 -12px 40px rgba(255, 255, 255, 0.22);
}

.banner-orb { position: absolute; border-radius: 999px; background: rgba(255,255,255,.13); }
.orb-one { width: 210px; height: 210px; right: -55px; top: -80px; }
.orb-two { width: 100px; height: 100px; right: 155px; bottom: -34px; }
.brand-line { position: relative; z-index: 2; display: flex; align-items: center; gap: 12px; }
.brand-mark { width: 48px; height: 48px; border-radius: 14px; object-fit: cover; border: 2px solid rgba(255,255,255,.72); box-shadow: 0 8px 20px rgba(10,55,120,.24); }
.brand-name { margin: 0; font-size: 19px; font-weight: 800; letter-spacing: .04em; }
.brand-slogan { margin: 3px 0 0; color: rgba(255,255,255,.78); font-size: 12px; }
.banner-copy { position: relative; z-index: 2; margin-top: 8px; }
.banner-kicker { font-size: 11px; font-weight: 800; letter-spacing: .22em; color: #d9f2ff; }
.banner-copy h1 { margin: 5px 0 3px; font-size: 29px; letter-spacing: .08em; }
.banner-copy p { margin: 0; color: rgba(255,255,255,.84); font-size: 14px; }

.auth-content { display: grid; grid-template-columns: 180px 1fr; gap: 34px; padding: 26px 46px 32px; }
.avatar-panel { display: flex; flex-direction: column; align-items: center; justify-content: center; }
.avatar-frame { width: 126px; height: 126px; padding: 6px; border-radius: 20px; background: linear-gradient(145deg, #fff, #dbeafe); border: 1px solid #cbd5e1; box-shadow: 0 12px 28px rgba(15,23,42,.14); }
.avatar-frame img { width: 100%; height: 100%; border-radius: 15px; object-fit: cover; }
.online-status { margin-top: 14px; color: #64748b; font-size: 12px; }
.online-status i, .secure-tip i { display: inline-block; width: 8px; height: 8px; margin-right: 6px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px #dcfce7; }
.form-panel { min-width: 0; }
.form-options { display: flex; justify-content: space-between; align-items: center; margin: -2px 0 19px; font-size: 13px; }
.secure-tip { color: #64748b; }
.form-options a { color: #1680d8; text-decoration: none; }
.verify-heading h2 { margin: 0 0 4px; font-size: 22px; }
.verify-heading p { margin: 0 0 20px; color: #64748b; font-size: 13px; }
.submit-button { width: 100%; height: 44px; font-size: 15px; font-weight: 700; letter-spacing: .12em; border: 0; border-radius: 7px; background: linear-gradient(180deg, #4cb5ee 0%, #1687d5 100%); box-shadow: 0 7px 16px rgba(14,116,190,.25); }
.submit-button:hover { background: linear-gradient(180deg, #36a9e9 0%, #0876c3 100%); }
.back-button { width: 100%; margin: 10px 0 0; }
.auth-footer { display: flex; justify-content: center; align-items: center; gap: 13px; min-height: 49px; padding: 0 20px; color: #64748b; font-size: 12px; border-top: 1px solid #e5eaf1; background: #f7f9fc; }
.auth-footer i { width: 3px; height: 3px; border-radius: 50%; background: #94a3b8; }
.copyright { margin: 16px 0 0; text-align: center; color: #94a3b8; font-size: 12px; }

:deep(.el-form-item) { margin-bottom: 17px; }
:deep(.el-form-item__label) { height: 23px; padding: 0; color: #334155; font-size: 13px; font-weight: 700; }
:deep(.el-input__wrapper) { min-height: 42px; border-radius: 7px; background: #f8fafc; box-shadow: 0 0 0 1px #cbd5e1 inset; }
:deep(.el-input__wrapper:hover), :deep(.el-input__wrapper.is-focus) { background: #fff; box-shadow: 0 0 0 1px #1687d5 inset, 0 0 0 3px rgba(22,135,213,.1); }

@media (max-width: 640px) {
  .auth-page { align-content: start; padding: 18px 12px; }
  .auth-window { width: 100%; border-radius: 14px; }
  .auth-banner { min-height: 205px; padding: 22px 24px 28px; }
  .banner-copy h1 { font-size: 25px; }
  .auth-content { display: block; padding: 24px; }
  .avatar-panel { display: none; }
  .banner-copy p { display: none; }
  .auth-footer { flex-wrap: wrap; gap: 8px; padding: 12px; }
}
</style>
