<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  type?: string
}>()

interface StatusConfig {
  type: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  label: string
}

const statusMap: Record<string, StatusConfig> = {
  pending: { type: 'warning', label: '待处理' },
  running: { type: 'primary', label: '运行中' },
  in_progress: { type: 'primary', label: '进行中' },
  completed: { type: 'success', label: '已完成' },
  finished: { type: 'success', label: '已完成' },
  failed: { type: 'danger', label: '失败' },
  paused: { type: 'info', label: '已暂停' },
  analyzing: { type: 'primary', label: '分析中' },
  analyzed: { type: 'success', label: '已分析' },
  optimizing: { type: 'warning', label: '优化中' },
  optimized: { type: 'success', label: '已优化' },
  submitted: { type: 'primary', label: '已投递' },
  viewed: { type: 'warning', label: '已被查看' },
  interviewing: { type: 'primary', label: '面试中' },
  accepted: { type: 'success', label: '已通过' },
  rejected: { type: 'danger', label: '未通过' },
  replied: { type: 'info', label: '已回复' },
  archived: { type: 'info', label: '已归档' },
}

const config = computed(() => {
  const key = props.type || props.status
  return statusMap[key] || { type: 'info', label: props.status }
})
</script>

<template>
  <el-tag
    :type="config.type"
    size="small"
    effect="light"
    class="status-tag"
    disable-transitions
  >
    {{ config.label }}
  </el-tag>
</template>

<style scoped>
.status-tag {
  font-weight: 500;
  border-radius: 4px;
  padding: 0 8px;
  height: 24px;
  line-height: 24px;
}
</style>