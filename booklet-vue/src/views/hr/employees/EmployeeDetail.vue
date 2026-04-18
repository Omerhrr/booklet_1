<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import Modal from '@/components/common/Modal.vue'
import TextInput from '@/components/forms/TextInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'
import * as hrApi from '@/api/hr'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const employee = ref(null)
const payrollConfig = ref(null)
const employmentHistory = ref([])
const loading = ref(true)
const savingConfig = ref(false)
const activeTab = ref(route.query.tab || 'info')

const showTerminateDialog = ref(false)
const terminateForm = reactive({
  termination_date: '',
  reason: '',
})
const terminateErrors = reactive({
  termination_date: '',
  reason: '',
})
const terminating = ref(false)

// Payroll config form
const showPayrollModal = ref(false)
const payrollForm = reactive({
  basic_salary: '',
  housing_allowance: '',
  transport_allowance: '',
  medical_allowance: '',
  other_allowances: '',
  tax_rate: '',
  pension_rate: '',
  other_deductions: '',
})
const payrollErrors = reactive({
  basic_salary: '',
  tax_rate: '',
  pension_rate: '',
})

const statusVariantMap = {
  active: 'success',
  terminated: 'danger',
}

const breadcrumbs = computed(() => [
  { text: 'HR', to: '/hr' },
  { text: 'Employees', to: '/hr/employees' },
  { text: getFullName(employee.value) || 'Employee Details' },
])

