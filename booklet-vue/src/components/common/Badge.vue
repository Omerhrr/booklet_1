<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: {
    type: String,
    default: '',
  },
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['success', 'warning', 'danger', 'info', 'default'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v),
  },
  dot: {
    type: Boolean,
    default: false,
  },
})

const variantClasses = computed(() => {
  const map = {
    success: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-400',
    danger: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400',
    info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-400',
    default: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  }
  return map[props.variant] || map.default
})

const dotClasses = computed(() => {
  const map = {
    success: 'bg-green-500 dark:bg-green-400',
    warning: 'bg-yellow-500 dark:bg-yellow-400',
    danger: 'bg-red-500 dark:bg-red-400',
    info: 'bg-blue-500 dark:bg-blue-400',
    default: 'bg-gray-500 dark:bg-gray-400',
  }
  return map[props.variant] || map.default
})

const sizeClasses = computed(() => {
  return props.size === 'sm'
    ? props.dot
      ? 'w-2 h-2'
      : 'px-2 py-0.5 text-xs'
    : props.dot
      ? 'w-2.5 h-2.5'
      : 'px-2.5 py-1 text-sm'
})
</script>

<template>
  <span
    v-if="dot"
    :class="['inline-flex rounded-full', dotClasses, sizeClasses]"
    :title="text"
  />
  <span
    v-else
    :class="['inline-flex items-center font-medium rounded-full', variantClasses, sizeClasses]"
  >
    {{ text }}
  </span>
</template>
