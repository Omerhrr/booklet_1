<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { getAnalysis, updateAnalysis, getSources, getSourceFields, queryAnalytics } from '@/api/analytics'

use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const saving = ref(false)
const querying = ref(false)

const form = ref({
  name: '',
  description: '',
  sourceId: '',
  selectedFields: [],
  filters: [],
  chartType: 'table',
})

const sourceOptions = ref([])
const fieldOptions = ref([])
const chartTypeOptions = [
  { value: 'table', label: 'Table' },
  { value: 'line', label: 'Line Chart' },
  { value: 'bar', label: 'Bar Chart' },
  { value: 'pie', label: 'Pie Chart' },
]
const operatorOptions = [
  { value: 'eq', label: 'Equals' },
  { value: 'neq', label: 'Not Equals' },
  { value: 'gt', label: 'Greater Than' },
  { value: 'lt', label: 'Less Than' },
  { value: 'contains', label: 'Contains' },
]

const results = ref([])
const tableColumns = ref([])
const chartOption = ref(null)

function addFilter() { form.value.filters.push({ field: '', operator: 'eq', value: '' }) }
function removeFilter(index) { form.value.filters.splice(index, 1) }

async function loadAnalysis() {
  loading.value = true
  try {
    const { data } = await getAnalysis(route.params.id)
    form.value = {
      name: data.name || '',
      description: data.description || '',
      sourceId: data.source_id || '',
      selectedFields: data.fields || [],
      filters: (data.filters || []).length > 0 ? data.filters : [{ field: '', operator: 'eq', value: '' }],
      chartType: data.chart_type || 'table',
    }
  } catch (error) {
    console.error('Failed to load analysis:', error)
  } finally {
    loading.value = false
  }
}

async function loadSources() {
  try {
    const { data } = await getSources()
    const items = Array.isArray(data) ? data : data.items || data.sources || []
    sourceOptions.value = items.map(s => ({ value: s.id || s.value, label: s.name || s.label }))
  } catch (error) {
    console.error('Failed to load sources:', error)
  }
}

async function loadFields() {
  if (!form.value.sourceId) { fieldOptions.value = []; return }
  try {
    const { data } = await getSourceFields(form.value.sourceId)
    const items = Array.isArray(data) ? data : data.items || data.fields || []
    fieldOptions.value = items.map(f => ({ value: f.key || f.name, label: f.label || f.name }))
  } catch (error) {
    console.error('Failed to load fields:', error)
  }
}

async function runQuery() {
  if (!form.value.sourceId || form.value.selectedFields.length === 0) return
  querying.value = true
  try {
    const { data } = await queryAnalytics({
      source_id: form.value.sourceId,
      fields: form.value.selectedFields,
      filters: form.value.filters.filter(f => f.field && f.value),
      chart_type: form.value.chartType,
    })
    results.value = Array.isArray(data) ? data : data.results || data.items || []
    tableColumns.value = form.value.selectedFields.map(f => ({ key: f, label: f, sortable: true }))
    buildChart()
  } catch (error) {
    console.error('Query failed:', error)
  } finally {
    querying.value = false
  }
}

function buildChart() {
  if (form.value.chartType === 'table' || results.value.length === 0) { chartOption.value = null; return }
  const f0 = form.value.selectedFields[0]
  if (form.value.chartType === 'pie') {
    chartOption.value = { tooltip: { trigger: 'item' }, series: [{ type: 'pie', radius: ['40%', '70%'], data: results.value.map(r => ({ name: r[f0], value: Number(r[form.value.selectedFields[1]]) || 1 })) }] }
  } else {
    chartOption.value = {
      tooltip: { trigger: 'axis' }, grid: { containLabel: true },
      xAxis: { type: 'category', data: results.value.map(r => r[f0]), axisLabel: { color: '#9ca3af' } },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' } },
      series: form.value.selectedFields.slice(1).map(f => ({ name: f, type: form.value.chartType, data: results.value.map(r => Number(r[f]) || 0), smooth: true })),
      backgroundColor: 'transparent',
    }
  }
}

