<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { createBill } from '@/api/purchases'
import { listVendors } from '@/api/crm'
import { listProducts } from '@/api/inventory'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const submitting = ref(false)
const loadingOptions = ref(true)
const errors = ref({})

// Form data
const form = ref({
  vendor_id: '',
  date: new Date().toISOString().split('T')[0],
  due_date: '',
  notes: '',
  terms: '',
  discount: 0,
  line_items: [
    createEmptyLineItem(),
  ],
})

// Dropdown options
const vendorOptions = ref([])
const productOptions = ref([])

function createEmptyLineItem() {
  return {
    product_id: '',
    description: '',
    quantity: 1,
    unit_price: 0,
    tax_rate: 0,
  }
}

// Computed line total for each item
function lineTotal(item) {
  const qty = Number(item.quantity) || 0
  const price = Number(item.unit_price) || 0
  const taxRate = Number(item.tax_rate) || 0
  const subtotal = qty * price
  const tax = subtotal * (taxRate / 100)
  return subtotal + tax
}

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

const discount = computed(() => {
  return Number(form.value.discount) || 0
})

const grandTotal = computed(() => {
  return subtotal.value + taxTotal.value - discount.value
})

function addLineItem() {
  form.value.line_items.push(createEmptyLineItem())
}

function removeLineItem(index) {
  if (form.value.line_items.length > 1) {
    form.value.line_items.splice(index, 1)
  }
}

function onProductSelect(index, productId) {
  const product = productOptions.value.find(p => p.value === productId)
  if (product) {
    form.value.line_items[index].description = product.label || product.description || ''
    form.value.line_items[index].unit_price = product.price || 0
    form.value.line_items[index].tax_rate = product.tax_rate || 0
  }
}

