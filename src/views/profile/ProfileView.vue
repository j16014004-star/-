<template>
  <div class="profile-view min-h-screen bg-gray-50 p-6 dark:bg-gray-900">
    <div class="mx-auto max-w-4xl" v-loading="initialLoading">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-gray-100">个人中心</h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">管理你的账户资料、安全设置和通知偏好</p>
      </div>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header>
          <div class="flex items-center gap-4">
            <el-upload
              class="avatar-uploader"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :http-request="handleAvatarUpload"
              :disabled="avatarUploading"
              accept="image/jpeg,image/png"
            >
              <el-avatar
                :size="72"
                :src="avatarDisplayUrl || undefined"
                class="cursor-pointer bg-indigo-100 text-2xl font-bold text-indigo-600 transition-opacity hover:opacity-80"
              >
                <span>{{ userInfo.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
              </el-avatar>
              <div class="avatar-overlay">
                <el-icon v-if="!avatarUploading" class="text-white"><Camera /></el-icon>
                <el-icon v-else class="is-loading text-white"><Loading /></el-icon>
              </div>
            </el-upload>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 class="text-xl font-bold text-gray-800 dark:text-gray-100">{{ userInfo.username || '用户' }}</h2>
                  <div class="mt-1 flex flex-wrap items-center gap-2">
                    <span class="text-sm text-gray-500 dark:text-gray-400">{{ userInfo.email }}</span>
                    <el-tag size="small" type="info">邮箱验证暂未开放</el-tag>
                  </div>
                </div>
                <el-button
                  v-if="userInfo.avatar"
                  text
                  type="danger"
                  size="small"
                  :loading="avatarRemoving"
                  @click="removeAvatar"
                >移除头像</el-button>
              </div>
              <p class="mt-2 text-xs text-gray-400">点击头像上传 JPG 或 PNG，最大 2MB</p>
              <el-progress v-if="avatarUploading" class="mt-2 max-w-xs" :percentage="avatarProgress" :stroke-width="6" />
            </div>
          </div>
        </template>

        <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-position="top">
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <el-form-item label="用户名" prop="username">
                <el-input v-model="profileForm.username" maxlength="50" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="邮箱" prop="email">
                <el-input :model-value="userInfo.email" disabled>
                  <template #append>暂不支持修改</template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :xs="24" :md="12">
              <el-form-item label="手机号" prop="phone">
                <el-input :model-value="userInfo.phone || '未绑定'" disabled>
                  <template #append>暂不支持修改</template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="注册时间">
                <el-input :model-value="formatDate(userInfo.created_at)" disabled />
              </el-form-item>
            </el-col>
          </el-row>
          <div class="flex justify-end gap-3">
            <el-button :disabled="profileSaving" @click="resetProfile">重置</el-button>
            <el-button type="primary" :loading="profileSaving" @click="saveProfile">保存修改</el-button>
          </div>
        </el-form>
      </el-card>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header><span class="font-semibold">账户安全</span></template>
        <div class="space-y-4">
          <div class="setting-row">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">修改密码</div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">修改成功后将撤销其他设备登录状态</div>
            </div>
            <el-button type="primary" plain size="small" @click="showPasswordDialog = true">修改密码</el-button>
          </div>
          <div class="setting-row">
            <div>
              <div class="flex items-center gap-2 font-medium text-gray-800 dark:text-gray-200">
                两步验证
                <el-tag :type="userInfo.two_factor_enabled ? 'success' : 'info'" size="small">
                  {{ userInfo.two_factor_enabled ? '已启用' : '未启用' }}
                </el-tag>
              </div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">登录时使用身份验证器动态验证码</div>
            </div>
            <el-switch
              :model-value="userInfo.two_factor_enabled"
              :loading="twoFactorLoading"
              @change="handleTwoFactorToggle"
            />
          </div>
          <div class="setting-row">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">登录记录</div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">查看最近登录设备、IP 和登录结果</div>
            </div>
            <el-button text type="primary" @click="openLoginHistory">查看记录</el-button>
          </div>
        </div>
      </el-card>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header><span class="font-semibold">通知设置</span></template>
        <div class="space-y-4">
          <div v-for="item in preferenceItems" :key="item.key" class="setting-row">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">{{ item.title }}</div>
              <div class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ item.description }}</div>
            </div>
            <el-switch
              :model-value="preferences[item.key]"
              :loading="preferenceSavingKey === item.key"
              @change="handlePreferenceChange(item.key, $event)"
            />
          </div>
        </div>
      </el-card>

      <el-card class="mb-6 border-0" shadow="never">
        <template #header><span class="font-semibold">外观设置</span></template>
        <el-form-item label="主题模式">
          <el-radio-group :model-value="appStore.theme" @change="handleThemeChange">
            <el-radio-button value="light"><el-icon class="mr-1"><Sunny /></el-icon>浅色</el-radio-button>
            <el-radio-button value="dark"><el-icon class="mr-1"><Moon /></el-icon>深色</el-radio-button>
            <el-radio-button value="auto"><el-icon class="mr-1"><Monitor /></el-icon>跟随系统</el-radio-button>
          </el-radio-group>
          <span class="ml-4 text-sm text-gray-400">{{ currentThemeLabel }}</span>
        </el-form-item>
        <el-form-item label="侧边栏默认展开">
          <el-switch :model-value="!appStore.sidebarCollapsed" @change="handleSidebarChange" />
        </el-form-item>
        <div class="text-xs text-gray-400">外观设置仅保存在当前浏览器，不上传服务器。</div>
      </el-card>

      <el-card class="border-0 border-l-4 border-l-red-400" shadow="never">
        <template #header><span class="font-semibold text-red-500">危险区域</span></template>
        <div class="space-y-3">
          <div class="flex items-center justify-between gap-4">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">退出登录</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">退出当前账户并清除本地登录状态</div>
            </div>
            <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
          </div>
          <div class="flex items-center justify-between gap-4 border-t border-gray-100 pt-3 dark:border-gray-700">
            <div>
              <div class="font-medium text-red-500">删除账户</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">永久删除账户及关联数据，操作无法恢复</div>
            </div>
            <el-button type="danger" size="small" @click="showDeleteDialog = true">删除账户</el-button>
          </div>
        </div>
      </el-card>

      <el-dialog v-model="showPasswordDialog" title="修改密码" width="min(460px, 92vw)" destroy-on-close>
        <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-position="top">
          <el-form-item label="当前密码" prop="currentPassword">
            <el-input v-model="passwordForm.currentPassword" type="password" show-password autocomplete="current-password" />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input v-model="passwordForm.newPassword" type="password" show-password autocomplete="new-password" />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input v-model="passwordForm.confirmPassword" type="password" show-password autocomplete="new-password" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button :disabled="passwordSaving" @click="showPasswordDialog = false">取消</el-button>
          <el-button type="primary" :loading="passwordSaving" @click="handleChangePassword">确认修改</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showTwoFactorSetupDialog" title="启用两步验证" width="min(520px, 92vw)" :close-on-click-modal="false">
        <div v-if="twoFactorSetup" class="text-center">
          <p class="mb-4 text-sm leading-6 text-gray-600">使用身份验证器扫描二维码，然后输入应用生成的 6 位验证码。</p>
          <img :src="twoFactorSetup.qr_code_data_url" alt="两步验证二维码" class="mx-auto h-44 w-44 rounded-lg border bg-white p-2" />
          <div class="mx-auto mt-4 max-w-sm rounded-lg bg-gray-50 p-3 text-left">
            <div class="text-xs text-gray-400">无法扫码时手动输入密钥</div>
            <div class="mt-1 flex items-center justify-between gap-2">
              <code class="break-all text-sm text-gray-700">{{ twoFactorSetup.secret }}</code>
              <el-button text type="primary" @click="copyText(twoFactorSetup.secret)">复制</el-button>
            </div>
          </div>
          <el-input v-model="twoFactorCode" maxlength="6" class="mx-auto mt-4 max-w-xs" placeholder="请输入 6 位验证码" />
        </div>
        <template #footer>
          <el-button :disabled="twoFactorLoading" @click="cancelTwoFactorSetup">取消</el-button>
          <el-button type="primary" :loading="twoFactorLoading" @click="confirmEnableTwoFactor">验证并启用</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showRecoveryCodesDialog" title="请保存恢复码" width="min(520px, 92vw)" :close-on-click-modal="false" :show-close="false">
        <el-alert title="每个恢复码只能使用一次。请立即保存到安全位置，关闭后不再完整展示。" type="warning" :closable="false" show-icon />
        <div class="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-gray-50 p-4 font-mono text-sm">
          <span v-for="code in recoveryCodes" :key="code">{{ code }}</span>
        </div>
        <template #footer>
          <el-button @click="copyText(recoveryCodes.join('\n'))">复制全部</el-button>
          <el-button type="primary" @click="showRecoveryCodesDialog = false">我已安全保存</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showTwoFactorDisableDialog" title="关闭两步验证" width="min(460px, 92vw)" destroy-on-close>
        <el-alert title="关闭后账户安全性会降低，请输入密码确认。" type="warning" :closable="false" class="mb-4" />
        <el-input v-model="disableTwoFactorForm.password" type="password" show-password placeholder="当前密码" />
        <el-input v-model="disableTwoFactorForm.code" maxlength="6" class="mt-3" placeholder="身份验证器验证码（后端可按安全策略要求）" />
        <template #footer>
          <el-button :disabled="twoFactorLoading" @click="showTwoFactorDisableDialog = false">取消</el-button>
          <el-button type="danger" :loading="twoFactorLoading" @click="confirmDisableTwoFactor">确认关闭</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="showLoginHistory" title="登录记录" width="min(820px, 94vw)">
        <el-table v-loading="loginLogsLoading" :data="loginLogs" size="small" empty-text="暂无登录记录">
          <el-table-column label="时间" min-width="170"><template #default="{ row }">{{ formatDate(row.login_time) }}</template></el-table-column>
          <el-table-column label="设备" min-width="180"><template #default="{ row }">{{ formatDevice(row) }}</template></el-table-column>
          <el-table-column prop="ip_address" label="IP 地址" min-width="135" />
          <el-table-column prop="location" label="位置" min-width="110" />
          <el-table-column label="状态" width="90"><template #default="{ row }"><el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">{{ row.status === 'success' ? '成功' : '失败' }}</el-tag></template></el-table-column>
        </el-table>
        <div class="mt-4 flex justify-end">
          <el-pagination
            v-model:current-page="loginLogsPage"
            :page-size="loginLogsPageSize"
            :total="loginLogsTotal"
            layout="prev, pager, next, total"
            @current-change="loadLoginLogs"
          />
        </div>
      </el-dialog>

      <el-dialog v-model="showDeleteDialog" title="永久删除账户" width="min(480px, 92vw)" destroy-on-close>
        <el-alert title="此操作无法恢复，账户、简历、规划、打卡和其他关联数据将被删除。" type="error" :closable="false" show-icon class="mb-4" />
        <el-input v-model="deleteForm.password" type="password" show-password placeholder="请输入当前密码" />
        <el-input v-model="deleteForm.confirmation" class="mt-3" placeholder="请输入“确认删除”" />
        <el-input v-if="userInfo.two_factor_enabled" v-model="deleteForm.code" class="mt-3" placeholder="请输入动态验证码或恢复码" />
        <template #footer>
          <el-button :disabled="accountDeleting" @click="showDeleteDialog = false">取消</el-button>
          <el-button
            type="danger"
            :loading="accountDeleting"
            :disabled="deleteForm.confirmation !== '确认删除' || !deleteForm.password || (userInfo.two_factor_enabled && !deleteForm.code)"
            @click="handleDeleteAccount"
          >永久删除</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Camera, Loading, Monitor, Moon, Sunny } from '@element-plus/icons-vue'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
  type UploadRequestOptions,
} from 'element-plus'
import { authApi } from '@/api/auth'
import { profileApi } from '@/api/profile'
import type {
  LoginLogItem,
  ProfileInfo,
  ProfilePreferences,
  ProfileUpdateParams,
  TwoFactorSetupResult,
} from '@/api/types/profile'
import { useAppStore } from '@/stores/app'
import { storage, TOKEN_KEY, USER_KEY } from '@/utils/storage'
import { resolveMediaUrl, withCacheVersion } from '@/utils/media'

