<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import Modal from '@/components/common/Modal.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import TextInput from '@/components/forms/TextInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'
import * as bankingApi from '@/api/banking'

const authStore = useAuthStore()
const toastStore = useToastStore()

const transfers = ref([])
const accounts = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showConfirmDialog = ref(false)
const submitting = ref(false)

// Create form
const form = reactive({
  from_account_id: '',
  to_account_id: '',
  amount: '',
  date: '',
  description: '',
  reference: '',
})
const formErrors = reactive({
  from_account_id: '',
  to_account_id: '',
  amount: '',
  date: '',
  description: '',
})

const breadcrumbs = [
  { text: 'Banking' },
  { text: 'Fund Transfers' },
]

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'from_account', label: 'From Account', sortable: true },
  { key: 'to_account', label: 'To Account', sortable: true },
  { key: 'amount', label: 'Amount', sortable: true, class: 'text-right' },
  { key: 'reference', label: 'Reference' },
  { key: 'status', label: 'Status', sortable: true },
]

function formatAmount(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

const accountOptions = computed(() => {
  return accounts.value.map(acc => ({
    value: acc.id,
    label: `${acc.account_name} (${acc.bank_name} - ${acc.account_number})`,
  }))
})

async function fetchTransfers() {
  loading.value = true
  try {
    const { data } = await bankingApi.listTransfers()
    transfers.value = Array.isArray(data) ? data : data.items || data.transfers || []
  } catch (error) {
    console.error('Failed to fetch transfers:', error)
    toastStore.show('Failed to load transfers', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchAccounts() {
  try {
    const { data } = await bankingApi.listBankAccounts()
    accounts.value = Array.isArray(data) ? data : data.items || data.accounts || []
  } catch (error) {
    console.error('Failed to fetch accounts:', error)
  }
}

function openCreateModal() {
  form.from_account_id = ''
  form.to_account_id = ''
  form.amount = ''
  form.date = new Date().toISOString().split('T')[0]
  form.description = ''
  form.reference = ''
  Object.keys(formErrors).forEach(k => formErrors[k] = '')
  showCreateModal.value = true
}

function validateForm() {
  let valid = true
  formErrors.from_account_id = ''
  formErrors.to_account_id = ''
  formErrors.amount = ''
  formErrors.date = ''
  formErrors.description = ''

  if (!form.from_account_id) {
    formErrors.from_account_id = 'From account is required'
    valid = false
  }
  if (!form.to_account_id) {
    formErrors.to_account_id = 'To account is required'
    valid = false
  }
  if (form.from_account_id && form.from_account_id === form.to_account_id) {
    formErrors.to_account_id = 'To account must be different from From account'
    valid = false
  }
  if (!form.amount || Number(form.amount) <= 0) {
    formErrors.amount = 'Amount must be greater than 0'
    valid = false
  }
  if (!form.date) {
    formErrors.date = 'Date is required'
    valid = false
  }
  if (!form.description.trim()) {
    formErrors.description = 'Description is required'
    valid = false
  }

  return valid
}

async function handleSubmit() {
  if (!validateForm()) return
  submitting.value = true
  try {
    await bankingApi.createTransfer({
      from_account_id: form.from_account_id,
      to_account_id: form.to_account_id,
      amount: Number(form.amount),
      date: form.date,
      description: form.description.trim(),
      reference: form.reference.trim(),
    })
    toastStore.show('Transfer created successfully')
    showCreateModal.value = false
    await fetchTransfers()
  } catch (error) {
    console.error('Failed to create transfer:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to create transfer'
    toastStore.show(message, 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  Promise.all([fetchTransfers(), fetchAccounts()])
})
</script>

<template>
  <div>
    <PageHeader title="Fund Transfers" :breadcrumbs="breadcrumbs">
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
          @click="openCreateModal"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Transfer
        </button>
      </template>
    </PageHeader>

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && transfers.length === 0"
      title="No transfers yet"
      message="Get started by creating your first fund transfer."
      action-text="New Transfer"
      @action="openCreateModal"
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="transfers"
        :loading="loading"
        search-placeholder="Search transfers..."
      >
        <!-- Date Column -->
        <template #cell-date="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDate(row.date, 'short') }}
          </span>
        </template>

        <!-- Amount Column -->
        <template #cell-amount="{ row }">
          <span class="text-sm font-bold text-gray-900 dark:text-white text-right block">
            {{ formatAmount(row.amount) }}
          </span>
        </template>

        <!-- Status Column -->
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" />
        </template>

        <!-- Actions -->
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <span class="text-xs text-gray-400 dark:text-gray-500">
              {{ formatDate(row.created_at, 'datetime') }}
            </span>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Create Transfer Modal -->
    <Modal
      v-model:show="showCreateModal"
      title="New Fund Transfer"
      size="lg"
    >
      <form class="space-y-6" @submit.prevent="handleSubmit">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <SelectInput
            v-model="form.from_account_id"
            label="From Account"
            name="from_account_id"
            :options="accountOptions"
            placeholder="Select source account"
            required
            :error="formErrors.from_account_id"
          />
          <SelectInput
            v-model="form.to_account_id"
            label="To Account"
            name="to_account_id"
            :options="accountOptions"
            placeholder="Select destination account"
            required
            :error="formErrors.to_account_id"
          />
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <TextInput
            v-model="form.amount"
            label="Amount"
            name="amount"
            type="number"
            placeholder="0.00"
            required
            :error="formErrors.amount"
          />
          <DateInput
            v-model="form.date"
            label="Date"
            name="date"
            required
            :error="formErrors.date"
          />
        </div>

        <TextInput
          v-model="form.reference"
          label="Reference"
          name="reference"
          placeholder="Optional reference number"
        />

        <TextareaInput
          v-model="form.description"
          label="Description"
          name="description"
          placeholder="Enter description for this transfer..."
          :rows="2"
          required
          :error="formErrors.description"
        />
      </form>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="showCreateModal = false"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="submitting"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleSubmit"
        >
          <LoadingSpinner v-if="submitting" size="sm" />
          {{ submitting ? 'Transferring...' : 'Create Transfer' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
