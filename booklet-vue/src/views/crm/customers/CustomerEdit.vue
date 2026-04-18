<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { useToastStore } from '@/stores/toast'
import * as crmApi from '@/api/crm'

const router = useRouter()
const route = useRoute()
const toastStore = useToastStore()

const loading = ref(false)
const fetchLoading = ref(true)
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
  notes: '',
})

const breadcrumbs = computed(() => [
  { text: 'CRM', to: '/crm' },
  { text: 'Customers', to: '/crm/customers' },
  { text: form.name || 'Customer', to: { name: 'CustomerDetail', params: { id: route.params.id } } },
  { text: 'Edit' },
])

async function fetchCustomer() {
  fetchLoading.value = true
  try {
    const { data } = await crmApi.getCustomer(route.params.id)
    form.name = data.name || ''
    form.email = data.email || ''
    form.phone = data.phone || ''
    form.address = data.address || ''
    form.city = data.city || ''
    form.state = data.state || ''
    form.country = data.country || ''
    form.tax_id = data.tax_id || ''
    form.notes = data.notes || ''
  } catch (error) {
    console.error('Failed to fetch customer:', error)
    toastStore.show('Failed to load customer', 'error')
  } finally {
    fetchLoading.value = false
  }
}

function validate() {
  let valid = true
  errors.name = ''
  errors.email = ''

  if (!form.name.trim()) {
    errors.name = 'Name is required'
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

async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    await crmApi.updateCustomer(route.params.id, form)
    toastStore.show('Customer updated successfully')
    router.push({ name: 'CustomerDetail', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update customer:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to update customer'
    toastStore.show(message, 'error')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push({ name: 'CustomerDetail', params: { id: route.params.id } })
}

onMounted(fetchCustomer)
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="fetchLoading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading customer..." />
    </div>

    <template v-else>
      <PageHeader title="Edit Customer" :breadcrumbs="breadcrumbs" />

      <div class="max-w-3xl mx-auto">
        <form
          class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
          @submit.prevent="handleSubmit"
        >
          <!-- Name -->
          <TextInput
            v-model="form.name"
            label="Name"
            name="name"
            placeholder="Enter customer name"
            required
            :error="errors.name"
          />

          <!-- Email -->
          <TextInput
            v-model="form.email"
            label="Email"
            name="email"
            type="email"
            placeholder="Enter email address"
            required
            :error="errors.email"
          />

          <!-- Phone -->
          <TextInput
            v-model="form.phone"
            label="Phone"
            name="phone"
            type="tel"
            placeholder="Enter phone number"
          />

          <!-- Address -->
          <TextInput
            v-model="form.address"
            label="Address"
            name="address"
            placeholder="Enter street address"
          />

          <!-- City & State -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
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
          </div>

          <!-- Country -->
          <TextInput
            v-model="form.country"
            label="Country"
            name="country"
            placeholder="Enter country"
          />

          <!-- Tax ID -->
          <TextInput
            v-model="form.tax_id"
            label="Tax ID"
            name="tax_id"
            placeholder="Enter tax identification number"
          />

          <!-- Notes -->
          <TextareaInput
            v-model="form.notes"
            label="Notes"
            name="notes"
            placeholder="Additional notes about this customer..."
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
              {{ loading ? 'Saving...' : 'Update Customer' }}
            </button>
          </div>
        </form>
      </div>
    </template>
  </div>
</template>
