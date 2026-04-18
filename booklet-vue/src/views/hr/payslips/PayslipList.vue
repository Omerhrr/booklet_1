<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { downloadBlob } from '@/utils/export'
import * as hrApi from '@/api/hr'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const payslips = ref([])
const loading = ref(true)
const exporting = ref(false)

// Filters
const filterMonth = ref(new Date().getMonth() + 1)
const filterYear = ref(new Date().getFullYear())

const breadcrumbs = [
  { text: 'HR' },
  { text: 'Payslips' },
]

const statusVariantMap = {
  pending: 'warning',
  paid: 'success',
}

const monthOptions = [
  { value: 0, label: 'All Months' },
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
]

const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = [{ value: 0, label: 'All Years' }]
  for (let y = currentYear - 3; y <= currentYear; y++) {
    years.push({ value: y, label: String(y) })
  }
  return years
})

function formatAmount(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

const columns = [
  { key: 'employee_name', label: 'Employee', sortable: true },
  { key: 'period', label: 'Month/Year', sortable: true },
  { key: 'gross_pay', label: 'Gross Pay', sortable: true, class: 'text-right' },
  { key: 'total_deductions', label: 'Deductions', sortable: true, class: 'text-right' },
  { key: 'net_pay', label: 'Net Pay', sortable: true, class: 'text-right' },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchPayslips() {
  loading.value = true
  try {
    const params = {}
    if (filterMonth.value) params.month = filterMonth.value
    if (filterYear.value) params.year = filterYear.value
    const { data } = await hrApi.listPayslips(params)
    payslips.value = Array.isArray(data) ? data : data.items || data.payslips || []
  } catch (error) {
    console.error('Failed to fetch payslips:', error)
    toastStore.show('Failed to load payslips', 'error')
  } finally {
    loading.value = false
  }
}

function viewPayslip(payslip) {
  router.push({ name: 'PayslipDetail', params: { id: payslip.id } })
}

async function markAsPaid(payslip) {
  try {
    await hrApi.markPayslipPaid(payslip.id)
    payslip.status = 'paid'
    toastStore.show('Payslip marked as paid')
  } catch (error) {
    console.error('Failed to mark payslip as paid:', error)
    toastStore.show('Failed to update payslip status', 'error')
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const params = {}
    if (filterMonth.value) params.month = filterMonth.value
    if (filterYear.value) params.year = filterYear.value
    const { data } = await hrApi.exportPayslipsExcel(params)
    const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    downloadBlob(blob, `Payslips_${filterMonth.value || 'All'}_${filterYear.value || 'All'}.xlsx`)
    toastStore.show('Excel export downloaded')
  } catch (error) {
    console.error('Failed to export payslips:', error)
    toastStore.show('Failed to export payslips', 'error')
  } finally {
    exporting.value = false
  }
}

onMounted(fetchPayslips)
</script>

<template>
  <div>
    <PageHeader title="Payslips" :breadcrumbs="breadcrumbs">
      <template #actions>
        <button
          type="button"
          :disabled="exporting || payslips.length === 0"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="exportExcel"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          {{ exporting ? 'Exporting...' : 'Export Excel' }}
        </button>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="w-full sm:w-48">
          <SelectInput
            v-model="filterMonth"
            label="Month"
            name="filter_month"
            :options="monthOptions"
          />
        </div>
        <div class="w-full sm:w-40">
          <SelectInput
            v-model="filterYear"
            label="Year"
            name="filter_year"
            :options="yearOptions"
          />
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="payslips"
      :loading="loading"
      search-placeholder="Search payslips..."
      :searchable="false"
    >
      <!-- Employee Name Column -->
      <template #cell-employee_name="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
          @click="viewPayslip(row)"
        >
          {{ row.employee_name || '—' }}
        </button>
      </template>

      <!-- Period Column -->
      <template #cell-period="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">
          {{ row.month_name || `Month ${row.month}` }} {{ row.year }}
        </span>
      </template>

      <!-- Gross Pay Column -->
      <template #cell-gross_pay="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white text-right block">
          {{ formatAmount(row.gross_pay) }}
        </span>
      </template>

      <!-- Deductions Column -->
      <template #cell-total_deductions="{ row }">
        <span class="text-sm text-red-600 dark:text-red-400 text-right block">
          {{ formatAmount(row.total_deductions) }}
        </span>
      </template>

      <!-- Net Pay Column -->
      <template #cell-net_pay="{ row }">
        <span class="text-sm font-bold text-green-600 dark:text-green-400 text-right block">
          {{ formatAmount(row.net_pay) }}
        </span>
      </template>

      <!-- Status Column -->
      <template #cell-status="{ row }">
        <StatusBadge :status="row.status" :variant-map="statusVariantMap" />
      </template>

      <!-- Actions -->
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <!-- View -->
          <button
            type="button"
            class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="View"
            @click="viewPayslip(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>

          <!-- Mark as Paid -->
          <button
            v-if="row.status === 'pending'"
            type="button"
            class="p-1.5 text-gray-500 hover:text-green-600 dark:text-gray-400 dark:hover:text-green-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Mark as Paid"
            @click="markAsPaid(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>
  </div>
</template>
