import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // ── State ────────────────────────────────────────────────
  const isDark = ref(true)

  // ── Actions ──────────────────────────────────────────────
  function init() {
    const stored = localStorage.getItem('theme')
    if (stored !== null) {
      isDark.value = stored === 'dark'
    } else {
      // Fallback to OS preference
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    applyTheme()
  }

  function toggle() {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // Watch for changes and toggle the dark class on <html>
  watch(isDark, () => {
    applyTheme()
  })

  return {
    isDark,
    init,
    toggle,
  }
})
