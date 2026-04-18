<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import Badge from '@/components/common/Badge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { getDashboard, deleteDashboard, queryAnalytics } from '@/api/analytics'
import { formatDate } from '@/utils/dates'

use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const dashboard = ref(null)
const analysisCards = ref([])
const deleteDialog = ref(false)

async function fetchDashboard() {
  loading.value = true
  try {
    const { data } = await getDashboard(route.params.id)
    dashboard.value = data
    const analyses = data.analyses || []
    const cards = []
    for (const analysis of analyses) {
      try {
        const { data: results } = await queryAnalytics({
          source_id: analysis.source_id,
          fields: analysis.fields,
          filters: analysis.filters || [],
          chart_type: analysis.chart_type,
        })
        const items = Array.isArray(results) ? results : results.results || results.items || []
        cards.push({
          id: analysis.id,
          name: analysis.name,
          chart_type: analysis.chart_type,
          data: items,
          fields: analysis.fields || [],
          chartOption: buildChartOption(analysis.chart_type, items, analysis.fields || []),
        })
      } catch (e) {
        cards.push({ id: analysis.id, name: analysis.name, chart_type: analysis.chart_type, data: [], fields: [], chartOption: null })
      }
    }
    analysisCards.value = cards
  } catch (error) {
    console.error('Failed to fetch dashboard:', error)
  } finally {
    loading.value = false
  }
}

function buildChartOption(chartType, data, fields) {
  if (chartType === 'table' || data.length === 0 || fields.length === 0) return null
  const f0 = fields[0]
  const f1 = fields[1]
  if (chartType === 'pie') {
    return {
      tooltip: { trigger: 'item' },
      legend: { type: 'scroll', bottom: 0, textStyle: { color: '#9ca3af', fontSize: 11 } },
      series: [{ type: 'pie', radius: ['35%', '65%'], data: data.map(r => ({ name: r[f0], value: f1 ? Number(r[f1]) : 1 })), label: { fontSize: 10 } }],
      backgroundColor: 'transparent',
    }
  }
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: data.map(r => r[f0]), axisLabel: { color: '#9ca3af', fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { color: '#9ca3af', fontSize: 10 } },
    series: fields.slice(1).map(f => ({ name: f, type: chartType, data: data.map(r => Number(r[f]) || 0), smooth: true })),
    backgroundColor: 'transparent',
  }
}

function editDashboard() {
  router.push({ name: 'DashboardEdit', params: { id: route.params.id } })
}

async function handleDelete() {
  try {
    await deleteDashboard(route.params.id)
    router.push({ name: 'DashboardList' })
  } catch (error) {
    console.error('Failed to delete dashboard:', error)
  }
}

onMounted(() => { fetchDashboard() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      :title="dashboard?.name || 'Dashboard'"
      :subtitle="dashboard?.description || ''"
      :breadcrumbs="[
        { text: 'Analytics', to: { name: 'AnalyticsHub' } },
        { text: 'Dashboards', to: { name: 'DashboardList' } },
        { text: dashboard?.name || 'View' },
      ]"
    >
      <template #actions>
        <div v-if="dashboard" class="flex items-center gap-2">
          <button type="button" class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors" @click="editDashboard">
            Edit
          </button>
          <button type="button" class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 bg-white border border-gray-300 rounded-lg hover:bg-red-50 dark:bg-gray-700 dark:text-red-400 dark:border-gray-600 dark:hover:bg-red-900/20 transition-colors" @click="deleteDialog = true">
            Delete
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" size="lg" text="Loading dashboard..." />

    <template v-else-if="dashboard">
      <EmptyState v-if="analysisCards.length === 0" title="Empty Dashboard" message="This dashboard has no analyses yet. Edit the dashboard to add analyses.">
        <button type="button" class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 transition-colors" @click="editDashboard">
          Edit Dashboard
        </button>
      </EmptyState>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div
          v-for="card in analysisCards"
          :key="card.id"
          class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5"
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-gray-900 dark:text-white">{{ card.name }}</h3>
            <Badge :text="card.chart_type" variant="info" size="sm" />
          </div>

          <!-- Chart Visualization -->
          <div v-if="card.chartOption" class="mb-3">
            <v-chart :option="card.chartOption" style="height: 250px" autoresize />
          </div>

          <!-- Table fallback -->
          <div v-else-if="card.data.length > 0" class="overflow-x-auto max-h-64">
            <table class="min-w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 dark:border-gray-700">
                  <th v-for="field in card.fields" :key="field" class="px-2 py-1 text-left text-xs font-medium text-gray-500 dark:text-gray-400">{{ field }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in card.data.slice(0, 5)" :key="idx" class="border-b border-gray-100 dark:border-gray-800">
                  <td v-for="field in card.fields" :key="field" class="px-2 py-1 text-xs text-gray-700 dark:text-gray-300">{{ row[field] }}</td>
                </tr>
              </tbody>
            </table>
            <p v-if="card.data.length > 5" class="mt-2 text-xs text-gray-400">Showing 5 of {{ card.data.length }} rows</p>
          </div>

          <p v-else class="text-sm text-gray-400 dark:text-gray-500 text-center py-6">No data available</p>
        </div>
      </div>
    </template>

    <ConfirmDialog
      :show="deleteDialog"
      title="Delete Dashboard"
      message="Are you sure you want to delete this dashboard? This action cannot be undone."
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
      @update:show="deleteDialog = $event"
    />
  </div>
</template>
