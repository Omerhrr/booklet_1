<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  text: {
    type: String,
    default: 'Loading...',
  },
})

const sizeClasses = computed(() => {
  const map = {
    sm: { spinner: 'w-5 h-5', text: 'text-xs', ring: 'h-5 w-5' },
    md: { spinner: 'w-8 h-8', text: 'text-sm', ring: 'h-8 w-8' },
    lg: { spinner: 'w-12 h-12', text: 'text-base', ring: 'h-12 w-12' },
  }
  return map[props.size] || map.md
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3">
    <div class="relative">
      <div
        :class="[
          'animate-spin rounded-full border-2 border-gray-200 dark:border-gray-700',
          sizeClasses.ring,
        ]"
      />
      <div
        :class="[
          'absolute top-0 left-0 animate-spin rounded-full border-2 border-transparent border-t-blue-600 dark:border-t-blue-400',
          sizeClasses.ring,
        ]"
        style="animation-duration: 0.8s;"
      />
    </div>
    <p v-if="text" :class="['text-gray-500 dark:text-gray-400', sizeClasses.text]">
      {{ text }}
    </p>
  </div>
</template>
