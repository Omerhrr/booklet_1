<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { useToastStore } from '@/stores/toast'
import * as bankingApi from '@/api/banking'

const router = useRouter()
const toastStore = useToastStore()

const loading = ref(false)
const errors = reactive({
  account_name: '',
  bank_name: '',
  account_number: '',
})

const form = reactive({
  account_name: '',
  bank_name: '',
  account_number: '',
  account_type: '',
  currency: '',
  description: '',
  opening_balance: '',
})

const accountTypeOptions = [
  { value: 'checking', label: 'Checking' },
  { value: 'savings', label: 'Savings' },
]

const currencyOptions = [
  { value: 'NGN', label: 'Nigerian Naira (NGN)' },
  { value: 'USD', label: 'US Dollar (USD)' },
  { value: 'EUR', label: 'Euro (EUR)' },
  { value: 'GBP', label: 'British Pound (GBP)' },
  { value: 'GHS', label: 'Ghanaian Cedi (GHS)' },
  { value: 'KES', label: 'Kenyan Shilling (KES)' },
  { value: 'ZAR', label: 'South African Rand (ZAR)' },
  { value: 'TZS', label: 'Tanzanian Shilling (TZS)' },
  { value: 'UGX', label: 'Ugandan Shilling (UGX)' },
]

const breadcrumbs = [
  { text: 'Banking', to: '/banking' },
  { text: 'Accounts', to: '/banking/accounts' },
  { text: 'New Account' },
]

function validate() {
  let valid = true
  errors.account_name = ''
  errors.bank_name = ''
  errors.account_number = ''

  if (!form.account_name.trim()) {
    errors.account_name = 'Account name is required'
    valid = false
  }
  if (!form.bank_name.trim()) {
    errors.bank_name = 'Bank name is required'
    valid = false
  }
  if (!form.account_number.trim()) {
    errors.account_number = 'Account number is required'
    valid = false
  }

  return valid
}

async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    await bankingApi.createBankAccount({
      ...form,
      opening_balance: Number(form.opening_balance) || 0,
    })
    toastStore.show('Bank account created successfully')
    router.push({ name: 'BankAccountList' })
  } catch (error) {
    console.error('Failed to create bank account:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to create bank account'
    toastStore.show(message, 'error')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push({ name: 'BankAccountList' })
}
</script>

<template>
  <div>
    <PageHeader title="New Bank Account" :breadcrumbs="breadcrumbs" />

    <div class="max-w-2xl mx-auto">
      <form
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
        @submit.prevent="handleSubmit"
      >
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.account_name"
            label="Account Name"
            name="account_name"
            placeholder="e.g., Main Operating Account"
            required
            :error="errors.account_name"
          />
          <TextInput
            v-model="form.bank_name"
            label="Bank Name"
            name="bank_name"
            placeholder="e.g., First Bank"
            required
            :error="errors.bank_name"
          />
          <TextInput
            v-model="form.account_number"
            label="Account Number"
            name="account_number"
            placeholder="Enter account number"
            required
            :error="errors.account_number"
          />
          <SelectInput
            v-model="form.account_type"
            label="Account Type"
            name="account_type"
            :options="accountTypeOptions"
            placeholder="Select account type"
            required
          />
          <SelectInput
            v-model="form.currency"
            label="Currency"
            name="currency"
            :options="currencyOptions"
            placeholder="Select currency"
            required
          />
          <TextInput
            v-model="form.opening_balance"
            label="Opening Balance"
            name="opening_balance"
            type="number"
            placeholder="0.00"
            help-text="Current balance of the account"
          />
        </div>

        <TextareaInput
          v-model="form.description"
          label="Description"
          name="description"
          placeholder="Optional description for this account..."
          :rows="3"
        />

        <!-- Actions -->
        <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
            @click="handleCancel"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <LoadingSpinner v-if="loading" size="sm" />
            {{ loading ? 'Creating...' : 'Create Account' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
