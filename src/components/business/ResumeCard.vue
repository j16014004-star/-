<script setup lang="ts">
import type { Resume } from '@/types'
import StatusTag from '@/components/common/StatusTag.vue'
import ScoreRing from '@/components/business/ScoreRing.vue'
import {
  Document,
  View,
  DataAnalysis,
  EditPen,
  Delete,
} from '@element-plus/icons-vue'
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  resume: Resume
  showActions?: boolean
}>(), {
  showActions: true,
})

const emit = defineEmits<{
  view: [resume: Resume]
  analyze: [resume: Resume]
  optimize: [resume: Resume]
  delete: [resume: Resume]
}>()

const fileTypeLabel = computed(() => {
  const map: Record<string, string> = {
    pdf: 'PDF',
    word: 'Word',
    doc: 'Word',
    docx: 'Word',
    text: '文本',
    txt: '文本',
    html: 'HTML',
  }
  return map[props.resume.file_type] || props.resume.file_type
})

const formattedDate = computed(() => {
  const date = props.resume.created_at
  if (!date) return ''
  try {
    const d = new Date(date)
    return d.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    })
  } catch {
    return date
  }
})
</script>

<template>
  <el-card
    class="resume-card group !border-gray-100 hover:!border-indigo-200 transition-all duration-300"
    shadow="hover"
  >
    <!-- Card top: icon + info -->
    <div class="flex items-start gap-4">
      <!-- File icon -->
      <div
        class="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0"
      >
        <el-icon :size="24" class="text-indigo-500">
          <Document />
        </el-icon>
      </div>

      <!-- Resume info -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h3 class="text-base font-semibold text-gray-900 truncate m-0">
            {{ resume.title }}
          </h3>
          <StatusTag :status="resume.status" />
        </div>
        <div class="mt-1 flex items-center gap-3 text-xs text-gray-500">
          <span>{{ fileTypeLabel }}</span>
          <span class="w-1 h-1 rounded-full bg-gray-300" />
          <span>上传于 {{ formattedDate }}</span>
        </div>
        <!-- Skills preview -->
        <div v-if="resume.analysis?.strengths" class="mt-2 flex flex-wrap gap-1">
          <el-tag
            v-for="skill in resume.analysis.strengths.slice(0, 3)"
            :key="skill"
            size="small"
            effect="plain"
            class="!bg-gray-50 !text-gray-600 !border-gray-200"
          >
            {{ skill }}
          </el-tag>
        </div>
      </div>

      <!-- Score ring -->
      <ScoreRing
        v-if="resume.score !== undefined"
        :score="resume.score"
        :size="64"
        :stroke-width="5"
      />
    </div>

    <!-- Actions -->
    <div
      v-if="showActions"
      class="mt-4 pt-3 border-t border-gray-100 flex items-center gap-1"
    >
      <el-button
        text
        size="small"
        @click="emit('view', resume)"
        class="action-btn"
      >
        <el-icon :size="14"><View /></el-icon>
        查看
      </el-button>
      <el-button
        text
        size="small"
        @click="emit('analyze', resume)"
        class="action-btn"
      >
        <el-icon :size="14"><DataAnalysis /></el-icon>
        分析
      </el-button>
      <el-button
        text
        size="small"
        @click="emit('optimize', resume)"
        class="action-btn"
      >
        <el-icon :size="14"><EditPen /></el-icon>
        优化
      </el-button>
      <el-button
        text
        size="small"
        type="danger"
        @click="emit('delete', resume)"
        class="action-btn"
      >
        <el-icon :size="14"><Delete /></el-icon>
        删除
      </el-button>
    </div>
  </el-card>
</template>

<style scoped>
.resume-card {
  border-radius: 12px;
}

.resume-card:hover {
  transform: translateY(-1px);
}

.action-btn {
  font-size: 12px;
  padding: 4px 8px;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background-color: #f5f3ff !important;
}
</style>