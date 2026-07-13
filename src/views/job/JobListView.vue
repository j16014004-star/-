<template>
  <div class="job-list-view p-6 bg-gray-50 min-h-screen">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">岗位推荐</h1>
      <p class="text-gray-500 text-sm mt-1">AI智能匹配的高薪职位推荐</p>
    </div>

    <!-- Filters -->
    <el-card class="mb-6 border-0">
      <el-row :gutter="20" align="middle">
        <el-col :xs="24" :sm="8" :md="6">
          <el-input v-model="filters.keyword" placeholder="搜索职位/公司" clearable>
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-select v-model="filters.city" placeholder="选择城市" clearable class="w-full">
            <el-option label="北京" value="北京" />
            <el-option label="上海" value="上海" />
            <el-option label="深圳" value="深圳" />
            <el-option label="杭州" value="杭州" />
            <el-option label="广州" value="广州" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="8" :md="6">
          <el-select v-model="filters.salary" placeholder="薪资范围" clearable class="w-full">
            <el-option label="10k以下" value="0-10" />
            <el-option label="10k-20k" value="10-20" />
            <el-option label="20k-40k" value="20-40" />
            <el-option label="40k以上" value="40-100" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="24" :md="6">
          <div class="flex gap-2">
            <el-button type="primary" @click="handleSearch">
              <el-icon class="mr-1"><Search /></el-icon>
              搜索
            </el-button>
            <el-switch v-model="aiMatch" active-text="AI匹配" inactive-text="" class="ml-4" />
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- Results Stats -->
    <div class="flex items-center justify-between mb-4">
      <div class="text-sm text-gray-500">
        共找到 <span class="font-semibold text-indigo-600">{{ jobs.length }}</span> 个匹配职位
      </div>
      <el-radio-group v-model="sortBy" size="small">
        <el-radio-button label="match">匹配度</el-radio-button>
        <el-radio-button label="salary">薪资</el-radio-button>
        <el-radio-button label="date">最新</el-radio-button>
      </el-radio-group>
    </div>

    <!-- Job Cards -->
    <el-row :gutter="20">
      <el-col v-for="job in pagedJobs" :key="job.id" :xs="24" :sm="12" :lg="8" class="mb-4">
        <el-card class="job-card border-0 cursor-pointer h-full" shadow="hover" body-style="padding: 24px">
          <!-- Header -->
          <div class="flex items-start justify-between mb-3">
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-gray-800 text-lg mb-1 truncate">{{ job.title }}</h3>
              <div class="flex items-center gap-2 text-sm text-gray-500">
                <span class="font-medium">{{ job.company }}</span>
                <span>•</span>
                <span>{{ job.city }}</span>
              </div>
            </div>
            <div class="flex-shrink-0 ml-4">
              <div class="relative w-16 h-16">
                <svg class="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="16" fill="none" :stroke="getMatchColor(job.matchScore)" stroke-width="3" />
                  <circle
                    cx="18" cy="18" r="16" fill="none"
                    :stroke="getMatchColor(job.matchScore)"
                    stroke-width="3"
                    :stroke-dasharray="100"
                    :stroke-dashoffset="100 - job.matchScore"
                    stroke-linecap="round"
                  />
                </svg>
                <div class="absolute inset-0 flex items-center justify-center text-xs font-bold" :style="{ color: getMatchColor(job.matchScore) }">
                  {{ job.matchScore }}%
                </div>
              </div>
            </div>
          </div>

          <!-- Salary -->
          <div class="text-2xl font-bold text-indigo-600 mb-3">
            {{ job.salaryMin }}k-{{ job.salaryMax }}k
          </div>

          <!-- Requirements -->
          <div class="flex flex-wrap gap-1 mb-3 text-xs">
            <el-tag size="small" type="info" effect="plain">{{ job.experience }}</el-tag>
            <el-tag size="small" type="info" effect="plain">{{ job.education }}</el-tag>
          </div>

          <!-- Skills -->
          <div class="flex flex-wrap gap-1 mb-4">
            <el-tag v-for="skill in job.skills" :key="skill" size="small" effect="light">{{ skill }}</el-tag>
          </div>

          <!-- Match Reasons -->
          <div class="text-xs text-gray-500 mb-4">
            <div class="font-medium mb-1">匹配原因：</div>
            <ul class="list-disc list-inside space-y-1">
              <li v-for="(reason, i) in job.matchReasons" :key="i">{{ reason }}</li>
            </ul>
          </div>

          <!-- Actions -->
          <div class="flex gap-2">
            <el-button type="primary" size="small" class="flex-1" @click="handleApply(job.id)">
              立即申请
            </el-button>
            <el-button size="small" @click="handleFavorite(job.id)">
              <el-icon><Star /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Pagination -->
    <div class="flex justify-center mt-8">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="9"
        :total="jobs.length"
        layout="prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { jobApi } from '@/api/job'

const filters = reactive({
  keyword: '',
  city: '',
  salary: '',
})

const aiMatch = ref(true)
const sortBy = ref('match')
const currentPage = ref(1)
const isLoading = ref(false)

const jobs = ref<any[]>([])

// 从后端 API 加载推荐岗位
async function loadJobs() {
  isLoading.value = true
  try {
    const response = await jobApi.getRecommendations({
      keyword: filters.keyword,
      city: filters.city,
      salary_min: filters.salary ? parseInt(filters.salary) : undefined,
      page: currentPage.value,
      page_size: pageSize
    })
    jobs.value = (response.data?.items || []).map((job: any) => ({
      id: job.id,
      title: job.title,
      company: job.company_name || job.company,
      city: job.city,
      salaryMin: job.salary_min,
      salaryMax: job.salary_max,
      experience: job.experience,
      education: job.education,
      skills: job.skills || [],
      matchScore: job.match_score || 0,
      matchReasons: job.match_reasons || []
    }))
  } catch (error) {
    ElMessage.error('加载岗位推荐失败')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadJobs()
})

const pageSize = 9
const pagedJobs = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return jobs.value.slice(start, start + pageSize)
})

function getMatchColor(score: number): string {
  if (score >= 85) return '#10b981'
  if (score >= 70) return '#f59e0b'
  return '#ef4444'
}

function handleSearch() {
  currentPage.value = 1
  loadJobs()
}

function handlePageChange(page: number) {
  currentPage.value = page
}

function handleApply(id: number) {
  ElMessage.success(`已申请职位 #${id}`)
}

function handleFavorite(id: number) {
  ElMessage.success(`已收藏职位 #${id}`)
}
</script>

<style scoped>
.job-list-view :deep(.el-card) {
  border-radius: 16px;
}
.job-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08) !important;
}
:deep(.el-button--primary) {
  border-radius: 10px;
  font-weight: 500;
}
</style>
