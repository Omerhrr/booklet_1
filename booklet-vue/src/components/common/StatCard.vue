<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: [String, Number],
    required: true,
  },
  icon: {
    type: String,
    default: '',
  },
  change: {
    type: String,
    default: '',
  },
  changeType: {
    type: String,
    default: 'neutral',
    validator: (v) => ['up', 'down', 'neutral'].includes(v),
  },
  color: {
    type: String,
    default: 'blue',
    validator: (v) => ['blue', 'green', 'purple', 'amber', 'red', 'indigo'].includes(v),
  },
})

const colorClasses = computed(() => {
  const map = {
    blue: {
      icon: 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400',
      border: 'border-blue-200 dark:border-blue-800',
    },
    green: {
      icon: 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400',
      border: 'border-green-200 dark:border-green-800',
    },
    purple: {
      icon: 'bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400',
      border: 'border-purple-200 dark:border-purple-800',
    },
    amber: {
      icon: 'bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400',
      border: 'border-amber-200 dark:border-amber-800',
    },
    red: {
      icon: 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400',
      border: 'border-red-200 dark:border-red-800',
    },
    indigo: {
      icon: 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400',
      border: 'border-indigo-200 dark:border-indigo-800',
    },
  }
  return map[props.color] || map.blue
})

const changeColorClasses = computed(() => {
  if (props.changeType === 'up') return 'text-green-600 dark:text-green-400'
  if (props.changeType === 'down') return 'text-red-600 dark:text-red-400'
  return 'text-gray-500 dark:text-gray-400'
})

const changeIcon = computed(() => {
  if (props.changeType === 'up') return 'M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25'
  if (props.changeType === 'down') return 'M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25'
  return ''
})
</script>

<template>
  <div
    :class="[
      'relative overflow-hidden rounded-xl border bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md dark:bg-gray-800 dark:border-gray-700',
      colorClasses.border,
    ]"
  >
    <!-- Decorative background -->
    <div
      class="absolute top-0 right-0 w-24 h-24 rounded-full -translate-y-8 translate-x-8 opacity-10"
      :class="colorClasses.icon"
    />

    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
          {{ title }}
        </p>
        <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
          {{ value }}
        </p>
      </div>
      <div
        v-if="icon"
        :class="['flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center', colorClasses.icon]"
      >
        <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" :d="icon" />
        </svg>
      </div>
    </div>

    <div v-if="change" class="mt-3 flex items-center gap-1">
      <svg
        v-if="changeIcon"
        class="w-4 h-4"
        :class="changeColorClasses"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="2"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" :d="changeIcon" />
      </svg>
      <span :class="['text-sm font-medium', changeColorClasses]">
        {{ change }}
      </span>
      <span class="text-sm text-gray-500 dark:text-gray-400">
        from last period
      </span>
    </div>
  </div>
</template>
