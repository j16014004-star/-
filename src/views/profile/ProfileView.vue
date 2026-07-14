<template>
  <div class="profile-view p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
    <div class="max-w-4xl mx-auto">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-gray-100">个人中心</h1>
        <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">管理你的账户信息和个人偏好</p>
      </div>

      <!-- User Info Card -->
      <el-card class="border-0 mb-6">
        <template #header>
          <div class="flex items-center gap-4">
            <!-- 头像上传区域 -->
            <el-upload
              class="avatar-uploader"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :http-request="handleAvatarUpload"
              accept="image/*"
            >
              <el-avatar
                :size="64"
                :src="userInfo.avatar || undefined"
                class="bg-indigo-100 text-indigo-600 text-2xl font-bold cursor-pointer hover:opacity-80 transition-opacity"
              >
                <span v-if="!userInfo.avatar">{{ userInfo.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
              </el-avatar>
              <div class="avatar-overlay" v-if="!userInfo.avatar">
                <el-icon class="text-white"><Camera /></el-icon>
              </div>
            </el-upload>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-xl font-bold text-gray-800 dark:text-gray-100">{{ userInfo.username }}</h2>
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ userInfo.email }}</p>
                </div>
                <el-button v-if="userInfo.avatar" text type="danger" size="small" @click="removeAvatar">
                  移除头像
                </el-button>
              </div>
              <p class="text-xs text-gray-400 mt-1">点击头像可上传新图片（支持 JPG/PNG，最大 2MB）</p>
            </div>
          </div>
        </template>

        <el-form :model="userInfo" label-position="top" class="mt-4">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="用户名">
                <el-input v-model="userInfo.username" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="邮箱">
                <el-input v-model="userInfo.email" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="手机号">
                <el-input v-model="userInfo.phone" placeholder="请输入手机号" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="注册时间">
                <el-input :model-value="formatDate(userInfo.created_at)" disabled />
              </el-form-item>
            </el-col>
          </el-row>
          <div class="flex justify-end gap-3">
            <el-button @click="resetProfile">重置</el-button>
            <el-button type="primary" @click="saveProfile">保存修改</el-button>
          </div>
        </el-form>
      </el-card>

      <!-- Account Security -->
      <el-card class="border-0 mb-6">
        <template #header>
          <span class="font-semibold">账户安全</span>
        </template>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">修改密码</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">定期修改密码可以保障账户安全</div>
            </div>
            <el-button type="primary" plain size="small" @click="showPasswordDialog = true">
              修改密码
            </el-button>
          </div>
          <div class="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">两步验证</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">启用后登录时需要额外验证</div>
            </div>
            <el-switch v-model="securitySettings.twoFactor" />
          </div>
          <div class="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">登录记录</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">查看最近的登录活动</div>
            </div>
            <el-button text type="primary" @click="showLoginHistory = true">
              查看记录
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- Notification Settings -->
      <el-card class="border-0 mb-6">
        <template #header>
          <span class="font-semibold">通知设置</span>
        </template>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">邮件通知</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">接收岗位匹配、面试提醒等邮件通知</div>
            </div>
            <el-switch v-model="notificationSettings.email" />
          </div>
          <div class="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">消息推送</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">HR消息、系统消息的实时推送</div>
            </div>
            <el-switch v-model="notificationSettings.push" />
          </div>
          <div class="flex items-center justify-between p-4 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">AI报告推送</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">简历分析完成后推送通知</div>
            </div>
            <el-switch v-model="notificationSettings.aiReport" />
          </div>
        </div>
      </el-card>

      <!-- Appearance -->
      <el-card class="border-0 mb-6">
        <template #header>
          <span class="font-semibold">外观设置</span>
        </template>
        <el-form-item label="主题模式">
          <el-radio-group v-model="appearanceTheme" @change="handleThemeChange">
            <el-radio-button value="light">
              <el-icon class="mr-1"><Sunny /></el-icon>浅色
            </el-radio-button>
            <el-radio-button value="dark">
              <el-icon class="mr-1"><Moon /></el-icon>深色
            </el-radio-button>
            <el-radio-button value="auto">
              <el-icon class="mr-1"><Monitor /></el-icon>跟随系统
            </el-radio-button>
          </el-radio-group>
          <span class="ml-4 text-sm text-gray-400">
            {{ currentThemeLabel }}
          </span>
        </el-form-item>
        <el-form-item label="侧边栏默认展开">
          <el-switch v-model="sidebarExpanded" @change="handleSidebarChange" />
        </el-form-item>
      </el-card>

      <!-- Danger Zone -->
      <el-card class="border-0 border-l-4 border-l-red-400">
        <template #header>
          <span class="font-semibold text-red-500">危险区域</span>
        </template>
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-800 dark:text-gray-200">退出登录</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">退出当前账户</div>
            </div>
            <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
          </div>
          <div class="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-700">
            <div>
              <div class="font-medium text-red-500">删除账户</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">删除账户后数据将无法恢复</div>
            </div>
            <el-button type="danger" size="small" @click="showDeleteDialog = true">删除账户</el-button>
          </div>
        </div>
      </el-card>

      <!-- Password Dialog -->
      <el-dialog v-model="showPasswordDialog" title="修改密码" width="450px">
        <el-form :model="passwordForm" label-position="top">
          <el-form-item label="当前密码">
            <el-input v-model="passwordForm.currentPassword" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="passwordForm.newPassword" type="password" show-password />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showPasswordDialog = false">取消</el-button>
          <el-button type="primary" @click="handleChangePassword">确认修改</el-button>
        </template>
      </el-dialog>

      <!-- Delete Dialog -->
      <el-dialog v-model="showDeleteDialog" title="删除账户" width="450px">
        <div class="text-sm text-gray-600 dark:text-gray-300 leading-relaxed mb-4">
          <p class="mb-2">删除账户后，以下数据将被永久删除：</p>
          <ul class="list-disc list-inside space-y-1 text-gray-500 dark:text-gray-400">
            <li>所有简历数据和分析报告</li>
            <li>面试记录和评分</li>
            <li>聊天记录和会话历史</li>
            <li>个人设置和偏好</li>
          </ul>
        </div>
        <el-input v-model="deleteConfirmText" placeholder="请输入 '确认删除' 以继续" />
        <template #footer>
          <el-button @click="showDeleteDialog = false">取消</el-button>
          <el-button type="danger" :disabled="deleteConfirmText !== '确认删除'" @click="handleDeleteAccount">
            永久删除
          </el-button>
        </template>
      </el-dialog>

      <!-- Login History Dialog -->
      <el-dialog v-model="showLoginHistory" title="登录记录" width="600px">
        <el-table :data="loginHistory" size="small">
          <el-table-column prop="time" label="时间" width="180" />
          <el-table-column prop="device" label="设备" width="150" />
          <el-table-column prop="ip" label="IP地址" width="140" />
          <el-table-column prop="location" label="位置" />
        </el-table>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Camera, Sunny, Moon, Monitor } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api/auth'
