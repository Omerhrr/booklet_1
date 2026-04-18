<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Modal from '@/components/common/Modal.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { listDebitNotes, applyDebitNote } from '@/api/purchases'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const debitNotes = ref([])
const loading = ref(true)

// Apply modal state
const showApplyModal = ref(false)
const selectedNote = ref(null)
const applyForm = ref({
  amount: '',
  apply_date: new Date().toISOString().split('T')[0],
  payment_method: '',
  notes: '',
})
const applying = ref(false)

const paymentMethodOptions = [
  { value: 'cash', label: 'Cash' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Card' },
  { value: 'credit', label: 'Credit to Account' },
  { value: 'other', label: 'Other' },
]

const columns = [
  { key: 'debit_note_number', label: 'DN #', sortable: true },
  { key: 'bill_number', label: 'Bill', sortable: true },
  { key: 'vendor_name', label: 'Vendor', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'total', label: 'Amount', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchDebitNotes() {
  loading.value = true
  try {
    const { data } = await listDebitNotes()
    debitNotes.value = Array.isArray(data) ? data : data.items || data.debit_notes || []
  } catch (error) {
    console.error('Failed to fetch debit notes:', error)
    debitNotes.value = []
  } finally {
    loading.value = false
  }
}

function viewDebitNote(note) {
  router.push({ name: 'DebitNoteDetail', params: { id: note.id } })
}

function openApplyModal(note) {
  selectedNote.value = note
  applyForm.value = {
    amount: Number(note.total || note.amount || 0).toFixed(2),
    apply_date: new Date().toISOString().split('T')[0],
    payment_method: '',
    notes: '',
  }
  showApplyModal.value = true
}

function closeApplyModal() {
  showApplyModal.value = false
  selectedNote.value = null
  applyForm.value = { amount: '', apply_date: '', payment_method: '', notes: '' }
}

async function handleApply() {
  if (!applyForm.value.payment_method) {
    toast.show('Please select a payment method', 'error')
    return
  }

  applying.value = true
  try {
    await applyDebitNote(selectedNote.value.id, {
      amount: Number(applyForm.value.amount),
      apply_date: applyForm.value.apply_date,
      payment_method: applyForm.value.payment_method,
      notes: applyForm.value.notes,
    })
    toast.show('Debit note applied successfully', 'success')
    closeApplyModal()
    await fetchDebitNotes()
  } catch (error) {
    console.error('Failed to apply debit note:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to apply debit note'
    toast.show(message, 'error')
  } finally {
    applying.value = false
  }
}

onMounted(() => {
  fetchDebitNotes()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Debit Notes"
      :breadcrumbs="[
        { text: 'Purchases' },
        { text: 'Debit Notes' }
      ]"
    />

    <DataTable
      :columns="columns"
      :data="debitNotes"
      :loading="loading"
      empty-message="No debit notes found"
    >
      <template #cell-debit_note_number="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-300 transition-colors"
          @click="viewDebitNote(row)"
        >
          {{ row.debit_note_number || `DN-${String(row.id).padStart(4, '0')}` }}
        </button>
      </template>

      <template #cell-bill_number="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">
          {{ row.bill_number || row.bill?.bill_number || '—' }}
        </span>
      </template>

      <template #cell-vendor_name="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">
          {{ row.vendor_name || row.vendor?.name || '—' }}
        </span>
      </template>

      <template #cell-date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
      </template>

      <template #cell-total="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ formatCurrency(row.total || row.amount, auth.branchCurrency) }}</span>
      </template>

      <template #cell-status="{ row }">
        <StatusBadge :status="row.status" />
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="View"
            @click="viewDebitNote(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            v-if="row.status === 'open' || row.status === 'draft'"
            type="button"
            class="p-1.5 text-gray-400 hover:text-violet-600 dark:hover:text-violet-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Apply"
            @click="openApplyModal(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Apply Debit Note Modal -->
    <Modal
      v-model:show="showApplyModal"
      title="Apply Debit Note"
      size="md"
    >
      <div class="space-y-4">
        <div v-if="selectedNote" class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <span class="text-sm text-gray-500 dark:text-gray-400">Debit Note Amount</span>
          <span class="text-lg font-bold text-gray-900 dark:text-white">
            {{ formatCurrency(selectedNote.total || selectedNote.amount, auth.branchCurrency) }}
          </span>
        </div>

        <TextInput
          v-model="applyForm.amount"
          label="Amount"
          name="amount"
          type="number"
          placeholder="0.00"
          :required="true"
        />

        <DateInput
          v-model="applyForm.apply_date"
          label="Date"
          name="apply_date"
          :required="true"
        />

        <SelectInput
          v-model="applyForm.payment_method"
          label="Payment Method"
          name="payment_method"
          :options="paymentMethodOptions"
          placeholder="Select method"
          :required="true"
        />

        <TextareaInput
          v-model="applyForm.notes"
          label="Notes"
          name="notes"
          placeholder="Optional notes..."
          :rows="2"
        />
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          @click="closeApplyModal"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="applying"
          class="px-4 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleApply"
        >
          {{ applying ? 'Applying...' : 'Apply Debit Note' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
