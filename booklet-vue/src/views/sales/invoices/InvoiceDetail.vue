<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { getInvoice, recordPayment, writeOff, createCreditNote } from '@/api/sales'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const invoice = ref(null)
const loading = ref(true)

// Write-off confirmation
const showWriteOffDialog = ref(false)
const writingOff = ref(false)

// Record Payment modal
const showPaymentModal = ref(false)
const paymentForm = ref({
  amount: '',
  payment_date: new Date().toISOString().split('T')[0],
  payment_method: '',
  reference: '',
  notes: '',
})
const paymentSubmitting = ref(false)
const paymentErrors = ref({})

const paymentMethodOptions = [
  { value: 'cash', label: 'Cash' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Card' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'mobile_money', label: 'Mobile Money' },
  { value: 'other', label: 'Other' },
]

const balanceDue = computed(() => {
  if (!invoice.value) return 0
  const total = Number(invoice.value.total) || 0
  const paymentsTotal = (invoice.value.payments || []).reduce((sum, p) => sum + (Number(p.amount) || 0), 0)
  return total - paymentsTotal
})

async function fetchInvoice() {
  loading.value = true
  try {
    const { data } = await getInvoice(route.params.id)
    invoice.value = data
  } catch (error) {
    console.error('Failed to fetch invoice:', error)
    toast.show('Failed to load invoice', 'error')
    router.push({ name: 'InvoiceList' })
  } finally {
    loading.value = false
  }
}

function openPaymentModal() {
  paymentForm.value = {
    amount: balanceDue.value > 0 ? balanceDue.value.toFixed(2) : '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_method: '',
    reference: '',
    notes: '',
  }
  paymentErrors.value = {}
  showPaymentModal.value = true
}

function closePaymentModal() {
  showPaymentModal.value = false
  paymentForm.value = { amount: '', payment_date: '', payment_method: '', reference: '', notes: '' }
  paymentErrors.value = {}
}

function validatePayment() {
  const newErrors = {}
  if (!paymentForm.value.amount || Number(paymentForm.value.amount) <= 0) {
    newErrors.amount = 'Amount is required and must be greater than 0'
  }
  if (Number(paymentForm.value.amount) > balanceDue.value) {
    newErrors.amount = `Amount cannot exceed balance due of ${formatCurrency(balanceDue.value, auth.branchCurrency)}`
  }
  if (!paymentForm.value.payment_method) {
    newErrors.payment_method = 'Payment method is required'
  }
  paymentErrors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleRecordPayment() {
  if (!validatePayment()) return

  paymentSubmitting.value = true
  try {
    await recordPayment(route.params.id, {
      amount: Number(paymentForm.value.amount),
      payment_date: paymentForm.value.payment_date,
      payment_method: paymentForm.value.payment_method,
      reference: paymentForm.value.reference,
      notes: paymentForm.value.notes,
    })
    toast.show('Payment recorded successfully', 'success')
    closePaymentModal()
    await fetchInvoice()
  } catch (error) {
    console.error('Failed to record payment:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to record payment'
    toast.show(message, 'error')
  } finally {
    paymentSubmitting.value = false
  }
}

async function handleWriteOff() {
  writingOff.value = true
  try {
    await writeOff(route.params.id)
    toast.show('Invoice written off', 'success')
    await fetchInvoice()
  } catch (error) {
    console.error('Failed to write off invoice:', error)
    const message = error.response?.data?.message || 'Failed to write off invoice'
    toast.show(message, 'error')
  } finally {
    writingOff.value = false
  }
}

function handleCreateCreditNote() {
  router.push({ name: 'CreditNoteCreate', params: { id: route.params.id } })
}

function handlePrint() {
  window.print()
}

function goBack() {
  router.push({ name: 'InvoiceList' })
}

onMounted(() => {
  fetchInvoice()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Invoice Details"
      :breadcrumbs="[
        { text: 'Sales' },
        { text: 'Invoices', to: { name: 'InvoiceList' } },
        { text: invoice?.invoice_number || 'Details' }
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
            v-if="invoice && invoice.status !== 'cancelled' && invoice.status !== 'paid'"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
            @click="openPaymentModal"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
            </svg>
            Record Payment
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading invoice..." />

    <template v-else-if="invoice">
      <!-- Invoice Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                {{ invoice.invoice_number || `INV-${String(invoice.id).padStart(4, '0')}` }}
              </h2>
              <StatusBadge :status="invoice.status" />
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                </svg>
                {{ formatDate(invoice.date, 'short') }}
              </span>
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Due: {{ formatDate(invoice.due_date, 'short') }}
              </span>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              v-if="invoice.status !== 'cancelled' && invoice.status !== 'written_off'"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-amber-700 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-400 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
              @click="handleCreateCreditNote"
            >
              Credit Note
            </button>
            <button
              v-if="invoice.status !== 'cancelled' && invoice.status !== 'written_off' && invoice.status !== 'paid'"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-700 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              @click="showWriteOffDialog = true"
            >
              Write Off
            </button>
          </div>
        </div>
      </div>

      <!-- Customer Info -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Bill To</h3>
        <div class="space-y-1">
          <p class="text-base font-medium text-gray-900 dark:text-white">
            {{ invoice.customer_name || invoice.customer?.name || '—' }}
          </p>
          <p v-if="invoice.customer?.email" class="text-sm text-gray-500 dark:text-gray-400">{{ invoice.customer.email }}</p>
          <p v-if="invoice.customer?.phone" class="text-sm text-gray-500 dark:text-gray-400">{{ invoice.customer.phone }}</p>
          <p v-if="invoice.customer?.address" class="text-sm text-gray-500 dark:text-gray-400">{{ invoice.customer.address }}</p>
        </div>
      </div>

      <!-- Line Items & Summary -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <!-- Line Items Table -->
        <div class="xl:col-span-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Line Items</h3>
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
                  v-for="(item, index) in (invoice.line_items || [])"
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

          <!-- Notes & Terms -->
          <div v-if="invoice.notes || invoice.terms" class="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
            <div v-if="invoice.notes">
              <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Notes</h4>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ invoice.notes }}</p>
            </div>
            <div v-if="invoice.terms">
              <h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Terms</h4>
              <p class="mt-1 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ invoice.terms }}</p>
            </div>
          </div>
        </div>

        <!-- Summary Card -->
        <div class="space-y-6">
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Summary</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Subtotal</span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(invoice.subtotal, auth.branchCurrency) }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Tax</span>
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(invoice.tax_total, auth.branchCurrency) }}</span>
              </div>
              <div v-if="invoice.discount > 0" class="flex items-center justify-between">
                <span class="text-sm text-gray-500 dark:text-gray-400">Discount</span>
                <span class="text-sm font-medium text-red-600 dark:text-red-400">-{{ formatCurrency(invoice.discount, auth.branchCurrency) }}</span>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div class="flex items-center justify-between">
                  <span class="text-base font-semibold text-gray-900 dark:text-white">Total</span>
                  <span class="text-lg font-bold text-gray-900 dark:text-white">{{ formatCurrency(invoice.total, auth.branchCurrency) }}</span>
                </div>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-500 dark:text-gray-400">Paid</span>
                  <span class="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                    -{{ formatCurrency((invoice.payments || []).reduce((s, p) => s + (Number(p.amount) || 0), 0), auth.branchCurrency) }}
                  </span>
                </div>
                <div class="flex items-center justify-between mt-2">
                  <span class="text-base font-semibold text-gray-900 dark:text-white">Balance Due</span>
                  <span class="text-lg font-bold" :class="balanceDue > 0 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'">
                    {{ formatCurrency(balanceDue, auth.branchCurrency) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Payment History -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Payment History</h3>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ (invoice.payments || []).length }} payment(s)
          </span>
        </div>

        <div v-if="(invoice.payments || []).length === 0" class="text-center py-8">
          <svg class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
          </svg>
          <p class="text-sm text-gray-500 dark:text-gray-400">No payments recorded yet</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Method</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Reference</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Amount</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="(payment, idx) in invoice.payments" :key="idx" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(payment.payment_date, 'short') }}</td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 capitalize">{{ (payment.payment_method || '').replace(/_/g, ' ') }}</td>
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ payment.reference || '—' }}</td>
                <td class="px-4 py-3 text-right text-sm font-medium text-emerald-600 dark:text-emerald-400">{{ formatCurrency(payment.amount, auth.branchCurrency) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Record Payment Modal -->
    <Modal
      v-model:show="showPaymentModal"
      title="Record Payment"
      size="md"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <span class="text-sm text-gray-500 dark:text-gray-400">Balance Due</span>
          <span class="text-lg font-bold text-gray-900 dark:text-white">{{ formatCurrency(balanceDue, auth.branchCurrency) }}</span>
        </div>

        <TextInput
          v-model="paymentForm.amount"
          label="Payment Amount"
          name="amount"
          type="number"
          placeholder="0.00"
          :required="true"
          :error="paymentErrors.amount"
        />

        <DateInput
          v-model="paymentForm.payment_date"
          label="Payment Date"
          name="payment_date"
          :required="true"
        />

        <SelectInput
          v-model="paymentForm.payment_method"
          label="Payment Method"
          name="payment_method"
          :options="paymentMethodOptions"
          placeholder="Select method"
          :required="true"
          :error="paymentErrors.payment_method"
        />

        <TextInput
          v-model="paymentForm.reference"
          label="Reference"
          name="reference"
          placeholder="e.g., Transaction ID"
        />

        <TextareaInput
          v-model="paymentForm.notes"
          label="Notes"
          name="notes"
          placeholder="Optional payment notes..."
          :rows="2"
        />
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          @click="closePaymentModal"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="paymentSubmitting"
          class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleRecordPayment"
        >
          {{ paymentSubmitting ? 'Recording...' : 'Record Payment' }}
        </button>
      </template>
    </Modal>

    <!-- Write Off Confirmation -->
    <ConfirmDialog
      v-model:show="showWriteOffDialog"
      title="Write Off Invoice"
      message="Are you sure you want to write off this invoice? This will mark it as uncollectable and cannot be undone."
      confirm-text="Write Off"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleWriteOff"
    />
  </div>
</template>
