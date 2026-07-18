<template>
  <div v-loading="isLoading" class="dashboard-view">
    <section class="welcome-panel classic-panel">
      <div class="panel-titlebar">
        <span><b>●</b> AI 自动化求职控制台</span>
        <span class="panel-tools">— □ ×</span>
      </div>
      <div class="welcome-body">
        <div class="welcome-user">
          <img src="/hakimi-logo.png" alt="哈基米AI" />
          <div>
            <h1>你好，{{ username }}</h1>
            <p><i></i> AI 求职助手在线，准备为你执行今天的求职任务</p>
          </div>
        </div>
        <div class="today-card">
          <strong>{{ todayDate }}</strong>
          <span>{{ todayWeekday }}</span>
        </div>
      </div>
    </section>

    <section class="automation-panel classic-panel">
      <div class="section-titlebar">
        <span>▾ 自动化求职流程</span>
        <small>根据简历自动完成岗位筛选、投递和沟通跟进</small>
      </div>
      <div class="automation-flow">
        <button v-for="(step, index) in automationSteps" :key="step.title" type="button" class="flow-step" @click="router.push(step.path)">
          <span class="step-number">{{ index + 1 }}</span>
          <span class="step-icon">{{ step.icon }}</span>
          <span class="step-copy"><strong>{{ step.title }}</strong><small>{{ step.desc }}</small></span>
          <span v-if="index < automationSteps.length - 1" class="flow-arrow">›</span>
        </button>
      </div>
    </section>

    <section class="stats-grid">
      <button v-for="stat in stats" :key="stat.label" type="button" class="stat-item" @click="router.push(stat.path)">
        <span class="stat-icon" :style="{ background: stat.bgColor }">{{ stat.icon }}</span>
        <span class="stat-copy"><strong>{{ stat.value }}</strong><small>{{ stat.label }}</small></span>
        <span class="stat-status"><i></i>{{ stat.status }}</span>
      </button>
    </section>

    <section class="dashboard-columns">
      <div class="classic-panel quick-panel">
        <div class="section-titlebar"><span>▾ 快捷入口</span><small>常用功能</small></div>
        <div class="quick-list">
          <button v-for="action in quickActions" :key="action.label" type="button" @click="action.handler">
            <span class="quick-icon">{{ action.icon }}</span>
            <span><strong>{{ action.label }}</strong><small>{{ action.desc }}</small></span>
            <b>›</b>
          </button>
        </div>
      </div>

      <div class="classic-panel activity-panel">
        <div class="section-titlebar">
          <span>▾ 最近动态</span>
          <button type="button" @click="router.push('/resume')">查看全部</button>
        </div>
        <div v-if="activities.length" class="activity-list">
          <div v-for="(activity, index) in activities" :key="index" class="activity-row">
            <span class="activity-icon" :style="{ background: activity.color }">{{ activity.icon }}</span>
            <span><strong>{{ activity.title }}</strong><small>{{ activity.desc }}</small></span>
            <time>{{ activity.time }}</time>
          </div>
        </div>
        <div v-else class="empty-state"><span>☁</span><p>暂无动态，先上传一份简历开始体验</p><el-button size="small" type="primary" @click="router.push('/resume/upload')">上传简历</el-button></div>
      </div>

      <div class="classic-panel interview-panel">
        <div class="section-titlebar"><span>▾ 即将到来的面试</span><small>{{ upcomingInterviews.length }} 项</small></div>
        <div v-if="upcomingInterviews.length" class="interview-list">
          <div v-for="item in upcomingInterviews" :key="item.id" class="interview-row">
            <span class="company-avatar">{{ item.company.charAt(0) }}</span>
            <span><strong>{{ item.position }}</strong><small>{{ item.company }}</small></span>
            <time>{{ item.date }}<small>{{ item.time }}</small></time>
          </div>
        </div>
        <div v-else class="empty-state compact"><span>◷</span><p>暂无即将到来的面试</p></div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { interviewApi } from '@/api/interview'
import { jobApi } from '@/api/job'
import { resumeApi } from '@/api/resume'
import { useHrAutomationStore } from '@/stores/hrAutomation'
import { storage, USER_KEY } from '@/utils/storage'
import type { Interview } from '@/types'

