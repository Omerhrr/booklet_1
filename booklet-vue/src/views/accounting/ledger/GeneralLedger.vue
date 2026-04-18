<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DateInput from '@/components/forms/DateInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { getGeneralLedger } from '@/api/accounting'
import { listAccounts } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const auth = useAuthStore()
const toast = useToastStore()

const entries = ref([])
const loading = ref(true)
const exporting = ref(false)

// Filters
const startDate = ref('')
const endDate = ref('')
const accountId = ref('')
const accountOptions = ref([])

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'account_name', label: 'Account', sortable: true },
  { key: 'reference', label: 'Reference', sortable: true },
  { key: 'description', label: 'Description', sortable: true },
  { key: 'debit', label: 'Debit', sortable: true },
  { key: 'credit', label: 'Credit', sortable: true },
  { key: 'balance', label: 'Balance', sortable: true },
]

async function fetchLedger() {
  loading.value = true
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (accountId.value) params.account_id = accountId.value

    const { data } = await getGeneralLedger(params)
    entries.value = Array.isArray(data) ? data : data.items || data.transactions || []
  } catch (error) {
    console.error('Failed to fetch general ledger:', error)
    entries.value = []
  } finally {
    loading.value = false
  }
}

async function loadAccountOptions() {
  try {
    const { data } = await listAccounts()
    const accounts = Array.isArray(data) ? data : data.items || data.accounts || []
    accountOptions.value = accounts.map((a) => ({
      value: String(a.id),
      label: `${a.code ? a.code + ' — ' : ''}${a.name}`,
    })).sort((a, b) => a.label.localeCompare(b.label))
  } catch (error) {
    console.error('Failed to load account options:', error)
  }
}

function applyFilters() {
  fetchLedger()
}

async function handleExportPdf() {
  exporting.value = true
  try {
    toast.show('PDF export initiated', 'success')
  } catch (error) {
    console.error('Failed to export PDF:', error)
    toast.show('Failed to export PDF', 'error')
  } finally {
    exporting.value = false
  }
}

async function handleExportExcel() {
  exporting.value = true
  try {
    toast.show('Excel export initiated', 'success')
  } catch (error) {
    console.error('Failed to export Excel:', error)
    toast.show('Failed to export Excel', 'error')
  } finally {
    exporting.value = false
  }
}

function handlePrint() {
  window.print()
}

onMounted(() => {
  loadAccountOptions()
  fetchLedger()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="General Ledger"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'General Ledger' }
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            type="button"
            :disabled="exporting"
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
            :disabled="exporting"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportPdf"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            PDF
          </button>
          <button
            type="button"
            :disabled="exporting"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportExcel"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-3.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-1.5A1.125 1.125 0 0118 18.375M20.625 4.5H3.375m17.25 0c.621 0 1.125.504 1.125 1.125M20.625 4.5h-1.5C18.504 4.5 18 5.004 18 5.625m3.75 0v1.5c0 .621-.504 1.125-1.125 1.125M3.375 4.5c-.621 0-1.125.504-1.125 1.125M3.375 4.5h1.5C5.496 4.5 6 5.004 6 5.625m-3.75 0v1.5c0 .621.504 1.125 1.125 1.125m0 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m1.5-3.75C5.496 8.25 6 7.746 6 7.125v-1.5M4.875 8.25C5.496 8.25 6 8.754 6 9.375v1.5m0-5.25v5.25m0-5.25C6 5.004 6.504 4.5 7.125 4.5h9.75c.621 0 1.125.504 1.125 1.125m1.125 2.625h1.5m-1.5 0A1.125 1.125 0 0118 7.125v-1.5m1.125 2.625c-.621 0-1.125.504-1.125 1.125v1.5m2.625-2.625c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125M18 5.625v5.25M7.125 12h9.75m-9.75 0A1.125 1.125 0 016 10.875M7.125 12C6.504 12 6 12.504 6 13.125m0-2.25c0 .621.504 1.125 1.125 1.125M18 10.875c0 .621-.504 1.125-1.125 1.125M18 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m-12 5.25v-5.25m0 5.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125m-12 0v-1.5c0-.621-.504-1.125-1.125-1.125M18 18.375v-5.25m0 5.25v-1.5c0-.621.504-1.125 1.125-1.125M18 13.125v1.5c0 .621.504 1.125 1.125 1.125M18 13.125c0-.621.504-1.125 1.125-1.125M6 13.125v1.5c0 .621-.504 1.125-1.125 1.125M6 13.125C6 12.504 5.496 12 4.875 12m-1.5 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M19.125 12h1.5m0 0c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h1.5m14.25 0h1.5" />
            </svg>
            Excel
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SelectInput
          v-model="accountId"
          label="Account"
          name="account"
          :options="accountOptions"
          placeholder="All Accounts"
        />
        <DateInput
          v-model="startDate"
          label="Start Date"
          name="start_date"
        />
        <DateInput
          v-model="endDate"
          label="End Date"
          name="end_date"
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
            Apply Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="entries"
      :loading="loading"
      :searchable="false"
      empty-message="No general ledger entries found"
    >
      <template #cell-date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
      </template>

      <template #cell-account_name="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300 font-medium">
          {{ row.account_name || row.account?.name || `#${row.account_id}` }}
        </span>
        <p v-if="row.account?.code" class="text-xs text-gray-500 dark:text-gray-400">{{ row.account.code }}</p>
      </template>

      <template #cell-reference="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300 font-mono">{{ row.reference || '—' }}</span>
      </template>

      <template #cell-description="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300 max-w-[200px] truncate block">{{ row.description || '—' }}</span>
      </template>

      <template #cell-debit="{ row }">
        <span v-if="row.debit" class="text-sm text-gray-900 dark:text-white font-medium">
          {{ formatCurrency(row.debit, auth.branchCurrency) }}
        </span>
        <span v-else class="text-sm text-gray-400 dark:text-gray-500">—</span>
      </template>

      <template #cell-credit="{ row }">
        <span v-if="row.credit" class="text-sm text-gray-900 dark:text-white font-medium">
          {{ formatCurrency(row.credit, auth.branchCurrency) }}
        </span>
        <span v-else class="text-sm text-gray-400 dark:text-gray-500">—</span>
      </template>

      <template #cell-balance="{ row }">
        <span
          class="text-sm font-semibold"
          :class="(row.balance || row.running_balance || 0) >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'"
        >
          {{ formatCurrency(row.balance || row.running_balance || 0, auth.branchCurrency) }}
        </span>
      </template>
    </DataTable>
  </div>
</template>
