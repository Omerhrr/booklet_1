<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DateInput from '@/components/forms/DateInput.vue'
import { getAccount, getAccountBalance, getAccountLedger } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const account = ref(null)
const balance = ref(0)
const ledger = ref([])
const loading = ref(true)
const exporting = ref(false)

// Filters
const startDate = ref('')
const endDate = ref('')

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'reference', label: 'Reference', sortable: true },
  { key: 'description', label: 'Description', sortable: true },
  { key: 'debit', label: 'Debit', sortable: true },
  { key: 'credit', label: 'Credit', sortable: true },
  { key: 'balance', label: 'Balance', sortable: true },
]

async function fetchAccount() {
  loading.value = true
  try {
    const { data } = await getAccount(route.params.id)
    account.value = data
  } catch (error) {
    console.error('Failed to fetch account:', error)
    toast.show('Failed to load account', 'error')
    router.push({ name: 'ChartOfAccounts' })
  } finally {
    loading.value = false
  }
}

async function fetchBalance() {
  try {
    const { data } = await getAccountBalance(route.params.id)
    balance.value = data.balance || data.amount || 0
  } catch (error) {
    console.error('Failed to fetch balance:', error)
  }
}

async function fetchLedger() {
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const { data } = await getAccountLedger(route.params.id, params)
    ledger.value = Array.isArray(data) ? data : data.items || data.transactions || []
  } catch (error) {
    console.error('Failed to fetch ledger:', error)
    ledger.value = []
  }
}

function applyFilters() {
  fetchLedger()
}

async function handleExportPdf() {
  exporting.value = true
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const response = await getAccountLedger(route.params.id, { ...params, format: 'pdf' })
    // Fallback: use the API directly if blob endpoint exists
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
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const response = await getAccountLedger(route.params.id, { ...params, format: 'excel' })
    toast.show('Excel export initiated', 'success')
  } catch (error) {
    console.error('Failed to export Excel:', error)
    toast.show('Failed to export Excel', 'error')
  } finally {
    exporting.value = false
  }
}

function goBack() {
  router.push({ name: 'ChartOfAccounts' })
}

function handlePrint() {
  window.print()
}

const accountTypeLabel = computed(() => {
  if (!account.value?.type) return ''
  return account.value.type.charAt(0).toUpperCase() + account.value.type.slice(1).toLowerCase()
})

onMounted(() => {
  fetchAccount()
  fetchBalance()
  fetchLedger()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Account Details"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Chart of Accounts', to: { name: 'ChartOfAccounts' } },
        { text: account?.name || 'Details' }
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="goBack"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Back
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
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
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportPdf"
          >
            PDF
          </button>
          <button
            type="button"
            :disabled="exporting"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportExcel"
          >
            Excel
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading account details..." />

    <template v-else-if="account">
      <!-- Account Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="md:col-span-2">
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                {{ account.name }}
              </h2>
              <span class="inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 capitalize">
                {{ accountTypeLabel }}
              </span>
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span v-if="account.code" class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 8.25h15m-16.5 7.5h15m-1.8-13.5l-3.9 19.5m-2.1-19.5l-3.9 19.5" />
                </svg>
                {{ account.code }}
              </span>
              <span v-if="account.parent" class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
                </svg>
                Parent: {{ account.parent.name || account.parent }}
              </span>
            </div>
            <p v-if="account.description" class="mt-2 text-sm text-gray-600 dark:text-gray-400">
              {{ account.description }}
            </p>
          </div>

          <!-- Balance Summary Card -->
          <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-5 border border-gray-200 dark:border-gray-700">
            <p class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Current Balance</p>
            <p
              class="text-2xl font-bold"
              :class="balance >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'"
            >
              {{ formatCurrency(balance, auth.branchCurrency) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Date Range Filters -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
              Apply
            </button>
          </div>
        </div>
      </div>

      <!-- Ledger Table -->
      <DataTable
        :columns="columns"
        :data="ledger"
        :loading="false"
        :searchable="false"
        empty-message="No ledger entries found"
      >
        <template #cell-date="{ row }">
          <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
        </template>

        <template #cell-reference="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300 font-mono">{{ row.reference || '—' }}</span>
        </template>

        <template #cell-description="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ row.description || '—' }}</span>
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
    </template>
  </div>
</template>