import { storage, USER_KEY } from '@/utils/storage'

const router = useRouter()
const appStore = useAppStore()

const userInfo = reactive({
  id: 1,
  username: '',
  email: '',
  phone: '',
  avatar: '',
  created_at: '2026-01-15T08:30:00Z',
})

const securitySettings = reactive({
  twoFactor: false,
})

const notificationSettings = reactive({
  email: true,
  push: true,
  aiReport: true,
})

// 主题设置 - 与 store 同步
const appearanceTheme = computed({
  get: () => appStore.theme,
  set: () => {}, // 通过 handleThemeChange 处理
})

const sidebarExpanded = computed({
  get: () => !appStore.sidebarCollapsed,
  set: () => {}, // 通过 handleSidebarChange 处理
})

const currentThemeLabel = computed(() => {
  const labels = { light: '当前：浅色模式', dark: '当前：深色模式', auto: '当前：跟随系统主题' }
  return labels[appStore.theme] || ''
})

const showPasswordDialog = ref(false)
const showDeleteDialog = ref(false)
const showLoginHistory = ref(false)
const deleteConfirmText = ref('')

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const loginHistory = ref([
  { time: '2026-07-13 14:30', device: 'Chrome / Windows', ip: '192.168.1.100', location: '上海' },
  { time: '2026-07-12 09:15', device: 'Safari / macOS', ip: '192.168.1.100', location: '上海' },
  { time: '2026-07-11 20:00', device: 'Chrome / iPhone', ip: '10.0.0.1', location: '上海' },
  { time: '2026-07-10 08:45', device: 'Chrome / Windows', ip: '192.168.1.100', location: '上海' },
])

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 头像上传相关
function beforeAvatarUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB！')
    return false
  }
  return true
}

