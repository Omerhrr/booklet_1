<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DataTable from '@/components/common/DataTable.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import {
  getInventoryReport,
  getInventoryPdf,
  getInventoryExcel,
} from '@/api/reports'
import { formatCurrency } from '@/utils/currency'
import { downloadBlob } from '@/utils/export'

const loading = ref(true)
const exporting = ref(false)
const reportData = ref([])
const summary = ref({
  total_products: 0,
  total_value: 0,
  low_stock_count: 0,
})

const filters = ref({
  category: '',
  status: '',
})

const statusOptions = [
  { value: 'in_stock', label: 'In Stock' },
  { value: 'low_stock', label: 'Low Stock' },
  { value: 'out_of_stock', label: 'Out of Stock' },
]

const categoryOptions = ref([])

const columns = [
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'quantity', label: 'Quantity', sortable: true },
  { key: 'cost_value', label: 'Cost Value', sortable: true },
  { key: 'selling_value', label: 'Selling Value', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (filters.value.category) params.category = filters.value.category
    if (filters.value.status) params.status = filters.value.status
    const { data } = await getInventoryReport(params)
    reportData.value = Array.isArray(data) ? data : data.items || data.products || []
    summary.value = data.summary || {
      total_products: reportData.value.length,
      total_value: reportData.value.reduce((s, i) => s + (i.selling_value || 0), 0),
      low_stock_count: reportData.value.filter(i => i.status === 'low_stock').length,
    }
    if (data.categories) {
      categoryOptions.value = data.categories.map(c => ({ value: c, label: c }))
    } else {
      const cats = [...new Set(reportData.value.map(i => i.category).filter(Boolean))]
      categoryOptions.value = cats.map(c => ({ value: c, label: c }))
    }
  } catch (error) {
    console.error('Failed to fetch inventory report:', error)
    reportData.value = []
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  fetchReport()
}

async function exportPdf() {
  exporting.value = true
  try {
    const { data } = await getInventoryPdf(filters.value)
    downloadBlob(data, 'inventory-report.pdf')
  } catch (error) {
    console.error('Failed to export PDF:', error)
  } finally {
    exporting.value = false
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const { data } = await getInventoryExcel(filters.value)
    downloadBlob(data, 'inventory-report.xlsx')
  } catch (error) {
    console.error('Failed to export Excel:', error)
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchReport()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Inventory Report"
      subtitle="Monitor stock levels and product values"
      :breadcrumbs="[
        { text: 'Reports', to: { name: 'ReportsIndex' } },
        { text: 'Inventory Report' },
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700 transition-colors"
            :disabled="exporting"
            @click="exportExcel"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-2.625 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-1.5A1.125 1.125 0 0118 18.375M20.625 4.5H3.375m17.25 0c.621 0 1.125.504 1.125 1.125M20.625 4.5h-1.5C18.504 4.5 18 5.004 18 5.625m3.75 0v1.5c0 .621-.504 1.125-1.125 1.125M3.375 4.5c-.621 0-1.125.504-1.125 1.125M3.375 4.5h1.5C5.496 4.5 6 5.004 6 5.625m-3.75 0v1.5c0 .621.504 1.125 1.125 1.125m0 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m1.5-3.75C5.496 8.25 6 7.746 6 7.125v-1.5M4.875 8.25C5.496 8.25 6 8.754 6 9.375v1.5m0-5.25v5.25m0-5.25C6 5.004 6.504 4.5 7.125 4.5h9.75c.621 0 1.125.504 1.125 1.125m1.125 2.625h1.5m-1.5 0A1.125 1.125 0 0118 7.125v-1.5m1.125 2.625c-.621 0-1.125.504-1.125 1.125v1.5m2.625-2.625c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125M18 5.625v5.25M7.125 12h9.75m-9.75 0A1.125 1.125 0 016 10.875M7.125 12C6.504 12 6 12.504 6 13.125m0-2.25c0 .621.504 1.125 1.125 1.125M18 10.875c0 .621-.504 1.125-1.125 1.125M18 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m-12 5.25v-5.25m0 5.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125m-12 0v-1.5c0-.621-.504-1.125-1.125-1.125M18 18.375v-5.25m0 5.25v-1.5c0-.621.504-1.125 1.125-1.125M18 13.125v1.5c0 .621.504 1.125 1.125 1.125M18 13.125c0-.621.504-1.125 1.125-1.125M6 13.125v1.5c0 .621-.504 1.125-1.125 1.125M6 13.125C6 12.504 5.496 12 4.875 12m-1.5 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m1.5-3.75c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125" />
            </svg>
            Excel
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-rose-600 rounded-lg hover:bg-rose-700 transition-colors"
            :disabled="exporting"
            @click="exportPdf"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            PDF
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SelectInput v-model="filters.category" label="Category" name="category" :options="categoryOptions" placeholder="All Categories" />
        <SelectInput v-model="filters.status" label="Status" name="status" :options="statusOptions" placeholder="All Statuses" />
        <div class="flex items-end">
          <button
            type="button"
            class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-cyan-600 rounded-lg hover:bg-cyan-700 transition-colors"
            @click="applyFilters"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard title="Total Products" :value="summary.total_products" icon="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" color="blue" />
      <StatCard title="Total Value" :value="formatCurrency(summary.total_value)" icon="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" color="green" />
      <StatCard title="Low Stock" :value="summary.low_stock_count" icon="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" color="red" />
    </div>

    <!-- Data Table -->
    <DataTable :columns="columns" :data="reportData" :loading="loading" :searchable="false" empty-message="No inventory data found">
      <template #cell-sku="{ row }">
        <span class="text-sm font-mono text-gray-600 dark:text-gray-400">{{ row.sku || '—' }}</span>
      </template>
      <template #cell-name="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ row.name }}</span>
      </template>
      <template #cell-category="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ row.category || '—' }}</span>
      </template>
      <template #cell-quantity="{ row }">
        <span :class="['text-sm font-medium', row.quantity <= (row.low_stock_threshold || 10) ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white']">
          {{ row.quantity }}
        </span>
      </template>
      <template #cell-cost_value="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(row.cost_value || row.cost_price * row.quantity) }}</span>
      </template>
      <template #cell-selling_value="{ row }">
        <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatCurrency(row.selling_value || row.selling_price * row.quantity) }}</span>
      </template>
      <template #cell-status="{ row }">
        <span
          :class="[
            'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
            row.status === 'in_stock' ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400' :
            row.status === 'low_stock' ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-400' :
            'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400',
          ]"
        >
          {{ (row.status || '').replace(/_/g, ' ') }}
        </span>
      </template>
    </DataTable>
  </div>
</template>
