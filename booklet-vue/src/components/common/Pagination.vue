<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: {
    type: Number,
    required: true,
  },
  totalPages: {
    type: Number,
    required: true,
  },
  onPageChange: {
    type: Function,
    default: () => {},
  },
})

const emit = defineEmits(['pageChange'])

const pages = computed(() => {
  const total = props.totalPages
  const current = props.currentPage
  const result = []

  if (total <= 7) {
    for (let i = 1; i <= total; i++) result.push(i)
    return result
  }

  // Always show first page
  result.push(1)

  if (current > 3) {
    result.push('...')
  }

  // Show pages around current
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)

  for (let i = start; i <= end; i++) {
    result.push(i)
  }

  if (current < total - 2) {
    result.push('...')
  }

  // Always show last page
  if (total > 1) {
    result.push(total)
  }

  return result
})

function goToPage(page) {
  if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
    props.onPageChange(page)
    emit('pageChange', page)
  }
}

function previousPage() {
  goToPage(props.currentPage - 1)
}

function nextPage() {
  goToPage(props.currentPage + 1)
}
</script>

<template>
  <nav class="flex items-center justify-center gap-1" aria-label="Pagination">
    <!-- Previous Button -->
    <button
      type="button"
      :disabled="currentPage <= 1"
      :class="[
        'inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border transition-colors',
        currentPage <= 1
          ? 'text-gray-300 dark:text-gray-600 border-gray-200 dark:border-gray-700 cursor-not-allowed'
          : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700',
      ]"
      @click="previousPage"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
      </svg>
      <span class="hidden sm:inline">Previous</span>
    </button>

    <!-- Page Numbers -->
    <template v-for="(page, index) in pages" :key="index">
      <span v-if="page === '...'" class="px-2 py-2 text-sm text-gray-500 dark:text-gray-400">
        ...
      </span>
      <button
        v-else
        type="button"
        :class="[
          'inline-flex items-center justify-center w-9 h-9 text-sm font-medium rounded-lg border transition-colors',
          page === currentPage
            ? 'bg-blue-600 text-white border-blue-600 dark:bg-blue-600 dark:border-blue-600'
            : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700',
        ]"
        @click="goToPage(page)"
      >
        {{ page }}
      </button>
    </template>

    <!-- Next Button -->
    <button
      type="button"
      :disabled="currentPage >= totalPages"
      :class="[
        'inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border transition-colors',
        currentPage >= totalPages
          ? 'text-gray-300 dark:text-gray-600 border-gray-200 dark:border-gray-700 cursor-not-allowed'
          : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700',
      ]"
      @click="nextPage"
    >
      <span class="hidden sm:inline">Next</span>
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
      </svg>
    </button>
  </nav>
</template>
