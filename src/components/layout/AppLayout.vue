<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="desktop-shell">
    <div class="wallpaper-glow glow-left"></div>
    <div class="wallpaper-glow glow-right"></div>

    <div class="desktop-layout">
      <AppSidebar />

      <section class="workspace-window">
        <AppHeader />
        <el-main class="workspace-content">
          <router-view />
        </el-main>
        <footer class="workspace-statusbar">
          <span><i class="status-dot"></i> AI 求职服务运行中</span>
          <span>筛选岗位 · 自动投递 · 联系 HR · 面试邀约</span>
        </footer>
      </section>
    </div>
  </div>
</template>

<style scoped>
.desktop-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 18px;
  background:
    linear-gradient(rgba(9, 38, 78, 0.12), rgba(4, 24, 57, 0.34)),
    radial-gradient(circle at 30% 0%, #356fac 0%, transparent 45%),
    linear-gradient(145deg, #153d6d 0%, #0b274f 53%, #071b38 100%);
}

.desktop-shell::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: .13;
  background-image: linear-gradient(rgba(255,255,255,.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.12) 1px, transparent 1px);
  background-size: 38px 38px;
  mask-image: linear-gradient(to bottom, black, transparent 75%);
}

.wallpaper-glow { position: absolute; border-radius: 999px; filter: blur(4px); opacity: .22; }
.glow-left { width: 430px; height: 430px; left: -180px; bottom: -210px; background: #38bdf8; }
.glow-right { width: 520px; height: 520px; right: -230px; top: -260px; background: #818cf8; }

.desktop-layout {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 14px;
  width: min(1680px, 100%);
  height: calc(100vh - 36px);
  margin: 0 auto;
}

.workspace-window {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,.7);
  border-radius: 12px;
  background: #f4f7fb;
  box-shadow: 0 18px 46px rgba(1, 12, 30, .38), 0 0 0 1px rgba(4, 44, 91, .42);
}

.workspace-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 0 !important;
  background: #f4f7fb;
}

.workspace-statusbar {
  display: flex;
  min-height: 31px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 15px;
  border-top: 1px solid #cddbea;
  color: #5f7288;
  font-size: 11px;
  background: linear-gradient(#f8fbfe, #e7eef6);
}

.status-dot { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 0 2px rgba(34,197,94,.16); }

html.dark .workspace-window,
html.dark .workspace-content { background: #111827; }
html.dark .workspace-statusbar { color: #94a3b8; border-color: #334155; background: #172033; }

@media (max-width: 900px) {
  .desktop-shell { padding: 0; }
  .desktop-layout { height: 100vh; gap: 0; }
  .workspace-window { border: 0; border-radius: 0; box-shadow: none; }
  .workspace-statusbar span:last-child { display: none; }
}
</style>