function getFullName(emp) {
  if (!emp) return ''
  return `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || emp.name || '—'
}

function formatAmount(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

async function fetchEmployee() {
  loading.value = true
  try {
    const { data } = await hrApi.getEmployee(route.params.id)
    employee.value = data
    payrollConfig.value = data.payroll_config || null
    employmentHistory.value = data.employment_history || []

    // Pre-fill payroll form if config exists
    if (payrollConfig.value) {
      payrollForm.basic_salary = payrollConfig.value.basic_salary || ''
      payrollForm.housing_allowance = payrollConfig.value.housing_allowance || ''
      payrollForm.transport_allowance = payrollConfig.value.transport_allowance || ''
      payrollForm.medical_allowance = payrollConfig.value.medical_allowance || ''
      payrollForm.other_allowances = payrollConfig.value.other_allowances || ''
      payrollForm.tax_rate = payrollConfig.value.tax_rate || ''
      payrollForm.pension_rate = payrollConfig.value.pension_rate || ''
      payrollForm.other_deductions = payrollConfig.value.other_deductions || ''
    } else {
      payrollForm.basic_salary = data.salary || ''
    }

    // Set active tab from query
    if (route.query.tab) {
      activeTab.value = route.query.tab
    }
  } catch (error) {
    console.error('Failed to fetch employee:', error)
    toastStore.show('Failed to load employee', 'error')
  } finally {
    loading.value = false
  }
}

function editEmployee() {
  router.push({ name: 'EmployeeEdit', params: { id: route.params.id } })
}

function goBack() {
  router.push({ name: 'EmployeeList' })
}

function openPayrollModal() {
  showPayrollModal.value = true
}

function validatePayrollForm() {
  let valid = true
  payrollErrors.basic_salary = ''
  payrollErrors.tax_rate = ''
  payrollErrors.pension_rate = ''

  if (!payrollForm.basic_salary || Number(payrollForm.basic_salary) <= 0) {
    payrollErrors.basic_salary = 'Basic salary is required'
    valid = false
  }
  if (payrollForm.tax_rate !== '' && (Number(payrollForm.tax_rate) < 0 || Number(payrollForm.tax_rate) > 100)) {
    payrollErrors.tax_rate = 'Tax rate must be between 0 and 100'
    valid = false
  }
  if (payrollForm.pension_rate !== '' && (Number(payrollForm.pension_rate) < 0 || Number(payrollForm.pension_rate) > 100)) {
    payrollErrors.pension_rate = 'Pension rate must be between 0 and 100'
    valid = false
  }

  return valid
}

async function savePayrollConfig() {
  if (!validatePayrollForm()) return
  savingConfig.value = true
  try {
    const payload = {
      basic_salary: Number(payrollForm.basic_salary),
      housing_allowance: Number(payrollForm.housing_allowance) || 0,
      transport_allowance: Number(payrollForm.transport_allowance) || 0,
      medical_allowance: Number(payrollForm.medical_allowance) || 0,
      other_allowances: Number(payrollForm.other_allowances) || 0,
      tax_rate: Number(payrollForm.tax_rate) || 0,
      pension_rate: Number(payrollForm.pension_rate) || 0,
      other_deductions: Number(payrollForm.other_deductions) || 0,
    }
    const { data } = await hrApi.updatePayrollConfig(route.params.id, payload)
    payrollConfig.value = data
    showPayrollModal.value = false
    toastStore.show('Payroll configuration saved successfully')
  } catch (error) {
    console.error('Failed to save payroll config:', error)
    toastStore.show('Failed to save payroll configuration', 'error')
  } finally {
    savingConfig.value = false
  }
}

function validateTerminateForm() {
  let valid = true
  terminateErrors.termination_date = ''
  terminateErrors.reason = ''

  if (!terminateForm.termination_date) {
    terminateErrors.termination_date = 'Termination date is required'
    valid = false
  }
  if (!terminateForm.reason.trim()) {
    terminateErrors.reason = 'Reason is required'
    valid = false
  }

  return valid
}

async function handleTerminate() {
  if (!validateTerminateForm()) return
  terminating.value = true
  try {
    await hrApi.terminateEmployee(route.params.id, terminateForm)
    toastStore.show(`${getFullName(employee.value)} has been terminated`)
    await fetchEmployee()
  } catch (error) {
    console.error('Failed to terminate employee:', error)
    toastStore.show('Failed to terminate employee', 'error')
  } finally {
    terminating.value = false
  }
}

onMounted(fetchEmployee)
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading employee..." />
    </div>

    <template v-else-if="employee">
      <PageHeader :title="getFullName(employee)" :breadcrumbs="breadcrumbs">
        <template #actions>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="goBack"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Back to List
            </button>

            <button
              v-if="authStore.hasPermission('employees:edit') && employee.status === 'active'"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
              @click="editEmployee"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
              Edit
            </button>

            <button
              v-if="authStore.hasPermission('employees:edit') && employee.status === 'active'"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-red-700 bg-red-50 border border-red-300 rounded-lg hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-700 dark:hover:bg-red-900/50 transition-colors"
              @click="showTerminateDialog = true"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
              Terminate
            </button>

            <button
              v-if="authStore.hasPermission('payroll:edit')"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-green-700 bg-green-50 border border-green-300 rounded-lg hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:border-green-700 dark:hover:bg-green-900/50 transition-colors"
              @click="openPayrollModal"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Configure Payroll
            </button>
          </div>
        </template>
      </PageHeader>

      <!-- Status Card -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Status</p>
          <div class="mt-2">
            <StatusBadge :status="employee.status" :variant-map="statusVariantMap" />
          </div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Department</p>
          <p class="text-xl font-bold text-gray-900 dark:text-white mt-1 capitalize">
            {{ employee.department || '—' }}
          </p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Monthly Salary</p>
          <p class="text-xl font-bold text-gray-900 dark:text-white mt-1">
            {{ formatAmount(employee.salary || 0) }}
          </p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav class="flex gap-6" aria-label="Tabs">
          <button
            v-for="tab in [
              { key: 'info', label: 'Details' },
              { key: 'payroll', label: 'Payroll' },
              { key: 'history', label: 'History' },
            ]"
            :key="tab.key"
            type="button"
            :class="[
              'pb-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:border-gray-600',
            ]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Info Tab -->
      <div v-if="activeTab === 'info'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Employee Information</h3>
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
          <div v-if="employee.email">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Email</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.email }}</dd>
          </div>
          <div v-if="employee.phone">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Phone</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.phone }}</dd>
          </div>
          <div v-if="employee.position">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Position</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.position }}</dd>
          </div>
          <div v-if="employee.hire_date">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Hire Date</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ formatDate(employee.hire_date) }}</dd>
          </div>
          <div v-if="employee.address">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Address</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.address }}</dd>
          </div>
          <div v-if="employee.bank_name">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Bank Name</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.bank_name }}</dd>
          </div>
          <div v-if="employee.bank_account_number">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Bank Account Number</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.bank_account_number }}</dd>
          </div>
          <div v-if="employee.tax_id">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Tax ID</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.tax_id }}</dd>
          </div>
          <div v-if="employee.emergency_contact">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Emergency Contact</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.emergency_contact }}</dd>
          </div>
          <div v-if="employee.emergency_phone">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Emergency Phone</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.emergency_phone }}</dd>
          </div>
          <div v-if="employee.termination_date && employee.status === 'terminated'" class="sm:col-span-2">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Termination Date</dt>
            <dd class="text-sm font-medium text-red-600 dark:text-red-400 mt-0.5">{{ formatDate(employee.termination_date) }}</dd>
          </div>
          <div v-if="employee.termination_reason && employee.status === 'terminated'" class="sm:col-span-2">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Termination Reason</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ employee.termination_reason }}</dd>
          </div>
          <div v-if="employee.notes" class="sm:col-span-2">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Notes</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5 whitespace-pre-wrap">{{ employee.notes }}</dd>
          </div>
        </dl>
      </div>

      <!-- Payroll Tab -->
      <div v-if="activeTab === 'payroll'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Payroll Configuration</h3>
          <button
            v-if="authStore.hasPermission('payroll:edit')"
            type="button"
            class="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
            @click="openPayrollModal"
          >
            Edit Configuration
          </button>
        </div>

        <div v-if="payrollConfig">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Earnings</h4>
              <dl class="space-y-2">
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Basic Salary</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payrollConfig.basic_salary) }}</dd>
                </div>
                <div v-if="payrollConfig.housing_allowance" class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Housing Allowance</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payrollConfig.housing_allowance) }}</dd>
                </div>
                <div v-if="payrollConfig.transport_allowance" class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Transport Allowance</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payrollConfig.transport_allowance) }}</dd>
                </div>
                <div v-if="payrollConfig.medical_allowance" class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Medical Allowance</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payrollConfig.medical_allowance) }}</dd>
                </div>
                <div v-if="payrollConfig.other_allowances" class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Other Allowances</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payrollConfig.other_allowances) }}</dd>
                </div>
              </dl>
            </div>
            <div>
              <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Deductions</h4>
              <dl class="space-y-2">
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Tax Rate</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ payrollConfig.tax_rate }}%</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Pension Rate</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ payrollConfig.pension_rate }}%</dd>
                </div>
                <div v-if="payrollConfig.other_deductions" class="flex justify-between">
                  <dt class="text-sm text-gray-500 dark:text-gray-400">Other Deductions</dt>
                  <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatAmount(payrollConfig.other_deductions) }}</dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">No payroll configuration set.</p>
          <button
            v-if="authStore.hasPermission('payroll:edit')"
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            @click="openPayrollModal"
          >
            Configure Payroll
          </button>
        </div>
      </div>

      <!-- History Tab -->
      <div v-if="activeTab === 'history'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div v-if="employmentHistory.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No employment history available.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Action</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Details</th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="record in employmentHistory"
                :key="record.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(record.date, 'short') }}</td>
                <td class="px-6 py-4">
                  <StatusBadge :status="record.action" />
                </td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ record.details || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Terminate Dialog -->
    <Modal
      v-model:show="showTerminateDialog"
      title="Terminate Employee"
      size="md"
    >
      <form class="space-y-4" @submit.prevent="handleTerminate">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          You are about to terminate <strong>{{ getFullName(employee) }}</strong>. Please provide the termination details.
        </p>
        <DateInput
          v-model="terminateForm.termination_date"
          label="Termination Date"
          name="termination_date"
          required
          :error="terminateErrors.termination_date"
        />
        <TextareaInput
          v-model="terminateForm.reason"
          label="Reason"
          name="reason"
          placeholder="Enter reason for termination..."
          :rows="3"
          required
          :error="terminateErrors.reason"
        />
      </form>
      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="showTerminateDialog = false"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="terminating"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleTerminate"
        >
          <LoadingSpinner v-if="terminating" size="sm" />
          {{ terminating ? 'Terminating...' : 'Terminate Employee' }}
        </button>
      </template>
    </Modal>

    <!-- Payroll Config Modal -->
    <Modal
      v-model:show="showPayrollModal"
      title="Configure Payroll"
      size="lg"
    >
      <form class="space-y-6" @submit.prevent="savePayrollConfig">
        <div>
          <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Earnings</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <TextInput
              v-model="payrollForm.basic_salary"
              label="Basic Salary"
              name="basic_salary"
              type="number"
              placeholder="0.00"
              required
              :error="payrollErrors.basic_salary"
            />
            <TextInput
              v-model="payrollForm.housing_allowance"
              label="Housing Allowance"
              name="housing_allowance"
              type="number"
              placeholder="0.00"
            />
            <TextInput
              v-model="payrollForm.transport_allowance"
              label="Transport Allowance"
              name="transport_allowance"
              type="number"
              placeholder="0.00"
            />
            <TextInput
              v-model="payrollForm.medical_allowance"
              label="Medical Allowance"
              name="medical_allowance"
              type="number"
              placeholder="0.00"
            />
            <TextInput
              v-model="payrollForm.other_allowances"
              label="Other Allowances"
              name="other_allowances"
              type="number"
              placeholder="0.00"
            />
          </div>
        </div>
        <div>
          <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Deductions</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <TextInput
              v-model="payrollForm.tax_rate"
              label="Tax Rate (%)"
              name="tax_rate"
              type="number"
              placeholder="0"
              :error="payrollErrors.tax_rate"
              help-text="Percentage of gross pay"
            />
            <TextInput
              v-model="payrollForm.pension_rate"
              label="Pension Rate (%)"
              name="pension_rate"
              type="number"
              placeholder="0"
              :error="payrollErrors.pension_rate"
              help-text="Percentage of basic salary"
            />
            <TextInput
              v-model="payrollForm.other_deductions"
              label="Other Deductions"
              name="other_deductions"
              type="number"
              placeholder="0.00"
            />
          </div>
        </div>
      </form>
      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="showPayrollModal = false"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="savingConfig"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="savePayrollConfig"
        >
          <LoadingSpinner v-if="savingConfig" size="sm" />
          {{ savingConfig ? 'Saving...' : 'Save Configuration' }}
        </button>
      </template>
    </Modal>
  </div>
</template>
