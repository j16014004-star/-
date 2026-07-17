<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="app-layout h-screen flex overflow-hidden bg-gray-50 dark:bg-slate-950">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Right area: header + main -->
    <div
      class="flex-1 flex flex-col min-w-0 transition-all duration-300"
      :style="{ marginLeft: '0px' }"
    >
      <!-- Header -->
      <AppHeader />

      <!-- Main content -->
      <el-main
        class="flex-1 overflow-auto !p-6"
        style="height: calc(100vh - 60px)"
      >
        <router-view />
      </el-main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  --header-height: 60px;
}
</style>
