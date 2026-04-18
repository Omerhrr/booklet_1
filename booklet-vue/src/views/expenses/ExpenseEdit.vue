<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { getExpense, updateExpense, getExpenseCategories } from '@/api/expenses'
import { getPaymentAccounts } from '@/api/banking'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(false)
const fetchLoading = ref(true)
const errors = ref({})

const form = ref({
  date: '',
  reference: '',
  category: '',
  amount: '',
  description: '',
  payment_method: '',
  bank_account_id: '',
  notes: '',
})

const categoryOptions = ref([])
const bankAccountOptions = ref([])
const paymentMethodOptions = [
  { value: 'cash', label: 'Cash' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'card', label: 'Card' },
  { value: 'cheque', label: 'Cheque' },
]

async function fetchExpense() {
  fetchLoading.value = true
  try {
    const [expenseRes, categoriesRes, accountsRes] = await Promise.all([
      getExpense(route.params.id),
      getExpenseCategories(),
      getPaymentAccounts(),
    ])

    const data = expenseRes.data
    form.value = {
      date: data.date || '',
      reference: data.reference || '',
      category: data.category || data.category_id || '',
      amount: data.amount || '',
      description: data.description || '',
      payment_method: data.payment_method || '',
      bank_account_id: data.bank_account_id || '',
      notes: data.notes || '',
    }

    const categories = Array.isArray(categoriesRes.data)
      ? categoriesRes.data
      : categoriesRes.data.categories || []
    categoryOptions.value = categories.map(c => ({
      value: typeof c === 'string' ? c : c.id || c.name,
      label: typeof c === 'string' ? c : c.name || c.label,
    }))

    const accounts = Array.isArray(accountsRes.data)
      ? accountsRes.data
      : accountsRes.data.accounts || []
    bankAccountOptions.value = accounts.map(a => ({
      value: a.id,
      label: a.name || a.account_name,
    }))
  } catch (error) {
    console.error('Failed to fetch expense:', error)
    toast.show('Failed to load expense', 'error')
    router.push({ name: 'ExpenseList' })
  } finally {
    fetchLoading.value = false
  }
}

function validate() {
  const newErrors = {}
  if (!form.value.date) newErrors.date = 'Date is required'
  if (!form.value.amount || Number(form.value.amount) <= 0) newErrors.amount = 'Valid amount is required'
  if (!form.value.description?.trim()) newErrors.description = 'Description is required'
  if (!form.value.category) newErrors.category = 'Category is required'
  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    const payload = {
      date: form.value.date,
      reference: form.value.reference,
      category: form.value.category,
      amount: Number(form.value.amount),
      description: form.value.description,
      payment_method: form.value.payment_method || null,
      bank_account_id: form.value.bank_account_id || null,
      notes: form.value.notes || null,
    }

    await updateExpense(route.params.id, payload)
    toast.show('Expense updated successfully', 'success')
    router.push({ name: 'ExpenseDetail', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update expense:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to update expense'
    toast.show(message, 'error')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push({ name: 'ExpenseDetail', params: { id: route.params.id } })
}

onMounted(() => {
  fetchExpense()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Edit Expense"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Expenses', to: { name: 'ExpenseList' } },
        { text: 'Edit' }
      ]"
    />

    <LoadingSpinner v-if="fetchLoading" text="Loading expense..." />

    <form v-else class="max-w-3xl mx-auto space-y-6" @submit.prevent="handleSubmit">
      <!-- Expense Details -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Expense Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DateInput
            v-model="form.date"
            label="Date"
            name="date"
            :required="true"
            :error="errors.date"
          />
          <TextInput
            v-model="form.reference"
            label="Reference #"
            name="reference"
            disabled
          />
          <SelectInput
            v-model="form.category"
            label="Category"
            name="category"
            :options="categoryOptions"
            placeholder="Select category"
            :required="true"
            :error="errors.category"
          />
          <TextInput
            v-model="form.amount"
            label="Amount"
            name="amount"
            type="number"
            placeholder="0.00"
            :required="true"
            :error="errors.amount"
          />
          <SelectInput
            v-model="form.payment_method"
            label="Payment Method"
            name="payment_method"
            :options="paymentMethodOptions"
            placeholder="Select payment method"
          />
          <SelectInput
            v-model="form.bank_account_id"
            label="Bank Account"
            name="bank_account_id"
            :options="bankAccountOptions"
            placeholder="Select bank account"
          />
        </div>

        <div class="mt-4">
          <TextInput
            v-model="form.description"
            label="Description"
            name="description"
            placeholder="Enter expense description"
            :required="true"
            :error="errors.description"
          />
        </div>
      </div>

      <!-- Notes -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <TextareaInput
          v-model="form.notes"
          label="Notes"
          name="notes"
          placeholder="Additional notes..."
          :rows="3"
        />
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-col-reverse sm:flex-row items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          class="w-full sm:w-auto px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          :disabled="loading"
          @click="handleCancel"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="loading"
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <LoadingSpinner v-if="loading" size="sm" />
          {{ loading ? 'Saving...' : 'Update Expense' }}
        </button>
      </div>
    </form>
  </div>
</template>
