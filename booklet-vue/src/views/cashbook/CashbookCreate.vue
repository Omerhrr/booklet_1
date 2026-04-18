<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { createCashbookEntry, fundAccount } from '@/api/cashbook'
import { getPaymentAccounts, listBankAccounts } from '@/api/banking'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const submitting = ref(false)
const loadingOptions = ref(true)
const errors = ref({})

// Form type: 'manual' or 'fund'
const formType = ref('manual')

// Manual entry form
const manualForm = ref({
  date: new Date().toISOString().split('T')[0],
  account_id: '',
  entry_type: 'debit',
  amount: '',
  description: '',
  reference: '',
})

// Fund account form
const fundForm = ref({
  account_id: '',
  amount: '',
  description: '',
  reference: '',
})

// Dropdown options
const accountOptions = ref([])

const entryTypeOptions = [
  { value: 'debit', label: 'Debit' },
  { value: 'credit', label: 'Credit' },
]

const formTypeTabs = [
  { key: 'manual', label: 'Manual Entry' },
  { key: 'fund', label: 'Fund Account' },
]

async function loadAccountOptions() {
  loadingOptions.value = true
  try {
    const [bankRes, paymentRes] = await Promise.all([
      listBankAccounts().catch(() => ({ data: [] })),
      getPaymentAccounts().catch(() => ({ data: [] })),
    ])

    const banks = Array.isArray(bankRes.data) ? bankRes.data : bankRes.data.items || bankRes.data.accounts || []
    const payments = Array.isArray(paymentRes.data) ? paymentRes.data : paymentRes.data.items || paymentRes.data.accounts || []

    const allAccounts = [...banks, ...payments].filter(
      (a, i, arr) => arr.findIndex((b) => String(b.id) === String(a.id)) === i
    )

    accountOptions.value = allAccounts.map((a) => ({
      value: String(a.id),
      label: a.name || a.account_name || a.account_number || `Account ${a.id}`,
    }))
  } catch (error) {
    console.error('Failed to load account options:', error)
    toast.show('Failed to load form options', 'error')
  } finally {
    loadingOptions.value = false
  }
}

function validateManual() {
  const newErrors = {}

  if (!manualForm.value.date) {
    newErrors.date = 'Date is required'
  }

  if (!manualForm.value.account_id) {
    newErrors.account_id = 'Account is required'
  }

  if (!manualForm.value.amount || Number(manualForm.value.amount) <= 0) {
    newErrors.amount = 'Amount is required and must be greater than 0'
  }

  if (!manualForm.value.description?.trim()) {
    newErrors.description = 'Description is required'
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

function validateFund() {
  const newErrors = {}

  if (!fundForm.value.account_id) {
    newErrors.account_id = 'Account is required'
  }

  if (!fundForm.value.amount || Number(fundForm.value.amount) <= 0) {
    newErrors.amount = 'Amount is required and must be greater than 0'
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleSubmit() {
  errors.value = {}

  if (formType.value === 'manual') {
    if (!validateManual()) return

    submitting.value = true
    try {
      await createCashbookEntry({
        date: manualForm.value.date,
        account_id: manualForm.value.account_id,
        entry_type: manualForm.value.entry_type,
        amount: Number(manualForm.value.amount),
        description: manualForm.value.description,
        reference: manualForm.value.reference,
      })
      toast.show('Cash book entry created successfully', 'success')
      router.push({ name: 'CashbookList' })
    } catch (error) {
      console.error('Failed to create entry:', error)
      const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to create entry'
      toast.show(message, 'error')
    } finally {
      submitting.value = false
    }
  } else {
    if (!validateFund()) return

    submitting.value = true
    try {
      await fundAccount({
        account_id: fundForm.value.account_id,
        amount: Number(fundForm.value.amount),
        description: fundForm.value.description,
        reference: fundForm.value.reference,
      })
      toast.show('Account funded successfully', 'success')
      router.push({ name: 'CashbookList' })
    } catch (error) {
      console.error('Failed to fund account:', error)
      const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to fund account'
      toast.show(message, 'error')
    } finally {
      submitting.value = false
    }
  }
}

function handleCancel() {
  router.push({ name: 'CashbookList' })
}

function switchFormType(type) {
  formType.value = type
  errors.value = {}
}

onMounted(() => {
  loadAccountOptions()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="New Cash Book Entry"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Cash Book', to: { name: 'CashbookList' } },
        { text: 'New' }
      ]"
    />

    <LoadingSpinner v-if="loadingOptions" text="Loading form options..." />

    <form v-else class="space-y-6" @submit.prevent="handleSubmit">
      <!-- Form Type Selector -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Entry Type</h2>
        <div class="flex border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <button
            v-for="tab in formTypeTabs"
            :key="tab.key"
            type="button"
            :class="[
              'flex-1 px-4 py-3 text-sm font-medium transition-colors',
              formType === tab.key
                ? 'bg-emerald-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
            ]"
            @click="switchFormType(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- Manual Entry Form -->
      <div v-if="formType === 'manual'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Manual Entry Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DateInput
            v-model="manualForm.date"
            label="Date"
            name="date"
            :required="true"
            :error="errors.date"
          />

          <SelectInput
            v-model="manualForm.account_id"
            label="Account"
            name="account"
            :options="accountOptions"
            placeholder="Select account"
            :required="true"
            :error="errors.account_id"
          />

          <SelectInput
            v-model="manualForm.entry_type"
            label="Entry Type"
            name="entry_type"
            :options="entryTypeOptions"
            :required="true"
          />

          <TextInput
            v-model="manualForm.amount"
            label="Amount"
            name="amount"
            type="number"
            placeholder="0.00"
            :required="true"
            :error="errors.amount"
            icon="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />

          <TextInput
            v-model="manualForm.reference"
            label="Reference"
            name="reference"
            placeholder="e.g., REC-001"
          />
        </div>

        <div class="mt-4">
          <TextareaInput
            v-model="manualForm.description"
            label="Description"
            name="description"
            placeholder="Enter a description for this entry"
            :rows="3"
            :required="true"
            :error="errors.description"
          />
        </div>
      </div>

      <!-- Fund Account Form -->
      <div v-if="formType === 'fund'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Fund Account Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SelectInput
            v-model="fundForm.account_id"
            label="Account"
            name="fund_account"
            :options="accountOptions"
            placeholder="Select account to fund"
            :required="true"
            :error="errors.account_id"
          />

          <TextInput
            v-model="fundForm.amount"
            label="Amount"
            name="fund_amount"
            type="number"
            placeholder="0.00"
            :required="true"
            :error="errors.amount"
            icon="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />

          <TextInput
            v-model="fundForm.reference"
            label="Reference"
            name="fund_reference"
            placeholder="e.g., FND-001"
          />
        </div>

        <div class="mt-4">
          <TextareaInput
            v-model="fundForm.description"
            label="Description"
            name="fund_description"
            placeholder="Enter a description for this funding"
            :rows="3"
          />
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
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          {{ submitting ? 'Saving...' : formType === 'manual' ? 'Create Entry' : 'Fund Account' }}
        </button>
      </div>
    </form>
  </div>
</template>
