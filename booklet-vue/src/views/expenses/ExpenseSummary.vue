<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatCard from '@/components/common/StatCard.vue'
import DateInput from '@/components/forms/DateInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { getExpenseCategories, getExpenseSummary } from '@/api/expenses'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(true)
const summaryData = ref(null)
const categories = ref([])
const filterStartDate = ref('')
const filterEndDate = ref('')

let chartInstance = null

function setDefaultDates() {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  filterStartDate.value = firstDay.toISOString().split('T')[0]
  filterEndDate.value = now.toISOString().split('T')[0]
}

async function fetchCategories() {
  try {
    const { data } = await getExpenseCategories()
    categories.value = (Array.isArray(data) ? data : data.categories || []).map(c => ({
      value: typeof c === 'string' ? c : c.id || c.name,
      label: typeof c === 'string' ? c : c.name || c.label,
    }))
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

async function fetchSummary() {
  loading.value = true
  try {
    const params = {}
    if (filterStartDate.value) params.start_date = filterStartDate.value
    if (filterEndDate.value) params.end_date = filterEndDate.value

    const { data } = await getExpenseSummary(params)
    summaryData.value = data
    await nextTick()
    renderCharts()
  } catch (error) {
    console.error('Failed to fetch expense summary:', error)
    toast.show('Failed to load expense summary', 'error')
  } finally {
    loading.value = false
  }
}

function renderCharts() {
  if (!summaryData.value?.by_category) return

  // Try to use ECharts if available
  const pieEl = document.getElementById('expense-pie-chart')
  const barEl = document.getElementById('expense-bar-chart')

  if (pieEl && typeof echarts !== 'undefined') {
    if (chartInstance) chartInstance.dispose()

    const categoryData = summaryData.value.by_category.map(item => ({
      name: item.category_name || item.category || 'Unknown',
      value: Number(item.total) || 0,
    }))

    chartInstance = echarts.init(pieEl)
    chartInstance.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'horizontal',
        bottom: 0,
        textStyle: { color: '#6B7280' },
      },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
        },
        data: categoryData,
        color: ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#3B82F6', '#EC4899', '#6366F1', '#14B8A6', '#F97316', '#64748B'],
      }],
    })

    window.addEventListener('resize', () => chartInstance?.resize())
  }

  if (barEl && typeof echarts !== 'undefined') {
    const barChart = echarts.init(barEl)
    const categoryData = summaryData.value.by_category.map(item => ({
      name: item.category_name || item.category || 'Unknown',
      value: Number(item.total) || 0,
    }))

    barChart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: categoryData.map(d => d.name),
        axisLabel: { rotate: 30, color: '#6B7280' },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#6B7280' },
      },
      series: [{
        type: 'bar',
        data: categoryData.map(d => d.value),
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#10B981' },
            { offset: 1, color: '#059669' },
          ]),
        },
        barMaxWidth: 40,
      }],
    })

    window.addEventListener('resize', () => barChart?.resize())
  }
}

const totalExpenses = () => {
  if (!summaryData.value) return 0
  return (summaryData.value.by_category || []).reduce((sum, item) => sum + (Number(item.total) || 0), 0)
}

const categoryCount = () => {
  if (!summaryData.value) return 0
  return (summaryData.value.by_category || []).length
}

const topCategory = () => {
  if (!summaryData.value?.by_category?.length) return '—'
  const sorted = [...summaryData.value.by_category].sort((a, b) => (Number(b.total) || 0) - (Number(a.total) || 0))
  return sorted[0].category_name || sorted[0].category || '—'
}

watch([filterStartDate, filterEndDate], () => {
  fetchSummary()
})

onMounted(() => {
  setDefaultDates()
  fetchCategories()
  fetchSummary()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Expense Summary"
      subtitle="Overview of expenses by category"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Expenses', to: { name: 'ExpenseList' } },
        { text: 'Summary' }
      ]"
    />

    <!-- Date Range Filter -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <DateInput
          v-model="filterStartDate"
          label="Start Date"
          name="start_date"
        />
        <DateInput
          v-model="filterEndDate"
          label="End Date"
          name="end_date"
        />
        <div class="flex items-end">
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
            @click="fetchSummary"
          >
            Apply
          </button>
        </div>
      </div>
    </div>

    <LoadingSpinner v-if="loading" text="Loading summary..." />

    <template v-else-if="summaryData">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Total Expenses"
          :value="formatCurrency(totalExpenses(), auth.branchCurrency)"
          color="red"
          icon="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"
        />
        <StatCard
          title="Categories Used"
          :value="categoryCount()"
          color="amber"
          icon="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
        />
        <StatCard
          title="Top Category"
          :value="topCategory()"
          color="green"
          icon="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"
        />
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Expense Distribution</h3>
          <div id="expense-pie-chart" class="w-full h-80"></div>
          <p v-if="typeof echarts === 'undefined'" class="text-sm text-gray-500 dark:text-gray-400 text-center mt-4">
            Install ECharts to view charts
          </p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Expenses by Category</h3>
          <div id="expense-bar-chart" class="w-full h-80"></div>
          <p v-if="typeof echarts === 'undefined'" class="text-sm text-gray-500 dark:text-gray-400 text-center mt-4">
            Install ECharts to view charts
          </p>
        </div>
      </div>

      <!-- Category Table -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Category Breakdown</h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Category</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Total Amount</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Transactions</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">% of Total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="item in (summaryData.by_category || [])"
                :key="item.category || item.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                  {{ item.category_name || item.category || '—' }}
                </td>
                <td class="px-4 py-3 text-right text-sm font-medium text-gray-900 dark:text-white">
                  {{ formatCurrency(item.total, auth.branchCurrency) }}
                </td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">
                  {{ item.count || 0 }}
                </td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">
                  {{ totalExpenses() > 0 ? ((Number(item.total) || 0) / totalExpenses() * 100).toFixed(1) : 0 }}%
                </td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <td class="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white">Total</td>
                <td class="px-4 py-3 text-right text-sm font-bold text-gray-900 dark:text-white">
                  {{ formatCurrency(totalExpenses(), auth.branchCurrency) }}
                </td>
                <td class="px-4 py-3 text-right text-sm font-semibold text-gray-900 dark:text-white">
                  {{ (summaryData.by_category || []).reduce((s, i) => s + (i.count || 0), 0) }}
                </td>
                <td class="px-4 py-3 text-right text-sm font-semibold text-gray-900 dark:text-white">100%</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