const router = useRouter()
const appStore = useAppStore()
const initialLoading = ref(false)
const profileSaving = ref(false)
const avatarUploading = ref(false)
const avatarRemoving = ref(false)
const avatarProgress = ref(0)
const avatarVersion = ref(0)
const passwordSaving = ref(false)
const twoFactorLoading = ref(false)
const preferenceSavingKey = ref<keyof ProfilePreferences | null>(null)
const accountDeleting = ref(false)

const emptyProfile = (): ProfileInfo => ({
  id: 0,
  username: '',
  email: '',
  phone: '',
  avatar: null,
  status: 'active',
  email_verified: false,
  phone_verified: false,
  two_factor_enabled: false,
  created_at: '',
  last_login_at: null,
})

const userInfo = reactive<ProfileInfo>(emptyProfile())
const originalProfile = ref<ProfileInfo | null>(null)
const profileForm = reactive<ProfileUpdateParams>({ username: '' })
const profileFormRef = ref<FormInstance>()

const profileRules: FormRules<ProfileUpdateParams> = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度为 2～50 个字符', trigger: 'blur' },
  ],
}

const preferences = reactive<ProfilePreferences>({
  email_notifications: true,
  push_notifications: true,
  ai_report_notifications: true,
})

const preferenceItems: Array<{ key: keyof ProfilePreferences; title: string; description: string }> = [
  { key: 'email_notifications', title: '邮件通知', description: '接收岗位匹配、面试提醒等邮件通知' },
  { key: 'push_notifications', title: '消息推送', description: '接收 HR 消息和系统消息实时推送' },
  { key: 'ai_report_notifications', title: 'AI 报告推送', description: '简历优化、职业规划和阶段考核完成后通知' },
]

