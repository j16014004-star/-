<script setup lang="ts">
import { FolderOpen } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  message?: string
  icon?: string
}>(), {
  message: '暂无数据',
  icon: '',
})
</script>

<template>
  <div class="empty-state flex flex-col items-center justify-center py-16 px-4">
    <!-- Icon -->
    <div class="empty-icon mb-4 text-gray-300">
      <el-icon :size="64">
        <component :is="icon || FolderOpen" />
      </el-icon>
    </div>

    <!-- Message -->
    <p class="text-sm text-gray-400 mb-6">{{ message }}</p>

    <!-- Action slot -->
    <div v-if="$slots.action" class="empty-action">
      <slot name="action" />
    </div>

    <!-- Default slot -->
    <slot />
  </div>
</template>

<style scoped>
.empty-state {
  user-select: none;
}

.empty-icon {
  opacity: 0.7;
}
</style>