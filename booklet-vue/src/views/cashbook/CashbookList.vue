<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import DateInput from '@/components/forms/DateInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import {
  listCashbookEntries,
  getCashFlow,
  exportCashbookPdf,
  exportCashbookExcel,
  deleteCashbookEntry,
} from '@/api/cashbook'
import { getPaymentAccounts, listBankAccounts } from '@/api/banking'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const entries = ref([])
const loading = ref(true)
const exporting = ref(false)
const activeType = ref('all')

// Filters
const startDate = ref('')
const endDate = ref('')
const accountId = ref('')
const accountOptions = ref([])

// Cash flow summary
const cashFlow = ref({ total_in: 0, total_out: 0, net: 0 })

// Delete confirmation
const showDeleteDialog = ref(false)
const deletingEntry = ref(null)
const deleting = ref(false)

const entryTypeOptions = [
  { value: 'all', label: 'All Types' },
  { value: 'credit', label: 'Credit' },
  { value: 'debit', label: 'Debit' },
]

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'reference', label: 'Reference', sortable: true },
  { key: 'account_name', label: 'Account', sortable: true },
  { key: 'description', label: 'Description', sortable: true },
  { key: 'debit', label: 'Debit', sortable: true },
  { key: 'credit', label: 'Credit', sortable: true },
  { key: 'balance', label: 'Balance', sortable: true },
  { key: 'entry_type', label: 'Entry Type', sortable: true },
]

async function fetchEntries() {
  loading.value = true
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (accountId.value) params.account_id = accountId.value
    if (activeType.value !== 'all') params.entry_type = activeType.value

    const { data } = await listCashbookEntries(params)
    entries.value = Array.isArray(data) ? data : data.items || data.entries || []
  } catch (error) {
    console.error('Failed to fetch cashbook entries:', error)
    entries.value = []
  } finally {
    loading.value = false
  }
}

async function fetchCashFlow() {
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    const { data } = await getCashFlow(params)
    cashFlow.value = {
      total_in: data.total_in || data.totalIn || 0,
      total_out: data.total_out || data.totalOut || 0,
      net: data.net || 0,
    }
  } catch (error) {
    console.error('Failed to fetch cash flow:', error)
  }
}

async function loadAccountOptions() {
  try {
    const [bankRes, paymentRes] = await Promise.all([
      listBankAccounts().catch(() => ({ data: [] })),
      getPaymentAccounts().catch(() => ({ data: [] })),
    ])

    const banks = Array.isArray(bankRes.data) ? bankRes.data : bankRes.data.items || bankRes.data.accounts || []
    const payments = Array.isArray(paymentRes.data) ? paymentRes.data : paymentRes.data.items || paymentRes.data.accounts || []

    const allAccounts = [...banks, ...payments].filter(
      (a, i, arr) => arr.findIndex((b) => String(b.id) === String(a.id)) === i
    )

    accountOptions.value = allAccounts.map((a) => ({
      value: String(a.id),
      label: a.name || a.account_name || a.account_number || `Account ${a.id}`,
    }))
  } catch (error) {
    console.error('Failed to load account options:', error)
  }
}

function applyFilters() {
  fetchEntries()
  fetchCashFlow()
}

function viewEntry(row) {
  if (row.entry_type === 'manual') {
    router.push({ name: 'CashbookAccountDetail', params: { id: row.account_id || row.id } })
  }
}

function viewAccount(row) {
  if (row.account_id) {
    router.push({ name: 'CashbookAccountDetail', params: { id: row.account_id } })
  }
}

function confirmDelete(row) {
  if (row.entry_type !== 'manual') {
    toast.show('Only manual entries can be deleted', 'warning')
    return
  }
  deletingEntry.value = row
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!deletingEntry.value) return
  deleting.value = true
  try {
    await deleteCashbookEntry(deletingEntry.value.id)
    toast.show('Entry deleted successfully', 'success')
    await fetchEntries()
    await fetchCashFlow()
  } catch (error) {
    console.error('Failed to delete entry:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to delete entry'
    toast.show(message, 'error')
  } finally {
    deleting.value = false
  }
}

