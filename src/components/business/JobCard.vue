<script setup lang="ts">
import type { Job } from '@/types'
import ScoreRing from '@/components/business/ScoreRing.vue'
import { Briefcase, Location, Money, School, Timer } from '@element-plus/icons-vue'
import { computed } from 'vue'

const props = defineProps<{
  job: Job
}>()

const salaryDisplay = computed(() => {
  if (props.job.salary_min && props.job.salary_max) {
    return `${props.job.salary_min / 1000}k-${props.job.salary_max / 1000}k`
  }
  return '薪资面议'
})

const matchLevel = computed(() => {
  const score = props.job.match_score
  if (score >= 80) return { label: '高度匹配', color: 'text-green-600', bg: 'bg-green-50' }
  if (score >= 60) return { label: '较为匹配', color: 'text-amber-600', bg: 'bg-amber-50' }
  if (score >= 40) return { label: '部分匹配', color: 'text-orange-600', bg: 'bg-orange-50' }
  return { label: '匹配度较低', color: 'text-red-600', bg: 'bg-red-50' }
})
</script>

<template>
  <el-card
    class="job-card group !border-gray-100 transition-all duration-300 cursor-pointer"
    shadow="hover"
    @click="$router.push(`/jobs/${job.id}`)"
  >
    <div class="flex items-start gap-4">
      <!-- Company logo placeholder -->
      <div
        class="w-14 h-14 rounded-xl bg-gray-50 border border-gray-200 flex items-center justify-center flex-shrink-0 overflow-hidden"
      >
        <img
          v-if="job.company_logo"
          :src="job.company_logo"
          :alt="job.company"
          class="w-full h-full object-contain p-1"
        />
        <el-icon v-else :size="28" class="text-gray-400">
          <Briefcase />
        </el-icon>
      </div>

      <!-- Job info -->
      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="text-base font-semibold text-gray-900 truncate m-0">
              {{ job.title }}
            </h3>
            <p class="mt-0.5 text-sm text-gray-500">{{ job.company }}</p>
          </div>

          <!-- Match score ring -->
          <div class="flex flex-col items-center flex-shrink-0">
            <ScoreRing :score="job.match_score" :size="56" :stroke-width="4" />
            <span
              class="text-[10px] font-medium mt-0.5 whitespace-nowrap"
              :class="matchLevel.color"
            >
              {{ matchLevel.label }}
            </span>
          </div>
        </div>

        <!-- Meta info -->
        <div class="mt-3 flex flex-wrap items-center gap-3 text-xs text-gray-500">
          <span class="flex items-center gap-1">
            <el-icon :size="12"><Money /></el-icon>
            <span class="font-medium text-indigo-600">{{ salaryDisplay }}</span>
          </span>
          <span class="flex items-center gap-1">
            <el-icon :size="12"><Location /></el-icon>
            {{ job.city }}
          </span>
          <span v-if="job.experience_required" class="flex items-center gap-1">
            <el-icon :size="12"><Timer /></el-icon>
            {{ job.experience_required }}
          </span>
          <span v-if="job.education_required" class="flex items-center gap-1">
            <el-icon :size="12"><School /></el-icon>
            {{ job.education_required }}
          </span>
        </div>

        <!-- Skills -->
        <div class="mt-3 flex flex-wrap gap-1.5">
          <el-tag
            v-for="skill in job.skills.slice(0, 5)"
            :key="skill"
            size="small"
            effect="plain"
            class="!rounded !bg-indigo-50 !text-indigo-700 !border-indigo-100 !text-xs"
          >
            {{ skill }}
          </el-tag>
          <el-tag
            v-if="job.skills.length > 5"
            size="small"
            class="!rounded !bg-gray-50 !text-gray-500 !border-gray-200 !text-xs"
          >
            +{{ job.skills.length - 5 }}
          </el-tag>
        </div>

        <!-- Match reasons -->
        <div v-if="job.match_reasons?.length" class="mt-3">
          <div class="flex flex-col gap-1">
            <div
              v-for="(reason, idx) in job.match_reasons.slice(0, 3)"
              :key="idx"
              class="flex items-start gap-1.5 text-xs text-gray-600"
            >
              <span class="text-green-500 mt-0.5 flex-shrink-0">&#10003;</span>
              <span>{{ reason }}</span>
            </div>
          </div>
        </div>

        <!-- View detail button -->
        <div class="mt-4 flex justify-end">
          <el-button
            type="primary"
            size="small"
            round
            @click.stop="$router.push(`/jobs/${job.id}`)"
          >
            查看详情
          </el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.job-card {
  border-radius: 12px;
}

.job-card:hover {
  transform: translateY(-2px);
}
</style>
