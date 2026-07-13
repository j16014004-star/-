<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage } from '@/types'
import StreamingText from '@/components/business/StreamingText.vue'
import { User, ChatDotSquare } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  message: ChatMessage
  isStreaming?: boolean
}>(), {
  isStreaming: false,
})

const isUser = computed(() => props.message.role === 'user')

const formattedTime = computed(() => {
  const ts = props.message.created_at
  if (!ts) return ''
  try {
    const d = new Date(ts)
    const now = new Date()
    const isToday = d.toDateString() === now.toDateString()
    if (isToday) {
      return d.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      })
    }
    return d.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return String(ts)
  }
})
</script>

<template>
  <div
    class="chat-bubble flex gap-3 mb-4"
    :class="isUser ? 'flex-row-reverse' : 'flex-row'"
  >
    <!-- Avatar -->
    <div
      class="chat-avatar flex-shrink-0"
      :class="isUser ? 'ml-3' : 'mr-3'"
    >
      <el-avatar
        v-if="isUser"
        :size="36"
        class="!bg-indigo-500"
        shape="circle"
      >
        <el-icon :size="20"><User /></el-icon>
      </el-avatar>
      <el-avatar
        v-else
        :size="36"
        class="!bg-indigo-100 !text-indigo-600"
        shape="circle"
      >
        <el-icon :size="20"><ChatDotSquare /></el-icon>
      </el-avatar>
    </div>

    <!-- Bubble content -->
    <div class="max-w-[75%] min-w-0">
      <!-- Role label -->
      <div
        class="text-xs text-gray-400 mb-1"
        :class="isUser ? 'text-right' : 'text-left'"
      >
        {{ isUser ? '你' : 'AI助手' }}
        <span class="ml-2">{{ formattedTime }}</span>
      </div>

      <!-- Message body -->
      <div
        class="rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words"
        :class="
          isUser
            ? 'bg-indigo-500 text-white rounded-tr-sm'
            : 'bg-gray-100 text-gray-800 rounded-tl-sm border border-gray-200'
        "
      >
        <!-- Streaming text for assistant -->
        <StreamingText
          v-if="!isUser && isStreaming"
          :text="message.content"
          :speed="25"
        />
        <!-- Normal text rendering -->
        <template v-else>
          {{ message.content }}
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-bubble {
  animation: fadeInUp 0.25s ease;
}

.chat-avatar {
  transition: transform 0.15s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>