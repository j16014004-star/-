<template>
  <div class="chat-assistant-view flex h-[calc(100vh-60px)]">
    <!-- Session Sidebar -->
    <div class="w-64 border-r bg-white flex-shrink-0 flex flex-col">
      <div class="p-4 border-b">
        <el-button type="primary" class="w-full" @click="createSession">
          <el-icon class="mr-1"><Plus /></el-icon>
          新建会话
        </el-button>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item px-4 py-3 cursor-pointer hover:bg-gray-50 flex items-center justify-between group"
          :class="{ 'bg-indigo-50 border-r-3 border-indigo-500': currentSession?.id === session.id }"
          @click="selectSession(session)"
        >
          <div class="flex-1 min-w-0">
            <div class="font-medium text-sm text-gray-800 truncate">{{ session.title }}</div>
            <div class="text-xs text-gray-400 mt-1">{{ formatTime(session.updatedAt) }}</div>
          </div>
          <el-popconfirm
            title="确定删除此会话？"
            confirm-button-text="删除"
            cancel-button-text="取消"
            @confirm="deleteSession(session.id)"
          >
            <template #reference>
              <el-button text size="small" class="opacity-0 group-hover:opacity-100 text-red-400">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 flex flex-col min-w-0 bg-gray-50">
      <!-- Header -->
      <div class="px-6 py-3 bg-white border-b flex items-center gap-3">
        <img class="assistant-logo" src="/hakimi-logo.png" alt="哈基米AI" />
        <div>
          <div class="font-medium text-gray-800">哈基米AI</div>
          <div class="text-xs text-green-500 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            全自动求职助手在线
          </div>
        </div>
      </div>

      <!-- Messages -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Welcome -->
        <div v-if="messages.length === 0" class="text-center py-12">
          <img class="welcome-logo mx-auto mb-4" src="/hakimi-logo.png" alt="哈基米AI" />
          <h3 class="text-xl font-semibold text-gray-700 mb-2">你好，我是哈基米AI</h3>
          <p class="text-gray-500 mb-6">找工作、做简历、定职业规划，AI 全程帮你做</p>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-lg mx-auto">
            <div
              v-for="suggestion in suggestions"
              :key="suggestion"
              class="p-3 rounded-xl bg-white border border-gray-100 cursor-pointer hover:border-indigo-200 hover:bg-indigo-50 transition-colors text-sm text-gray-600 text-left"
              @click="sendSuggestion(suggestion)"
            >
              {{ suggestion }}
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div v-for="msg in messages" :key="msg.id" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <div class="max-w-3xl" :class="msg.role === 'user' ? 'order-2' : 'order-1'">
            <!-- Avatar -->
            <div v-if="msg.role === 'assistant'" class="flex items-center gap-3 mb-2">
              <img class="message-logo" src="/hakimi-logo.png" alt="哈基米AI" />
              <span class="text-xs text-gray-400">哈基米AI</span>
            </div>
            <!-- Bubble -->
            <div
              class="px-4 py-3 rounded-2xl leading-relaxed text-sm"
              :class="msg.role === 'user'
                ? 'bg-indigo-600 text-white rounded-br-sm'
                : 'bg-white text-gray-700 shadow-sm rounded-bl-sm border border-gray-100'"
            >
              {{ msg.content }}
            </div>
            <div class="text-xs text-gray-400 mt-1" :class="msg.role === 'user' ? 'text-right' : ''">
              {{ formatMessageTime(msg.createdAt) }}
            </div>
          </div>
        </div>

        <!-- Streaming -->
        <div v-if="isStreaming" class="flex justify-start">
          <div class="max-w-3xl">
            <div class="flex items-center gap-3 mb-2">
              <img class="message-logo" src="/hakimi-logo.png" alt="哈基米AI" />
              <span class="text-xs text-gray-400">哈基米AI</span>
            </div>
            <div class="px-4 py-3 rounded-2xl bg-white text-gray-700 shadow-sm rounded-bl-sm border border-gray-100">
              <span>{{ streamingText }}</span>
              <span class="animate-pulse text-indigo-600">|</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 bg-white border-t">
        <div class="flex gap-3">
          <el-input
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入你的问题..."
            class="flex-1"
            @keydown.enter.exact.prevent="handleSend"
            resize="none"
          />
          <el-button type="primary" size="large" :loading="isStreaming" @click="handleSend" class="self-end">
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
        <div class="text-xs text-gray-400 mt-2">按 Enter 发送，Shift + Enter 换行</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, watch } from 'vue'
import { Plus, Delete, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '@/api/chat'

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt: string
}