async function handleSubmit() {
  if (!form.value.name || !form.value.sourceId || form.value.selectedFields.length === 0) return
  saving.value = true
  try {
    await updateAnalysis(route.params.id, {
      name: form.value.name,
      description: form.value.description,
      source_id: form.value.sourceId,
      fields: form.value.selectedFields,
      filters: form.value.filters.filter(f => f.field && f.value),
      chart_type: form.value.chartType,
    })
    router.push({ name: 'AnalysisView', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update analysis:', error)
  } finally {
    saving.value = false
  }
}

watch(() => form.value.sourceId, () => {
  form.value.selectedFields = []
  form.value.filters = []
  results.value = []
  chartOption.value = null
  loadFields()
})

onMounted(async () => {
  await Promise.all([loadSources(), loadAnalysis()])
  if (form.value.sourceId) await loadFields()
  if (form.value.selectedFields.length > 0) await runQuery()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Edit Analysis" :breadcrumbs="[{ text: 'Analytics', to: { name: 'AnalyticsHub' } }, { text: 'Analyses', to: { name: 'SavedAnalyses' } }, { text: 'Edit' }]" />

    <LoadingSpinner v-if="loading" size="lg" text="Loading..." />

    <template v-else>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-1 space-y-5">
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
            <TextInput v-model="form.name" label="Name" name="name" required />
            <TextareaInput v-model="form.description" label="Description" name="description" />
            <SelectInput v-model="form.sourceId" label="Data Source" name="source" :options="sourceOptions" required />
            <SelectInput v-model="form.chartType" label="Chart Type" name="chart_type" :options="chartTypeOptions" />
            <SelectInput v-model="form.selectedFields" label="Fields" name="fields" :options="fieldOptions" placeholder="Select fields..." multiple required />
          </div>

          <!-- Filters -->
          <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Filters</span>
              <button type="button" class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300" @click="addFilter">+ Add</button>
            </div>
            <div v-for="(filter, index) in form.filters" :key="index" class="flex gap-2 mb-2">
              <select v-model="filter.field" class="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 px-2 py-1.5 text-gray-700 dark:text-gray-300">
                <option value="">Field</option>
                <option v-for="fo in fieldOptions" :key="fo.value" :value="fo.value">{{ fo.label }}</option>
              </select>
              <select v-model="filter.operator" class="w-24 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 px-2 py-1.5 text-gray-700 dark:text-gray-300">
                <option v-for="op in operatorOptions" :key="op.value" :value="op.value">{{ op.label }}</option>
              </select>
              <input v-model="filter.value" type="text" placeholder="Value" class="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 px-2 py-1.5 text-gray-700 dark:text-gray-300" />
              <button type="button" class="text-red-400 hover:text-red-600 text-xs" @click="removeFilter(index)">&times;</button>
            </div>
            <button type="button" class="w-full px-3 py-2 text-xs font-medium text-gray-700 bg-gray-100 dark:bg-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors" @click="runQuery" :disabled="!form.sourceId || form.selectedFields.length === 0">Preview</button>
          </div>

          <div class="flex gap-3">
            <button type="button" class="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 transition-colors" @click="router.back()">Cancel</button>
            <button type="button" class="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors" :disabled="!form.name || !form.sourceId || form.selectedFields.length === 0 || saving" @click="handleSubmit">{{ saving ? 'Saving...' : 'Update' }}</button>
          </div>
        </div>

        <div class="lg:col-span-2 space-y-5">
          <LoadingSpinner v-if="querying" size="lg" text="Running query..." />
          <template v-else-if="results.length > 0">
            <div v-if="form.chartType !== 'table' && chartOption" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <v-chart :option="chartOption" style="height: 400px" autoresize />
            </div>
            <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
              <DataTable :columns="tableColumns" :data="results" :loading="false" :searchable="true" empty-message="No results" />
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>
