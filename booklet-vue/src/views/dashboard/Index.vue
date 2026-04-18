<script setup>
import { ref, computed, onMounted, onUnmounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { getStats, getSalesChart, getExpenseChart, getFull } from '@/api/dashboard'
import { formatCurrency } from '@/utils/currency'
import { formatRelative, formatDate } from '@/utils/dates'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const isDark = computed(() => themeStore.isDark)

const loading = ref(true)
const chartsLoading = ref(false)

const stats = ref(null)
const recentTransactions = ref([])
const salesChartData = ref({ labels: [], values: [] })
const expenseChartData = ref({ labels: [], values: [] })
const topProducts = ref([])
const topCustomers = ref([])

const salesPeriod = ref(30)
const expensePeriod = ref(30)

const currency = computed(() => authStore.branchCurrency || 'USD')

const salesChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderColor: '#e5e7eb',
    borderWidth: 1,
    textStyle: { color: '#374151', fontSize: 13 },
    formatter: (params) => {
      const date = params[0].axisValue
      const val = params[0].value
      return `<strong>${date}</strong><br/>${formatCurrency(val, currency.value)}`
    },
  },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: salesChartData.value.labels || [],
    axisLine: { lineStyle: { color: '#8b5cf6' } },
    axisLabel: {
      color: '#9ca3af',
      fontSize: 11,
      formatter: (value) => {
        try {
          const d = new Date(value)
          return `${d.getMonth() + 1}/${d.getDate()}`
        } catch {
          return value
        }
      },
    },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      color: '#9ca3af',
      fontSize: 11,
      formatter: (v) => formatCompact(v),
    },
    splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
  },
  series: [
    {
      data: salesChartData.value.values || [],
      type: 'line',
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
            { offset: 1, color: 'rgba(139, 92, 246, 0.02)' },
          ],
        },
      },
      lineStyle: { color: '#8b5cf6', width: 2.5 },
      itemStyle: { color: '#8b5cf6' },
      symbol: 'circle',
      symbolSize: 6,
      showSymbol: false,
    },
  ],
}))

const expenseChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderColor: '#e5e7eb',
    borderWidth: 1,
    textStyle: { color: '#374151', fontSize: 13 },
    formatter: (params) => {
      const date = params[0].axisValue
      const val = params[0].value
      return `<strong>${date}</strong><br/>${formatCurrency(val, currency.value)}`
    },
  },
  grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
  xAxis: {
    type: 'category',
    data: expenseChartData.value.labels || [],
    axisLine: { lineStyle: { color: '#f59e0b' } },
    axisLabel: {
      color: '#9ca3af',
      fontSize: 11,
      formatter: (value) => {
        try {
          const d = new Date(value)
          return `${d.getMonth() + 1}/${d.getDate()}`
        } catch {
          return value
        }
      },
    },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      color: '#9ca3af',
      fontSize: 11,
      formatter: (v) => formatCompact(v),
    },
    splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
  },
  series: [
    {
      data: expenseChartData.value.values || [],
      type: 'bar',
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#f59e0b' },
            { offset: 1, color: '#fbbf24' },
          ],
        },
        borderRadius: [4, 4, 0, 0],
      },
      barMaxWidth: 24,
    },
  ],
}))

function formatCompact(value) {
  if (value >= 1000000000) return (value / 1000000000).toFixed(1) + 'B'
  if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'
  if (value >= 1000) return (value / 1000).toFixed(1) + 'K'
  return String(value)
}

function formatGrowth(value) {
  if (value > 0) return `+${Number(value).toFixed(1)}%`
  if (value < 0) return `${Number(value).toFixed(1)}%`
  return '0%'
}

function txStatusBadge(status) {
  if (!status) return { text: 'Pending', variant: 'default' }
  const s = status.toLowerCase()
  if (['paid'].includes(s)) return { text: status, variant: 'success' }
  if (['partial', 'partially_paid'].includes(s)) return { text: status, variant: 'warning' }
  if (['overdue', 'cancelled'].includes(s)) return { text: status, variant: 'danger' }
  return { text: status, variant: 'default' }
}

