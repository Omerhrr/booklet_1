<script setup>
import { ref, computed, useSlots } from 'vue'
import SearchInput from './SearchInput.vue'
import LoadingSpinner from './LoadingSpinner.vue'

const props = defineProps({
  columns: {
    type: Array,
    required: true,
    default: () => [],
  },
  data: {
    type: Array,
    required: true,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  emptyMessage: {
    type: String,
    default: 'No data available',
  },
  hoverable: {
    type: Boolean,
    default: true,
  },
  striped: {
    type: Boolean,
    default: true,
  },
  searchable: {
    type: Boolean,
    default: true,
  },
  searchPlaceholder: {
    type: String,
    default: 'Search...',
  },
})

const searchQuery = ref('')
const sortKey = ref('')
const sortDirection = ref('asc')
const slots = useSlots()

const filteredData = computed(() => {
  if (!searchQuery.value) return props.data

  const query = searchQuery.value.toLowerCase()
  return props.data.filter(row => {
    return props.columns.some(col => {
      const cellValue = row[col.key]
      if (cellValue == null) return false
      return String(cellValue).toLowerCase().includes(query)
    })
  })
})

const sortedData = computed(() => {
  if (!sortKey.value) return filteredData.value

  return [...filteredData.value].sort((a, b) => {
    const valA = a[sortKey.value]
    const valB = b[sortKey.value]

    if (valA == null && valB == null) return 0
    if (valA == null) return sortDirection.value === 'asc' ? -1 : 1
    if (valB == null) return sortDirection.value === 'asc' ? 1 : -1

    let comparison = 0
    if (typeof valA === 'number' && typeof valB === 'number') {
      comparison = valA - valB
    } else {
      comparison = String(valA).localeCompare(String(valB))
    }

    return sortDirection.value === 'asc' ? comparison : -comparison
  })
})

function handleSort(column) {
  if (!column.sortable) return

  if (sortKey.value === column.key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = column.key
    sortDirection.value = 'asc'
  }
}

function getCellValue(row, column) {
  return row[column.key]
}
</script>

<template>
  <div class="w-full">
    <!-- Search -->
    <div v-if="searchable" class="mb-4">
      <SearchInput
        v-model="searchQuery"
        :placeholder="searchPlaceholder"
      />
    </div>

    <!-- Table Wrapper -->
    <div class="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              :class="[
                'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400',
                column.sortable ? 'cursor-pointer select-none hover:text-gray-700 dark:hover:text-gray-200' : '',
                column.class || '',
              ]"
              @click="handleSort(column)"
            >
              <div class="flex items-center gap-1">
                <span>{{ column.label }}</span>
                <span v-if="column.sortable" class="flex flex-col ml-1">
                  <svg
                    class="w-3 h-3 transition-colors"
                    :class="sortKey === column.key && sortDirection === 'asc' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500'"
                    viewBox="0 0 10 6"
                    fill="currentColor"
                  >
                    <path d="M5 0L10 6H0z" />
                  </svg>
                  <svg
                    class="w-3 h-3 -mt-1 transition-colors"
                    :class="sortKey === column.key && sortDirection === 'desc' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500'"
                    viewBox="0 0 10 6"
                    fill="currentColor"
                  >
                    <path d="M5 6L0 0h10z" />
                  </svg>
                </span>
              </div>
            </th>
            <th
              v-if="$slots.actions"
              class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          <!-- Loading State -->
          <tr v-if="loading">
            <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-12">
              <div class="flex items-center justify-center">
                <LoadingSpinner size="lg" text="Loading data..." />
              </div>
            </td>
          </tr>

          <!-- Empty State -->
          <tr v-else-if="sortedData.length === 0">
            <td :colspan="columns.length + ($slots.actions ? 1 : 0)" class="px-4 py-12">
              <div class="flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p class="text-sm">{{ emptyMessage }}</p>
              </div>
            </td>
          </tr>

          <!-- Data Rows -->
          <tr
            v-else
            v-for="(row, rowIndex) in sortedData"
            :key="row.id || rowIndex"
            :class="[
              'transition-colors',
              hoverable ? 'hover:bg-gray-50 dark:hover:bg-gray-800' : '',
              striped && rowIndex % 2 === 1 ? 'bg-gray-50/50 dark:bg-gray-800' : '',
            ]"
          >
            <td
              v-for="column in columns"
              :key="column.key"
              :class="[
                'px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap',
                column.class || '',
              ]"
            >
              <slot :name="`cell-${column.key}`" :row="row" :value="getCellValue(row, column)">
                {{ getCellValue(row, column) }}
              </slot>
            </td>
            <td
              v-if="$slots.actions"
              class="px-4 py-3 text-sm text-right whitespace-nowrap"
            >
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