const showPasswordDialog = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({ currentPassword: '', newPassword: '', confirmPassword: '' })
const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value !== passwordForm.newPassword) callback(new Error('两次输入的新密码不一致'))
  else callback()
}
const passwordRules: FormRules = {
  currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 64, message: '新密码长度为 8～64 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

const showTwoFactorSetupDialog = ref(false)
const showTwoFactorDisableDialog = ref(false)
const showRecoveryCodesDialog = ref(false)
const twoFactorSetup = ref<TwoFactorSetupResult | null>(null)
const twoFactorCode = ref('')
const recoveryCodes = ref<string[]>([])
const disableTwoFactorForm = reactive({ password: '', code: '' })

const showLoginHistory = ref(false)
const loginLogsLoading = ref(false)
const loginLogs = ref<LoginLogItem[]>([])
const loginLogsPage = ref(1)
const loginLogsPageSize = 20
const loginLogsTotal = ref(0)

const showDeleteDialog = ref(false)
const deleteForm = reactive({ password: '', confirmation: '', code: '' })

const currentThemeLabel = computed(() => ({
  light: '当前：浅色模式', dark: '当前：深色模式', auto: '当前：跟随系统主题',
})[appStore.theme])

const avatarDisplayUrl = computed(() =>
  withCacheVersion(resolveMediaUrl(userInfo.avatar), avatarVersion.value),
)

const loadPage = async () => {
  initialLoading.value = true
  try {
    const [profileResult, preferencesResult] = await Promise.allSettled([
      profileApi.getProfile(),
      profileApi.getPreferences(),
    ])
    if (profileResult.status === 'fulfilled') applyProfile(profileResult.value.data)
    else loadProfileFallback()
    if (preferencesResult.status === 'fulfilled') Object.assign(preferences, preferencesResult.value.data)
  } finally {
    initialLoading.value = false
  }
}

const applyProfile = (profile: ProfileInfo) => {
  const normalizedProfile = {
    ...profile,
    avatar: resolveMediaUrl(profile.avatar) || null,
  }
  Object.assign(userInfo, normalizedProfile)
  originalProfile.value = { ...normalizedProfile }
  profileForm.username = profile.username || ''
  appStore.user.name = profile.username || '用户'
  appStore.setAvatar(normalizedProfile.avatar || '')
  const stored = storage.get<Record<string, unknown>>(USER_KEY) || {}
  storage.set(USER_KEY, { ...stored, ...normalizedProfile })
}

const loadProfileFallback = () => {
  const stored = storage.get<Partial<ProfileInfo>>(USER_KEY)
  if (!stored) return
  applyProfile({ ...emptyProfile(), ...stored } as ProfileInfo)
  ElMessage.warning('用户资料接口暂时不可用，当前显示本地缓存')
}

const saveProfile = async () => {
  if (!profileFormRef.value || profileSaving.value) return
  const valid = await profileFormRef.value.validate().catch(() => false)
  if (!valid) return
  profileSaving.value = true
  try {
    const payload: ProfileUpdateParams = {
      username: profileForm.username.trim(),
    }
    const response = await profileApi.updateProfile(payload)
    applyProfile(response.data)
    ElMessage.success('个人资料已保存')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '保存个人资料失败'))
  } finally {
    profileSaving.value = false
  }
}

