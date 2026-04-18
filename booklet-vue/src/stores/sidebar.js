import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSidebarStore = defineStore('sidebar', () => {
  // ── State ────────────────────────────────────────────────
  const isOpen = ref(false)       // Mobile sidebar
  const isCollapsed = ref(false)  // Desktop sidebar

  // ── Actions ──────────────────────────────────────────────
  function toggleMobile() {
    isOpen.value = !isOpen.value
  }

  function toggleCollapsed() {
    isCollapsed.value = !isCollapsed.value
  }

  return {
    isOpen,
    isCollapsed,
    toggleMobile,
    toggleCollapsed,
  }
})
