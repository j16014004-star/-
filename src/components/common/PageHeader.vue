<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

defineProps<{
  title: string
  description?: string
  showBack?: boolean
}>()

const router = useRouter()

function goBack() {
  router.back()
}
</script>

<template>
  <div class="page-header mb-6">
    <div class="flex items-start gap-4">
      <!-- Back button -->
      <el-button
        v-if="showBack"
        :icon="ArrowLeft"
        text
        size="small"
        class="!mt-1 !text-gray-400 hover:!text-indigo-600"
        @click="goBack"
      />

      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-3">
          <h1 class="text-2xl font-bold text-gray-900 m-0">{{ title }}</h1>
        </div>
        <p
          v-if="description"
          class="mt-1 text-sm text-gray-500 leading-relaxed"
        >
          {{ description }}
        </p>
      </div>

      <!-- Actions slot -->
      <div class="flex-shrink-0">
        <slot name="actions" />
      </div>
    </div>

    <!-- Bottom separator -->
    <div class="mt-4 border-b border-gray-200" />
  </div>
</template>

<style scoped>
.page-header {
  user-select: none;
}
</style>