function txTypeBadge(type) {
  if (!type) return { text: 'Other', classes: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' }
  const t = type.toLowerCase()
  if (t.includes('sales') || t.includes('invoice'))
    return { text: type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), classes: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' }
  if (t.includes('purchase') || t.includes('bill'))
    return { text: type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), classes: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400' }
  if (t.includes('expense'))
    return { text: type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), classes: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' }
  return { text: type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), classes: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300' }
}

async function fetchDashboardData() {
  loading.value = true
  try {
    const [statsRes, fullRes] = await Promise.allSettled([
      getStats(),
      getFull().catch(() => null),
    ])

    if (statsRes.status === 'fulfilled') {
      stats.value = statsRes.value.data
    }
    if (fullRes.status === 'fulfilled' && fullRes.value) {
      const full = fullRes.value.data
      if (!stats.value && full.stats) {
        stats.value = full.stats
      }
      if (full.recent_transactions) {
        recentTransactions.value = full.recent_transactions.slice(0, 10)
      }
      if (full.sales_chart) {
        salesChartData.value = full.sales_chart
      }
      if (full.expense_chart) {
        expenseChartData.value = full.expense_chart
      }
      if (full.top_products) {
        topProducts.value = full.top_products
      }
      if (full.top_customers) {
        topCustomers.value = full.top_customers
      }
    }
  } catch (err) {
    console.error('Failed to load dashboard:', err)
  } finally {
    loading.value = false
  }
}

async function fetchSalesChart(days) {
  try {
    const { data } = await getSalesChart(days)
    salesChartData.value = data
  } catch (err) {
    console.error('Failed to load sales chart:', err)
  }
}

async function fetchExpenseChart(days) {
  try {
    const { data } = await getExpenseChart(days)
    expenseChartData.value = data
  } catch (err) {
    console.error('Failed to load expense chart:', err)
  }
}

function onSalesPeriodChange() {
  fetchSalesChart(salesPeriod.value)
}

function onExpensePeriodChange() {
  fetchExpenseChart(expensePeriod.value)
}

let resizeTimer = null
function handleResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    window.dispatchEvent(new Event('resize'))
  }, 150)
}

