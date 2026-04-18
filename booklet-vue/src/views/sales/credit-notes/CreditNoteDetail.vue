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
import { getCreditNote, applyCreditNote } from '@/api/sales'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const creditNote = ref(null)
const loading = ref(true)

// Apply modal state
const showApplyModal = ref(false)
const applyForm = ref({
  amount: '',
  refund_date: new Date().toISOString().split('T')[0],
  refund_method: '',
  notes: '',
})
const applying = ref(false)

const refundMethodOptions = [
  { value: 'cash', label: 'Cash' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Card' },
  { value: 'credit', label: 'Credit to Account' },
  { value: 'other', label: 'Other' },
]

const subtotal = computed(() => {
  if (!creditNote.value) return 0
  return (creditNote.value.line_items || []).reduce((sum, item) => {
    return sum + ((Number(item.quantity) || 0) * (Number(item.unit_price) || 0))
  }, 0)
})

const taxTotal = computed(() => {
  if (!creditNote.value) return 0
  return (creditNote.value.line_items || []).reduce((sum, item) => {
    const lineSub = (Number(item.quantity) || 0) * (Number(item.unit_price) || 0)
    return sum + (lineSub * ((Number(item.tax_rate) || 0) / 100))
  }, 0)
})

async function fetchCreditNote() {
  loading.value = true
  try {
    const { data } = await getCreditNote(route.params.id)
    creditNote.value = data
  } catch (error) {
    console.error('Failed to fetch credit note:', error)
    toast.show('Failed to load credit note', 'error')
    router.push({ name: 'CreditNoteList' })
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'CreditNoteList' })
}

function openApplyModal() {
  applyForm.value = {
    amount: Number(creditNote.value.total || creditNote.value.amount || 0).toFixed(2),
    refund_date: new Date().toISOString().split('T')[0],
    refund_method: '',
    notes: '',
  }
  showApplyModal.value = true
}

function closeApplyModal() {
  showApplyModal.value = false
  applyForm.value = { amount: '', refund_date: '', refund_method: '', notes: '' }
}

async function handleApply() {
  if (!applyForm.value.refund_method) {
    toast.show('Please select a refund method', 'error')
    return
  }

  applying.value = true
  try {
    await applyCreditNote(route.params.id, {
      amount: Number(applyForm.value.amount),
      refund_date: applyForm.value.refund_date,
      refund_method: applyForm.value.refund_method,
      notes: applyForm.value.notes,
    })
    toast.show('Credit note applied successfully', 'success')
    closeApplyModal()
    await fetchCreditNote()
  } catch (error) {
    console.error('Failed to apply credit note:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to apply credit note'
    toast.show(message, 'error')
  } finally {
    applying.value = false
  }
}

onMounted(() => {
  fetchCreditNote()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Credit Note Details"
      :breadcrumbs="[
        { text: 'Sales' },
        { text: 'Credit Notes', to: { name: 'CreditNoteList' } },
        { text: creditNote?.credit_note_number || 'Details' }
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
            v-if="creditNote && (creditNote.status === 'open' || creditNote.status === 'draft')"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
            @click="openApplyModal"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Apply Credit Note
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading credit note..." />

    <template v-else-if="creditNote">
      <!-- Credit Note Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                {{ creditNote.credit_note_number || `CN-${String(creditNote.id).padStart(4, '0')}` }}
              </h2>
              <StatusBadge :status="creditNote.status" />
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                </svg>
                {{ formatDate(creditNote.date, 'short') }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Associated Invoice -->
      <div v-if="creditNote.invoice" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Associated Invoice</h3>
        <router-link
          :to="{ name: 'InvoiceDetail', params: { id: creditNote.invoice.id } }"
          class="inline-flex items-center gap-2 text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          {{ creditNote.invoice_number || creditNote.invoice.invoice_number || `INV-${String(creditNote.invoice.id).padStart(4, '0')}` }}
        </router-link>
        <p v-if="creditNote.reason" class="mt-2 text-sm text-gray-500 dark:text-gray-400">
          <span class="font-medium">Reason:</span> {{ creditNote.reason }}
        </p>
      </div>

      <!-- Customer Info -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Customer</h3>
        <p class="text-base font-medium text-gray-900 dark:text-white">
          {{ creditNote.customer_name || creditNote.customer?.name || '—' }}
        </p>
        <p v-if="creditNote.customer?.email" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ creditNote.customer.email }}</p>
      </div>

      <!-- Line Items & Summary -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- Line Items Table -->
        <div class="xl:col-span-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Credit Note Items</h3>
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
                  v-for="(item, index) in (creditNote.line_items || [])"
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
              <div v-if="creditNote.discount > 0" class="flex items-center justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Discount</span>
                <span class="text-sm font-medium text-red-600 dark:text-red-400">-{{ formatCurrency(creditNote.discount, auth.branchCurrency) }}</span>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div class="flex items-center justify-between">
                  <span class="text-base font-semibold text-gray-900 dark:text-white">Total Credit</span>
                  <span class="text-lg font-bold text-red-600 dark:text-red-400">
                    -{{ formatCurrency(creditNote.total || creditNote.amount, auth.branchCurrency) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Apply Credit Note Modal -->
    <Modal
      v-model:show="showApplyModal"
      title="Apply Credit Note"
      size="md"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <span class="text-sm text-gray-500 dark:text-gray-400">Credit Note Amount</span>
          <span class="text-lg font-bold text-gray-900 dark:text-white">
            {{ formatCurrency(creditNote?.total || creditNote?.amount, auth.branchCurrency) }}
          </span>
        </div>

        <TextInput
          v-model="applyForm.amount"
          label="Refund Amount"
          name="amount"
          type="number"
          placeholder="0.00"
          :required="true"
        />

        <DateInput
          v-model="applyForm.refund_date"
          label="Refund Date"
          name="refund_date"
          :required="true"
        />

        <SelectInput
          v-model="applyForm.refund_method"
          label="Refund Method"
          name="refund_method"
          :options="refundMethodOptions"
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
          class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleApply"
        >
          {{ applying ? 'Applying...' : 'Apply Credit Note' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
