<script setup lang="ts">
import { computed, type Component } from 'vue'
import { CaretTop, CaretBottom } from '@element-plus/icons-vue'

const props = defineProps<{
  title: string
  value: string | number
  icon?: string | Component
  color?: string
  trend?: number
}>()

const trendIcon = computed(() => {
  if (props.trend === undefined) return null
  return props.trend >= 0 ? CaretTop : CaretBottom
})

const trendColor = computed(() => {
  if (props.trend === undefined) return ''
  return props.trend >= 0 ? 'text-green-500' : 'text-red-500'
})

const trendText = computed(() => {
  if (props.trend === undefined) return ''
  const abs = Math.abs(props.trend)
  return `${abs}%`
})

const displayValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})
</script>

<template>
  <el-card
    class="stat-card group cursor-pointer !border-none"
    shadow="hover"
    :body-style="{ padding: '20px' }"
  >
    <div class="flex items-start justify-between">
      <!-- Icon -->
      <div
        class="stat-icon w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
        :class="color ? '' : 'bg-indigo-50 text-indigo-600'"
        :style="color ? { backgroundColor: color + '15', color: color } : {}"
      >
        <el-icon :size="24">
          <component :is="icon" v-if="icon" />
          <svg v-else viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
          </svg>
        </el-icon>
      </div>

      <!-- Trend badge -->
      <div
        v-if="trend !== undefined"
        class="flex items-center gap-0.5 text-xs font-medium"
        :class="trendColor"
      >
        <el-icon :size="14">
          <component :is="trendIcon" />
        </el-icon>
        {{ trendText }}
      </div>
    </div>

    <!-- Value and label -->
    <div class="mt-4">
      <div class="text-2xl font-bold text-gray-900 leading-none">
        {{ displayValue }}
      </div>
      <div class="mt-2 text-sm text-gray-500">{{ title }}</div>
    </div>

    <!-- Extra slot -->
    <slot />
  </el-card>
</template>

<style scoped>
.stat-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  transition: transform 0.2s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.05);
}
</style>