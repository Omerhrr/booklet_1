<script setup>
import { ref, onMounted, computed } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import DateInput from '@/components/forms/DateInput.vue'
import { getIncomeStatement } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const auth = useAuthStore()
const toast = useToastStore()

const report = ref(null)
const loading = ref(true)
const startDate = ref('')
const endDate = ref('')

const revenueItems = computed(() => report.value?.revenue || [])
const expenseItems = computed(() => report.value?.expenses || [])
const totalRevenue = computed(() => report.value?.total_revenue || 0)
const totalExpenses = computed(() => report.value?.total_expenses || 0)
const netIncome = computed(() => report.value?.net_income || totalRevenue.value - totalExpenses.value)

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const { data } = await getIncomeStatement(params)
    report.value = data
  } catch (error) {
    console.error('Failed to fetch profit & loss:', error)
    report.value = null
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  fetchReport()
}

function handlePrint() {
  window.print()
}

function handleExportPdf() {
  toast.show('PDF export initiated', 'success')
}

function handleExportExcel() {
  toast.show('Excel export initiated', 'success')
}

onMounted(() => {
  fetchReport()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Profit & Loss Statement"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Reports' },
        { text: 'Profit & Loss' }
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handlePrint"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18.75 7.131s0 0 0 0" />
            </svg>
            Print
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportPdf"
          >
            PDF
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handleExportExcel"
          >
            Excel
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DateInput
          v-model="startDate"
          label="Start Date"
          name="start_date"
        />
        <DateInput
          v-model="endDate"
          label="End Date"
          name="end_date"
        />
        <div class="flex items-end">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            @click="applyFilters"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z" />
            </svg>
            Generate Report
          </button>
        </div>
      </div>
    </div>

    <LoadingSpinner v-if="loading" text="Loading profit & loss statement..." />

    <EmptyState
      v-else-if="!report"
      title="No data available"
      message="Could not generate the profit & loss statement. Please check your date range and try again."
    />

    <template v-else>
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <!-- REVENUE SECTION -->
        <div class="p-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 pb-2 border-b-2 border-emerald-500">
            Revenue
          </h2>

          <div class="space-y-2 ml-4">
            <div
              v-for="item in revenueItems"
              :key="item.code || item.name"
              class="flex justify-between items-center py-1.5"
            >
              <span class="text-sm text-gray-600 dark:text-gray-400">
                <span v-if="item.code" class="font-mono text-xs mr-2">{{ item.code }}</span>
                {{ item.name }}
              </span>
              <span class="text-sm font-medium text-gray-900 dark:text-white">
                {{ formatCurrency(item.balance || item.amount || 0, auth.branchCurrency) }}
              </span>
            </div>
            <div v-if="revenueItems.length === 0" class="text-sm text-gray-400 dark:text-gray-500 italic py-2">No revenue items</div>
          </div>

          <!-- Total Revenue -->
          <div class="flex justify-between items-center py-3 px-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg mt-4">
            <span class="text-base font-bold text-gray-900 dark:text-white">Total Revenue</span>
            <span class="text-base font-bold text-emerald-600 dark:text-emerald-400">
              {{ formatCurrency(totalRevenue, auth.branchCurrency) }}
            </span>
          </div>
        </div>

        <div class="border-t border-gray-200 dark:border-gray-700" />

        <!-- EXPENSES SECTION -->
        <div class="p-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 pb-2 border-b-2 border-red-500">
            Expenses
          </h2>

          <div class="space-y-2 ml-4">
            <div
              v-for="item in expenseItems"
              :key="item.code || item.name"
              class="flex justify-between items-center py-1.5"
            >
              <span class="text-sm text-gray-600 dark:text-gray-400">
                <span v-if="item.code" class="font-mono text-xs mr-2">{{ item.code }}</span>
                {{ item.name }}
              </span>
              <span class="text-sm font-medium text-gray-900 dark:text-white">
                {{ formatCurrency(item.balance || item.amount || 0, auth.branchCurrency) }}
              </span>
            </div>
            <div v-if="expenseItems.length === 0" class="text-sm text-gray-400 dark:text-gray-500 italic py-2">No expense items</div>
          </div>

          <!-- Total Expenses -->
          <div class="flex justify-between items-center py-3 px-4 bg-red-50 dark:bg-red-900/20 rounded-lg mt-4">
            <span class="text-base font-bold text-gray-900 dark:text-white">Total Expenses</span>
            <span class="text-base font-bold text-red-600 dark:text-red-400">
              {{ formatCurrency(totalExpenses, auth.branchCurrency) }}
            </span>
          </div>
        </div>

        <div class="border-t-2 border-gray-300 dark:border-gray-600" />

        <!-- NET INCOME -->
        <div class="p-6">
          <div
            class="flex justify-between items-center py-4 px-4 rounded-lg"
            :class="netIncome >= 0 ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'"
          >
            <span class="text-lg font-bold text-gray-900 dark:text-white">
              {{ netIncome >= 0 ? 'Net Income' : 'Net Loss' }}
            </span>
            <span
              class="text-xl font-bold"
              :class="netIncome >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
            >
              {{ formatCurrency(Math.abs(netIncome), auth.branchCurrency) }}
              <span v-if="netIncome < 0" class="text-base">(Loss)</span>
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
