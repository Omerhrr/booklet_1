<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DataTable from '@/components/common/DataTable.vue'
import DateInput from '@/components/forms/DateInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import {
  getExpensesReport,
  getExpensesPdf,
  getExpensesExcel,
} from '@/api/reports'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'
import { downloadBlob } from '@/utils/export'

const loading = ref(true)
const exporting = ref(false)
const reportData = ref([])
const categoryBreakdown = ref([])
const summary = ref({
  total_expenses: 0,
  category_count: 0,
  transaction_count: 0,
})

const filters = ref({
  start_date: '',
  end_date: '',
  category: '',
})

const categoryOptions = ref([])

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'reference', label: 'Reference', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'description', label: 'Description' },
  { key: 'amount', label: 'Amount', sortable: true },
  { key: 'payment_method', label: 'Payment Method', sortable: true },
]

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (filters.value.start_date) params.start_date = filters.value.start_date
    if (filters.value.end_date) params.end_date = filters.value.end_date
    if (filters.value.category) params.category = filters.value.category
    const { data } = await getExpensesReport(params)
    reportData.value = Array.isArray(data) ? data : data.items || data.expenses || []
    summary.value = data.summary || {
      total_expenses: reportData.value.reduce((s, i) => s + (i.amount || 0), 0),
      category_count: new Set(reportData.value.map(i => i.category)).size,
      transaction_count: reportData.value.length,
    }
    categoryBreakdown.value = data.category_breakdown || []
    if (data.categories) {
      categoryOptions.value = data.categories.map(c => ({ value: c, label: c }))
    } else {
      const cats = [...new Set(reportData.value.map(i => i.category).filter(Boolean))]
      categoryOptions.value = cats.map(c => ({ value: c, label: c }))
    }
  } catch (error) {
    console.error('Failed to fetch expenses report:', error)
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
    const { data } = await getExpensesPdf(filters.value)
    downloadBlob(data, 'expenses-report.pdf')
  } catch (error) {
    console.error('Failed to export PDF:', error)
  } finally {
    exporting.value = false
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const { data } = await getExpensesExcel(filters.value)
    downloadBlob(data, 'expenses-report.xlsx')
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
      title="Expenses Report"
      subtitle="Track and analyze your business expenses"
      :breadcrumbs="[
        { text: 'Reports', to: { name: 'ReportsIndex' } },
        { text: 'Expenses Report' },
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
        <DateInput v-model="filters.start_date" label="Start Date" name="start_date" />
        <DateInput v-model="filters.end_date" label="End Date" name="end_date" />
        <SelectInput v-model="filters.category" label="Category" name="category" :options="categoryOptions" placeholder="All Categories" />
        <div class="flex items-end">
          <button
            type="button"
            class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors"
            @click="applyFilters"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="Total Expenses" :value="formatCurrency(summary.total_expenses)" icon="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" color="amber" />
      <StatCard title="Categories" :value="summary.category_count" icon="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" color="purple" />
      <StatCard title="Transactions" :value="summary.transaction_count" icon="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" color="green" />
    </div>

    <!-- Category Breakdown -->
    <div v-if="categoryBreakdown.length > 0" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
      <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">Category Breakdown</h3>
      <div class="space-y-2 max-h-64 overflow-y-auto">
        <div
          v-for="cat in categoryBreakdown"
          :key="cat.category"
          class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
        >
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ cat.category }}</span>
          <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatCurrency(cat.total || cat.amount) }}</span>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable :columns="columns" :data="reportData" :loading="loading" :searchable="false" empty-message="No expense data for the selected period">
      <template #cell-date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
      </template>
      <template #cell-reference="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ row.reference || '—' }}</span>
      </template>
      <template #cell-category="{ row }">
        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-400">
          {{ row.category || '—' }}
        </span>
      </template>
      <template #cell-description="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ row.description || '—' }}</span>
      </template>
      <template #cell-amount="{ row }">
        <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatCurrency(row.amount) }}</span>
      </template>
      <template #cell-payment_method="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ row.payment_method || '—' }}</span>
      </template>
    </DataTable>
  </div>
</template>