function validate() {
  const newErrors = {}

  if (!form.value.vendor_id) {
    newErrors.vendor_id = 'Vendor is required'
  }

  if (!form.value.date) {
    newErrors.date = 'Bill date is required'
  }

  if (!form.value.due_date) {
    newErrors.due_date = 'Due date is required'
  }

  if (form.value.line_items.length === 0) {
    newErrors.line_items = 'At least one line item is required'
  }

  const hasEmptyLine = form.value.line_items.some(item => !item.product_id && !item.description)
  if (hasEmptyLine) {
    newErrors.line_items = 'All line items must have a product or description'
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function loadOptions() {
  loadingOptions.value = true
  try {
    const [vendorsRes, productsRes] = await Promise.all([
      listVendors({ limit: 200 }),
      listProducts({ limit: 200 }),
    ])

    const vendors = Array.isArray(vendorsRes.data)
      ? vendorsRes.data
      : vendorsRes.data.items || vendorsRes.data.vendors || []

    vendorOptions.value = vendors.map(v => ({
      value: v.id,
      label: v.name || v.display_name,
    }))

    const products = Array.isArray(productsRes.data)
      ? productsRes.data
      : productsRes.data.items || productsRes.data.products || []

    productOptions.value = products.map(p => ({
      value: p.id,
      label: p.name,
      price: p.cost_price || p.price || 0,
      tax_rate: p.tax_rate || 0,
      description: p.description,
    }))
  } catch (error) {
    console.error('Failed to load options:', error)
    toast.show('Failed to load form options', 'error')
  } finally {
    loadingOptions.value = false
  }
}

async function handleSubmit() {
  if (!validate()) return

  submitting.value = true
  try {
    const payload = {
      vendor_id: form.value.vendor_id,
      date: form.value.date,
      due_date: form.value.due_date,
      notes: form.value.notes,
      terms: form.value.terms,
      discount: form.value.discount,
      line_items: form.value.line_items.map(item => ({
        product_id: item.product_id || null,
        description: item.description,
        quantity: Number(item.quantity),
        unit_price: Number(item.unit_price),
        tax_rate: Number(item.tax_rate),
      })),
    }

    await createBill(payload)
    toast.show('Bill created successfully', 'success')
    router.push({ name: 'BillList' })
  } catch (error) {
    console.error('Failed to create bill:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to create bill'
    toast.show(message, 'error')
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  router.push({ name: 'BillList' })
}

onMounted(() => {
  loadOptions()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="New Bill"
      :breadcrumbs="[
        { text: 'Purchases', to: { name: 'BillList' } },
        { text: 'Bills', to: { name: 'BillList' } },
        { text: 'New' }
      ]"
    />

    <LoadingSpinner v-if="loadingOptions" text="Loading form options..." />

    <form v-else class="space-y-6" @submit.prevent="handleSubmit">
      <!-- Vendor & Dates Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Bill Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SelectInput
            v-model="form.vendor_id"
            label="Vendor"
            name="vendor"
            :options="vendorOptions"
            placeholder="Select a vendor"
            :required="true"
            :error="errors.vendor_id"
          />

          <DateInput
            v-model="form.date"
            label="Bill Date"
            name="date"
            :required="true"
            :error="errors.date"
          />

          <DateInput
            v-model="form.due_date"
            label="Due Date"
            name="due_date"
            :required="true"
            :error="errors.due_date"
          />

          <TextInput
            v-model="form.discount"
            label="Discount"
            name="discount"
            type="number"
            placeholder="0.00"
            help-text="Enter discount amount"
          />
        </div>
      </div>

      <!-- Line Items Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Line Items</h2>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-violet-700 bg-violet-50 dark:bg-violet-900/20 dark:text-violet-400 rounded-lg hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors"
            @click="addLineItem"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Add Item
          </button>
        </div>

        <p v-if="errors.line_items" class="mb-4 text-sm text-red-600 dark:text-red-400">{{ errors.line_items }}</p>

        <!-- Line Items Table -->
        <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-8">#</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Product / Service</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Description</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-24">Qty</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-32">Unit Price</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-28">Tax %</th>
                <th class="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-32">Line Total</th>
                <th class="px-3 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(item, index) in form.line_items"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <td class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">{{ index + 1 }}</td>

                <td class="px-3 py-2">
                  <select
                    v-model="item.product_id"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                    @change="onProductSelect(index, item.product_id)"
                  >
                    <option value="">Select product</option>
                    <option v-for="product in productOptions" :key="product.value" :value="product.value">
                      {{ product.label }}
                    </option>
                  </select>
                </td>

                <td class="px-3 py-2">
                  <input
                    v-model="item.description"
                    type="text"
                    placeholder="Description"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                  />
                </td>

                <td class="px-3 py-2">
                  <input
                    v-model="item.quantity"
                    type="number"
                    min="0"
                    step="1"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                  />
                </td>

                <td class="px-3 py-2">
                  <input
                    v-model="item.unit_price"
                    type="number"
                    min="0"
                    step="0.01"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                  />
                </td>

                <td class="px-3 py-2">
                  <input
                    v-model="item.tax_rate"
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
                  />
                </td>

                <td class="px-3 py-2 text-right">
                  <span class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(lineTotal(item), auth.branchCurrency) }}
                  </span>
                </td>

                <td class="px-3 py-2 text-center">
                  <button
                    type="button"
                    :disabled="form.line_items.length <= 1"
                    :class="[
                      'p-1 rounded-md transition-colors',
                      form.line_items.length <= 1
                        ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                        : 'text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
                    ]"
                    title="Remove item"
                    @click="removeLineItem(index)"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Totals Section -->
      <div class="flex flex-col lg:flex-row gap-6">
        <!-- Notes & Terms -->
        <div class="flex-1 space-y-4">
          <TextareaInput
            v-model="form.notes"
            label="Notes"
            name="notes"
            placeholder="Add any notes for the bill..."
            :rows="3"
          />
          <TextareaInput
            v-model="form.terms"
            label="Terms & Conditions"
            name="terms"
            placeholder="Enter terms and conditions..."
            :rows="3"
          />
        </div>

        <!-- Summary Card -->
        <div class="w-full lg:w-80">
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-3">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Summary</h3>

            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">Subtotal</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(subtotal, auth.branchCurrency) }}</span>
            </div>

            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">Tax</span>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ formatCurrency(taxTotal, auth.branchCurrency) }}</span>
            </div>

            <div v-if="discount > 0" class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">Discount</span>
              <span class="text-sm font-medium text-red-600 dark:text-red-400">-{{ formatCurrency(discount, auth.branchCurrency) }}</span>
            </div>

            <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
              <div class="flex items-center justify-between">
                <span class="text-base font-semibold text-gray-900 dark:text-white">Grand Total</span>
                <span class="text-lg font-bold text-violet-600 dark:text-violet-400">{{ formatCurrency(grandTotal, auth.branchCurrency) }}</span>
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
          {{ submitting ? 'Creating...' : 'Create Bill' }}
        </button>
      </div>
    </form>
  </div>
</template>
