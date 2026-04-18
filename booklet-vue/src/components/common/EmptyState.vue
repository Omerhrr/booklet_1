<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  title: {
    type: String,
    default: 'No data yet',
  },
  message: {
    type: String,
    default: 'Get started by creating your first item.',
  },
  icon: {
    type: String,
    default: '',
  },
  actionText: {
    type: String,
    default: '',
  },
  actionRoute: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['action'])
const router = useRouter()

const defaultIcon = 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4'

function handleAction() {
  if (props.actionRoute) {
    router.push(props.actionRoute)
  } else {
    emit('action')
  }
}
</script>

<template>
  <div class="flex flex-col items-center justify-center py-12 px-4 text-center">
    <div class="w-16 h-16 mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
      <svg
        class="w-8 h-8 text-gray-400 dark:text-gray-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" :d="icon || defaultIcon" />
      </svg>
    </div>

    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
      {{ title }}
    </h3>
    <p class="text-sm text-gray-500 dark:text-gray-400 max-w-sm mb-6">
      {{ message }}
    </p>

    <button
      v-if="actionText"
      type="button"
      class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
      @click="handleAction"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
      </svg>
      {{ actionText }}
    </button>

    <slot />
  </div>
</template>
