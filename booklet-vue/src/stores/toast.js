import { defineStore } from 'pinia'
import { ref } from 'vue'

let toastCounter = 0

export const useToastStore = defineStore('toast', () => {
  // ── State ────────────────────────────────────────────────
  const toasts = ref([])

  // ── Actions ──────────────────────────────────────────────
  function show(message, type = 'success') {
    const id = ++toastCounter
    const toast = { id, message, type, show: true }
    toasts.value.push(toast)

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      dismiss(id)
    }, 5000)

    return id
  }

  function dismiss(id) {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  function clearAll() {
    toasts.value.splice(0, toasts.value.length)
  }

  return {
    toasts,
    show,
    dismiss,
    clearAll,
  }
})
