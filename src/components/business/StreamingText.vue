<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  text: string
  speed?: number
}>(), {
  speed: 30,
})

const emit = defineEmits<{
  complete: []
}>()

const displayText = ref('')
let currentIndex = 0
let timer: ReturnType<typeof setInterval> | null = null

function startTyping() {
  stopTyping()
  if (!props.text) {
    emit('complete')
    return
  }

  currentIndex = 0
  displayText.value = ''

  timer = setInterval(() => {
    if (currentIndex < props.text.length) {
      // Handle multi-byte characters (emojis, CJK, etc.)
      const char = props.text.charAt(currentIndex)
      displayText.value += char
      currentIndex++
    } else {
      stopTyping()
      emit('complete')
    }
  }, props.speed)
}

function stopTyping() {
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
}

// Watch for text changes
watch(
  () => props.text,
  (newText) => {
    if (newText) {
      startTyping()
    } else {
      stopTyping()
      displayText.value = ''
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  stopTyping()
})
</script>

<template>
  <span class="streaming-text">
    {{ displayText }}
    <span
      v-if="displayText.length < text.length"
      class="cursor-blink inline-block w-[2px] h-[1.1em] bg-indigo-500 align-middle ml-0.5"
    />
  </span>
</template>

<style scoped>
.streaming-text {
  word-break: break-word;
  line-height: 1.6;
}

.cursor-blink {
  animation: blink 0.8s step-end infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
</style>