const sessions = ref<any[]>([])
const currentSession = ref<any | null>(null)
const messages = ref<Message[]>([])
const isLoading = ref(false)

// 每个会话的消息存储
const sessionMessagesMap = reactive<Record<number, Message[]>>({})

// 自动同步当前消息到会话存储
watch(messages, (newMessages) => {
  if (currentSession.value) {
    sessionMessagesMap[currentSession.value.id] = [...newMessages]
  }
}, { deep: true })

const inputText = ref('')
const isStreaming = ref(false)
const streamingText = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const suggestions = [
  '如何优化简历中的工作经历？',
  '技术面试前需要准备什么？',
  '前端工程师的职业发展路径',
  '如何回答"你的缺点是什么"？',
  '简历中是否需要写自我评价？',
  '跳槽的最佳时机是什么？',
]

function formatTime(str: string): string {
  return str.split(' ')[1] || ''
}

function formatMessageTime(str: string): string {
  return str
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 从后端 API 加载会话列表
async function loadSessions() {
  isLoading.value = true
  try {
    const response = await chatApi.getSessions()
    sessions.value = (response.data || []).map((session: any) => ({
      id: session.id,
      title: session.title || '未命名会话',
      updatedAt: session.updated_at || new Date().toLocaleString('zh-CN')
    }))

    // 选择第一个会话
    if (sessions.value.length > 0) {
      await selectSession(sessions.value[0])
    }
  } catch (error) {
    ElMessage.error('加载会话列表失败')
  } finally {
    isLoading.value = false
  }
}

// 从后端 API 加载会话消息
async function loadMessages(sessionId: number) {
  try {
    const response = await chatApi.getMessages(sessionId)
    messages.value = (response.data || []).map((msg: any) => ({
      id: msg.id.toString(),
      role: msg.role,
      content: msg.content,
      createdAt: msg.created_at || new Date().toLocaleString('zh-CN')
    }))
  } catch (error) {
    ElMessage.error('加载消息列表失败')
  }
}

function createSession() {
  const newSession = {
    id: Date.now(),
    title: `新会话 ${sessions.value.length + 1}`,
  }
  sessions.value.unshift(newSession)
  sessionMessagesMap[newSession.id] = []
  currentSession.value = newSession
  messages.value = []
  loadMessages(newSession.id)
}

async function selectSession(session: any) {
  if (currentSession.value) {
    sessionMessagesMap[currentSession.value.id] = messages.value
  }
  currentSession.value = session
  await loadMessages(session.id)
}

async function deleteSession(id: number) {
  try {
    await chatApi.deleteSession(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    delete sessionMessagesMap[id]
    if (currentSession.value?.id === id) {
      currentSession.value = sessions.value[0] || null
      messages.value = []
    }
    ElMessage.success('会话已删除')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '删除失败，请稍后重试')
  }
}

function sendSuggestion(text: string) {
  inputText.value = text
  handleSend()
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  // 添加用户消息
  messages.value.push({
    id: 'msg_' + Date.now(),
    role: 'user',
    content: text,
    createdAt: new Date().toLocaleString('zh-CN'),
  })
  inputText.value = ''
  scrollToBottom()

  // 调用后端 API 发送消息
  isStreaming.value = true
  streamingText.value = ''

  chatApi.sendMessage({
    session_id: currentSession.value?.id,
    message: text
  }).then((response) => {
    const newMessage = response.data
    streamingText.value = newMessage.content
    isStreaming.value = false
    messages.value.push({
      id: newMessage.id.toString(),
      role: newMessage.role,
      content: newMessage.content,
      createdAt: newMessage.created_at || new Date().toLocaleString('zh-CN')
    })
    scrollToBottom()

    // 更新会话标题
    if (currentSession.value && messages.value.length <= 1) {
      currentSession.value.title = text.substring(0, 20) + (text.length > 20 ? '...' : '')
    }
  }).catch((error) => {
    ElMessage.error(error.response?.data?.message || '发送失败，请稍后重试')
    isStreaming.value = false
  })
}

// 页面加载时加载会话列表
onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.session-item {
  border-left: 3px solid transparent;
  transition: all 0.2s;
}
.session-item:hover {
  background-color: #f9fafb;
}

.assistant-logo {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 12px;
  object-fit: cover;
}

.welcome-logo {
  width: 88px;
  height: 88px;
  border-radius: 24px;
  object-fit: cover;
  box-shadow: 0 16px 32px rgba(79, 70, 229, 0.18);
}

.message-logo {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 9px;
  object-fit: cover;
}

:deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  resize: none;
  font-size: 14px;
}
:deep(.el-textarea__inner:focus) {
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}
</style>