const resetProfile = () => {
  if (!originalProfile.value) return
  profileForm.username = originalProfile.value.username
  profileFormRef.value?.clearValidate()
}

const beforeAvatarUpload = (file: File) => {
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    ElMessage.error('头像只支持 JPG 或 PNG 格式')
    return false
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像大小不能超过 2MB')
    return false
  }
  return true
}

const handleAvatarUpload = async (options: UploadRequestOptions) => {
  avatarUploading.value = true
  avatarProgress.value = 0
  try {
    const response = await profileApi.uploadAvatar(options.file, (value) => { avatarProgress.value = value })
    const avatarUrl = resolveMediaUrl(response.data.avatar_url)
    userInfo.avatar = avatarUrl
    originalProfile.value = originalProfile.value ? { ...originalProfile.value, avatar: avatarUrl } : null
    appStore.setAvatar(avatarUrl)
    avatarVersion.value = Date.now()
    avatarProgress.value = 100
    options.onSuccess(response.data)
    ElMessage.success('头像上传成功')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '头像上传失败'))
  } finally {
    avatarUploading.value = false
  }
}

const removeAvatar = async () => {
  try {
    await ElMessageBox.confirm('确定移除当前头像吗？', '移除头像', { type: 'warning', confirmButtonText: '移除', cancelButtonText: '取消' })
    avatarRemoving.value = true
    await profileApi.removeAvatar()
    userInfo.avatar = null
    originalProfile.value = originalProfile.value ? { ...originalProfile.value, avatar: null } : null
    appStore.setAvatar('')
    ElMessage.success('头像已移除')
  } catch (error: unknown) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(getErrorMessage(error, '移除头像失败'))
  } finally {
    avatarRemoving.value = false
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value || passwordSaving.value) return
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return
  passwordSaving.value = true
  try {
    await profileApi.changePassword({
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword,
    })
    showPasswordDialog.value = false
    Object.assign(passwordForm, { currentPassword: '', newPassword: '', confirmPassword: '' })
    clearLocalSession()
    ElMessage.success('密码修改成功，请重新登录')
    await router.replace('/login')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '修改密码失败'))
  } finally {
    passwordSaving.value = false
  }
}

