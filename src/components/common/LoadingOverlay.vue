<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'

defineProps<{
  loading: boolean
  text?: string
}>()
</script>

<template>
  <div
    v-if="loading"
    class="loading-overlay fixed inset-0 z-[999] flex items-center justify-center"
  >
    <!-- Semi-transparent background -->
    <div class="absolute inset-0 bg-white/70 backdrop-blur-sm" />

    <!-- Spinner content -->
    <div class="relative flex flex-col items-center gap-3">
      <el-icon class="loading-spinner !text-indigo-500" :size="40">
        <Loading />
      </el-icon>
      <p
        v-if="text"
        class="text-sm text-gray-500 font-medium"
      >
        {{ text }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.loading-overlay {
  animation: fadeIn 0.2s ease;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>