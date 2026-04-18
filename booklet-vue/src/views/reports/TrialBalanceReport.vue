<script setup>
import { ref, onMounted, computed } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DateInput from '@/components/forms/DateInput.vue'
import {
  getTrialBalanceReport,
  getTrialBalancePdf,
  getTrialBalanceExcel,
} from '@/api/reports'
import { formatCurrency } from '@/utils/currency'
import { downloadBlob } from '@/utils/export'

const loading = ref(true)
const exporting = ref(false)
const accounts = ref([])

const filters = ref({
  as_of_date: '',
})

const totals = computed(() => {
  if (!accounts.value.length) return { total_debit: 0, total_credit: 0 }
  return accounts.value.reduce((acc, row) => {
    acc.total_debit += row.debit || 0
    acc.total_credit += row.credit || 0
    return acc
  }, { total_debit: 0, total_credit: 0 })
})

const isBalanced = computed(() => {
  const diff = Math.abs(totals.value.total_debit - totals.value.total_credit)
  return diff < 0.01
})

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (filters.value.as_of_date) params.as_of_date = filters.value.as_of_date
    const { data } = await getTrialBalanceReport(params)
    accounts.value = Array.isArray(data) ? data : data.items || data.accounts || []
  } catch (error) {
    console.error('Failed to fetch trial balance:', error)
    accounts.value = []
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
    const { data } = await getTrialBalancePdf(filters.value)
    downloadBlob(data, 'trial-balance.pdf')
  } catch (error) {
    console.error('Failed to export PDF:', error)
  } finally {
    exporting.value = false
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const { data } = await getTrialBalanceExcel(filters.value)
    downloadBlob(data, 'trial-balance.xlsx')
  } catch (error) {
    console.error('Failed to export Excel:', error)
  } finally {
    exporting.value = false
  }
}

function printReport() {
  window.print()
}

onMounted(() => {
  fetchReport()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Trial Balance"
      subtitle="Verify debit and credit balances"
      :breadcrumbs="[
        { text: 'Reports', to: { name: 'ReportsIndex' } },
        { text: 'Trial Balance' },
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700 transition-colors"
            :disabled="exporting"
            @click="printReport"
          >
            Print
          </button>
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
            class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors"
            @click="applyFilters"
          >
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Balance Status -->
    <div
      v-if="!loading && accounts.length > 0"
      :class="[
        'flex items-center gap-3 px-4 py-3 rounded-lg border',
        isBalanced
          ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
          : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800',
      ]"
    >
      <svg v-if="isBalanced" class="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <svg v-else class="w-5 h-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
      <span
        :class="[
          'text-sm font-medium',
          isBalanced ? 'text-green-800 dark:text-green-400' : 'text-red-800 dark:text-red-400',
        ]"
      >
        {{ isBalanced ? 'Trial Balance is balanced' : `Trial Balance is out of balance by ${formatCurrency(Math.abs(totals.total_debit - totals.total_credit))}` }}
      </span>
    </div>

    <!-- Table -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <LoadingSpinner v-if="loading" size="lg" text="Loading trial balance..." />
      <div v-else-if="accounts.length === 0" class="py-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        No trial balance data found.
      </div>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account Code</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account Name</th>
              <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Debit</th>
              <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Credit</th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="(row, idx) in accounts" :key="row.id || idx" class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
              <td class="px-4 py-3 text-sm font-mono text-gray-600 dark:text-gray-400 whitespace-nowrap">
                {{ row.code || row.account_code || '—' }}
              </td>
              <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                {{ row.name || row.account_name }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 text-right whitespace-nowrap">
                {{ row.debit ? formatCurrency(row.debit) : '—' }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 text-right whitespace-nowrap">
                {{ row.credit ? formatCurrency(row.credit) : '—' }}
              </td>
            </tr>
            <!-- Totals Row -->
            <tr class="bg-gray-50 dark:bg-gray-800 font-semibold">
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white" colspan="2">Total</td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white text-right">
                {{ formatCurrency(totals.total_debit) }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white text-right">
                {{ formatCurrency(totals.total_credit) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
