<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatCard from '@/components/common/StatCard.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import * as hrApi from '@/api/hr'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const employees = ref([])
const loading = ref(true)
const running = ref(false)
const showConfirmDialog = ref(false)

// Payroll period
const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1
const payrollYear = ref(currentYear)
const payrollMonth = ref(currentMonth)

// Selected employee IDs
const selectedIds = ref([])

const breadcrumbs = [
  { text: 'HR' },
  { text: 'Run Payroll' },
]

const monthOptions = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
]

const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear - 2; y <= currentYear + 1; y++) {
    years.push({ value: y, label: String(y) })
  }
  return years
})

function formatAmount(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

function getFullName(emp) {
  return `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || emp.name || '—'
}

function getAllowances(emp) {
  const config = emp.payroll_config || {}
  return (Number(config.housing_allowance) || 0) +
    (Number(config.transport_allowance) || 0) +
    (Number(config.medical_allowance) || 0) +
    (Number(config.other_allowances) || 0)
}

function getGrossPay(emp) {
  const config = emp.payroll_config || {}
  return (Number(config.basic_salary) || Number(emp.salary) || 0) + getAllowances(emp)
}

function getTax(emp) {
  const config = emp.payroll_config || {}
  const gross = getGrossPay(emp)
  const taxRate = Number(config.tax_rate) || 0
  return gross * (taxRate / 100)
}

function getPension(emp) {
  const config = emp.payroll_config || {}
  const basic = Number(config.basic_salary) || Number(emp.salary) || 0
  const pensionRate = Number(config.pension_rate) || 0
  return basic * (pensionRate / 100)
}

function getOtherDeductions(emp) {
  const config = emp.payroll_config || {}
  return Number(config.other_deductions) || 0
}

function getTotalDeductions(emp) {
  return getTax(emp) + getPension(emp) + getOtherDeductions(emp)
}

function getNetPay(emp) {
  return getGrossPay(emp) - getTotalDeductions(emp)
}

// Only active employees with payroll config
const eligibleEmployees = computed(() => {
  return employees.value.filter(emp => emp.status === 'active' && emp.payroll_config)
})

const selectedEmployees = computed(() => {
  return eligibleEmployees.value.filter(emp => selectedIds.value.includes(emp.id))
})

const totalGross = computed(() => selectedEmployees.value.reduce((sum, emp) => sum + getGrossPay(emp), 0))
const totalDeductions = computed(() => selectedEmployees.value.reduce((sum, emp) => sum + getTotalDeductions(emp), 0))
const totalNet = computed(() => selectedEmployees.value.reduce((sum, emp) => sum + getNetPay(emp), 0))

function toggleSelectAll() {
  if (selectedIds.value.length === eligibleEmployees.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = eligibleEmployees.value.map(emp => emp.id)
  }
}

function toggleSelect(empId) {
  const index = selectedIds.value.indexOf(empId)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(empId)
  }
}

async function fetchEmployees() {
  loading.value = true
  try {
    const { data } = await hrApi.listEmployees()
    employees.value = Array.isArray(data) ? data : data.items || data.employees || []
    // Auto-select all eligible
    selectedIds.value = employees.value
      .filter(emp => emp.status === 'active' && emp.payroll_config)
      .map(emp => emp.id)
  } catch (error) {
    console.error('Failed to fetch employees:', error)
    toastStore.show('Failed to load employees', 'error')
  } finally {
    loading.value = false
  }
}

async function runPayroll() {
  running.value = true
  try {
    await hrApi.runPayroll({
      year: payrollYear.value,
      month: payrollMonth.value,
      employee_ids: selectedIds.value,
    })
    toastStore.show(`Payroll for ${monthOptions[payrollMonth.value - 1].label} ${payrollYear.value} processed successfully`)
    router.push({ name: 'PayslipList' })
  } catch (error) {
    console.error('Failed to run payroll:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to run payroll'
    toastStore.show(message, 'error')
  } finally {
    running.value = false
  }
}

onMounted(fetchEmployees)
</script>

<template>
  <div>
    <PageHeader title="Run Payroll" :breadcrumbs="breadcrumbs" />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading payroll data..." />
    </div>

    <template v-else>
      <!-- Payroll Period Selection -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">Payroll Period</h3>
        <div class="flex flex-col sm:flex-row gap-4">
          <div class="w-full sm:w-48">
            <SelectInput
              v-model="payrollMonth"
              label="Month"
              name="payroll_month"
              :options="monthOptions"
            />
          </div>
          <div class="w-full sm:w-40">
            <SelectInput
              v-model="payrollYear"
              label="Year"
              name="payroll_year"
              :options="yearOptions"
            />
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <EmptyState
        v-if="eligibleEmployees.length === 0"
        title="No eligible employees"
        message="No active employees with payroll configuration found. Configure payroll for employees first."
      />

      <template v-else>
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <StatCard
            title="Total Gross Pay"
            :value="formatAmount(totalGross)"
            color="green"
            icon="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"
          />
          <StatCard
            title="Total Deductions"
            :value="formatAmount(totalDeductions)"
            color="red"
            icon="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
          />
          <StatCard
            title="Total Net Pay"
            :value="formatAmount(totalNet)"
            color="blue"
            icon="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </div>

        <!-- Employee Table -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    :checked="selectedIds.length === eligibleEmployees.length && eligibleEmployees.length > 0"
                    class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                    @change="toggleSelectAll"
                  />
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Select All ({{ selectedIds.length }} / {{ eligibleEmployees.length }})
                  </span>
                </label>
              </div>
              <button
                v-if="selectedIds.length > 0"
                type="button"
                :disabled="running"
                class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                @click="showConfirmDialog = true"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
                </svg>
                Run Payroll
              </button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-4 py-3 text-left w-10">
                    <span class="sr-only">Select</span>
                  </th>
                  <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Name</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Basic Salary</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Allowances</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Gross Pay</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Tax</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Pension</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Other Ded.</th>
                  <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Net Pay</th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                <tr
                  v-for="emp in eligibleEmployees"
                  :key="emp.id"
                  :class="[
                    'transition-colors',
                    selectedIds.includes(emp.id) ? 'bg-blue-50/50 dark:bg-blue-900/10' : 'hover:bg-gray-50 dark:hover:bg-gray-800',
                  ]"
                >
                  <td class="px-4 py-3">
                    <input
                      type="checkbox"
                      :checked="selectedIds.includes(emp.id)"
                      class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                      @change="toggleSelect(emp.id)"
                    />
                  </td>
                  <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white whitespace-nowrap">
                    {{ getFullName(emp) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 text-right whitespace-nowrap">
                    {{ formatAmount(emp.payroll_config?.basic_salary || emp.salary || 0) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 text-right whitespace-nowrap">
                    {{ formatAmount(getAllowances(emp)) }}
                  </td>
                  <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white text-right whitespace-nowrap">
                    {{ formatAmount(getGrossPay(emp)) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-red-600 dark:text-red-400 text-right whitespace-nowrap">
                    {{ formatAmount(getTax(emp)) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-red-600 dark:text-red-400 text-right whitespace-nowrap">
                    {{ formatAmount(getPension(emp)) }}
                  </td>
                  <td class="px-4 py-3 text-sm text-red-600 dark:text-red-400 text-right whitespace-nowrap">
                    {{ formatAmount(getOtherDeductions(emp)) }}
                  </td>
                  <td class="px-4 py-3 text-sm font-bold text-green-600 dark:text-green-400 text-right whitespace-nowrap">
                    {{ formatAmount(getNetPay(emp)) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Running overlay -->
        <div v-if="running" class="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div class="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-2xl flex flex-col items-center gap-4">
            <LoadingSpinner size="lg" text="Processing payroll..." />
            <p class="text-sm text-gray-500 dark:text-gray-400">Please do not close this page.</p>
          </div>
        </div>
      </template>
    </template>

    <!-- Confirm Dialog -->
    <ConfirmDialog
      v-model:show="showConfirmDialog"
      title="Run Payroll"
      :message="`Generate payslips for ${selectedIds.length} employee(s) for ${monthOptions[payrollMonth - 1].label} ${payrollYear}? This will create payslip records that can be viewed and marked as paid later.`"
      confirm-text="Run Payroll"
      type="info"
      @confirm="runPayroll"
    />
  </div>
</template>
