<script setup>
import { ref, onMounted, computed } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import DateInput from '@/components/forms/DateInput.vue'
import { getTrialBalance } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const auth = useAuthStore()
const toast = useToastStore()

const accounts = ref([])
const loading = ref(true)
const asOfDate = ref('')

const columns = [
  { key: 'code', label: 'Account Code', sortable: true },
  { key: 'name', label: 'Account Name', sortable: true },
  { key: 'debit', label: 'Debit', sortable: true },
  { key: 'credit', label: 'Credit', sortable: true },
]

const totalDebit = computed(() => {
  return accounts.value.reduce((sum, item) => sum + (Number(item.debit) || 0), 0)
})

const totalCredit = computed(() => {
  return accounts.value.reduce((sum, item) => sum + (Number(item.credit) || 0), 0)
})

const isBalanced = computed(() => Math.abs(totalDebit.value - totalCredit.value) < 0.01)

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (asOfDate.value) params.as_of_date = asOfDate.value

    const { data } = await getTrialBalance(params)
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

function handlePrint() {
  window.print()
}

function handleExportPdf() {
  toast.show('PDF export initiated', 'success')
}

function handleExportExcel() {
  toast.show('Excel export initiated', 'success')
}

onMounted(() => {
  fetchReport()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Trial Balance"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Reports' },
        { text: 'Trial Balance' }
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handlePrint"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18.75 7.131s0 0 0 0" />
            </svg>
            Print
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportPdf"
          >
            PDF
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportExcel"
          >
            Excel
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Filter -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DateInput
          v-model="asOfDate"
          label="As of Date"
          name="as_of_date"
          help-text="Leave blank for today"
        />
        <div class="flex items-end">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            @click="applyFilters"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z" />
            </svg>
            Generate Report
          </button>
        </div>
      </div>
    </div>

    <!-- Balance Check -->
    <div v-if="!loading && accounts.length > 0" class="flex justify-center">
      <div
        class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
        :class="isBalanced ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path
            v-if="isBalanced"
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
          <path
            v-else
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
          />
        </svg>
        {{ isBalanced ? 'Trial balance is balanced' : `Trial balance is not balanced (difference: ${formatCurrency(Math.abs(totalDebit - totalCredit), auth.branchCurrency)})` }}
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="accounts"
      :loading="loading"
      :searchable="false"
      empty-message="No trial balance data available"
    >
      <template #cell-code="{ row }">
        <span class="text-sm font-mono text-gray-700 dark:text-gray-300 font-medium">{{ row.code || '—' }}</span>
      </template>

      <template #cell-name="{ row }">
        <div>
          <span class="text-sm font-medium text-gray-900 dark:text-white">{{ row.name || '—' }}</span>
          <p v-if="row.type" class="text-xs text-gray-500 dark:text-gray-400 capitalize">{{ row.type }}</p>
        </div>
      </template>

      <template #cell-debit="{ row }">
        <span v-if="row.debit" class="text-sm font-medium text-gray-900 dark:text-white">
          {{ formatCurrency(row.debit, auth.branchCurrency) }}
        </span>
        <span v-else class="text-sm text-gray-400 dark:text-gray-500">—</span>
      </template>

      <template #cell-credit="{ row }">
        <span v-if="row.credit" class="text-sm font-medium text-gray-900 dark:text-white">
          {{ formatCurrency(row.credit, auth.branchCurrency) }}
        </span>
        <span v-else class="text-sm text-gray-400 dark:text-gray-500">—</span>
      </template>
    </DataTable>

    <!-- Totals Row -->
    <div
      v-if="!loading && accounts.length > 0"
      class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
    >
      <div class="flex items-center justify-between">
        <span class="text-base font-bold text-gray-900 dark:text-white">Total</span>
        <div class="flex items-center gap-8">
          <span class="text-base font-bold text-gray-900 dark:text-white">
            {{ formatCurrency(totalDebit, auth.branchCurrency) }}
          </span>
          <span class="text-base font-bold text-gray-900 dark:text-white">
            {{ formatCurrency(totalCredit, auth.branchCurrency) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
