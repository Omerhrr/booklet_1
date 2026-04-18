<script setup>
import { useToastStore } from '@/stores/toast.js'

const toastStore = useToastStore()

const typeStyles = {
  success: {
    bg: 'bg-green-50 dark:bg-green-900/40 border-green-200 dark:border-green-800',
    text: 'text-green-800 dark:text-green-300',
    icon: 'text-green-500 dark:text-green-400',
    iconPath: 'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-900/40 border-red-200 dark:border-red-800',
    text: 'text-red-800 dark:text-red-300',
    icon: 'text-red-500 dark:text-red-400',
    iconPath: 'M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z',
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-900/40 border-blue-200 dark:border-blue-800',
    text: 'text-blue-800 dark:text-blue-300',
    icon: 'text-blue-500 dark:text-blue-400',
    iconPath: 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z',
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/40 border-yellow-200 dark:border-yellow-800',
    text: 'text-yellow-800 dark:text-yellow-300',
    icon: 'text-yellow-500 dark:text-yellow-400',
    iconPath: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
  },
}
</script>

<template>
  <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 w-full max-w-sm pointer-events-none">
    <TransitionGroup
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="translate-x-full opacity-0"
      enter-to-class="translate-x-0 opacity-100"
      leave-active-class="transition-all duration-300 ease-in"
      leave-from-class="translate-x-0 opacity-100"
      leave-to-class="translate-x-full opacity-0"
    >
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        :class="[
          'pointer-events-auto flex items-start gap-3 p-4 rounded-lg border shadow-lg backdrop-blur-sm',
          typeStyles[toast.type]?.bg || typeStyles.info.bg,
        ]"
      >
        <svg
          class="w-5 h-5 flex-shrink-0 mt-0.5"
          :class="typeStyles[toast.type]?.icon || typeStyles.info.icon"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            :d="typeStyles[toast.type]?.iconPath || typeStyles.info.iconPath"
          />
        </svg>
        <p
          :class="['flex-1 text-sm font-medium', typeStyles[toast.type]?.text || typeStyles.info.text]"
        >
          {{ toast.message }}
        </p>
        <button
          type="button"
          :class="['flex-shrink-0 p-1 rounded-md hover:bg-black/10 dark:hover:bg-white/10 transition-colors', typeStyles[toast.type]?.icon || typeStyles.info.icon]"
          @click="toastStore.dismiss(toast.id)"
          aria-label="Dismiss"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
