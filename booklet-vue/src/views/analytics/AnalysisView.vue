<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Badge from '@/components/common/Badge.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { getAnalysis, deleteAnalysis, toggleAnalysisFavorite, queryAnalytics } from '@/api/analytics'
import { formatDate } from '@/utils/dates'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const analysis = ref(null)
const results = ref([])
const tableColumns = ref([])
const chartOption = ref(null)
const deleteDialog = ref(false)

async function fetchAnalysis() {
  loading.value = true
  try {
    const { data } = await getAnalysis(route.params.id)
    analysis.value = data
    if (data.fields && data.fields.length > 0) {
      await loadResults()
    }
  } catch (error) {
    console.error('Failed to fetch analysis:', error)
  } finally {
    loading.value = false
  }
}

async function loadResults() {
  if (!analysis.value) return
  try {
    const { data } = await queryAnalytics({
      source_id: analysis.value.source_id,
      fields: analysis.value.fields,
      filters: analysis.value.filters || [],
      chart_type: analysis.value.chart_type,
    })
    results.value = Array.isArray(data) ? data : data.results || data.items || []
    tableColumns.value = (analysis.value.fields || []).map(f => ({
      key: f, label: f, sortable: true,
    }))
    buildChart()
  } catch (error) {
    console.error('Failed to load results:', error)
  }
}

function buildChart() {
  if (analysis.value.chart_type === 'table' || results.value.length === 0) { chartOption.value = null; return }
  const fields = analysis.value.fields || []
  const f0 = fields[0]
  const f1 = fields[1]
  if (analysis.value.chart_type === 'pie') {
    chartOption.value = {
      tooltip: { trigger: 'item' },
      legend: { type: 'scroll', bottom: 0, textStyle: { color: '#9ca3af' } },
      series: [{ type: 'pie', radius: ['40%', '70%'], data: results.value.map(r => ({ name: r[f0], value: f1 ? Number(r[f1]) : 1 })) }],
    }
  } else {
    chartOption.value = {
      tooltip: { trigger: 'axis' },
      legend: { textStyle: { color: '#9ca3af' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: results.value.map(r => r[f0]), axisLabel: { color: '#9ca3af' } },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' } },
      series: fields.slice(1).map(f => ({ name: f, type: analysis.value.chart_type, data: results.value.map(r => Number(r[f]) || 0), smooth: true })),
      backgroundColor: 'transparent',
    }
  }
}

function editAnalysis() {
  router.push({ name: 'AnalysisEdit', params: { id: route.params.id } })
}

async function handleDelete() {
  try {
    await deleteAnalysis(route.params.id)
    router.push({ name: 'SavedAnalyses' })
  } catch (error) {
    console.error('Failed to delete analysis:', error)
  }
}

async function toggleFavorite() {
  try {
    await toggleAnalysisFavorite(route.params.id)
    analysis.value.is_favorite = !analysis.value.is_favorite
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
  }
}

onMounted(() => { fetchAnalysis() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      :title="analysis?.name || 'Analysis'"
      :subtitle="analysis?.description || ''"
      :breadcrumbs="[
        { text: 'Analytics', to: { name: 'AnalyticsHub' } },
        { text: 'Analyses', to: { name: 'SavedAnalyses' } },
        { text: analysis?.name || 'View' },
      ]"
    >
      <template #actions>
        <div v-if="analysis" class="flex items-center gap-2">
          <button type="button" class="p-2 rounded-lg transition-colors" :class="analysis.is_favorite ? 'text-amber-400 hover:text-amber-500' : 'text-gray-400 hover:text-amber-400'" @click="toggleFavorite">
            <svg class="w-5 h-5" :class="{ 'fill-amber-400': analysis.is_favorite }" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
          </button>
          <button type="button" class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors" @click="editAnalysis">
            Edit
          </button>
          <button type="button" class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 bg-white border border-gray-300 rounded-lg hover:bg-red-50 dark:bg-gray-700 dark:text-red-400 dark:border-gray-600 dark:hover:bg-red-900/20 transition-colors" @click="deleteDialog = true">
            Delete
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" size="lg" text="Loading analysis..." />

    <template v-else-if="analysis">
      <!-- Meta -->
      <div class="flex flex-wrap gap-4 text-sm text-gray-500 dark:text-gray-400">
        <div class="flex items-center gap-1.5">
          <span class="font-medium">Source:</span>
          <Badge :text="analysis.data_source || 'N/A'" variant="info" size="sm" />
        </div>
        <div class="flex items-center gap-1.5">
          <span class="font-medium">Chart:</span>
          <Badge :text="analysis.chart_type" variant="default" size="sm" />
        </div>
        <div v-if="analysis.created_at" class="flex items-center gap-1.5">
          <span class="font-medium">Created:</span>
          <span>{{ formatDate(analysis.created_at, 'short') }}</span>
        </div>
        <div v-if="analysis.updated_at" class="flex items-center gap-1.5">
          <span class="font-medium">Updated:</span>
          <span>{{ formatDate(analysis.updated_at, 'short') }}</span>
        </div>
      </div>

      <!-- Chart -->
      <div v-if="chartOption" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <v-chart :option="chartOption" style="height: 400px" autoresize />
      </div>

      <!-- Table -->
      <div v-if="results.length > 0" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <DataTable :columns="tableColumns" :data="results" :loading="false" :searchable="true" empty-message="No results" />
      </div>
    </template>

    <ConfirmDialog
      :show="deleteDialog"
      title="Delete Analysis"
      message="Are you sure you want to delete this analysis? This action cannot be undone."
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
      @update:show="deleteDialog = $event"
    />
  </div>
</template>
