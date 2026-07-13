<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  score: number
}>()

const levelConfig = computed(() => {
  const s = props.score
  if (s >= 90) {
    return {
      label: '完美匹配',
      description: '您的经历与该岗位高度契合，强烈推荐投递',
      color: 'bg-green-500',
      textColor: 'text-green-700',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
    }
  }
  if (s >= 80) {
    return {
      label: '优秀',
      description: '您的条件非常符合该岗位要求',
      color: 'bg-emerald-500',
      textColor: 'text-emerald-700',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
    }
  }
  if (s >= 60) {
    return {
      label: '良好',
      description: '您具备该岗位的基础条件，可尝试投递',
      color: 'bg-amber-500',
      textColor: 'text-amber-700',
      bgColor: 'bg-amber-50',
      borderColor: 'border-amber-200',
    }
  }
  if (s >= 40) {
    return {
      label: '一般',
      description: '部分条件匹配，建议补充相关经验后投递',
      color: 'bg-orange-500',
      textColor: 'text-orange-700',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
    }
  }
  return {
    label: '较低',
    description: '与该岗位要求差距较大，建议寻找其他机会',
    color: 'bg-red-500',
    textColor: 'text-red-700',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
  }
})
</script>

<template>
  <el-tooltip
    :content="levelConfig.description"
    placement="top"
    :show-after="300"
    popper-class="match-badge-tooltip"
  >
    <span
      class="match-badge inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border"
      :class="[
        levelConfig.bgColor,
        levelConfig.textColor,
        levelConfig.borderColor,
      ]"
    >
      <span
        class="w-1.5 h-1.5 rounded-full"
        :class="levelConfig.color"
      />
      {{ score }}% {{ levelConfig.label }}
    </span>
  </el-tooltip>
</template>

<style scoped>
.match-badge {
  white-space: nowrap;
  transition: all 0.15s ease;
}

.match-badge:hover {
  filter: brightness(0.95);
}
</style>

<style>
.match-badge-tooltip {
  max-width: 240px;
  font-size: 12px;
  line-height: 1.5;
}
</style>