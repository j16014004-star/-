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
        <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
          <span class="text-lg">&#x1F916;</span>
        </div>
        <div>
          <div class="font-medium text-gray-800">AI求职助手</div>
          <div class="text-xs text-green-500 flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            在线
          </div>
        </div>
      </div>

      <!-- Messages -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Welcome -->
        <div v-if="messages.length === 0" class="text-center py-12">
          <div class="text-6xl mb-4">&#x1F916;</div>
          <h3 class="text-xl font-semibold text-gray-700 mb-2">你好，我是AI求职助手</h3>
          <p class="text-gray-500 mb-6">我可以帮你分析简历、准备面试、解答求职问题</p>
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
              <div class="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
                <span class="text-sm">&#x1F916;</span>
              </div>
              <span class="text-xs text-gray-400">AI助手</span>
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
              <div class="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
                <span class="text-sm">&#x1F916;</span>
              </div>
              <span class="text-xs text-gray-400">AI助手</span>
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
import { ref, reactive, nextTick, watch } from 'vue'
import { Plus, Delete, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Session {
  id: number
  title: string
  updatedAt: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}

const sessions = ref<Session[]>([
  { id: 1, title: '简历优化咨询', updatedAt: '2026-07-13 10:30' },
  { id: 2, title: '面试准备', updatedAt: '2026-07-12 15:20' },
  { id: 3, title: '职业规划建议', updatedAt: '2026-07-11 09:15' },
])

const currentSession = ref<Session | null>(sessions.value[0])
const initialMessages: Message[] = [
  {
    id: 'm1',
    role: 'assistant',
    content: '你好！我是AI求职助手。你可以问我关于简历优化、面试准备、职业规划等方面的问题。有什么我可以帮你的吗？',
    createdAt: '2026-07-13 10:30:00',
  },
]
const messages = ref<Message[]>([...initialMessages])

// 每个会话的消息存储
const sessionMessagesMap = reactive<Record<number, Message[]>>({
  1: [...initialMessages],
  2: [
    {
      id: 'm2_1',
      role: 'assistant',
      content: '面试准备是一个非常系统的工作。你想了解哪方面的准备？技术面试还是行为面试？',
      createdAt: '2026-07-12 15:20:00',
    },
  ],
  3: [
    {
      id: 'm3_1',
      role: 'assistant',
      content: '职业规划是一个长期过程。你目前处于什么阶段？我可以给你针对性的建议。',
      createdAt: '2026-07-11 09:15:00',
    },
  ],
})

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
  const parts = str.split(' ')
  return parts[1] || ''
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function createSession() {
  const newSession = {
    id: Date.now(),
    title: `新会话 ${sessions.value.length + 1}`,
    updatedAt: new Date().toLocaleString('zh-CN'),
  }
  sessions.value.unshift(newSession)
  sessionMessagesMap[newSession.id] = []
  // 保存当前会话消息
  if (currentSession.value) {
    sessionMessagesMap[currentSession.value.id] = [...messages.value]
  }
  currentSession.value = newSession
  messages.value = []
}

function selectSession(session: Session) {
  // 保存当前会话的消息
  if (currentSession.value) {
    sessionMessagesMap[currentSession.value.id] = [...messages.value]
  }
  currentSession.value = session
  // 加载目标会话的消息
  messages.value = sessionMessagesMap[session.id]
    ? [...sessionMessagesMap[session.id]]
    : []
}

function deleteSession(id: number) {
  sessions.value = sessions.value.filter(s => s.id !== id)
  delete sessionMessagesMap[id]
  if (currentSession.value?.id === id) {
    currentSession.value = sessions.value[0] || null
    messages.value = currentSession.value && sessionMessagesMap[currentSession.value.id]
      ? [...sessionMessagesMap[currentSession.value.id]]
      : []
  }
  ElMessage.success('会话已删除')
}

function sendSuggestion(text: string) {
  inputText.value = text
  handleSend()
}

// AI responses for demo
const aiResponses: Record<string, string> = {
  '简历': '优化简历中的工作经历时，建议使用STAR法则（Situation情境、Task任务、Action行动、Result结果）来描述你的工作经历。重点突出你取得的**量化成果**，比如"提升了30%的页面加载速度"比"优化了性能"更有说服力。此外，确保简历中的技能与目标岗位要求相匹配，使用行业关键词。',
  '面试': '技术面试前建议做好以下准备：\n\n1. **基础知识复习**：HTML/CSS/JavaScript核心概念\n2. **框架原理**：Vue/React的生命周期、响应式原理等\n3. **手撕代码**：练习常见的算法题和手写API\n4. **项目复盘**：深入理解你简历上的每个项目\n5. **模拟面试**：使用我们的AI面试功能进行练习',
  '职业': '前端工程师的典型发展路径：\n\n1. **初级工程师**（0-2年）：掌握基础技术栈，能独立完成页面开发\n2. **中级工程师**（2-5年）：具备架构思维，能主导项目\n3. **高级工程师**（5-8年）：技术专家，能制定技术方案\n4. **技术专家/架构师**（8年+）：技术决策者，影响团队技术方向\n5. **技术管理**：转向技术管理，如Tech Lead或CTO\n\n建议在工作中持续学习，关注行业趋势，积极参与开源项目。',
  '缺点': '回答"你的缺点"时的技巧：\n\n1. 选择**真实的但非致命的**缺点\n2. 展示你已经在**积极改进**\n3. 举例说明你采取的**具体行动**\n\n示例："我有时候会过于追求代码完美，导致开发进度偏慢。后来我学会了在项目初期就设定好质量标准，在质量和效率之间找到平衡。现在我能更好地控制代码质量与交付时间的关系。"',
  '评价': '自我评价不是必须的，但写得好可以加分：\n\n1. 避免空洞的形容词（如"吃苦耐劳"）\n2. 结合具体能力来写（如"3年前端经验，擅长性能优化"）\n3. 放在简历顶部作为"个人总结"\n4. 控制在3-4句话\n\n更好的做法是用简洁的"个人优势"模块替代传统的自我评价。',
  '跳槽': '跳槽的最佳时机取决于多个因素：\n\n1. **时机**：金三银四（3-4月）和金九银十（9-10月）\n2. **准备**：确保技能达到目标岗位要求\n3. **市场**：关注行业招聘趋势\n4. **内部发展**：先考虑内部晋升机会\n\n建议至少在当前公司待满1-2年，频繁跳槽会影响简历评分。',
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  // Add user message
  messages.value.push({
    id: 'msg_' + Date.now(),
    role: 'user',
    content: text,
    createdAt: new Date().toLocaleString('zh-CN'),
  })
  inputText.value = ''
  scrollToBottom()

  // Simulate AI response with streaming
  isStreaming.value = true
  streamingText.value = ''

  setTimeout(() => {
    const keyword = Object.keys(aiResponses).find(k => text.includes(k)) || '简历'
    const response = aiResponses[keyword]

    let charIndex = 0
    const streamInterval = setInterval(() => {
      if (charIndex < response.length) {
        streamingText.value += response[charIndex]
        charIndex++
        scrollToBottom()
      } else {
        clearInterval(streamInterval)
        isStreaming.value = false
        messages.value.push({
          id: 'msg_' + Date.now(),
          role: 'assistant',
          content: response,
          createdAt: new Date().toLocaleString('zh-CN'),
        })
        scrollToBottom()
      }
    }, 30)
  }, 800)
}
</script>

<style scoped>
.session-item {
  border-left: 3px solid transparent;
  transition: all 0.2s;
}
.session-item:hover {
  background-color: #f9fafb;
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
