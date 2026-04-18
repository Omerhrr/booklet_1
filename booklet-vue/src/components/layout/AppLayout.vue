<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSidebarStore } from '@/stores/sidebar'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import MobileSidebar from './MobileSidebar.vue'

const route = useRoute()
const sidebarStore = useSidebarStore()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const pageTitle = computed(() => route.meta.title || 'Dashboard')
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white transition-colors">
    <!-- Desktop Sidebar -->
    <Sidebar class="hidden lg:block" />
    
    <!-- Mobile Sidebar Overlay -->
    <MobileSidebar />
    
    <!-- Main Content Area -->
    <div 
      class="transition-all duration-300"
      :class="[
        sidebarStore.isCollapsed ? 'lg:ml-16' : 'lg:ml-64'
      ]"
    >
      <Header :title="pageTitle" />
      
      <main class="p-4 sm:p-6 lg:p-8">
        <router-view />
      </main>
    </div>
  </div>
</template>