const handleTwoFactorToggle = async (value: string | number | boolean) => {
  if (Boolean(value)) {
    twoFactorLoading.value = true
    try {
      const { value: password } = await ElMessageBox.prompt('为保护账户，请输入当前密码', '启用两步验证', {
        inputType: 'password', confirmButtonText: '继续', cancelButtonText: '取消',
        inputValidator: (value) => Boolean(value) || '请输入当前密码',
      })
      const response = await profileApi.setupTwoFactor({ password })
      twoFactorSetup.value = response.data
      twoFactorCode.value = ''
      showTwoFactorSetupDialog.value = true
    } catch (error: unknown) {
      ElMessage.error(getErrorMessage(error, '初始化两步验证失败'))
    } finally {
      twoFactorLoading.value = false
    }
  } else {
    Object.assign(disableTwoFactorForm, { password: '', code: '' })
    showTwoFactorDisableDialog.value = true
  }
}

const cancelTwoFactorSetup = () => {
  showTwoFactorSetupDialog.value = false
  twoFactorSetup.value = null
  twoFactorCode.value = ''
}

const confirmEnableTwoFactor = async () => {
  if (!/^\d{6}$/.test(twoFactorCode.value)) {
    ElMessage.warning('请输入身份验证器生成的 6 位验证码')
    return
  }
  twoFactorLoading.value = true
  try {
    const response = await profileApi.enableTwoFactor({ code: twoFactorCode.value })
    userInfo.two_factor_enabled = response.data.enabled
    recoveryCodes.value = response.data.recovery_codes || twoFactorSetup.value?.recovery_codes || []
    showTwoFactorSetupDialog.value = false
    twoFactorSetup.value = null
    if (recoveryCodes.value.length) showRecoveryCodesDialog.value = true
    ElMessage.success('两步验证已启用')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '启用两步验证失败'))
  } finally {
    twoFactorLoading.value = false
  }
}

