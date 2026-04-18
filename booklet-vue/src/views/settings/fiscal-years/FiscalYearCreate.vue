<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextInput from '@/components/forms/TextInput.vue'
import { useToastStore } from '@/stores/toast'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const toastStore = useToastStore()

const saving = ref(false)
const errors = reactive({
  name: '',
  start_date: '',
  end_date: '',
  overlap: '',
})

const form = reactive({
  name: '',
  start_date: '',
  end_date: '',
  is_current: false,
})

const breadcrumbs = [
  { text: 'Settings', to: '/settings' },
  { text: 'New Fiscal Year' },
]

function validate() {
  let valid = true
  errors.name = ''
  errors.start_date = ''
  errors.end_date = ''
  errors.overlap = ''

  if (!form.name.trim()) {
    errors.name = 'Fiscal year name is required'
    valid = false
  }

  if (!form.start_date) {
    errors.start_date = 'Start date is required'
    valid = false
  }

  if (!form.end_date) {
    errors.end_date = 'End date is required'
    valid = false
  }

  if (form.start_date && form.end_date) {
    const start = new Date(form.start_date)
    const end = new Date(form.end_date)
    if (end <= start) {
      errors.end_date = 'End date must be after start date'
      valid = false
    }
  }

  return valid
}

async function handleSubmit() {
  if (!validate()) return

  saving.value = true
  try {
    await settingsApi.createFiscalYear?.(form) ?? await fetch('/api/settings/fiscal-years', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    }).then((r) => {
      if (!r.ok) {
        return r.json().then((err) => { throw new Error(err.detail || err.message || 'Failed to create fiscal year') })
      }
      return r.json()
    })

    // If is_current is set, ensure it's handled server-side
    toastStore.show('Fiscal year created successfully')
    router.push({ name: 'SettingsIndex' })
  } catch (error) {
    console.error('Failed to create fiscal year:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'Failed to create fiscal year'
    if (message.toLowerCase().includes('overlap')) {
      errors.overlap = message
    } else {
      toastStore.show(message, 'error')
    }
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'SettingsIndex' })
}
</script>

<template>
  <div>
    <PageHeader title="Create Fiscal Year" :breadcrumbs="breadcrumbs" />

    <div class="max-w-3xl mx-auto">
      <form
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
        @submit.prevent="handleSubmit"
      >
        <!-- Name -->
        <TextInput
          v-model="form.name"
          label="Fiscal Year Name"
          name="name"
          placeholder="e.g. FY 2024/2025"
          required
          :error="errors.name"
        />

        <!-- Start Date & End Date -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <DateInput
            v-model="form.start_date"
            label="Start Date"
            name="start_date"
            required
            :error="errors.start_date"
          />
          <DateInput
            v-model="form.end_date"
            label="End Date"
            name="end_date"
            required
            :error="errors.end_date"
            :min="form.start_date"
          />
        </div>

        <!-- Overlap Error -->
        <div v-if="errors.overlap" class="p-4 rounded-lg border border-red-300 bg-red-50 dark:bg-red-900/20 dark:border-red-700">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="w-5 h-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            <div class="ml-3">
              <p class="text-sm text-red-700 dark:text-red-400">
                {{ errors.overlap }}
              </p>
            </div>
          </div>
        </div>

        <!-- Is Current -->
        <label class="flex items-center gap-3 cursor-pointer">
          <input
            v-model="form.is_current"
            type="checkbox"
            class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
          />
          <div>
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
              Set as current fiscal year
            </span>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              This will replace the currently active fiscal year
            </p>
          </div>
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
            :disabled="saving"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <LoadingSpinner v-if="saving" size="sm" />
            {{ saving ? 'Creating...' : 'Create Fiscal Year' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
