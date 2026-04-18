<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import * as hrApi from '@/api/hr'

const authStore = useAuthStore()
const toastStore = useToastStore()

const summary = ref(null)
const breakdown = ref([])
const loading = ref(true)

const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1
const filterYear = ref(currentYear)
const filterMonth = ref(currentMonth)

const breadcrumbs = [
  { text: 'HR' },
  { text: 'Payroll Summary' },
]

const monthOptions = [
  { value: 0, label: 'All Months' },
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
  const years = [{ value: 0, label: 'All Years' }]
  for (let y = currentYear - 3; y <= currentYear; y++) {
    years.push({ value: y, label: String(y) })
  }
  return years
})

function formatAmount(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

const totalEmployees = computed(() => summary.value?.total_employees || breakdown.value.length || 0)
const totalGross = computed(() => summary.value?.total_gross_pay || breakdown.value.reduce((sum, b) => sum + (b.gross_pay || 0), 0))
const totalDeductions = computed(() => summary.value?.total_deductions || breakdown.value.reduce((sum, b) => sum + (b.total_deductions || 0), 0))
const totalNet = computed(() => summary.value?.total_net_pay || breakdown.value.reduce((sum, b) => sum + (b.net_pay || 0), 0))

async function fetchSummary() {
  loading.value = true
  try {
    const params = {}
    if (filterMonth.value) params.month = filterMonth.value
    if (filterYear.value) params.year = filterYear.value
    const { data } = await hrApi.listPayslips(params)
    const payslips = Array.isArray(data) ? data : data.items || data.payslips || []

    // Build summary from payslips
    summary.value = {
      total_employees: new Set(payslips.map(p => p.employee_id)).size,
      total_gross_pay: payslips.reduce((sum, p) => sum + (p.gross_pay || 0), 0),
      total_deductions: payslips.reduce((sum, p) => sum + (p.total_deductions || 0), 0),
      total_net_pay: payslips.reduce((sum, p) => sum + (p.net_pay || 0), 0),
    }

    // Group by employee for breakdown
    const empMap = {}
    for (const ps of payslips) {
      const key = ps.employee_id
      if (!empMap[key]) {
        empMap[key] = {
          employee_id: key,
          employee_name: ps.employee_name,
          department: ps.department,
          gross_pay: 0,
          total_deductions: 0,
          net_pay: 0,
          payslip_count: 0,
        }
      }
      empMap[key].gross_pay += ps.gross_pay || 0
      empMap[key].total_deductions += ps.total_deductions || 0
      empMap[key].net_pay += ps.net_pay || 0
      empMap[key].payslip_count++
    }
    breakdown.value = Object.values(empMap)
  } catch (error) {
    console.error('Failed to fetch payroll summary:', error)
    toastStore.show('Failed to load payroll summary', 'error')
  } finally {
    loading.value = false
  }
}

watch([filterMonth, filterYear], fetchSummary)

onMounted(fetchSummary)
</script>

<template>
  <div>
    <PageHeader title="Payroll Summary" :breadcrumbs="breadcrumbs" />

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="w-full sm:w-48">
          <SelectInput
            v-model="filterMonth"
            label="Month"
            name="filter_month"
            :options="monthOptions"
          />
        </div>
        <div class="w-full sm:w-40">
          <SelectInput
            v-model="filterYear"
            label="Year"
            name="filter_year"
            :options="yearOptions"
          />
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading payroll summary..." />
    </div>

    <template v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Employees"
          :value="String(totalEmployees)"
          color="blue"
          icon="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
        />
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
          color="amber"
          icon="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </div>

      <!-- Employee Breakdown -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Employee Breakdown</h3>
        </div>

        <div v-if="breakdown.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No payroll data available for the selected period.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Employee</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Department</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Gross Pay</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Deductions</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Net Pay</th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="emp in breakdown"
                :key="emp.employee_id"
                class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">
                  {{ emp.employee_name || '—' }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300 capitalize">
                  {{ emp.department || '—' }}
                </td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white text-right">
                  {{ formatAmount(emp.gross_pay) }}
                </td>
                <td class="px-6 py-4 text-sm text-red-600 dark:text-red-400 text-right">
                  {{ formatAmount(emp.total_deductions) }}
                </td>
                <td class="px-6 py-4 text-sm font-bold text-green-600 dark:text-green-400 text-right">
                  {{ formatAmount(emp.net_pay) }}
                </td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <td class="px-6 py-3 text-sm font-bold text-gray-900 dark:text-white" colspan="2">Total</td>
                <td class="px-6 py-3 text-sm font-bold text-gray-900 dark:text-white text-right">{{ formatAmount(totalGross) }}</td>
                <td class="px-6 py-3 text-sm font-bold text-red-600 dark:text-red-400 text-right">{{ formatAmount(totalDeductions) }}</td>
                <td class="px-6 py-3 text-sm font-bold text-green-600 dark:text-green-400 text-right">{{ formatAmount(totalNet) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
