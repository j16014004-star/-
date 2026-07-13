<template>
  <div class="hr-chat-view flex h-[calc(100vh-60px)]">
    <!-- Message List -->
    <div class="w-80 border-r bg-white flex-shrink-0 flex flex-col">
      <div class="p-4 border-b">
        <div class="font-semibold text-gray-800">HR消息</div>
        <div class="text-xs text-gray-400 mt-1">共 {{ messages.length }} 条消息</div>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div
          v-for="msg in messages"
          :key="msg.id"
          class="message-item px-4 py-3 cursor-pointer hover:bg-gray-50 border-b border-gray-50"
          :class="{ 'bg-indigo-50': selectedMessage?.id === msg.id, 'border-l-3 border-l-indigo-500': selectedMessage?.id === msg.id }"
          @click="selectMessage(msg)"
        >
          <div class="flex items-start gap-3">
            <el-avatar :size="40" class="bg-indigo-100 text-indigo-600 font-bold">
              {{ msg.hrName.charAt(0) }}
            </el-avatar>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <span class="font-medium text-sm text-gray-800">{{ msg.hrName }}</span>
                <span class="text-xs text-gray-400">{{ formatTime(msg.createdAt) }}</span>
              </div>
              <div class="text-xs text-gray-500 truncate mt-1">{{ msg.company }}</div>
              <div class="text-xs text-gray-400 truncate mt-1">{{ msg.content }}</div>
            </div>
            <div v-if="msg.status === 'pending'" class="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0 mt-2"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Message Detail -->
    <div class="flex-1 flex flex-col min-w-0 bg-gray-50">
      <template v-if="selectedMessage">
        <!-- Header -->
        <div class="px-6 py-4 bg-white border-b">
          <div class="flex items-center gap-3">
            <el-avatar :size="44" class="bg-indigo-100 text-indigo-600 font-bold text-lg">
              {{ selectedMessage.hrName.charAt(0) }}
            </el-avatar>
            <div class="flex-1">
              <div class="font-semibold text-gray-800">{{ selectedMessage.hrName }}</div>
              <div class="text-sm text-gray-500">{{ selectedMessage.company }} · HR</div>
            </div>
            <el-tag :type="selectedMessage.status === 'pending' ? 'warning' : selectedMessage.status === 'replied' ? 'success' : 'info'" effect="plain">
              {{ selectedMessage.status === 'pending' ? '待回复' : selectedMessage.status === 'replied' ? '已回复' : '已归档' }}
            </el-tag>
          </div>
        </div>

        <!-- Message Content -->
        <div class="flex-1 overflow-y-auto p-6">
          <div class="max-w-2xl mx-auto">
            <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
              <div class="text-gray-700 leading-relaxed whitespace-pre-wrap">{{ selectedMessage.content }}</div>
              <div class="text-xs text-gray-400 mt-4">{{ selectedMessage.createdAt }}</div>
            </div>

            <!-- AI Reply Suggestions -->
            <div class="mt-6" v-if="selectedMessage.status === 'pending'">
              <div class="font-medium text-sm text-gray-700 mb-3">
                <el-icon class="mr-1"><MagicStick /></el-icon>
                AI回复建议
              </div>
              <div v-if="!showSuggestions">
                <el-button type="primary" plain @click="generateSuggestions">
                  <el-icon class="mr-1"><MagicStick /></el-icon>
                  生成回复建议
                </el-button>
              </div>
              <div v-else class="space-y-3">
                <div
                  v-for="(suggestion, index) in replySuggestions"
                  :key="index"
                  class="p-4 rounded-xl bg-indigo-50 border border-indigo-100 cursor-pointer hover:bg-indigo-100 transition-colors"
                  @click="useSuggestion(index)"
                >
                  <div class="text-sm text-gray-700 leading-relaxed">{{ suggestion }}</div>
                </div>
              </div>
            </div>

            <!-- Reply History -->
            <div v-if="replies.length > 0" class="mt-6 space-y-4">
              <div v-for="reply in replies" :key="reply.id" class="flex" :class="reply.role === 'user' ? 'justify-end' : 'justify-start'">
                <div
                  class="max-w-lg px-4 py-3 rounded-2xl text-sm leading-relaxed"
                  :class="reply.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 border border-gray-100'"
                >
                  {{ reply.content }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Reply Input -->
        <div v-if="selectedMessage.status === 'pending'" class="p-4 bg-white border-t">
          <div class="flex gap-3 max-w-2xl mx-auto">
            <el-input
              v-model="replyText"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 4 }"
              placeholder="输入回复内容..."
              class="flex-1"
              resize="none"
            />
            <div class="flex flex-col gap-2">
              <el-button type="primary" @click="sendReply" :disabled="!replyText.trim()">
                发送
              </el-button>
              <el-button @click="archiveMessage">
                归档
              </el-button>
            </div>
          </div>
        </div>
      </template>

      <!-- Empty State -->
      <div v-else class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <div class="text-6xl mb-4">&#x1F4E7;</div>
          <h3 class="text-lg font-semibold text-gray-600 mb-2">选择一条消息</h3>
          <p class="text-gray-400">从左侧选择一条HR消息查看详细内容</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Message {
  id: number
  hrName: string
  company: string
  content: string
  status: 'pending' | 'replied' | 'archived'
  createdAt: string
}

