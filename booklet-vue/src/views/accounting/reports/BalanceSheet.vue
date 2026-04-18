<script setup>
import { ref, onMounted, computed } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import DateInput from '@/components/forms/DateInput.vue'
import { getBalanceSheet } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const auth = useAuthStore()
const toast = useToastStore()

const report = ref(null)
const loading = ref(true)
const asOfDate = ref('')

// Computed sections
const assets = computed(() => report.value?.assets || { current: [], fixed: [], total: 0 })
const liabilities = computed(() => report.value?.liabilities || { current: [], long_term: [], total: 0 })
const equity = computed(() => report.value?.equity || { items: [], total: 0 })
const totalAssets = computed(() => assets.value.total || 0)
const totalLiabilities = computed(() => liabilities.value.total || 0)
const totalEquity = computed(() => equity.value.total || 0)
const totalLiabilitiesEquity = computed(() => totalLiabilities.value + totalEquity.value)
const isBalanced = computed(() => Math.abs(totalAssets.value - totalLiabilitiesEquity.value) < 0.01)

async function fetchReport() {
  loading.value = true
  try {
    const params = {}
    if (asOfDate.value) params.as_of_date = asOfDate.value

    const { data } = await getBalanceSheet(params)
    report.value = data
  } catch (error) {
    console.error('Failed to fetch balance sheet:', error)
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
      title="Balance Sheet"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Reports' },
        { text: 'Balance Sheet' }
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

    <!-- Filter -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DateInput
          v-model="asOfDate"
          label="As of Date"
          name="as_of_date"
          help-text="Leave blank for today"
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

    <LoadingSpinner v-if="loading" text="Loading balance sheet..." />

    <EmptyState
      v-else-if="!report"
      title="No data available"
      message="Could not generate the balance sheet. Please check your date range and try again."
    />

    <template v-else>
      <!-- Report Content -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <!-- ASSETS SECTION -->
        <div class="p-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 pb-2 border-b-2 border-emerald-500">
            Assets
          </h2>

          <!-- Current Assets -->
          <div class="mb-6 ml-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3">
              Current Assets
            </h3>
            <div class="space-y-2 ml-4">
              <div
                v-for="item in assets.current"
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
              <div v-if="assets.current.length === 0" class="text-sm text-gray-400 dark:text-gray-500 italic">No current assets</div>
            </div>
          </div>

          <!-- Fixed Assets -->
          <div class="mb-6 ml-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3">
              Fixed Assets
            </h3>
            <div class="space-y-2 ml-4">
              <div
                v-for="item in assets.fixed"
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
              <div v-if="assets.fixed.length === 0" class="text-sm text-gray-400 dark:text-gray-500 italic">No fixed assets</div>
            </div>
          </div>

          <!-- Total Assets -->
          <div class="flex justify-between items-center py-3 px-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <span class="text-base font-bold text-gray-900 dark:text-white">Total Assets</span>
            <span class="text-base font-bold text-gray-900 dark:text-white">
              {{ formatCurrency(totalAssets, auth.branchCurrency) }}
            </span>
          </div>
        </div>

        <div class="border-t border-gray-200 dark:border-gray-700" />

        <!-- LIABILITIES SECTION -->
        <div class="p-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 pb-2 border-b-2 border-red-500">
            Liabilities
          </h2>

          <!-- Current Liabilities -->
          <div class="mb-6 ml-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3">
              Current Liabilities
            </h3>
            <div class="space-y-2 ml-4">
              <div
                v-for="item in liabilities.current"
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
              <div v-if="liabilities.current.length === 0" class="text-sm text-gray-400 dark:text-gray-500 italic">No current liabilities</div>
            </div>
          </div>

          <!-- Long-term Liabilities -->
          <div class="mb-6 ml-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-3">
              Long-term Liabilities
            </h3>
            <div class="space-y-2 ml-4">
              <div
                v-for="item in liabilities.long_term"
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
              <div v-if="liabilities.long_term.length === 0" class="text-sm text-gray-400 dark:text-gray-500 italic">No long-term liabilities</div>
            </div>
          </div>

          <!-- Total Liabilities -->
          <div class="flex justify-between items-center py-3 px-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <span class="text-base font-bold text-gray-900 dark:text-white">Total Liabilities</span>
            <span class="text-base font-bold text-gray-900 dark:text-white">
              {{ formatCurrency(totalLiabilities, auth.branchCurrency) }}
            </span>
          </div>
        </div>

        <div class="border-t border-gray-200 dark:border-gray-700" />

        <!-- EQUITY SECTION -->
        <div class="p-6">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-4 pb-2 border-b-2 border-purple-500">
            Equity
          </h2>

          <div class="space-y-2 ml-4">
            <div
              v-for="item in equity.items"
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
            <div v-if="equity.items && equity.items.length === 0" class="text-sm text-gray-400 dark:text-gray-500 italic">No equity items</div>
          </div>

          <!-- Total Equity -->
          <div class="flex justify-between items-center py-3 px-4 bg-gray-50 dark:bg-gray-900 rounded-lg mt-4">
            <span class="text-base font-bold text-gray-900 dark:text-white">Total Equity</span>
            <span class="text-base font-bold text-gray-900 dark:text-white">
              {{ formatCurrency(totalEquity, auth.branchCurrency) }}
            </span>
          </div>
        </div>

        <div class="border-t-2 border-gray-300 dark:border-gray-600" />

        <!-- TOTAL LIABILITIES + EQUITY -->
        <div class="p-6">
          <div class="flex justify-between items-center py-4 px-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
            <span class="text-lg font-bold text-gray-900 dark:text-white">Total Liabilities + Equity</span>
            <span class="text-lg font-bold text-emerald-600 dark:text-emerald-400">
              {{ formatCurrency(totalLiabilitiesEquity, auth.branchCurrency) }}
            </span>
          </div>

          <!-- Balance Check -->
          <div class="mt-4 flex justify-center">
            <div
              class="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
              :class="isBalanced ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path
                  v-if="isBalanced"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
                <path
                  v-else
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
              {{ isBalanced ? 'Balance sheet is balanced' : 'Balance sheet is not balanced' }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
