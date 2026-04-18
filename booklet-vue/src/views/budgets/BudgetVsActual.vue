<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { getBudget, getBudgetVsActual } from '@/api/budgets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(true)
const budget = ref(null)
const comparisonData = ref(null)

let barChart = null

async function fetchData() {
  loading.value = true
  try {
    const [budgetRes, vsActualRes] = await Promise.all([
      getBudget(route.params.id),
      getBudgetVsActual(route.params.id),
    ])

    budget.value = budgetRes.data
    comparisonData.value = vsActualRes.data

    await nextTick()
    renderChart()
  } catch (error) {
    console.error('Failed to fetch budget vs actual:', error)
    toast.show('Failed to load budget comparison', 'error')
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!comparisonData.value?.items || typeof echarts === 'undefined') return

  const el = document.getElementById('budget-vs-actual-chart')
  if (!el) return

  if (barChart) barChart.dispose()

  const items = comparisonData.value.items
  const categories = items.map(item => item.account_name || item.account || 'Unknown')
  const budgeted = items.map(item => Number(item.budgeted) || 0)
  const actual = items.map(item => Number(item.actual) || 0)

  barChart = echarts.init(el)
  barChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: {
      data: ['Budgeted', 'Actual'],
      bottom: 0,
      textStyle: { color: '#6B7280' },
    },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { rotate: 30, color: '#6B7280', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#6B7280' },
    },
    series: [
      {
        name: 'Budgeted',
        type: 'bar',
        data: budgeted,
        itemStyle: { borderRadius: [4, 4, 0, 0], color: '#10B981' },
        barMaxWidth: 30,
      },
      {
        name: 'Actual',
        type: 'bar',
        data: actual,
        itemStyle: { borderRadius: [4, 4, 0, 0], color: '#6366F1' },
        barMaxWidth: 30,
      },
    ],
  })

  window.addEventListener('resize', () => barChart?.resize())
}

const totalBudgeted = computed(() => {
  if (!comparisonData.value) return 0
  return (comparisonData.value.items || []).reduce((sum, item) => sum + (Number(item.budgeted) || 0), 0)
})

const totalActual = computed(() => {
  if (!comparisonData.value) return 0
  return (comparisonData.value.items || []).reduce((sum, item) => sum + (Number(item.actual) || 0), 0)
})

const totalVariance = computed(() => totalBudgeted.value - totalActual.value)

function getVarianceClass(item) {
  const variance = (Number(item.budgeted) || 0) - (Number(item.actual) || 0)
  return variance >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
}

function getVarianceBgClass(item) {
  const variance = (Number(item.budgeted) || 0) - (Number(item.actual) || 0)
  return variance >= 0
    ? 'bg-emerald-50 dark:bg-emerald-900/20'
    : 'bg-red-50 dark:bg-red-900/20'
}

function getAccountName(item) {
  return item.account_name || item.account || '—'
}

function goBack() {
  router.push({ name: 'BudgetDetail', params: { id: route.params.id } })
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Budget vs Actual"
      :subtitle="budget?.name || ''"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Budgets', to: { name: 'BudgetList' } },
        { text: budget?.name || 'Budget', to: { name: 'BudgetDetail', params: { id: route.params.id } } },
        { text: 'vs Actual' }
      ]"
    >
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          @click="goBack"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to Budget
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading comparison data..." />

    <template v-else-if="comparisonData">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Total Budgeted"
          :value="formatCurrency(totalBudgeted, auth.branchCurrency)"
          color="green"
          icon="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
        <StatCard
          title="Total Actual"
          :value="formatCurrency(totalActual, auth.branchCurrency)"
          color="purple"
          icon="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75z"
        />
        <StatCard
          title="Total Variance"
          :value="formatCurrency(totalVariance, auth.branchCurrency)"
          :color="totalVariance >= 0 ? 'green' : 'red'"
          :icon="totalVariance >= 0
            ? 'M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941'
            : 'M2.25 6L9 12.75l4.286-4.286a11.948 11.948 0 014.306 6.43l.776 2.898m0 0l3.182-5.511m-3.182 5.51l-5.511-3.181'"
        />
      </div>

      <!-- Bar Chart -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Budget vs Actual Comparison</h3>
        <div id="budget-vs-actual-chart" class="w-full h-96"></div>
        <p v-if="typeof echarts === 'undefined'" class="text-sm text-gray-500 dark:text-gray-400 text-center mt-4">
          Install ECharts to view charts
        </p>
      </div>

      <!-- Comparison Table -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Line Item Comparison</h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Type</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Budgeted</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Actual</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Variance</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Variance %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(item, index) in (comparisonData.items || [])"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ getAccountName(item) }}</td>
                <td class="px-4 py-3">
                  <span
                    :class="[
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                      item.type === 'revenue'
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-400'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400'
                    ]"
                  >
                    {{ item.type || 'expense' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">
                  {{ formatCurrency(item.budgeted, auth.branchCurrency) }}
                </td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">
                  {{ formatCurrency(item.actual, auth.branchCurrency) }}
                </td>
                <td class="px-4 py-3 text-right">
                  <span
                    :class="[
                      'text-sm font-medium px-2 py-1 rounded',
                      getVarianceClass(item),
                      getVarianceBgClass(item)
                    ]"
                  >
                    {{ formatCurrency((Number(item.budgeted) || 0) - (Number(item.actual) || 0), auth.branchCurrency) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  <span
                    v-if="Number(item.budgeted) > 0"
                    :class="['text-sm font-medium', getVarianceClass(item)]"
                  >
                    {{ (((Number(item.budgeted) || 0) - (Number(item.actual) || 0)) / Number(item.budgeted) * 100).toFixed(1) }}%
                  </span>
                  <span v-else class="text-sm text-gray-400">—</span>
                </td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 dark:bg-gray-900 font-semibold">
              <tr>
                <td class="px-4 py-3 text-sm text-gray-900 dark:text-white" colspan="2">Total</td>
                <td class="px-4 py-3 text-right text-sm text-gray-900 dark:text-white">{{ formatCurrency(totalBudgeted, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right text-sm text-gray-900 dark:text-white">{{ formatCurrency(totalActual, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right">
                  <span
                    :class="[
                      'text-sm font-medium',
                      totalVariance >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                    ]"
                  >
                    {{ formatCurrency(totalVariance, auth.branchCurrency) }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  <span
                    v-if="totalBudgeted > 0"
                    :class="['text-sm font-medium', totalVariance >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400']"
                  >
                    {{ (totalVariance / totalBudgeted * 100).toFixed(1) }}%
                  </span>
                  <span v-else class="text-sm text-gray-400">—</span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

