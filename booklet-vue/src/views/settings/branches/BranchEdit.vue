<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useToastStore } from '@/stores/toast'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const route = useRoute()
const toastStore = useToastStore()

const loading = ref(false)
const saving = ref(false)
const settingDefault = ref(false)
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
  { text: 'Edit Branch' },
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

function validate() {
  let valid = true
  errors.name = ''

  if (!form.name.trim()) {
    errors.name = 'Branch name is required'
    valid = false
  }

  return valid
}

async function fetchBranch() {
  loading.value = true
  try {
    const { data } = await settingsApi.getBranch(route.params.id)
    Object.keys(form).forEach((key) => {
      if (data[key] !== undefined) {
        form[key] = data[key]
      }
    })
  } catch (error) {
    console.error('Failed to fetch branch:', error)
    toastStore.show('Failed to load branch', 'error')
    router.push({ name: 'SettingsIndex' })
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!validate()) return

  saving.value = true
  try {
    await settingsApi.updateBranch(route.params.id, form)
    toastStore.show('Branch updated successfully')
    router.push({ name: 'SettingsIndex' })
  } catch (error) {
    console.error('Failed to update branch:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to update branch'
    toastStore.show(message, 'error')
  } finally {
    saving.value = false
  }
}

async function handleSetDefault() {
  settingDefault.value = true
  try {
    await settingsApi.setDefaultBranch(route.params.id)
    form.is_default = true
    toastStore.show('Branch set as default successfully')
  } catch (error) {
    console.error('Failed to set default branch:', error)
    toastStore.show('Failed to set branch as default', 'error')
  } finally {
    settingDefault.value = false
  }
}

function handleCancel() {
  router.push({ name: 'SettingsIndex' })
}

onMounted(fetchBranch)
</script>

<template>
  <div>
    <PageHeader title="Edit Branch" :breadcrumbs="breadcrumbs" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading branch..." />
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
        />

        <!-- Address -->
        <TextInput
          v-model="form.address"
          label="Address"
          name="address"
          placeholder="Enter street address"
        />

        <!-- City, State, Country -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <TextInput
            v-model="form.city"
            label="City"
            name="city"
            placeholder="Enter city"
          />
          <TextInput
            v-model="form.state"
            label="State / Province"
            name="state"
            placeholder="Enter state"
          />
          <TextInput
            v-model="form.country"
            label="Country"
            name="country"
            placeholder="Enter country"
          />
        </div>

        <!-- Currency -->
        <SelectInput
          v-model="form.currency"
          label="Currency"
          name="currency"
          :options="currencyOptions"
          placeholder="Select currency"
        />

        <!-- Phone & Email -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.phone"
            label="Phone"
            name="phone"
            type="tel"
            placeholder="Enter phone number"
          />
          <TextInput
            v-model="form.email"
            label="Email"
            name="email"
            type="email"
            placeholder="Enter email address"
          />
        </div>

        <!-- Is Default -->
        <label class="flex items-center gap-3 cursor-pointer">
          <input
            v-model="form.is_default"
            type="checkbox"
            class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
          />
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            Set as default branch
          </span>
        </label>

        <!-- Actions -->
        <div class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <!-- Set as Default (left side) -->
          <button
            v-if="!form.is_default"
            type="button"
            :disabled="settingDefault"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-300 rounded-lg hover:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700 dark:hover:bg-amber-900/50 disabled:opacity-50 transition-colors"
            @click="handleSetDefault"
          >
            <LoadingSpinner v-if="settingDefault" size="sm" />
            {{ settingDefault ? 'Setting...' : 'Set as Default' }}
          </button>
          <div v-else />

          <!-- Cancel & Save (right side) -->
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="handleCancel"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <LoadingSpinner v-if="saving" size="sm" />
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>
