<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useToastStore } from '@/stores/toast'
import { formatDate } from '@/utils/dates'
import * as inventoryApi from '@/api/inventory'

const toastStore = useToastStore()

const adjustments = ref([])
const loading = ref(true)
const productFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')

const breadcrumbs = [
  { text: 'Inventory' },
  { text: 'Stock Adjustments' },
]

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'product', label: 'Product', sortable: true },
  { key: 'previous_quantity', label: 'Previous Qty', sortable: true, class: 'text-right' },
  { key: 'new_quantity', label: 'New Qty', sortable: true, class: 'text-right' },
  { key: 'difference', label: 'Difference', sortable: true, class: 'text-right' },
  { key: 'reason', label: 'Reason' },
  { key: 'adjusted_by', label: 'Adjusted By' },
]

const filteredAdjustments = ref([])

function applyFilters() {
  let result = [...adjustments.value]

  if (productFilter.value) {
    const query = productFilter.value.toLowerCase()
    result = result.filter((adj) =>
      (adj.product_name || adj.product || '').toLowerCase().includes(query)
    )
  }

  if (dateFrom.value) {
    result = result.filter((adj) => {
      const adjDate = adj.date || adj.created_at || ''
      return adjDate >= dateFrom.value
    })
  }

  if (dateTo.value) {
    result = result.filter((adj) => {
      const adjDate = adj.date || adj.created_at || ''
      return adjDate <= dateTo.value + 'T23:59:59'
    })
  }

  filteredAdjustments.value = result
}

function clearFilters() {
  productFilter.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  filteredAdjustments.value = [...adjustments.value]
}

async function fetchAdjustments() {
  loading.value = true
  try {
    const { data } = await inventoryApi.listStockAdjustments()
    adjustments.value = Array.isArray(data) ? data : data.items || data.adjustments || []
    filteredAdjustments.value = [...adjustments.value]
  } catch (error) {
    console.error('Failed to fetch stock adjustments:', error)
    toastStore.show('Failed to load stock adjustments', 'error')
  } finally {
    loading.value = false
  }
}

function getProductName(row) {
  return row.product_name || row.product || '—'
}

function getAdjustedBy(row) {
  return row.adjusted_by_name || row.adjusted_by || '—'
}

onMounted(fetchAdjustments)
</script>

<template>
  <div>
    <PageHeader title="Stock Adjustments" :breadcrumbs="breadcrumbs" subtitle="History of all stock level changes" />

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Product Search -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Product</label>
          <input
            v-model="productFilter"
            type="text"
            placeholder="Filter by product name..."
            class="block w-full px-3 py-2.5 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white transition-colors"
            @input="applyFilters"
          />
        </div>

        <!-- Date From -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">From Date</label>
          <input
            v-model="dateFrom"
            type="date"
            class="block w-full px-3 py-2.5 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white transition-colors"
            @input="applyFilters"
          />
        </div>

        <!-- Date To -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">To Date</label>
          <input
            v-model="dateTo"
            type="date"
            class="block w-full px-3 py-2.5 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:text-white transition-colors"
            @input="applyFilters"
          />
        </div>

        <!-- Clear Filters -->
        <div class="flex items-end">
          <button
            v-if="productFilter || dateFrom || dateTo"
            type="button"
            class="w-full px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
            @click="clearFilters"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && filteredAdjustments.length === 0"
      title="No stock adjustments found"
      message="No stock adjustments match your current filters."
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="filteredAdjustments"
        :loading="loading"
        search-placeholder="Search adjustments..."
      >
        <!-- Date Column -->
        <template #cell-date="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDate(row.date || row.created_at, 'short') }}
          </span>
        </template>

        <!-- Product Column -->
        <template #cell-product="{ row }">
          <span class="text-sm font-medium text-gray-900 dark:text-white">
            {{ getProductName(row) }}
          </span>
        </template>

        <!-- Previous Quantity Column -->
        <template #cell-previous_quantity="{ row }">
          <span class="text-sm text-gray-600 dark:text-gray-400">
            {{ row.previous_quantity ?? '—' }}
          </span>
        </template>

        <!-- New Quantity Column -->
        <template #cell-new_quantity="{ row }">
          <span class="text-sm font-medium text-gray-900 dark:text-white">
            {{ row.new_quantity ?? '—' }}
          </span>
        </template>

        <!-- Difference Column -->
        <template #cell-difference="{ row }">
          <span
            :class="[
              'text-sm font-semibold',
              (row.difference || 0) > 0
                ? 'text-green-600 dark:text-green-400'
                : (row.difference || 0) < 0
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-gray-500 dark:text-gray-400',
            ]"
          >
            {{ (row.difference || 0) > 0 ? '+' : '' }}{{ row.difference ?? '—' }}
          </span>
        </template>

        <!-- Reason Column -->
        <template #cell-reason="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300 max-w-xs truncate block">
            {{ row.reason || '—' }}
          </span>
        </template>

        <!-- Adjusted By Column -->
        <template #cell-adjusted_by="{ row }">
          <span class="text-sm text-gray-600 dark:text-gray-400">
            {{ getAdjustedBy(row) }}
          </span>
        </template>
      </DataTable>
    </div>
  </div>
</template>
