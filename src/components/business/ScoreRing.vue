<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'

const props = withDefaults(defineProps<{
  score: number
  size?: number
  strokeWidth?: number
}>(), {
  size: 80,
  strokeWidth: 6,
})

const animatedScore = ref(0)

onMounted(() => {
  // Animate score counting
  const target = Math.min(Math.max(props.score, 0), 100)
  const duration = 800
  const start = performance.now()

  function animate(time: number) {
    const elapsed = time - start
    const progress = Math.min(elapsed / duration, 1)
    // Ease-out cubic
    const eased = 1 - Math.pow(1 - progress, 3)
    animatedScore.value = Math.round(target * eased)
    if (progress < 1) {
      requestAnimationFrame(animate)
    }
  }
  requestAnimationFrame(animate)
})

const radius = computed(() => {
  return (props.size - props.strokeWidth) / 2
})

const circumference = computed(() => {
  return 2 * Math.PI * radius.value
})

const center = computed(() => props.size / 2)

const strokeDashoffset = computed(() => {
  const clamped = Math.min(Math.max(props.score, 0), 100)
  return circumference.value * (1 - clamped / 100)
})

const strokeColor = computed(() => {
  if (props.score >= 80) return '#10b981'
  if (props.score >= 60) return '#f59e0b'
  return '#ef4444'
})

const trackColor = computed(() => {
  if (props.score >= 80) return '#d1fae5'
  if (props.score >= 60) return '#fef3c7'
  return '#fee2e2'
})

const textColor = computed(() => {
  if (props.score >= 70) return 'text-green-600'
  if (props.score >= 50) return 'text-amber-600'
  return 'text-red-600'
})
</script>

<template>
  <div
    class="score-ring inline-flex items-center justify-center"
    :style="{ width: size + 'px', height: size + 'px' }"
  >
    <svg
      :width="size"
      :height="size"
      :viewBox="`0 0 ${size} ${size}`"
      class="transform -rotate-90"
    >
      <!-- Track circle -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        :stroke="trackColor"
        :stroke-width="strokeWidth"
        fill="none"
        class="transition-colors duration-500"
      />
      <!-- Progress circle -->
      <circle
        :cx="center"
        :cy="center"
        :r="radius"
        :stroke="strokeColor"
        :stroke-width="strokeWidth"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="strokeDashoffset"
        stroke-linecap="round"
        fill="none"
        class="progress-circle transition-colors duration-500"
      />
    </svg>
    <!-- Score text centered -->
    <span
      class="score-text absolute font-bold leading-none"
      :class="textColor"
      :style="{ fontSize: Math.max(size * 0.22, 12) + 'px' }"
    >
      {{ animatedScore }}
    </span>
  </div>
</template>

<style scoped>
.score-ring {
  position: relative;
}

.progress-circle {
  transition: stroke-dashoffset 0.3s ease;
}

.score-text {
  pointer-events: none;
}
</style>