const router = useRouter()
const hrStore = useHrAutomationStore()
const username = ref('用户')
const isLoading = ref(false)
const activities = ref<any[]>([])
const upcomingInterviews = ref<any[]>([])

const todayDate = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
const todayWeekday = new Date().toLocaleDateString('zh-CN', { weekday: 'long' })

const baseStats = ref([
  { label: '我的简历', value: '0', icon: '▤', status: '资料中心', path: '/resume', bgColor: '#dbeafe' },
  { label: '面试次数', value: '0', icon: '▣', status: '能力训练', path: '/interview', bgColor: '#d1fae5' },
  { label: '匹配岗位', value: '0', icon: '◎', status: '智能筛选', path: '/jobs', bgColor: '#fef3c7' },
])

const stats = computed(() => [
  ...baseStats.value,
  ...(hrStore.hasWorkspace ? [{
    label: '进行中投递', value: String(hrStore.overview.active_workspaces), icon: '✉', status: 'HR 助手', path: '/hr', bgColor: '#e0e7ff',
  }] : []),
])

const automationSteps = [
  { icon: '▤', title: '上传简历', desc: 'AI 解析能力与经历', path: '/resume/upload' },
  { icon: '⌕', title: '筛选岗位', desc: '匹配最新招聘岗位', path: '/jobs' },
  { icon: '➤', title: '自动投递', desc: '验证岗位后一键投递', path: '/jobs' },
  { icon: '✉', title: '联系 HR', desc: '同步消息与面试邀约', path: '/hr' },
]

const quickActions = computed(() => [
  { icon: '▤', label: '上传简历', desc: '上传并分析简历', handler: () => router.push('/resume/upload') },
  { icon: '⌕', label: '查看岗位', desc: '浏览匹配岗位', handler: () => router.push('/jobs') },
  { icon: '▣', label: '开始面试', desc: 'AI 模拟面试训练', handler: () => router.push('/interview/lobby') },
  ...(hrStore.hasWorkspace ? [{ icon: '✉', label: 'HR 助手', desc: '查看投递与 HR 沟通', handler: () => router.push('/hr') }] : []),
])

async function loadDashboardData() {
  isLoading.value = true
  baseStats.value.forEach(item => { item.value = '0' })
  activities.value = []
  upcomingInterviews.value = []
  try {
    const [resumeRes, interviewRes] = await Promise.all([
      resumeApi.getList({ page: 1, page_size: 10 }).catch(() => null),
      interviewApi.getList().catch(() => null),
    ])
    const resumeItems = resumeRes?.data?.items || []
    const interviews = (interviewRes?.data || []) as unknown as Interview[]
    const resumeCount = resumeRes?.data?.total || 0
    let jobRes = null

    if (resumeCount > 0) {
      const currentTaskRes = await jobApi.getCurrentRecommendation().catch(() => null)
      const currentTask = currentTaskRes?.data?.task
      if (currentTask && ['success', 'no_results'].includes(currentTask.status)) {
        jobRes = await jobApi.getRecommendations({ page: 1, page_size: 10 }).catch(() => null)
      }
    }

    const jobItems = jobRes?.data?.items || []
    const jobCount = jobRes?.data?.total || 0
    baseStats.value[0].value = String(resumeCount)
    baseStats.value[1].value = String(interviews.length)
    baseStats.value[2].value = String(jobCount)

    if (resumeItems.length) {
      const latest = resumeItems[0]
      activities.value.push({ title: `简历“${latest.title}”分析完成`, desc: latest.score ? `AI 评分 ${latest.score} 分` : '已生成简历分析结果', time: formatTimeAgo(latest.created_at), icon: '▤', color: '#dbeafe' })
    }
    if (interviews.length) {
      const latest = interviews[0]
      activities.value.push({ title: 'AI 模拟面试已更新', desc: `${latest.position}，${latest.score ? `评分 ${latest.score} 分` : '等待评分'}`, time: formatTimeAgo(latest.created_at), icon: '▣', color: '#d1fae5' })
    }
    if (jobItems.length) {
      activities.value.push({ title: `发现 ${jobCount} 个匹配岗位`, desc: '根据当前简历与目标方向推荐', time: '今天', icon: '⌕', color: '#fef3c7' })
    }

    upcomingInterviews.value = interviews
      .filter(item => item.status === 'pending' || item.status === 'in_progress')
      .slice(0, 3)
      .map((item: any) => ({ id: item.id, company: item.company || '未指定', position: item.position, date: item.scheduled_date || item.created_at?.split('T')[0] || '', time: item.scheduled_time || '10:00' }))
  } catch {
    ElMessage.error('加载工作台数据失败')
  } finally {
    isLoading.value = false
  }
}

