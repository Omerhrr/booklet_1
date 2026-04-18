<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  breadcrumbs: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <div class="mb-6">
    <!-- Breadcrumbs -->
    <nav v-if="breadcrumbs.length > 0" class="mb-3" aria-label="Breadcrumb">
      <ol class="flex items-center gap-2 text-sm">
        <li v-for="(crumb, index) in breadcrumbs" :key="index" class="flex items-center gap-2">
          <svg
            v-if="index > 0"
            class="w-4 h-4 text-gray-400 dark:text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
          <router-link
            v-if="crumb.to"
            :to="crumb.to"
            class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          >
            {{ crumb.text }}
          </router-link>
          <span v-else class="text-gray-400 dark:text-gray-500">{{ crumb.text }}</span>
        </li>
      </ol>
    </nav>

    <!-- Title Row -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ title }}
        </h1>
        <p v-if="subtitle" class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {{ subtitle }}
        </p>
      </div>

      <!-- Actions Slot -->
      <div v-if="$slots.actions" class="flex items-center gap-3 flex-shrink-0">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>