interface Reply {
  id: number
  role: 'hr' | 'user'
  content: string
}

const messages = ref<Message[]>([
  {
    id: 1,
    hrName: '李经理',
    company: '阿里巴巴',
    content: '您好，我们查看了您的简历，觉得您非常符合我们前端开发工程师的岗位要求。请问您下周有空来参加面试吗？我们提供线上面试选项。',
    status: 'pending',
    createdAt: '2026-07-13 14:30:00',
  },
  {
    id: 2,
    hrName: '王HR',
    company: '字节跳动',
    content: '你好，我们是字节跳动技术团队，目前我们正在招聘高级前端工程师。看到您的项目经验很丰富，不知是否有兴趣聊聊？薪资范围35k-60k。',
    status: 'pending',
    createdAt: '2026-07-13 11:20:00',
  },
  {
    id: 3,
    hrName: '张招聘',
    company: '腾讯',
    content: '您好，感谢您投递简历。经过初步筛选，您的简历已通过我们的人事初审。请准备以下材料：1. 技术自测表 2. 项目作品链接 3. 期望薪资说明。',
    status: 'replied',
    createdAt: '2026-07-12 16:45:00',
  },
  {
    id: 4,
    hrName: '赵总监',
    company: '美团',
    content: '面试后你好，我们技术团队对你的表现印象很深。目前已经进入最终轮HR面，请问你本周五下午3点方便吗？',
    status: 'replied',
    createdAt: '2026-07-12 10:00:00',
  },
  {
    id: 5,
    hrName: '刘HR',
    company: '百度',
    content: '抱歉，经过综合评估，该岗位已有更合适的候选人。但您的简历已入库，后续有合适的岗位我们会第一时间联系您。感谢您的关注！',
    status: 'archived',
    createdAt: '2026-07-11 09:30:00',
  },
])

const selectedMessage = ref<Message | null>(messages.value[0])
const replyText = ref('')
const showSuggestions = ref(false)
const replySuggestions = ref<string[]>([
  '您好，非常感谢贵公司的认可！我下周时间都比较灵活，可以配合贵公司的面试安排。请问具体是哪个时间段比较方便？',
  '感谢联系！我对这个岗位很感兴趣。希望能了解更多关于团队架构和技术栈的信息，方便安排面试吗？',
  '您好，非常感谢！我很乐意参加面试。请告诉我具体的面试形式和需要准备的材料，我会提前做好准备。',
])
const replies = ref<Reply[]>([
  { id: 1, role: 'user', content: '您好，非常感谢贵公司的认可！我本周五下午3点可以参加面试。请问面试的具体形式是什么？需要准备什么材料吗？' },
  { id: 2, role: 'hr', content: '好的，周五下午3点，我们会通过腾讯会议进行面试。需要准备：1.自我介绍5分钟 2.一个你最有成就感的项目介绍 3.技术问题问答。祝你面试顺利！' },
])

let nextReplyId = 3

function formatTime(str: string): string {
  return str.split(' ')[1] || ''
}

function selectMessage(msg: Message) {
  selectedMessage.value = msg
}

function generateSuggestions() {
  showSuggestions.value = true
}

function useSuggestion(index: number) {
  replyText.value = replySuggestions.value[index]
}

function sendReply() {
  if (!replyText.value.trim() || !selectedMessage.value) return
  replies.value.push({
    id: nextReplyId++,
    role: 'user',
    content: replyText.value,
  })
  selectedMessage.value.status = 'replied'
  replyText.value = ''
  ElMessage.success('回复已发送')
}

function archiveMessage() {
  if (selectedMessage.value) {
    selectedMessage.value.status = 'archived'
    ElMessage.success('已归档')
  }
}
</script>

<style scoped>
.hr-chat-view :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  resize: none;
}
.message-item {
  transition: all 0.2s;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
