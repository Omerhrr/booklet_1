<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { getBill, createDebitNote } from '@/api/purchases'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(true)
const submitting = ref(false)
const bill = ref(null)
const errors = ref({})

const form = ref({
  reason: '',
  line_items: [],
})

const subtotal = computed(() => {
  return form.value.line_items.reduce((sum, item) => {
    return sum + ((Number(item.quantity) || 0) * (Number(item.unit_price) || 0))
  }, 0)
})

const taxTotal = computed(() => {
  return form.value.line_items.reduce((sum, item) => {
    const lineSub = (Number(item.quantity) || 0) * (Number(item.unit_price) || 0)
    return sum + (lineSub * ((Number(item.tax_rate) || 0) / 100))
  }, 0)
})

const grandTotal = computed(() => {
  return subtotal.value + taxTotal.value
})

function lineTotal(item) {
  const qty = Number(item.quantity) || 0
  const price = Number(item.unit_price) || 0
  const taxRate = Number(item.tax_rate) || 0
  return (qty * price) + ((qty * price) * (taxRate / 100))
}

function updateItemQty(index, value) {
  form.value.line_items[index].quantity = Math.max(0, Number(value) || 0)
}

function updateItemPrice(index, value) {
  form.value.line_items[index].unit_price = Math.max(0, Number(value) || 0)
}

function updateItemTax(index, value) {
  form.value.line_items[index].tax_rate = Math.max(0, Math.min(100, Number(value) || 0))
}

function validate() {
  const newErrors = {}
  if (form.value.line_items.length === 0) {
    newErrors.line_items = 'At least one line item is required'
  }
  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function fetchBill() {
  loading.value = true
  try {
    const { data } = await getBill(route.params.id)
    bill.value = data
    // Pre-fill line items from the original bill
    form.value.line_items = (data.line_items || []).map(item => ({
      product_id: item.product_id || null,
      description: item.description || item.product_name || '',
      quantity: item.quantity || 0,
      unit_price: item.unit_price || 0,
      tax_rate: item.tax_rate || 0,
    }))
  } catch (error) {
    console.error('Failed to fetch bill:', error)
    toast.show('Failed to load bill', 'error')
    router.push({ name: 'BillList' })
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!validate()) return

  submitting.value = true
  try {
    const payload = {
      bill_id: route.params.id,
      reason: form.value.reason,
      line_items: form.value.line_items.map(item => ({
        product_id: item.product_id || null,
        description: item.description,
        quantity: Number(item.quantity),
        unit_price: Number(item.unit_price),
        tax_rate: Number(item.tax_rate),
      })),
    }

    await createDebitNote(payload)
    toast.show('Debit note created successfully', 'success')
    router.push({ name: 'DebitNoteList' })
  } catch (error) {
    console.error('Failed to create debit note:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to create debit note'
    toast.show(message, 'error')
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  router.push({ name: 'BillDetail', params: { id: route.params.id } })
}

onMounted(() => {
  fetchBill()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Create Debit Note"
      :breadcrumbs="[
        { text: 'Purchases' },
        { text: 'Bills', to: { name: 'BillList' } },
        { text: bill?.bill_number || 'Bill', to: { name: 'BillDetail', params: { id: route.params.id } } },
        { text: 'Debit Note' }
      ]"
    />

    <LoadingSpinner v-if="loading" text="Loading bill data..." />

    <form v-else class="space-y-6" @submit.prevent="handleSubmit">
      <!-- Bill Reference -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Bill Reference</h2>
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            <svg class="w-5 h-5 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <span class="text-sm font-medium text-gray-900 dark:text-white">
              {{ bill?.bill_number || `BILL-${String(bill?.id).padStart(4, '0')}` }}
            </span>
          </div>
          <div class="flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            <svg class="w-5 h-5 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0" />
            </svg>
            <span class="text-sm text-gray-700 dark:text-gray-300">
              {{ bill?.vendor_name || bill?.vendor?.name || '—' }}
            </span>
          </div>
          <div class="flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
            <span class="text-sm text-gray-500 dark:text-gray-400">Total:</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">
              {{ formatCurrency(bill?.total, auth.branchCurrency) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Line Items -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Debit Note Items</h2>
        <p class="mb-4 text-sm text-gray-500 dark:text-gray-400">Edit the items to include in this debit note. Adjust quantities as needed.</p>

        <p v-if="errors.line_items" class="mb-4 text-sm text-red-600 dark:text-red-400">{{ errors.line_items }}</p>

        <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Description</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-24">Qty</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-32">Unit Price</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-28">Tax %</th>
                <th class="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-32">Line Total</th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(item, index) in form.line_items"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <td class="px-3 py-2">
                  <span class="text-sm text-gray-900 dark:text-white">{{ item.description || '—' }}</span>
                </td>
                <td class="px-3 py-2">
                  <input
                    :value="item.quantity"
                    type="number"
                    min="0"
                    step="1"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                    @input="updateItemQty(index, $event.target.value)"
                  />
                </td>
                <td class="px-3 py-2">
                  <input
                    :value="item.unit_price"
                    type="number"
                    min="0"
                    step="0.01"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                    @input="updateItemPrice(index, $event.target.value)"
                  />
                </td>
                <td class="px-3 py-2">
                  <input
                    :value="item.tax_rate"
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                    @input="updateItemTax(index, $event.target.value)"
                  />
                </td>
                <td class="px-3 py-2 text-right">
                  <span class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(lineTotal(item), auth.branchCurrency) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Reason & Summary -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TextareaInput
          v-model="form.reason"
          label="Reason"
          name="reason"
          placeholder="Explain why this debit note is being issued..."
          :rows="4"
        />

        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 h-fit">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Summary</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">Subtotal</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(subtotal, auth.branchCurrency) }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">Tax</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(taxTotal, auth.branchCurrency) }}</span>
            </div>
            <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
              <div class="flex items-center justify-between">
                <span class="text-base font-semibold text-gray-900 dark:text-white">Total Debit</span>
                <span class="text-lg font-bold text-violet-600 dark:text-violet-400">
                  {{ formatCurrency(grandTotal, auth.branchCurrency) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-col-reverse sm:flex-row items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          class="w-full sm:w-auto px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          :disabled="submitting"
          @click="handleCancel"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="submitting"
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          {{ submitting ? 'Creating...' : 'Create Debit Note' }}
        </button>
      </div>
    </form>
  </div>
</template>
