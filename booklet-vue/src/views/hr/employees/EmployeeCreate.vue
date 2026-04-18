<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { useToastStore } from '@/stores/toast'
import * as hrApi from '@/api/hr'

const router = useRouter()
const toastStore = useToastStore()

const loading = ref(false)
const errors = reactive({
  first_name: '',
  last_name: '',
  email: '',
  hire_date: '',
  salary: '',
})

const form = reactive({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  department: '',
  position: '',
  hire_date: '',
  salary: '',
  bank_name: '',
  bank_account_number: '',
  tax_id: '',
  address: '',
  emergency_contact: '',
  emergency_phone: '',
  notes: '',
})

const departmentOptions = [
  { value: 'engineering', label: 'Engineering' },
  { value: 'marketing', label: 'Marketing' },
  { value: 'sales', label: 'Sales' },
  { value: 'finance', label: 'Finance' },
  { value: 'hr', label: 'Human Resources' },
  { value: 'operations', label: 'Operations' },
  { value: 'administration', label: 'Administration' },
  { value: 'customer_service', label: 'Customer Service' },
  { value: 'other', label: 'Other' },
]

const breadcrumbs = [
  { text: 'HR', to: '/hr' },
  { text: 'Employees', to: '/hr/employees' },
  { text: 'New Employee' },
]

function validate() {
  let valid = true
  errors.first_name = ''
  errors.last_name = ''
  errors.email = ''
  errors.hire_date = ''
  errors.salary = ''

  if (!form.first_name.trim()) {
    errors.first_name = 'First name is required'
    valid = false
  }
  if (!form.last_name.trim()) {
    errors.last_name = 'Last name is required'
    valid = false
  }
  if (!form.email.trim()) {
    errors.email = 'Email is required'
    valid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Please enter a valid email address'
    valid = false
  }
  if (!form.hire_date) {
    errors.hire_date = 'Hire date is required'
    valid = false
  }
  if (!form.salary || Number(form.salary) <= 0) {
    errors.salary = 'Monthly salary must be greater than 0'
    valid = false
  }

  return valid
}

async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    await hrApi.createEmployee({
      ...form,
      salary: Number(form.salary),
    })
    toastStore.show('Employee created successfully')
    router.push({ name: 'EmployeeList' })
  } catch (error) {
    console.error('Failed to create employee:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to create employee'
    toastStore.show(message, 'error')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push({ name: 'EmployeeList' })
}
</script>

<template>
  <div>
    <PageHeader title="New Employee" :breadcrumbs="breadcrumbs" />

    <div class="max-w-3xl mx-auto">
      <form
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
        @submit.prevent="handleSubmit"
      >
        <!-- Personal Information -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Personal Information</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TextInput
              v-model="form.first_name"
              label="First Name"
              name="first_name"
              placeholder="Enter first name"
              required
              :error="errors.first_name"
            />
            <TextInput
              v-model="form.last_name"
              label="Last Name"
              name="last_name"
              placeholder="Enter last name"
              required
              :error="errors.last_name"
            />
          </div>
        </div>

        <!-- Contact Information -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Contact Information</h3>
          <div class="space-y-6">
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
            <TextInput
              v-model="form.address"
              label="Address"
              name="address"
              placeholder="Enter street address"
            />
          </div>
        </div>

        <!-- Employment Information -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Employment Information</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <SelectInput
              v-model="form.department"
              label="Department"
              name="department"
              :options="departmentOptions"
              placeholder="Select department"
            />
            <TextInput
              v-model="form.position"
              label="Position"
              name="position"
              placeholder="Enter job title"
            />
            <DateInput
              v-model="form.hire_date"
              label="Hire Date"
              name="hire_date"
              required
              :error="errors.hire_date"
            />
            <TextInput
              v-model="form.salary"
              label="Monthly Salary"
              name="salary"
              type="number"
              placeholder="0.00"
              required
              :error="errors.salary"
              help-text="Enter monthly salary amount"
            />
          </div>
        </div>

        <!-- Bank Information -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Bank Information</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TextInput
              v-model="form.bank_name"
              label="Bank Name"
              name="bank_name"
              placeholder="Enter bank name"
            />
            <TextInput
              v-model="form.bank_account_number"
              label="Bank Account Number"
              name="bank_account_number"
              placeholder="Enter account number"
            />
            <TextInput
              v-model="form.tax_id"
              label="Tax ID"
              name="tax_id"
              placeholder="Enter tax identification number"
            />
          </div>
        </div>

        <!-- Emergency Contact -->
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Emergency Contact</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TextInput
              v-model="form.emergency_contact"
              label="Emergency Contact Name"
              name="emergency_contact"
              placeholder="Enter contact name"
            />
            <TextInput
              v-model="form.emergency_phone"
              label="Emergency Contact Phone"
              name="emergency_phone"
              type="tel"
              placeholder="Enter contact phone"
            />
          </div>
        </div>

        <!-- Notes -->
        <TextareaInput
          v-model="form.notes"
          label="Notes"
          name="notes"
          placeholder="Additional notes about this employee..."
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
            {{ loading ? 'Creating...' : 'Create Employee' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
