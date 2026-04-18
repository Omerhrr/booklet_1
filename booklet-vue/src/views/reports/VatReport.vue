<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DataTable from '@/components/common/DataTable.vue'
import DateInput from '@/components/forms/DateInput.vue'
import {
  getVatReport,
  getVatPdf,
  getVatExcel,
} from '@/api/reports'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'
import { downloadBlob } from '@/utils/export'

const loading = ref(true)
const exporting = ref(false)
const reportData = ref([])
const summary = ref({
  total_output_vat: 0,
  total_input_vat: 0,
  net_vat_payable: 0,
})

const filters = ref({
  start_date: '',
  end_date: '',
})

const columns = [
  { key: 'reference', label: 'Invoice/Bill #', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'type', label: 'Type', sortable: true },
  { key: 'amount', label: 'Amount', sortable: true },
  { key: 'vat_amount', label: 'VAT Amount', sortable: true },
]

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (filters.value.start_date) params.start_date = filters.value.start_date
    if (filters.value.end_date) params.end_date = filters.value.end_date
    const { data } = await getVatReport(params)
    reportData.value = Array.isArray(data) ? data : data.items || data.transactions || []
    summary.value = data.summary || {
      total_output_vat: reportData.value.filter(i => i.type === 'Sales').reduce((s, i) => s + (i.vat_amount || 0), 0),
      total_input_vat: reportData.value.filter(i => i.type === 'Purchase').reduce((s, i) => s + (i.vat_amount || 0), 0),
      net_vat_payable: 0,
    }
    summary.value.net_vat_payable = summary.value.total_output_vat - summary.value.total_input_vat
  } catch (error) {
    console.error('Failed to fetch VAT report:', error)
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
    const { data } = await getVatPdf(filters.value)
    downloadBlob(data, 'vat-report.pdf')
  } catch (error) {
    console.error('Failed to export PDF:', error)
  } finally {
    exporting.value = false
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const { data } = await getVatExcel(filters.value)
    downloadBlob(data, 'vat-report.xlsx')
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
      title="VAT Report"
      subtitle="Track output and input VAT obligations"
      :breadcrumbs="[
        { text: 'Reports', to: { name: 'ReportsIndex' } },
        { text: 'VAT Report' },
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
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <DateInput v-model="filters.start_date" label="Start Date" name="start_date" />
        <DateInput v-model="filters.end_date" label="End Date" name="end_date" />
        <div class="flex items-end">
          <button
            type="button"
            class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-teal-600 rounded-lg hover:bg-teal-700 transition-colors"
            @click="applyFilters"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard
        title="Total Output VAT"
        :value="formatCurrency(summary.total_output_vat)"
        icon="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"
        color="green"
      />
      <StatCard
        title="Total Input VAT"
        :value="formatCurrency(summary.total_input_vat)"
        icon="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-5.98.572M7.5 14.25a3 3 0 01-5.98-.572m11.98 0a3 3 0 10-5.98.572M7.5 14.25a3 3 0 11-5.98-.572"
        color="blue"
      />
      <StatCard
        title="Net VAT Payable"
        :value="formatCurrency(summary.net_vat_payable)"
        :change-type="summary.net_vat_payable >= 0 ? 'up' : 'down'"
        icon="M9 14.25l6-6m4.5-3.493V21.75l-3.75-1.5-3.75 1.5-3.75-1.5-3.75 1.5V4.757c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0c1.1.128 1.907 1.077 1.907 2.185zM9.75 9h.008v.008H9.75V9zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm4.125 4.5h.008v.008h-.008V13.5zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
        :color="summary.net_vat_payable >= 0 ? 'amber' : 'red'"
      />
    </div>

    <!-- Data Table -->
    <DataTable :columns="columns" :data="reportData" :loading="loading" :searchable="false" empty-message="No VAT data for the selected period">
      <template #cell-reference="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">
          {{ row.reference || row.invoice_number || row.bill_number || '—' }}
        </span>
      </template>
      <template #cell-date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
      </template>
      <template #cell-type="{ row }">
        <span
          :class="[
            'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
            row.type === 'Sales' || row.type === 'sales'
              ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400'
              : 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-400',
          ]"
        >
          {{ row.type }}
        </span>
      </template>
      <template #cell-amount="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(row.amount) }}</span>
      </template>
      <template #cell-vat_amount="{ row }">
        <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ formatCurrency(row.vat_amount) }}</span>
      </template>
    </DataTable>
  </div>
</template>
