<template>
  <div class="hr-chat-view flex h-[calc(100vh-60px)]">
    <!-- Conversation List -->
    <div class="w-80 border-r bg-white flex-shrink-0 flex flex-col">
      <div class="p-4 border-b">
        <div class="flex items-center justify-between mb-2">
          <div class="font-semibold text-gray-800">AI Agent 沟通中心</div>
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" type="primary" />
        </div>
        <div class="text-xs text-gray-400">Boss直聘 · 实时同步</div>
        <div class="flex items-center gap-2 mt-2">
          <div class="w-2 h-2 rounded-full" :class="websocketConnected ? 'bg-green-500' : 'bg-red-500'"></div>
          <span class="text-xs" :class="websocketConnected ? 'text-green-600' : 'text-red-600'">
            {{ websocketConnected ? '已连接' : '未连接' }}
          </span>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="px-4 py-2 border-b">
        <el-radio-group v-model="filterStatus" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="active">进行中</el-radio-button>
          <el-radio-button label="paused">已暂停</el-radio-button>
        </el-radio-group>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div
          v-for="conv in filteredConversations"
          :key="conv.id"
          class="conversation-item px-4 py-3 cursor-pointer hover:bg-gray-50 border-b border-gray-50"
          :class="{
            'bg-indigo-50': selectedConversation?.id === conv.id,
            'border-l-3 border-l-indigo-500': selectedConversation?.id === conv.id
          }"
          @click="selectConversation(conv)"
        >
          <div class="flex items-start gap-3">
            <el-avatar :size="40" class="bg-indigo-100 text-indigo-600 font-bold">
              {{ conv.hrName.charAt(0) }}
            </el-avatar>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <span class="font-medium text-sm text-gray-800">{{ conv.hrName }}</span>
                <span class="text-xs text-gray-400">{{ formatTime(conv.lastMessageAt) }}</span>
              </div>
              <div class="text-xs text-gray-500 truncate mt-1">{{ conv.company }}</div>
              <div class="flex items-center gap-2 mt-1">
                <el-tag
                  :type="conv.aiManaged ? 'success' : 'warning'"
                  size="small"
                  effect="plain"
                >
                  {{ conv.aiManaged ? 'AI托管' : '人工' }}
                </el-tag>
                <span v-if="conv.unreadCount > 0" class="text-xs text-indigo-600 font-medium">
                  {{ conv.unreadCount }} 条新消息
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Messages -->
    <div class="flex-1 flex flex-col min-w-0 bg-gray-50">
      <template v-if="selectedConversation">
        <!-- Header -->
        <div class="px-6 py-4 bg-white border-b">
          <div class="flex items-center gap-3">
            <el-avatar :size="44" class="bg-indigo-100 text-indigo-600 font-bold text-lg">
              {{ selectedConversation.hrName.charAt(0) }}
            </el-avatar>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="font-semibold text-gray-800">{{ selectedConversation.hrName }}</span>
                <el-tag
                  v-if="selectedConversation.hrTitle"
                  size="small"
                  type="info"
                >
                  {{ selectedConversation.hrTitle }}
                </el-tag>
              </div>
              <div class="text-sm text-gray-500">{{ selectedConversation.company }}</div>
            </div>
            <div class="flex items-center gap-2">
              <el-button
                size="small"
                @click="openBossPage"
                type="primary"
                plain
              >
                <el-icon class="mr-1"><Link /></el-icon>
                Boss原网页
              </el-button>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div class="flex-1 overflow-y-auto p-6">
          <div class="max-w-3xl mx-auto space-y-4">
            <div
              v-for="msg in currentMessages"
              :key="msg.id"
              class="flex"
              :class="msg.senderType === 'hr' ? 'justify-start' : 'justify-end'"
            >
              <div class="max-w-2xl">
                <!-- Message Header -->
                <div class="flex items-center gap-2 mb-1" :class="msg.senderType === 'hr' ? '' : 'justify-end'">
                  <span class="text-xs font-medium" :class="msg.senderType === 'hr' ? 'text-gray-600' : 'text-indigo-600'">
                    {{ msg.senderType === 'hr' ? selectedConversation.hrName : '我' }}
                  </span>
                  <el-tag v-if="msg.isAiGenerated" size="small" type="success" effect="plain">
                    AI回复
                  </el-tag>
                  <span class="text-xs text-gray-400">{{ formatTime(msg.sentAt) }}</span>
                </div>

                <!-- Message Bubble -->
                <div
                  class="px-4 py-3 rounded-2xl text-sm leading-relaxed"
                  :class="msg.senderType === 'hr'
                    ? 'bg-white text-gray-700 border border-gray-100'
                    : 'bg-indigo-600 text-white'"
                >
                  {{ msg.content }}
                </div>

                <!-- Message Status -->
                <div class="flex items-center gap-2 mt-1" :class="msg.senderType === 'hr' ? '' : 'justify-end'">
                  <span v-if="msg.status === 'sending'" class="text-xs text-gray-400">发送中...</span>
                  <span v-else-if="msg.status === 'sent'" class="text-xs text-gray-400">已发送</span>
                  <span v-else-if="msg.status === 'read'" class="text-xs text-green-500">已读</span>
                  <el-icon v-if="msg.status === 'failed'" class="text-red-500 text-xs"><WarningFilled /></el-icon>
                </div>
              </div>
            </div>

            <!-- Loading indicator -->
            <div v-if="isLoadingMessages" class="text-center py-4">
              <el-icon class="is-loading text-gray-400"><Loading /></el-icon>
              <span class="text-sm text-gray-400 ml-2">加载中...</span>
            </div>
          </div>
        </div>
      </template>

      <!-- Empty State -->
      <div v-else class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <div class="text-6xl mb-4">&#x1F916;</div>
          <h3 class="text-lg font-semibold text-gray-600 mb-2">AI Agent 沟通中心</h3>
          <p class="text-gray-400 mb-4">选择左侧对话查看聊天记录</p>
          <p class="text-xs text-gray-400">AI 正在自动与 HR 沟通，您可以随时接管</p>
        </div>
      </div>
    </div>

    <!-- AI Control Panel -->
    <div class="w-80 border-l bg-white flex-shrink-0 flex flex-col">
      <div class="p-4 border-b">
        <div class="font-semibold text-gray-800">AI 控制面板</div>
        <div class="text-xs text-gray-400 mt-1">管理 AI 自动回复行为</div>
      </div>

      <div class="flex-1 overflow-y-auto p-4">
        <template v-if="selectedConversation">
          <!-- AI Status -->
          <div class="mb-6">
            <div class="text-sm font-medium text-gray-700 mb-3">AI 托管状态</div>
            <el-switch
              v-model="selectedConversation.aiManaged"
              active-text="AI 自动回复"
              inactive-text="手动模式"
              @change="toggleAiManaged"
            />
            <div class="mt-2 text-xs text-gray-500">
              {{ selectedConversation.aiManaged
                ? 'AI 正在自动回复 HR 消息'
                : '需要您手动回复消息' }}
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="mb-6">
            <div class="text-sm font-medium text-gray-700 mb-3">快捷操作</div>
            <div class="space-y-2">
              <el-button
                v-if="selectedConversation.aiManaged"
                type="warning"
                plain
                class="w-full"
                @click="pauseAi"
              >
                <el-icon class="mr-1"><VideoPause /></el-icon>
                暂停 AI
              </el-button>
              <el-button
                v-else
                type="success"
                plain
                class="w-full"
                @click="resumeAi"
              >
                <el-icon class="mr-1"><VideoPlay /></el-icon>
                恢复 AI
              </el-button>
              <el-button
                type="primary"
                plain
                class="w-full"
                @click="takeOver"
              >
                <el-icon class="mr-1"><User /></el-icon>
                人工接管
              </el-button>
              <el-button
                type="info"
                plain
                class="w-full"
                @click="generateReply"
              >
                <el-icon class="mr-1"><MagicStick /></el-icon>
                生成回复建议
              </el-button>
            </div>
          </div>

          <!-- AI Suggestions -->
          <div v-if="aiSuggestions.length > 0" class="mb-6">
            <div class="text-sm font-medium text-gray-700 mb-3">AI 建议回复</div>
            <div class="space-y-2">
              <div
                v-for="(suggestion, index) in aiSuggestions"
                :key="index"
                class="p-3 rounded-lg bg-indigo-50 border border-indigo-100 text-sm text-gray-700 cursor-pointer hover:bg-indigo-100 transition-colors"
                @click="useSuggestion(suggestion)"
              >
                {{ suggestion }}
              </div>
            </div>
          </div>

          <!-- Statistics -->
          <div>
            <div class="text-sm font-medium text-gray-700 mb-3">统计数据</div>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-500">总消息数</span>
                <span class="font-medium">{{ currentMessages.length }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">AI 回复数</span>
                <span class="font-medium text-green-600">{{ aiReplyCount }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">未读消息</span>
                <span class="font-medium text-indigo-600">{{ selectedConversation.unreadCount }}</span>
              </div>
            </div>
          </div>
        </template>

        <div v-else class="text-center py-12 text-gray-400 text-sm">
          选择对话以查看控制面板
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { MagicStick, Link, VideoPause, VideoPlay, User, WarningFilled, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { hrApi } from '@/api/hr'

interface Conversation {
  id: number
  hrName: string
  hrTitle?: string
  company: string
  platformName: string
  aiManaged: boolean
  unreadCount: number
  lastMessageAt: string
  bossConversationUrl: string
}

interface Message {
  id: number
  conversationId: number
  senderType: 'hr' | 'user'
  content: string
  isAiGenerated: boolean
  status: 'sending' | 'sent' | 'read' | 'failed'
  sentAt: string
}

const websocketConnected = ref(true) // WebSocket connection status
const filterStatus = ref<'all' | 'active' | 'paused'>('all')
const isLoadingMessages = ref(false)
const aiSuggestions = ref<string[]>([])

const conversations = ref<Conversation[]>([])
const currentMessages = ref<Message[]>([])
const selectedConversation = ref<Conversation | null>(null)

// 消息按会话分组存储
const messagesMap = ref<Record<number, Message[]>>({})

// 从后端 API 加载对话列表
async function loadConversations() {
  try {
    const response = await hrApi.getMessages()
    const data = response.data || []

    // 映射为前端会话结构
    conversations.value = data.map((msg: any) => ({
      id: msg.conversation_id || msg.id,
      hrName: msg.hr_name || '未知',
      hrTitle: msg.hr_title || '',
      company: msg.company || '',
      platformName: msg.platform_name || 'boss',
      aiManaged: msg.ai_managed || false,
      unreadCount: msg.unread_count || 0,
      lastMessageAt: msg.last_message_at || new Date().toLocaleString('zh-CN'),
      bossConversationUrl: msg.boss_conversation_url || ''
    }))

    if (conversations.value.length > 0) {
      selectedConversation.value = conversations.value[0]
      loadMessages(conversations.value[0].id)
    }
  } catch (error) {
    ElMessage.error('加载对话列表失败')
  }
}

// 加载指定会话的消息
async function loadMessages(conversationId: number) {
  isLoadingMessages.value = true
  try {
    // 如果已缓存，使用缓存
    if (messagesMap.value[conversationId]) {
      currentMessages.value = messagesMap.value[conversationId]
    } else {
      // 否则从 API 加载
      const response = await hrApi.getMessages()
      const data = response.data || []
      // 筛选当前会话的消息
      const msgs = data
        .filter((msg: any) => (msg.conversation_id || msg.id) === conversationId)
        .map((msg: any) => ({
          id: msg.id,
          conversationId: msg.conversation_id || conversationId,
          senderType: msg.sender_type || (msg.is_hr ? 'hr' : 'user'),
          content: msg.content,
          isAiGenerated: msg.is_ai_generated || false,
          status: msg.status || 'read',
          sentAt: msg.sent_at || new Date().toLocaleString('zh-CN')
        }))
      messagesMap.value[conversationId] = msgs
      currentMessages.value = msgs
    }
  } catch (error) {
    ElMessage.error('加载消息失败')
  } finally {
    isLoadingMessages.value = false
  }
}

const unreadCount = computed(() => {
  return conversations.value.reduce((sum, conv) => sum + conv.unreadCount, 0)
})

const aiReplyCount = computed(() => {
  return currentMessages.value.filter(msg => msg.isAiGenerated).length
})

const filteredConversations = computed(() => {
  if (filterStatus.value === 'all') return conversations.value
  if (filterStatus.value === 'active') {
    return conversations.value.filter(conv => conv.aiManaged)
  }
  return conversations.value.filter(conv => !conv.aiManaged)
})

function formatTime(str: string): string {
  const date = new Date(str)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return str.split(' ')[1]?.substring(0, 5) || ''
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  }
  return str.substring(5, 10)
}

function selectConversation(conv: Conversation) {
  selectedConversation.value = conv
  loadMessages(conv.id)
}

function openBossPage() {
  if (selectedConversation.value) {
    window.open(selectedConversation.value.bossConversationUrl, '_blank')
  }
}

async function toggleAiManaged() {
  if (selectedConversation.value) {
    try {
      // 这里可以调用 API 更新 AI 托管状态
      const status = selectedConversation.value.aiManaged ? '暂停' : '启用'
      ElMessage.success(`已${status} AI 自动回复`)
    } catch (error) {
      ElMessage.error('操作失败，请稍后重试')
    }
  }
}

async function pauseAi() {
  if (selectedConversation.value) {
    try {
      selectedConversation.value.aiManaged = false
      ElMessage.success('AI 已暂停，需要手动回复')
    } catch (error) {
      ElMessage.error('暂停失败，请稍后重试')
    }
  }
}

async function resumeAi() {
  if (selectedConversation.value) {
    try {
      selectedConversation.value.aiManaged = true
      ElMessage.success('AI 已恢复自动回复')
    } catch (error) {
      ElMessage.error('恢复失败，请稍后重试')
    }
  }
}

async function takeOver() {
  if (selectedConversation.value) {
    try {
      selectedConversation.value.aiManaged = false
      ElMessage.info('已切换到手动模式，请手动回复消息')
    } catch (error) {
      ElMessage.error('操作失败，请稍后重试')
    }
  }
}

async function generateReply() {
  if (!selectedConversation.value) return

  try {
    const response = await hrApi.getSuggestions(selectedConversation.value.id)
    aiSuggestions.value = response.data?.suggestions || []
    ElMessage.success('AI 已生成回复建议')
  } catch (error) {
    ElMessage.error('生成回复建议失败，请稍后重试')
  }
}

async function useSuggestion(suggestion: string) {
  if (!selectedConversation.value) return

  try {
    // 调用后端 API 发送回复
    await hrApi.reply({
      message_id: selectedConversation.value.id,
      content: suggestion
    })

    const newMessage: Message = {
      id: Date.now(),
      conversationId: selectedConversation.value.id,
      senderType: 'user',
      content: suggestion,
      isAiGenerated: true,
      status: 'sent',
      sentAt: new Date().toLocaleString('zh-CN'),
    }
    currentMessages.value.push(newMessage)
    aiSuggestions.value = []
    ElMessage.success('回复已发送')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '发送失败，请稍后重试')
  }
}

onMounted(() => {
  loadConversations()
})

onUnmounted(() => {
  // 清理资源
})
</script>

<style scoped>
.hr-chat-view {
  background-color: #f9fafb;
}

.conversation-item {
  transition: all 0.2s;
}

.conversation-item:hover {
  background-color: #f9fafb;
}

:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}

:deep(.el-switch__label) {
  font-size: 13px;
}
</style>
