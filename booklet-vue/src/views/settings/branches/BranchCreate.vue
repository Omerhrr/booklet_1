<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const loading = ref(false)
const saving = ref(false)
const errors = reactive({
  name: '',
})

const form = reactive({
  name: '',
  address: '',
  city: '',
  state: '',
  country: '',
  currency: 'NGN',
  phone: '',
  email: '',
  is_default: false,
})

const breadcrumbs = [
  { text: 'Settings', to: '/settings' },
  { text: 'New Branch' },
]

const currencyOptions = [
  { value: 'NGN', label: 'NGN - Nigerian Naira' },
  { value: 'USD', label: 'USD - US Dollar' },
  { value: 'EUR', label: 'EUR - Euro' },
  { value: 'GBP', label: 'GBP - British Pound' },
  { value: 'KES', label: 'KES - Kenyan Shilling' },
  { value: 'GHS', label: 'GHS - Ghanaian Cedi' },
  { value: 'ZAR', label: 'ZAR - South African Rand' },
  { value: 'TZS', label: 'TZS - Tanzanian Shilling' },
  { value: 'UGX', label: 'UGX - Ugandan Shilling' },
  { value: 'RWF', label: 'RWF - Rwandan Franc' },
  { value: 'XOF', label: 'XOF - West African CFA Franc' },
  { value: 'XAF', label: 'XAF - Central African CFA Franc' },
  { value: 'EGP', label: 'EGP - Egyptian Pound' },
  { value: 'MAD', label: 'MAD - Moroccan Dirham' },
  { value: 'JPY', label: 'JPY - Japanese Yen' },
  { value: 'CNY', label: 'CNY - Chinese Yuan' },
  { value: 'INR', label: 'INR - Indian Rupee' },
  { value: 'CAD', label: 'CAD - Canadian Dollar' },
  { value: 'AUD', label: 'AUD - Australian Dollar' },
  { value: 'CHF', label: 'CHF - Swiss Franc' },
]

const atBranchLimit = computed(() => {
  return !authStore.canCreateBranch()
})

function validate() {
  let valid = true
  errors.name = ''

  if (!form.name.trim()) {
    errors.name = 'Branch name is required'
    valid = false
  }

  return valid
}

async function handleSubmit() {
  if (!validate()) return
  if (atBranchLimit.value) {
    toastStore.show('You have reached the branch limit for your plan. Please upgrade to create more branches.', 'error')
    return
  }

  saving.value = true
  try {
    await settingsApi.createBranch(form)
    toastStore.show('Branch created successfully')
    router.push({ name: 'SettingsIndex' })
  } catch (error) {
    console.error('Failed to create branch:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to create branch'
    toastStore.show(message, 'error')
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'SettingsIndex' })
}

onMounted(async () => {
  loading.value = true
  try {
    await authStore.fetchPlanLimits()
    await authStore.fetchBranches()
  } catch (error) {
    console.error('Failed to load plan info:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <PageHeader title="Create Branch" :breadcrumbs="breadcrumbs" />

    <!-- Plan Limit Warning -->
    <div v-if="atBranchLimit && !loading" class="mb-6 p-4 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-amber-800 dark:text-amber-300">Branch Limit Reached</h3>
          <p class="mt-1 text-sm text-amber-700 dark:text-amber-400">
            You have reached the maximum number of branches allowed by your current plan. Please upgrade your subscription to create additional branches.
          </p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading..." />
    </div>

    <div v-else class="max-w-3xl mx-auto">
      <form
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
        @submit.prevent="handleSubmit"
      >
        <!-- Branch Name -->
        <TextInput
          v-model="form.name"
          label="Branch Name"
          name="name"
          placeholder="Enter branch name"
          required
          :error="errors.name"
          :disabled="atBranchLimit"
        />

        <!-- Address -->
        <TextInput
          v-model="form.address"
          label="Address"
          name="address"
          placeholder="Enter street address"
          :disabled="atBranchLimit"
        />

        <!-- City, State, Country -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <TextInput
            v-model="form.city"
            label="City"
            name="city"
            placeholder="Enter city"
            :disabled="atBranchLimit"
          />
          <TextInput
            v-model="form.state"
            label="State / Province"
            name="state"
            placeholder="Enter state"
            :disabled="atBranchLimit"
          />
          <TextInput
            v-model="form.country"
            label="Country"
            name="country"
            placeholder="Enter country"
            :disabled="atBranchLimit"
          />
        </div>

        <!-- Currency -->
        <SelectInput
          v-model="form.currency"
          label="Currency"
          name="currency"
          :options="currencyOptions"
          placeholder="Select currency"
          :disabled="atBranchLimit"
        />

        <!-- Phone & Email -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.phone"
            label="Phone"
            name="phone"
            type="tel"
            placeholder="Enter phone number"
            :disabled="atBranchLimit"
          />
          <TextInput
            v-model="form.email"
            label="Email"
            name="email"
            type="email"
            placeholder="Enter email address"
            :disabled="atBranchLimit"
          />
        </div>

        <!-- Is Default -->
        <label class="flex items-center gap-3 cursor-pointer">
          <input
            v-model="form.is_default"
            type="checkbox"
            :disabled="atBranchLimit"
            class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
          />
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Set as default branch
          </span>
        </label>

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
            :disabled="saving || atBranchLimit"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <LoadingSpinner v-if="saving" size="sm" />
            {{ saving ? 'Creating...' : 'Create Branch' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
