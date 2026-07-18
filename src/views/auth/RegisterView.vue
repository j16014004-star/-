<template>
  <main class="auth-page">
    <section class="auth-window" aria-labelledby="register-title">
      <header class="auth-banner">
        <div class="banner-orb orb-one"></div>
        <div class="banner-orb orb-two"></div>
        <div class="brand-line">
          <img src="/hakimi-logo.png" alt="哈基米AI" class="brand-mark" />
          <div>
            <p class="brand-name">哈基米 AI 求职助手</p>
            <p class="brand-slogan">创建你的智能求职工作台</p>
          </div>
        </div>
        <div class="banner-copy">
          <span class="banner-kicker">JOIN AI CAREER AGENT</span>
          <h1 id="register-title">注册新账号</h1>
          <p>填写基础信息，即刻开始你的 AI 求职旅程</p>
        </div>
      </header>

      <div class="auth-content register-content">
        <aside class="avatar-panel" aria-hidden="true">
          <div class="avatar-frame"><img src="/hakimi-logo.png" alt="" /></div>
          <p>一个账号，连接自动化求职全流程</p>
          <div class="feature-tags"><span>筛选岗位</span><span>自动投递</span><span>联系 HR</span><span>面试邀约</span></div>
        </aside>

        <div class="form-panel">
          <el-form ref="formRef" :model="form" :rules="rules" size="large" label-position="top" @keyup.enter="handleRegister">
            <div class="field-grid">
              <el-form-item label="用户名" prop="username">
                <el-input v-model="form.username" placeholder="2～20 个字符" :prefix-icon="User" autocomplete="username" />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="form.email" placeholder="请输入邮箱地址" :prefix-icon="Message" autocomplete="email" />
              </el-form-item>
              <el-form-item label="密码" prop="password">
                <el-input v-model="form.password" type="password" placeholder="至少 6 个字符" :prefix-icon="Lock" autocomplete="new-password" show-password />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" :prefix-icon="Lock" autocomplete="new-password" show-password />
              </el-form-item>
            </div>

            <div class="form-options">
              <span class="secure-tip"><i></i> 信息将被安全加密</span>
              <router-link to="/login">已有账号？去登录</router-link>
            </div>

            <el-button type="primary" class="submit-button" :loading="loading" @click="handleRegister">
              {{ loading ? '注册中...' : '注 册' }}
            </el-button>
          </el-form>
        </div>
      </div>

      <footer class="auth-footer">智能筛选岗位 · 自动投递简历 · AI 联系 HR · 跟进面试邀约</footer>
    </section>
    <p class="copyright">© 2026 哈基米AI · AI Career Agent</p>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Lock, Message, User } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({ username: '', email: '', password: '', confirmPassword: '' })

