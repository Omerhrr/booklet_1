<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Modal from '@/components/common/Modal.vue'
import DataTable from '@/components/common/DataTable.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextInput from '@/components/forms/TextInput.vue'
import { getAccountTransactions, reconcileCashbook, exportCashbookPdf, exportCashbookExcel } from '@/api/cashbook'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const account = ref(null)
const transactions = ref([])
const loading = ref(true)
const exporting = ref(false)

// Date filters
const startDate = ref('')
const endDate = ref('')

// Reconcile modal
const showReconcileModal = ref(false)
const reconcileSubmitting = ref(false)
const reconcileErrors = ref({})
const reconcileForm = ref({
  date: new Date().toISOString().split('T')[0],
  ending_balance: '',
})

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'reference', label: 'Reference', sortable: true },
  { key: 'description', label: 'Description', sortable: true },
  { key: 'debit', label: 'Debit', sortable: true },
  { key: 'credit', label: 'Credit', sortable: true },
  { key: 'balance', label: 'Balance', sortable: true },
]

async function fetchTransactions() {
  loading.value = true
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const { data } = await getAccountTransactions(route.params.id, params)
    transactions.value = Array.isArray(data) ? data : data.items || data.transactions || []
    account.value = data.account || account.value
  } catch (error) {
    console.error('Failed to fetch transactions:', error)
    toast.show('Failed to load account transactions', 'error')
    router.push({ name: 'CashbookList' })
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  fetchTransactions()
}

function openReconcileModal() {
  reconcileForm.value = {
    date: new Date().toISOString().split('T')[0],
    ending_balance: '',
  }
  reconcileErrors.value = {}
  showReconcileModal.value = true
}

function closeReconcileModal() {
  showReconcileModal.value = false
  reconcileForm.value = { date: '', ending_balance: '' }
  reconcileErrors.value = {}
}

function validateReconcile() {
  const newErrors = {}
  if (!reconcileForm.value.date) {
    newErrors.date = 'Date is required'
  }
  if (!reconcileForm.value.ending_balance && reconcileForm.value.ending_balance !== 0) {
    newErrors.ending_balance = 'Ending balance is required'
  }
  reconcileErrors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleReconcile() {
  if (!validateReconcile()) return

  reconcileSubmitting.value = true
  try {
    await reconcileCashbook(route.params.id, {
      date: reconcileForm.value.date,
      ending_balance: Number(reconcileForm.value.ending_balance),
    })
    toast.show('Account reconciled successfully', 'success')
    closeReconcileModal()
    await fetchTransactions()
  } catch (error) {
    console.error('Failed to reconcile:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to reconcile account'
    toast.show(message, 'error')
  } finally {
    reconcileSubmitting.value = false
  }
}

async function handleExportPdf() {
  exporting.value = true
  try {
    const params = { account_id: route.params.id }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const { data } = await exportCashbookPdf(params)
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `account-${route.params.id}-transactions.pdf`)
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
    const params = { account_id: route.params.id }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const { data } = await exportCashbookExcel(params)
    const url = window.URL.createObjectURL(new Blob([data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `account-${route.params.id}-transactions.xlsx`)
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

function goBack() {
  router.push({ name: 'CashbookList' })
}

function handlePrint() {
  window.print()
}

onMounted(() => {
  fetchTransactions()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Cash Book Account Details"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Cash Book', to: { name: 'CashbookList' } },
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
            :disabled="exporting"
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
          <button
            v-if="auth.hasPermission('accounting:create')"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
            @click="openReconcileModal"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Reconcile
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading account transactions..." />

    <template v-else>
      <!-- Account Info Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">
              {{ account?.name || account?.account_name || `Account #${route.params.id}` }}
            </h2>
            <p v-if="account?.account_number" class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ account.account_number }}
            </p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-500 dark:text-gray-400">Current Balance</p>
            <p
              class="text-2xl font-bold"
              :class="(account?.balance || 0) >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'"
            >
              {{ formatCurrency(account?.balance || 0, auth.branchCurrency) }}
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

      <!-- Transactions Table -->
      <DataTable
        :columns="columns"
        :data="transactions"
        :loading="false"
        :searchable="false"
        empty-message="No transactions found for this account"
      >
        <template #cell-date="{ row }">
          <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
        </template>

        <template #cell-reference="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300 font-mono">{{ row.reference || '—' }}</span>
        </template>

        <template #cell-description="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300 max-w-[250px] truncate block">{{ row.description || '—' }}</span>
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
            :class="(row.balance || 0) >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'"
          >
            {{ formatCurrency(row.balance, auth.branchCurrency) }}
          </span>
        </template>
      </DataTable>
    </template>

    <!-- Reconcile Modal -->
    <Modal
      v-model:show="showReconcileModal"
      title="Reconcile Account"
      size="md"
    >
      <div class="space-y-4">
        <div class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Enter the ending balance from your bank statement to reconcile this account.
          </p>
        </div>

        <DateInput
          v-model="reconcileForm.date"
          label="Statement Date"
          name="reconcile_date"
          :required="true"
          :error="reconcileErrors.date"
        />

        <TextInput
          v-model="reconcileForm.ending_balance"
          label="Ending Balance"
          name="ending_balance"
          type="number"
          placeholder="0.00"
          :required="true"
          :error="reconcileErrors.ending_balance"
          icon="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          @click="closeReconcileModal"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="reconcileSubmitting"
          class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleReconcile"
        >
          {{ reconcileSubmitting ? 'Reconciling...' : 'Reconcile' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