const confirmDisableTwoFactor = async () => {
  if (!disableTwoFactorForm.password) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!disableTwoFactorForm.code) {
    ElMessage.warning('请输入动态验证码或恢复码')
    return
  }
  twoFactorLoading.value = true
  try {
    const response = await profileApi.disableTwoFactor({
      password: disableTwoFactorForm.password,
      code: disableTwoFactorForm.code,
    })
    userInfo.two_factor_enabled = response.data.enabled
    showTwoFactorDisableDialog.value = false
    ElMessage.success('两步验证已关闭')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '关闭两步验证失败'))
  } finally {
    twoFactorLoading.value = false
  }
}

const savePreference = async (key: keyof ProfilePreferences, value: boolean) => {
  if (preferenceSavingKey.value) return
  const previous = preferences[key]
  preferences[key] = value
  preferenceSavingKey.value = key
  try {
    const response = await profileApi.updatePreferences({ [key]: value })
    Object.assign(preferences, response.data)
    ElMessage.success('通知设置已保存')
  } catch (error: unknown) {
    preferences[key] = previous
    ElMessage.error(getErrorMessage(error, '保存通知设置失败'))
  } finally {
    preferenceSavingKey.value = null
  }
}

const handlePreferenceChange = (key: keyof ProfilePreferences, value: string | number | boolean) => {
  void savePreference(key, Boolean(value))
}

const openLoginHistory = () => {
  showLoginHistory.value = true
  loginLogsPage.value = 1
  void loadLoginLogs()
}

const loadLoginLogs = async () => {
  loginLogsLoading.value = true
  try {
    const response = await profileApi.getLoginLogs(loginLogsPage.value, loginLogsPageSize)
    loginLogs.value = response.data.items
    loginLogsTotal.value = response.data.total
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '加载登录记录失败'))
  } finally {
    loginLogsLoading.value = false
  }
}

const handleThemeChange = (value: string | number | boolean) => {
  appStore.setTheme(value as 'light' | 'dark' | 'auto')
}

const handleSidebarChange = (value: string | number | boolean) => {
  appStore.setSidebarCollapsed(!Boolean(value))
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定退出所有设备上的当前账户吗？', '确认退出', { type: 'warning', confirmButtonText: '退出所有设备', cancelButtonText: '取消' })
    try {
      await authApi.logout()
    } catch {
      ElMessage.warning('服务端登出失败，已清除本地登录状态')
    }
    clearLocalSession()
    ElMessage.success('已退出所有设备')
    await router.replace('/login')
  } catch (error: unknown) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(getErrorMessage(error, '退出失败'))
  }
}

const handleDeleteAccount = async () => {
  accountDeleting.value = true
  try {
    await profileApi.deleteAccount({ password: deleteForm.password, confirmation: '确认删除', code: deleteForm.code || undefined })
    clearLocalSession()
    showDeleteDialog.value = false
    ElMessage.success('账户已删除')
    await router.replace('/login')
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '删除账户失败'))
  } finally {
    accountDeleting.value = false
  }
}

const clearLocalSession = () => {
  storage.remove(TOKEN_KEY)
  storage.remove('refresh_token')
  storage.remove('token_type')
  storage.remove('expires_in')
  storage.remove('token_expires_at')
  storage.remove(USER_KEY)
  localStorage.removeItem('userAvatar')
  appStore.logout()
}

const copyText = async (value: string) => {
  try {
    await navigator.clipboard.writeText(value)
    ElMessage.success('已复制')
  } catch {
    ElMessage.warning('复制失败，请手动选择复制')
  }
}

const formatDate = (value?: string | null) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN')
}

const formatDevice = (item: LoginLogItem) => [item.browser, item.operating_system, item.device].filter(Boolean).join(' / ') || '-'

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof Error && error.message) return error.message
  const data = (error as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data
  if (typeof data?.message === 'string') return data.message
  if (typeof data?.detail === 'string') return data.detail
  return fallback
}

onMounted(() => { void loadPage() })
</script>

<style scoped>
.profile-view :deep(.el-card) {
  border-radius: 16px;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-radius: 0.75rem;
  background: #f9fafb;
  padding: 1rem;
}

html.dark .setting-row {
  background: #172033;
  border: 1px solid #334155;
}

.avatar-uploader,
.avatar-uploader :deep(.el-upload) {
  position: relative;
  display: inline-block;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.avatar-uploader:hover .avatar-overlay,
.avatar-uploader.is-disabled .avatar-overlay {
  opacity: 1;
}
</style>