function handleAvatarUpload(options: { file: File }) {
  const file = options.file
  const reader = new FileReader()
  reader.onload = (e) => {
    const base64 = e.target?.result as string
    userInfo.avatar = base64
    appStore.setAvatar(base64)
    // 同步到 user storage
    const storedUser = storage.get<any>(USER_KEY)
    if (storedUser) {
      storedUser.avatar = base64
      storage.set(USER_KEY, storedUser)
    }
    ElMessage.success('头像上传成功')
  }
  reader.readAsDataURL(file)
}

function removeAvatar() {
  ElMessageBox.confirm('确定要移除头像吗？', '确认', {
    type: 'warning',
    confirmButtonText: '移除',
    cancelButtonText: '取消',
  }).then(() => {
    userInfo.avatar = ''
    appStore.setAvatar('')
    const storedUser = storage.get<any>(USER_KEY)
    if (storedUser) {
      storedUser.avatar = ''
      storage.set(USER_KEY, storedUser)
    }
    localStorage.removeItem('userAvatar')
    ElMessage.success('头像已移除')
  }).catch(() => {})
}

// 主题切换
function handleThemeChange(val: string | number | boolean) {
  const theme = val as 'light' | 'dark' | 'auto'
  appStore.setTheme(theme)
  ElMessage.success(`已切换为${theme === 'light' ? '浅色' : theme === 'dark' ? '深色' : '跟随系统'}模式`)
}

// 侧边栏设置
function handleSidebarChange(val: string | number | boolean) {
  appStore.setSidebarCollapsed(!val)
}

onMounted(async () => {
  // 从后端 API 获取用户信息
  try {
    const response = await authApi.getUserInfo()
    const user = response.data
    userInfo.id = user.id
    userInfo.username = user.username || '用户'
    userInfo.email = user.email || ''
    userInfo.phone = user.phone || ''
    userInfo.avatar = user.avatar || ''
    userInfo.created_at = user.created_at || ''
    // 同步到 store
    appStore.user.name = userInfo.username
    appStore.user.avatar = userInfo.avatar
  } catch (error) {
    // 如果 API 失败，从 storage 加载
    const storedUser = storage.get<any>(USER_KEY)
    if (storedUser) {
      userInfo.username = storedUser.username || '用户'
      userInfo.email = storedUser.email || ''
      userInfo.phone = storedUser.phone || ''
      userInfo.avatar = storedUser.avatar || ''
    }
  }
})

async function saveProfile() {
  try {
    // 调用后端 API 更新用户资料
    await authApi.updateProfile({
      username: userInfo.username,
      email: userInfo.email,
      phone: userInfo.phone,
      avatar: userInfo.avatar
    })
    // 同步到 store
    appStore.user.name = userInfo.username
    ElMessage.success('个人信息保存成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '保存失败，请稍后重试')
  }
}

function resetProfile() {
  const storedUser = storage.get<any>(USER_KEY)
  if (storedUser) {
    userInfo.username = storedUser.username || '用户'
    userInfo.email = storedUser.email || ''
    userInfo.phone = storedUser.phone || ''
    userInfo.avatar = storedUser.avatar || ''
  }
}

function handleChangePassword() {
  if (!passwordForm.currentPassword) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!passwordForm.newPassword || passwordForm.newPassword.length < 6) {
    ElMessage.warning('新密码至少6个字符')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  ElMessage.success('密码修改成功')
  showPasswordDialog.value = false
  passwordForm.currentPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '确认退出', {
      type: 'warning',
      confirmButtonText: '退出',
      cancelButtonText: '取消',
    })

    // 调用后端登出 API
    await authApi.logout()

    // 清除本地存储
    storage.remove(TOKEN_KEY)
    storage.remove('refresh_token')
    storage.remove(USER_KEY)
    localStorage.removeItem('userAvatar')
    appStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch (error) {
    // 用户取消或 API 错误
    if (error !== 'cancel') {
      ElMessage.error('退出失败，请稍后重试')
    }
  }
}

function handleDeleteAccount() {
  storage.remove(TOKEN_KEY)
  storage.remove(USER_KEY)
  localStorage.removeItem('userAvatar')
  ElMessage.error('账户已删除')
  showDeleteDialog.value = false
  router.push('/login')
}
</script>

<style scoped>
.profile-view :deep(.el-card) {
  border-radius: 16px;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
:deep(.el-input__wrapper) {
  border-radius: 10px;
}

/* 头像上传样式 */
.avatar-uploader {
  position: relative;
  display: inline-block;
}

.avatar-uploader :deep(.el-upload) {
  position: relative;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.avatar-uploader:hover .avatar-overlay {
  opacity: 1;
}
</style>
