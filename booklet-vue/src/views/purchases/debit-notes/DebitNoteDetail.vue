<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Modal from '@/components/common/Modal.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { getDebitNote, applyDebitNote } from '@/api/purchases'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const debitNote = ref(null)
const loading = ref(true)

// Apply modal state
const showApplyModal = ref(false)
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

const subtotal = computed(() => {
  if (!debitNote.value) return 0
  return (debitNote.value.line_items || []).reduce((sum, item) => {
    return sum + ((Number(item.quantity) || 0) * (Number(item.unit_price) || 0))
  }, 0)
})

const taxTotal = computed(() => {
  if (!debitNote.value) return 0
  return (debitNote.value.line_items || []).reduce((sum, item) => {
    const lineSub = (Number(item.quantity) || 0) * (Number(item.unit_price) || 0)
    return sum + (lineSub * ((Number(item.tax_rate) || 0) / 100))
  }, 0)
})

async function fetchDebitNote() {
  loading.value = true
  try {
    const { data } = await getDebitNote(route.params.id)
    debitNote.value = data
  } catch (error) {
    console.error('Failed to fetch debit note:', error)
    toast.show('Failed to load debit note', 'error')
    router.push({ name: 'DebitNoteList' })
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'DebitNoteList' })
}

function openApplyModal() {
  applyForm.value = {
    amount: Number(debitNote.value.total || debitNote.value.amount || 0).toFixed(2),
    apply_date: new Date().toISOString().split('T')[0],
    payment_method: '',
    notes: '',
  }
  showApplyModal.value = true
}

function closeApplyModal() {
  showApplyModal.value = false
  applyForm.value = { amount: '', apply_date: '', payment_method: '', notes: '' }
}

async function handleApply() {
  if (!applyForm.value.payment_method) {
    toast.show('Please select a payment method', 'error')
    return
  }

  applying.value = true
  try {
    await applyDebitNote(route.params.id, {
      amount: Number(applyForm.value.amount),
      apply_date: applyForm.value.apply_date,
      payment_method: applyForm.value.payment_method,
      notes: applyForm.value.notes,
    })
    toast.show('Debit note applied successfully', 'success')
    closeApplyModal()
    await fetchDebitNote()
  } catch (error) {
    console.error('Failed to apply debit note:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to apply debit note'
    toast.show(message, 'error')
  } finally {
    applying.value = false
  }
}

onMounted(() => {
  fetchDebitNote()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Debit Note Details"
      :breadcrumbs="[
        { text: 'Purchases' },
        { text: 'Debit Notes', to: { name: 'DebitNoteList' } },
        { text: debitNote?.debit_note_number || 'Details' }
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
            v-if="debitNote && (debitNote.status === 'open' || debitNote.status === 'draft')"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 transition-colors"
            @click="openApplyModal"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Apply Debit Note
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading debit note..." />

    <template v-else-if="debitNote">
      <!-- Debit Note Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                {{ debitNote.debit_note_number || `DN-${String(debitNote.id).padStart(4, '0')}` }}
              </h2>
              <StatusBadge :status="debitNote.status" />
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                </svg>
                {{ formatDate(debitNote.date, 'short') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Associated Bill -->
      <div v-if="debitNote.bill" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Associated Bill</h3>
        <router-link
          :to="{ name: 'BillDetail', params: { id: debitNote.bill.id } }"
          class="inline-flex items-center gap-2 text-sm font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-300 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          {{ debitNote.bill_number || debitNote.bill.bill_number || `BILL-${String(debitNote.bill.id).padStart(4, '0')}` }}
        </router-link>
        <p v-if="debitNote.reason" class="mt-2 text-sm text-gray-500 dark:text-gray-400">
          <span class="font-medium">Reason:</span> {{ debitNote.reason }}
        </p>
      </div>

      <!-- Vendor Info -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Vendor</h3>
        <p class="text-base font-medium text-gray-900 dark:text-white">
          {{ debitNote.vendor_name || debitNote.vendor?.name || '—' }}
        </p>
        <p v-if="debitNote.vendor?.email" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ debitNote.vendor.email }}</p>
      </div>

      <!-- Line Items & Summary -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- Line Items Table -->
        <div class="xl:col-span-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Debit Note Items</h3>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Item</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Qty</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Unit Price</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Tax</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr
                  v-for="(item, index) in (debitNote.line_items || [])"
                  :key="index"
                  class="hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <td class="px-4 py-3">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ item.description || item.product_name || '—' }}</p>
                  </td>
                  <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ item.quantity }}</td>
                  <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(item.unit_price, auth.branchCurrency) }}</td>
                  <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ item.tax_rate }}%</td>
                  <td class="px-4 py-3 text-right text-sm font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(item.line_total || (item.quantity * item.unit_price), auth.branchCurrency) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Summary Card -->
        <div>
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Amount Breakdown</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Subtotal</span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(subtotal, auth.branchCurrency) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Tax</span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(taxTotal, auth.branchCurrency) }}</span>
              </div>
              <div v-if="debitNote.discount > 0" class="flex items-center justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Discount</span>
                <span class="text-sm font-medium text-red-600 dark:text-red-400">-{{ formatCurrency(debitNote.discount, auth.branchCurrency) }}</span>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div class="flex items-center justify-between">
                  <span class="text-base font-semibold text-gray-900 dark:text-white">Total Debit</span>
                  <span class="text-lg font-bold text-violet-600 dark:text-violet-400">
                    {{ formatCurrency(debitNote.total || debitNote.amount, auth.branchCurrency) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Apply Debit Note Modal -->
    <Modal
      v-model:show="showApplyModal"
      title="Apply Debit Note"
      size="md"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <span class="text-sm text-gray-500 dark:text-gray-400">Debit Note Amount</span>
          <span class="text-lg font-bold text-gray-900 dark:text-white">
            {{ formatCurrency(debitNote?.total || debitNote?.amount, auth.branchCurrency) }}
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