function createEntry() {
  router.push({ name: 'CashbookCreate' })
}

async function handleExportPdf() {
  exporting.value = true
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (accountId.value) params.account_id = accountId.value
    if (activeType.value !== 'all') params.entry_type = activeType.value

    const { data } = await exportCashbookPdf(params)
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'cashbook.pdf')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    toast.show('PDF exported successfully', 'success')
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
    if (accountId.value) params.account_id = accountId.value
    if (activeType.value !== 'all') params.entry_type = activeType.value

    const { data } = await exportCashbookExcel(params)
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'cashbook.xlsx')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    toast.show('Excel exported successfully', 'success')
  } catch (error) {
    console.error('Failed to export Excel:', error)
    toast.show('Failed to export Excel', 'error')
  } finally {
    exporting.value = false
  }
}

watch(activeType, () => {
  applyFilters()
})

onMounted(() => {
  loadAccountOptions()
  fetchEntries()
  fetchCashFlow()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Cash Book"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Cash Book' }
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
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
          <button
            v-if="auth.hasPermission('accounting:create')"
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
            @click="createEntry"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Create Entry
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Cash Flow Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard
        title="Total In"
        :value="formatCurrency(cashFlow.total_in, auth.branchCurrency)"
        color="green"
        icon="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"
      />
      <StatCard
        title="Total Out"
        :value="formatCurrency(cashFlow.total_out, auth.branchCurrency)"
        color="red"
        icon="M2.25 6L9 12.75l4.286-4.286a11.948 11.948 0 014.306 6.43l.776 2.898m0 0l3.182-5.511m-3.182 5.51l-5.511-3.181"
      />
      <StatCard
        title="Net Cash Flow"
        :value="formatCurrency(cashFlow.net, auth.branchCurrency)"
        :color="cashFlow.net >= 0 ? 'green' : 'red'"
        :change-type="cashFlow.net >= 0 ? 'up' : 'down'"
        icon="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
      />
    </div>

    <!-- Filters -->
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
        <SelectInput
          v-model="accountId"
          label="Account"
          name="account"
          :options="accountOptions"
          placeholder="All Accounts"
        />
        <SelectInput
          v-model="activeType"
          label="Entry Type"
          name="entry_type"
          :options="entryTypeOptions"
        />
      </div>
      <div class="mt-4 flex justify-end">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          @click="applyFilters"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z" />
          </svg>
          Apply Filters
        </button>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="entries"
      :loading="loading"
      :searchable="false"
      empty-message="No cash book entries found"
    >
      <template #cell-date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
      </template>

      <template #cell-reference="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300 font-mono">{{ row.reference || '—' }}</span>
      </template>

      <template #cell-account_name="{ row }">
        <button
          v-if="row.account_id"
          type="button"
          class="text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors"
          @click="viewAccount(row)"
        >
          {{ row.account_name || row.account?.name || '—' }}
        </button>
        <span v-else class="text-sm text-gray-700 dark:text-gray-300">{{ row.account_name || '—' }}</span>
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
          :class="row.balance >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'"
        >
          {{ formatCurrency(row.balance, auth.branchCurrency) }}
        </span>
      </template>

      <template #cell-entry_type="{ row }">
        <StatusBadge
          v-if="row.entry_type"
          :status="row.entry_type === 'manual' ? 'draft' : row.entry_type"
          :variant-map="{
            manual: 'default',
            credit: 'success',
            debit: 'warning',
            funding: 'info',
            invoice: 'info',
            payment: 'info',
          }"
        />
        <span v-else class="text-sm text-gray-400 dark:text-gray-500">—</span>
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="View"
            @click="viewEntry(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            v-if="row.entry_type === 'manual'"
            type="button"
            class="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            title="Delete"
            @click="confirmDelete(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Entry"
      message="Are you sure you want to delete this cash book entry? This action cannot be undone."
      confirm-text="Delete"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