onMounted(() => {
  fetchDashboardData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div>
    <PageHeader
      title="Dashboard"
      subtitle="Overview of your business performance"
    />

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <div
          v-for="i in 8"
          :key="i"
          class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
            <div class="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          </div>
          <div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-2"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
        </div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4"></div>
          <div class="h-64 bg-gray-100 dark:bg-gray-700 rounded-xl"></div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4"></div>
          <div class="h-64 bg-gray-100 dark:bg-gray-700 rounded-xl"></div>
        </div>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-36 mb-4"></div>
          <div class="space-y-3">
            <div v-for="i in 3" :key="i" class="h-14 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
          </div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
          <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-36 mb-4"></div>
          <div class="space-y-3">
            <div v-for="i in 3" :key="i" class="h-14 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
          </div>
        </div>
        <div class="space-y-6">
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
            <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-4"></div>
            <div class="space-y-2">
              <div v-for="i in 3" :key="i" class="h-12 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
            </div>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
            <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-28 mb-4"></div>
            <div class="grid grid-cols-2 gap-3">
              <div v-for="i in 4" :key="i" class="h-16 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
        <div class="h-6 bg-gray-200 dark:bg-gray-700 rounded w-44 mb-4"></div>
        <div class="space-y-3">
          <div v-for="i in 5" :key="i" class="h-10 bg-gray-100 dark:bg-gray-700 rounded-lg"></div>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-6">

      <!-- ═══ Stats Cards Row 1 ═══ -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <!-- Total Sales -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd"/>
                </svg>
              </div>
              <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Total Sales</p>
            </div>
            <span
              v-if="stats"
              :class="[
                'text-xs px-2 py-1 rounded-full',
                (stats.sales_growth || 0) >= 0
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
              ]"
            >
              {{ formatGrowth(stats.sales_growth || 0) }}
            </span>
          </div>
          <p class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white break-words">
            {{ formatCurrency(stats?.total_sales || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ stats?.invoices_count || 0 }} invoices this month</p>
        </div>

        <!-- Total Purchases -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 1a1 1 0 000 2h1.22l.305 1.222a.997.997 0 00.01.042l1.358 5.43-.893.892C3.74 11.846 4.632 14 6.414 14H15a1 1 0 000-2H6.414l1-1H14a1 1 0 00.894-.553l3-6A1 1 0 0017 3H6.28l-.31-1.243A1 1 0 005 1H3z"/>
                </svg>
              </div>
              <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Total Purchases</p>
            </div>
            <span
              v-if="stats"
              :class="[
                'text-xs px-2 py-1 rounded-full',
                (stats.purchases_growth || 0) >= 0
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                  : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
              ]"
            >
              {{ formatGrowth(stats.purchases_growth || 0) }}
            </span>
          </div>
          <p class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white break-words">
            {{ formatCurrency(stats?.total_purchases || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ stats?.bills_count || 0 }} bills this month</p>
        </div>

        <!-- Gross Profit -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-emerald-100 dark:bg-emerald-900 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
              </svg>
            </div>
            <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Gross Profit</p>
          </div>
          <p
            :class="[
              'text-xl md:text-2xl font-bold break-words',
              (stats?.gross_profit || 0) >= 0
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-red-600 dark:text-red-400',
            ]"
          >
            {{ formatCurrency(stats?.gross_profit || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ Number(stats?.gross_profit_margin || 0).toFixed(1) }}% margin</p>
        </div>

        <!-- Cash Balance -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/>
                <path fill-rule="evenodd" d="M2 8v6a2 2 0 002 2h12a2 2 0 002-2V8H2zm2 2a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/>
              </svg>
            </div>
            <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Cash Balance</p>
          </div>
          <p class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white break-words">
            {{ formatCurrency(stats?.cash_balance || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Available funds</p>
        </div>
      </div>

      <!-- ═══ Stats Cards Row 2 ═══ -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        <!-- Total Expenses -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-red-600 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clip-rule="evenodd"/>
                </svg>
              </div>
              <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Total Expenses</p>
            </div>
            <span
              v-if="stats"
              :class="[
                'text-xs px-2 py-1 rounded-full',
                (stats.expenses_growth || 0) > 0
                  ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                  : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
              ]"
            >
              {{ formatGrowth(stats.expenses_growth || 0) }}
            </span>
          </div>
          <p class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white break-words">
            {{ formatCurrency(stats?.total_expenses || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">This month</p>
        </div>

        <!-- Net Profit -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-indigo-100 dark:bg-indigo-900 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
              </svg>
            </div>
            <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Net Profit</p>
          </div>
          <p
            :class="[
              'text-xl md:text-2xl font-bold break-words',
              (stats?.net_profit || 0) >= 0
                ? 'text-indigo-600 dark:text-indigo-400'
                : 'text-red-600 dark:text-red-400',
            ]"
          >
            {{ formatCurrency(stats?.net_profit || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ Number(stats?.net_profit_margin || 0).toFixed(1) }}% margin</p>
        </div>

        <!-- Accounts Receivable -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-yellow-100 dark:bg-yellow-900 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-yellow-600 dark:text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
              </svg>
            </div>
            <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Accounts Receivable</p>
          </div>
          <p class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white break-words">
            {{ formatCurrency(stats?.total_receivables || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {{ stats?.total_customers || 0 }} customers
            <span v-if="stats?.overdue_invoices && stats.overdue_invoices > 0" class="text-red-500">
              ({{ stats.overdue_invoices }} overdue)
            </span>
          </p>
        </div>

        <!-- Accounts Payable -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 md:p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-8 h-8 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-orange-600 dark:text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
              </svg>
            </div>
            <p class="text-xs md:text-sm font-medium text-gray-500 dark:text-gray-400">Accounts Payable</p>
          </div>
          <p class="text-xl md:text-2xl font-bold text-gray-900 dark:text-white break-words">
            {{ formatCurrency(stats?.total_payables || 0, currency) }}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ stats?.total_vendors || 0 }} vendors</p>
        </div>
      </div>

      <!-- ═══ Charts ═══ -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Sales Chart -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Sales Overview</h3>
            <select
              v-model="salesPeriod"
              @change="onSalesPeriodChange"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              <option :value="7">Last 7 days</option>
              <option :value="30">Last 30 days</option>
              <option :value="90">Last 90 days</option>
            </select>
          </div>
          <div style="height: 280px;">
            <v-chart
              v-if="salesChartData.labels && salesChartData.labels.length > 0"
              :option="salesChartOption"
              autoresize
              class="w-full h-full"
            />
            <div v-else class="flex items-center justify-center h-full">
              <div class="text-center text-gray-400 dark:text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
                <p class="text-sm">No sales data yet</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Expense Chart -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Expenses Overview</h3>
            <select
              v-model="expensePeriod"
              @change="onExpensePeriodChange"
              class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              <option :value="7">Last 7 days</option>
              <option :value="30">Last 30 days</option>
              <option :value="90">Last 90 days</option>
            </select>
          </div>
          <div style="height: 280px;">
            <v-chart
              v-if="expenseChartData.labels && expenseChartData.labels.length > 0"
              :option="expenseChartOption"
              autoresize
              class="w-full h-full"
            />
            <div v-else class="flex items-center justify-center h-full">
              <div class="text-center text-gray-400 dark:text-gray-500">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
                <p class="text-sm">No expense data yet</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ Additional Metrics Row ═══ -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Top Selling Products -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Selling Products</h3>
          <div class="space-y-3">
            <template v-if="topProducts.length > 0">
              <div
                v-for="product in topProducts"
                :key="product.id || product.sku"
                class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-xl"
              >
                <div>
                  <p class="font-medium text-gray-900 dark:text-white text-sm">{{ product.name }}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{{ product.sku || 'N/A' }}</p>
                </div>
                <div class="text-right">
                  <p class="font-medium text-gray-900 dark:text-white text-sm">{{ formatCurrency(product.revenue || 0, currency) }}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{{ product.quantity }} sold</p>
                </div>
              </div>
            </template>
            <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
              <svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"/>
              </svg>
              <p class="text-sm">No sales data yet</p>
            </div>
          </div>
        </div>

        <!-- Top Customers -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Top Customers</h3>
          <div class="space-y-3">
            <template v-if="topCustomers.length > 0">
              <div
                v-for="customer in topCustomers"
                :key="customer.id || customer.name"
                class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-xl"
              >
                <div>
                  <p class="font-medium text-gray-900 dark:text-white text-sm">{{ customer.name }}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{{ customer.invoice_count }} invoices</p>
                </div>
                <div class="text-right">
                  <p class="font-medium text-gray-900 dark:text-white text-sm">{{ formatCurrency(customer.total_purchases || 0, currency) }}</p>
                </div>
              </div>
            </template>
            <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
              <svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
              </svg>
              <p class="text-sm">No customer data yet</p>
            </div>
          </div>
        </div>

        <!-- Quick Actions & At a Glance -->
        <div class="space-y-6">
          <!-- Quick Actions -->
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
            <div class="space-y-2">
              <router-link
                to="/sales/invoices/new"
                class="flex items-center p-3 bg-primary-50 dark:bg-blue-900 rounded-xl hover:bg-primary-100 dark:hover:bg-blue-800 transition"
              >
                <div class="w-8 h-8 bg-primary-100 dark:bg-blue-800 rounded-lg flex items-center justify-center">
                  <svg class="w-4 h-4 text-primary-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <span class="ml-3 font-medium text-gray-700 dark:text-gray-300 text-sm">New Sales Invoice</span>
              </router-link>

              <router-link
                to="/purchases/bills/new"
                class="flex items-center p-3 bg-blue-50 dark:bg-indigo-900 rounded-xl hover:bg-blue-100 dark:hover:bg-indigo-800 transition"
              >
                <div class="w-8 h-8 bg-blue-100 dark:bg-indigo-800 rounded-lg flex items-center justify-center">
                  <svg class="w-4 h-4 text-blue-600 dark:text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <span class="ml-3 font-medium text-gray-700 dark:text-gray-300 text-sm">New Purchase Bill</span>
              </router-link>

              <router-link
                to="/inventory/products"
                class="flex items-center p-3 bg-green-50 dark:bg-emerald-900 rounded-xl hover:bg-green-100 dark:hover:bg-emerald-800 transition"
              >
                <div class="w-8 h-8 bg-green-100 dark:bg-emerald-800 rounded-lg flex items-center justify-center">
                  <svg class="w-4 h-4 text-green-600 dark:text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"/>
                  </svg>
                </div>
                <span class="ml-3 font-medium text-gray-700 dark:text-gray-300 text-sm">Manage Inventory</span>
              </router-link>
            </div>
          </div>

          <!-- At a Glance -->
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">At a Glance</h3>
            <div class="grid grid-cols-2 gap-3">
              <div class="bg-gray-50 dark:bg-gray-700 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats?.total_products || 0 }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">Products</p>
              </div>
              <div class="bg-gray-50 dark:bg-gray-700 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats?.total_employees || 0 }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">Employees</p>
              </div>
              <div class="bg-yellow-50 dark:bg-yellow-900 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{{ stats?.low_stock_products || 0 }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">Low Stock</p>
              </div>
              <div class="bg-gray-50 dark:bg-gray-700 rounded-xl p-3 text-center">
                <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ formatCurrency(stats?.total_other_income || 0, currency) }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">Other Income</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ Recent Transactions ═══ -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Transactions</h3>
          <a href="#" class="text-sm text-primary-600 dark:text-primary-400 hover:underline">View All</a>
        </div>
        <div class="overflow-x-auto">
          <table v-if="recentTransactions.length > 0" class="w-full">
            <thead>
              <tr class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <th class="pb-3">Type</th>
                <th class="pb-3">Number</th>
                <th class="pb-3">Party</th>
                <th class="pb-3">Date</th>
                <th class="pb-3 text-right">Amount</th>
                <th class="pb-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="tx in recentTransactions"
                :key="tx.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-700/50"
              >
                <td class="py-3">
                  <span :class="['inline-flex items-center px-2 py-1 rounded-full text-xs font-medium', txTypeBadge(tx.type).classes]">
                    {{ txTypeBadge(tx.type).text }}
                  </span>
                </td>
                <td class="py-3 text-sm text-gray-900 dark:text-white font-medium">{{ tx.number || '—' }}</td>
                <td class="py-3 text-sm text-gray-600 dark:text-gray-400">{{ tx.party || '—' }}</td>
                <td class="py-3 text-sm text-gray-600 dark:text-gray-400">{{ tx.date || formatDate(tx.created_at, 'short') }}</td>
                <td class="py-3 text-sm text-gray-900 dark:text-white font-medium text-right">{{ formatCurrency(tx.amount || tx.total || 0, currency) }}</td>
                <td class="py-3 text-right">
                  <span :class="['inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                    txStatusBadge(tx.status).variant === 'success' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' :
                    txStatusBadge(tx.status).variant === 'warning' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400' :
                    txStatusBadge(tx.status).variant === 'danger' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400' :
                    'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300']">
                    {{ tx.status ? tx.status.replace(/\b\w/g, c => c.toUpperCase()) : 'Pending' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
            <svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/>
              <path fill-rule="evenodd" d="M2 8v6a2 2 0 002 2h12a2 2 0 002-2V8H2zm2 2a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/>
            </svg>
            <p>No recent transactions</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