function formatTimeAgo(dateString: string) {
  if (!dateString) return '未知'
  const difference = Date.now() - new Date(dateString).getTime()
  const minutes = Math.floor(difference / 60000)
  const hours = Math.floor(difference / 3600000)
  const days = Math.floor(difference / 86400000)
  if (minutes < 60) return `${Math.max(0, minutes)} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return new Date(dateString).toLocaleDateString('zh-CN')
}

onMounted(() => {
  const storedUser = storage.get<any>(USER_KEY)
  if (storedUser?.username) username.value = storedUser.username
  void Promise.all([loadDashboardData(), hrStore.loadOverview(true)])
})
</script>

<style scoped>
.dashboard-view { min-height: 100%; padding: 12px; color: #294760; background: #eef4f8; }
.classic-panel { overflow: hidden; border: 1px solid #aec8dc; border-radius: 6px; background: #fff; box-shadow: 0 1px 3px rgba(20,76,115,.08); }
.panel-titlebar, .section-titlebar { display: flex; align-items: center; justify-content: space-between; }
.panel-titlebar { height: 31px; padding: 0 10px; color: #fff; font-size: 12px; font-weight: 700; background: linear-gradient(#42bbed,#148fcf); border-bottom: 1px solid #0874ad; text-shadow: 0 1px rgba(0,70,110,.45); }
.panel-titlebar b { color: #c8f6ff; font-size: 8px; }
.panel-tools { letter-spacing: .3em; opacity: .84; }
.welcome-body { display: flex; min-height: 105px; align-items: center; justify-content: space-between; gap: 24px; padding: 18px 23px; background: linear-gradient(115deg,#effaff 0%,#fff 58%,#e8f7ff 100%); }
.welcome-user { display: flex; align-items: center; gap: 16px; }
.welcome-user img { width: 66px; height: 66px; border: 3px solid #fff; border-radius: 14px; object-fit: cover; box-shadow: 0 5px 13px rgba(11,89,139,.2); }
.welcome-user h1 { margin: 0; color: #19577f; font-size: 23px; }
.welcome-user p { margin: 8px 0 0; color: #607c91; font-size: 13px; }
.welcome-user p i { display: inline-block; width: 8px; height: 8px; margin-right: 7px; border-radius: 50%; background: #22c55e; }
.today-card { min-width: 150px; padding: 12px 17px; text-align: center; border: 1px solid #b8d8eb; border-radius: 6px; background: linear-gradient(#fff,#e5f5fd); }
.today-card strong, .today-card span { display: block; }
.today-card strong { color: #1685c1; font-size: 16px; }.today-card span { margin-top: 4px; color: #71869a; font-size: 11px; }
.automation-panel { margin-top: 10px; }
.section-titlebar { height: 31px; padding: 0 10px; color: #244b67; font-size: 12px; font-weight: 800; border-bottom: 1px solid #c5d8e6; background: linear-gradient(#fafdff,#e7f2f9); }
.section-titlebar small { color: #8396a5; font-size: 10px; font-weight: 400; }
.section-titlebar button { padding: 0; color: #1688c8; font-size: 11px; border: 0; background: transparent; cursor: pointer; }
.automation-flow { display: grid; grid-template-columns: repeat(4,1fr); padding: 13px; }
.flow-step { position: relative; display: flex; min-width: 0; align-items: center; gap: 10px; padding: 11px 18px 11px 13px; text-align: left; border: 0; border-right: 1px dashed #b8cfdf; background: transparent; cursor: pointer; }
.flow-step:last-child { border-right: 0; }.flow-step:hover { background: #edf9ff; }
.step-number { position: absolute; top: 4px; left: 5px; color: #a3b8c8; font-size: 9px; }
.step-icon { display: grid; width: 40px; height: 40px; flex: 0 0 auto; place-items: center; color: #087dbd; font-size: 21px; border: 1px solid #b4d7e9; border-radius: 8px; background: linear-gradient(#fff,#dff4fd); }
.step-copy { display: flex; min-width: 0; flex-direction: column; }.step-copy strong { color: #275673; font-size: 13px; }.step-copy small { overflow: hidden; margin-top: 4px; color: #8496a5; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.flow-arrow { position: absolute; right: -5px; z-index: 1; color: #31a4db; font-size: 24px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(190px,1fr)); gap: 9px; margin-top: 10px; }
.stat-item { display: flex; min-width: 0; align-items: center; gap: 11px; padding: 11px 13px; text-align: left; border: 1px solid #c5d7e4; border-radius: 5px; background: linear-gradient(#fff,#f2f7fb); cursor: pointer; }.stat-item:hover { border-color: #7fc3e5; background: #eef9ff; }
.stat-icon { display: grid; width: 40px; height: 40px; flex: 0 0 auto; place-items: center; color: #205f87; font-size: 20px; border-radius: 7px; }
.stat-copy { display: flex; flex-direction: column; }.stat-copy strong { color: #164f76; font-size: 20px; }.stat-copy small { color: #71869a; font-size: 11px; }
.stat-status { margin-left: auto; color: #91a1ae; font-size: 9px; }.stat-status i { display: inline-block; width: 6px; height: 6px; margin-right: 4px; border-radius: 50%; background: #22c55e; }
.dashboard-columns { display: grid; grid-template-columns: minmax(210px,.72fr) minmax(340px,1.35fr) minmax(270px,1fr); gap: 10px; margin-top: 10px; }
.quick-list button { display: flex; width: 100%; min-height: 51px; align-items: center; gap: 10px; padding: 7px 10px; text-align: left; border: 0; border-bottom: 1px solid #e0eaf1; background: #fff; cursor: pointer; }.quick-list button:hover { background: #eaf8ff; }.quick-list button:last-child { border-bottom: 0; }
.quick-icon { display: grid; width: 34px; height: 34px; place-items: center; color: #1688c8; font-size: 18px; border: 1px solid #c5deed; border-radius: 5px; background: #eff9fe; }
.quick-list button > span:nth-child(2), .activity-row > span:nth-child(2), .interview-row > span:nth-child(2) { display: flex; min-width: 0; flex: 1; flex-direction: column; }.quick-list strong, .activity-row strong, .interview-row strong { overflow: hidden; color: #35556c; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }.quick-list small, .activity-row small, .interview-row small { margin-top: 3px; color: #8a9aa7; font-size: 10px; }.quick-list b { color: #38a5d7; }
.activity-row, .interview-row { display: flex; min-height: 56px; align-items: center; gap: 10px; padding: 8px 10px; border-bottom: 1px solid #e1eaf0; }.activity-row:last-child, .interview-row:last-child { border-bottom: 0; }
.activity-icon, .company-avatar { display: grid; width: 34px; height: 34px; flex: 0 0 auto; place-items: center; color: #246182; border-radius: 6px; }.company-avatar { color: #fff; font-weight: 700; background: linear-gradient(#53bde9,#168bc8); }
.activity-row time { color: #9aa8b3; font-size: 9px; }.interview-row time { display: flex; flex-direction: column; color: #55748a; font-size: 10px; text-align: right; }
.empty-state { display: grid; min-height: 138px; place-content: center; justify-items: center; color: #8da0ae; font-size: 11px; }.empty-state span { color: #6ebde2; font-size: 30px; }.empty-state p { margin: 7px 0; }.empty-state.compact { min-height: 120px; }
html.dark .dashboard-view { background: #111827; } html.dark .classic-panel, html.dark .stat-item, html.dark .quick-list button { color: #cbd5e1; border-color: #334155; background: #1e293b; } html.dark .welcome-body { background: #172033; } html.dark .section-titlebar { color: #d5e6f5; border-color: #334155; background: #263449; }
@media (max-width: 1100px) { .dashboard-columns { grid-template-columns: 1fr 1fr; }.interview-panel { grid-column: 1 / -1; }.stats-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 760px) { .dashboard-view { padding: 7px; }.welcome-body { align-items: flex-start; padding: 14px; }.today-card { display: none; }.automation-flow { grid-template-columns: 1fr 1fr; }.flow-step:nth-child(2) { border-right: 0; }.stats-grid, .dashboard-columns { grid-template-columns: 1fr; }.interview-panel { grid-column: auto; }.stat-status, .section-titlebar small { display: none; } }
</style>
