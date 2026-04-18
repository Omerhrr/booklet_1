<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import FileUpload from '@/components/common/FileUpload.vue'
import { useToastStore } from '@/stores/toast'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const toastStore = useToastStore()

const loading = ref(false)
const saving = ref(false)
const logoFile = ref(null)
const errors = reactive({
  name: '',
  email: '',
})

const form = reactive({
  name: '',
  email: '',
  phone: '',
  address: '',
  city: '',
  state: '',
  country: '',
  tax_id: '',
  website: '',
})

const breadcrumbs = [
  { text: 'Settings', to: '/settings' },
  { text: 'Business Settings' },
]

function validate() {
  let valid = true
  errors.name = ''
  errors.email = ''

  if (!form.name.trim()) {
    errors.name = 'Business name is required'
    valid = false
  }
  if (!form.email.trim()) {
    errors.email = 'Email is required'
    valid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Please enter a valid email address'
    valid = false
  }

  return valid
}

async function fetchBusiness() {
  loading.value = true
  try {
    const { data } = await settingsApi.getBusiness()
    Object.keys(form).forEach((key) => {
      if (data[key] !== undefined) {
        form[key] = data[key]
      }
    })
  } catch (error) {
    console.error('Failed to fetch business settings:', error)
    toastStore.show('Failed to load business settings', 'error')
  } finally {
    loading.value = false
  }
}

function handleLogoSelected(file) {
  logoFile.value = file
}

function handleUploadError(message) {
  toastStore.show(message, 'error')
}

async function handleSubmit() {
  if (!validate()) return

  saving.value = true
  try {
    const payload = { ...form }
    if (logoFile.value) {
      const formData = new FormData()
      Object.keys(payload).forEach((key) => {
        formData.append(key, payload[key])
      })
      formData.append('logo', logoFile.value)
      await settingsApi.updateBusiness(formData)
    } else {
      await settingsApi.updateBusiness(payload)
    }
    toastStore.show('Business settings updated successfully')
    router.push({ name: 'SettingsIndex' })
  } catch (error) {
    console.error('Failed to update business settings:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to update business settings'
    toastStore.show(message, 'error')
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'SettingsIndex' })
}

onMounted(fetchBusiness)
</script>

<template>
  <div>
    <PageHeader title="Business Settings" :breadcrumbs="breadcrumbs" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading business settings..." />
    </div>

    <div v-else class="max-w-3xl mx-auto">
      <form
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
        @submit.prevent="handleSubmit"
      >
        <!-- Business Name -->
        <TextInput
          v-model="form.name"
          label="Business Name"
          name="name"
          placeholder="Enter business name"
          required
          :error="errors.name"
        />

        <!-- Email & Phone -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.email"
            label="Email"
            name="email"
            type="email"
            placeholder="Enter email address"
            required
            :error="errors.email"
          />
          <TextInput
            v-model="form.phone"
            label="Phone"
            name="phone"
            type="tel"
            placeholder="Enter phone number"
          />
        </div>

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

        <!-- Tax ID & Website -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.tax_id"
            label="Tax ID"
            name="tax_id"
            placeholder="Enter tax identification number"
          />
          <TextInput
            v-model="form.website"
            label="Website"
            name="website"
            type="url"
            placeholder="https://example.com"
          />
        </div>

        <!-- Logo Upload -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Business Logo
          </label>
          <FileUpload
            accept="image/*"
            :max-size="5"
            label="Upload Logo"
            help-text="PNG, JPG or SVG. Max 5MB."
            @file-selected="handleLogoSelected"
            @error="handleUploadError"
          />
        </div>

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
            :disabled="saving"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <LoadingSpinner v-if="saving" size="sm" />
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