const validatePass = (_rule: any, value: string, callback: any) => {
  if (value === '') callback(new Error('请再次输入密码'))
  else if (value !== form.password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度为 2～20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authApi.register({ username: form.username, email: form.email, password: form.password })
    ElMessage.success({ message: '注册成功！请登录你的账号', duration: 2000 })
    router.push('/login')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || error.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page { min-height: 100vh; display: grid; place-content: center; padding: 30px 20px; background: radial-gradient(circle at 15% 18%, rgba(96,165,250,.25), transparent 28%), radial-gradient(circle at 88% 80%, rgba(45,212,191,.18), transparent 30%), linear-gradient(145deg, #eef6ff 0%, #f7f9fc 48%, #ecf8f8 100%); color: #17233d; }
.auth-window { width: min(820px, calc(100vw - 40px)); overflow: hidden; border: 1px solid rgba(148,163,184,.42); border-radius: 18px; background: rgba(255,255,255,.97); box-shadow: 0 28px 80px rgba(13,100,140,.17), 0 4px 14px rgba(15,23,42,.08); }
.auth-banner { position: relative; min-height: 205px; overflow: hidden; padding: 25px 38px 28px; color: #fff; background: linear-gradient(135deg, #075bb8 0%, #1688df 48%, #4dbfbf 100%); }
.auth-banner::after { content: ''; position: absolute; left: -8%; right: -8%; bottom: -68px; height: 112px; border-radius: 50%; background: rgba(255,255,255,.94); box-shadow: 0 -12px 40px rgba(255,255,255,.22); }
.banner-orb { position: absolute; border-radius: 999px; background: rgba(255,255,255,.13); }
.orb-one { width: 210px; height: 210px; right: -55px; top: -80px; }
.orb-two { width: 100px; height: 100px; right: 155px; bottom: -34px; }
.brand-line { position: relative; z-index: 2; display: flex; align-items: center; gap: 12px; }
.brand-mark { width: 48px; height: 48px; border-radius: 14px; object-fit: cover; border: 2px solid rgba(255,255,255,.72); box-shadow: 0 8px 20px rgba(10,55,120,.24); }
.brand-name { margin: 0; font-size: 19px; font-weight: 800; letter-spacing: .04em; }
.brand-slogan { margin: 3px 0 0; color: rgba(255,255,255,.78); font-size: 12px; }
.banner-copy { position: relative; z-index: 2; margin-top: 8px; }
.banner-kicker { font-size: 11px; font-weight: 800; letter-spacing: .22em; color: #d9f2ff; }
.banner-copy h1 { margin: 5px 0 3px; font-size: 27px; letter-spacing: .06em; }
.banner-copy p { margin: 0; color: rgba(255,255,255,.84); font-size: 14px; }
.auth-content { display: grid; grid-template-columns: 190px 1fr; gap: 34px; padding: 24px 42px 29px; }
.avatar-panel { display: flex; flex-direction: column; align-items: center; justify-content: center; }
.avatar-frame { width: 112px; height: 112px; padding: 6px; border-radius: 20px; background: linear-gradient(145deg,#fff,#dbeafe); border: 1px solid #cbd5e1; box-shadow: 0 12px 28px rgba(15,23,42,.14); }
.avatar-frame img { width: 100%; height: 100%; border-radius: 15px; object-fit: cover; }
.avatar-panel p { margin: 12px 0 10px; color: #64748b; font-size: 12px; text-align: center; }
.feature-tags { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; }
.feature-tags span { padding: 3px 7px; color: #1477b8; font-size: 11px; border: 1px solid #bae6fd; border-radius: 5px; background: #f0f9ff; }
.form-panel { min-width: 0; }
.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 14px; }
.form-options { display: flex; justify-content: space-between; align-items: center; margin: -2px 0 16px; font-size: 13px; }
.secure-tip { color: #64748b; }
.secure-tip i { display: inline-block; width: 8px; height: 8px; margin-right: 6px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 3px #dcfce7; }
.form-options a { color: #1680d8; text-decoration: none; }
.submit-button { width: 100%; height: 44px; font-size: 15px; font-weight: 700; letter-spacing: .12em; border: 0; border-radius: 7px; background: linear-gradient(180deg,#4cb5ee 0%,#1687d5 100%); box-shadow: 0 7px 16px rgba(14,116,190,.25); }
.submit-button:hover { background: linear-gradient(180deg,#36a9e9 0%,#0876c3 100%); }
.auth-footer { display: flex; justify-content: center; align-items: center; min-height: 48px; padding: 0 20px; color: #64748b; font-size: 12px; border-top: 1px solid #e5eaf1; background: #f7f9fc; }
.copyright { margin: 14px 0 0; text-align: center; color: #94a3b8; font-size: 12px; }
:deep(.el-form-item) { margin-bottom: 15px; }
:deep(.el-form-item__label) { height: 23px; padding: 0; color: #334155; font-size: 13px; font-weight: 700; }
:deep(.el-input__wrapper) { min-height: 40px; border-radius: 7px; background: #f8fafc; box-shadow: 0 0 0 1px #cbd5e1 inset; }
:deep(.el-input__wrapper:hover), :deep(.el-input__wrapper.is-focus) { background: #fff; box-shadow: 0 0 0 1px #1687d5 inset, 0 0 0 3px rgba(22,135,213,.1); }
@media (max-width: 700px) { .auth-page { align-content: start; padding: 18px 12px; } .auth-window { width: 100%; border-radius: 14px; } .auth-banner { min-height: 195px; padding: 22px 24px 27px; } .auth-content { display: block; padding: 24px; } .avatar-panel { display: none; } .field-grid { grid-template-columns: 1fr; } .banner-copy p { display: none; } }
</style>
