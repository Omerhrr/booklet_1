<script setup>
import { ref, onMounted, computed } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DateInput from '@/components/forms/DateInput.vue'
import {
  getAgingReport,
  getAgingPdf,
  getAgingExcel,
} from '@/api/reports'
import { formatCurrency } from '@/utils/currency'
import { downloadBlob } from '@/utils/export'

const loading = ref(true)
const exporting = ref(false)
const agingData = ref([])

const filters = ref({
  as_of_date: '',
})

const bucketColumns = [
  { key: 'current', label: 'Current' },
  { key: 'days_1_30', label: '1–30 Days' },
  { key: 'days_31_60', label: '31–60 Days' },
  { key: 'days_61_90', label: '61–90 Days' },
  { key: 'days_over_90', label: '90+ Days' },
]

const totals = computed(() => {
  if (!agingData.value.length) return { total_outstanding: 0, current: 0, days_1_30: 0, days_31_60: 0, days_61_90: 0, days_over_90: 0 }
  return agingData.value.reduce((acc, row) => {
    acc.total_outstanding += row.total_outstanding || 0
    acc.current += row.current || 0
    acc.days_1_30 += row.days_1_30 || 0
    acc.days_31_60 += row.days_31_60 || 0
    acc.days_61_90 += row.days_61_90 || 0
    acc.days_over_90 += row.days_over_90 || 0
    return acc
  }, { total_outstanding: 0, current: 0, days_1_30: 0, days_31_60: 0, days_61_90: 0, days_over_90: 0 })
})

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (filters.value.as_of_date) params.as_of_date = filters.value.as_of_date
    const { data } = await getAgingReport(params)
    agingData.value = Array.isArray(data) ? data : data.items || data.customers || []
  } catch (error) {
    console.error('Failed to fetch aging report:', error)
    agingData.value = []
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
    const { data } = await getAgingPdf(filters.value)
    downloadBlob(data, 'aging-report.pdf')
  } catch (error) {
    console.error('Failed to export PDF:', error)
  } finally {
    exporting.value = false
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const { data } = await getAgingExcel(filters.value)
    downloadBlob(data, 'aging-report.xlsx')
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
      title="Aging Report"
      subtitle="Receivables and payables aging analysis"
      :breadcrumbs="[
        { text: 'Reports', to: { name: 'ReportsIndex' } },
        { text: 'Aging Report' },
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
            Excel
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-rose-600 rounded-lg hover:bg-rose-700 transition-colors"
            :disabled="exporting"
            @click="exportPdf"
          >
            PDF
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <DateInput v-model="filters.as_of_date" label="As of Date" name="as_of_date" />
        <div class="flex items-end">
          <button
            type="button"
            class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-rose-600 rounded-lg hover:bg-rose-700 transition-colors"
            @click="applyFilters"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
      <StatCard title="Total Outstanding" :value="formatCurrency(totals.total_outstanding)" icon="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" color="red" />
      <StatCard title="Current" :value="formatCurrency(totals.current)" icon="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" color="green" />
      <StatCard title="1–30 Days" :value="formatCurrency(totals.days_1_30)" icon="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" color="blue" />
      <StatCard title="31–60 Days" :value="formatCurrency(totals.days_31_60)" icon="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" color="amber" />
      <StatCard title="61–90 Days" :value="formatCurrency(totals.days_61_90)" icon="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" color="orange" />
      <StatCard title="90+ Days" :value="formatCurrency(totals.days_over_90)" icon="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" color="red" />
    </div>

    <!-- Aging Table -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <LoadingSpinner v-if="loading" size="lg" text="Loading aging data..." />
      <div v-else-if="agingData.length === 0" class="py-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        No aging data found for the selected period.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Customer</th>
              <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total Outstanding</th>
              <th v-for="bucket in bucketColumns" :key="bucket.key" class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                {{ bucket.label }}
              </th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="(row, idx) in agingData" :key="row.id || idx" class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
              <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white whitespace-nowrap">
                {{ row.customer_name || row.customer?.name || '—' }}
              </td>
              <td class="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white text-right whitespace-nowrap">
                {{ formatCurrency(row.total_outstanding) }}
              </td>
              <td v-for="bucket in bucketColumns" :key="bucket.key" class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 text-right whitespace-nowrap">
                {{ formatCurrency(row[bucket.key]) }}
              </td>
            </tr>
            <!-- Totals Row -->
            <tr class="bg-gray-50 dark:bg-gray-800 font-semibold">
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">Total</td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white text-right">
                {{ formatCurrency(totals.total_outstanding) }}
              </td>
              <td v-for="bucket in bucketColumns" :key="bucket.key" class="px-4 py-3 text-sm text-gray-900 dark:text-white text-right">
                {{ formatCurrency(totals[bucket.key]) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
