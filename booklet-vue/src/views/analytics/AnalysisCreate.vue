<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { getSources, getSourceFields, queryAnalytics, createAnalysis } from '@/api/analytics'

use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()
const saving = ref(false)
const querying = ref(false)

const sources = ref([])
const fields = ref([])
const results = ref([])
const tableColumns = ref([])
const chartOption = ref(null)

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
  { value: 'gte', label: 'Greater or Equal' },
  { value: 'lt', label: 'Less Than' },
  { value: 'lte', label: 'Less or Equal' },
  { value: 'contains', label: 'Contains' },
]

function addFilter() {
  form.value.filters.push({ field: '', operator: 'eq', value: '' })
}

function removeFilter(index) {
  form.value.filters.splice(index, 1)
}

function updateFilterField(index, fieldKey) {
  form.value.filters[index].field = fieldKey
}

async function loadSources() {
  try {
    const { data } = await getSources()
    sources.value = Array.isArray(data) ? data : data.items || data.sources || []
    sourceOptions.value = sources.value.map(s => ({ value: s.id || s.value, label: s.name || s.label }))
  } catch (error) {
    console.error('Failed to load sources:', error)
  }
}

async function loadFields() {
  if (!form.value.sourceId) { fieldOptions.value = []; fields.value = []; return }
  try {
    const { data } = await getSourceFields(form.value.sourceId)
    fields.value = Array.isArray(data) ? data : data.items || data.fields || []
    fieldOptions.value = fields.value.map(f => ({ value: f.key || f.name, label: f.label || f.name }))
  } catch (error) {
    console.error('Failed to load fields:', error)
  }
}

async function runQuery() {
  if (!form.value.sourceId || form.value.selectedFields.length === 0) return
  querying.value = true
  try {
    const payload = {
      source_id: form.value.sourceId,
      fields: form.value.selectedFields,
      filters: form.value.filters.filter(f => f.field && f.value),
      chart_type: form.value.chartType,
    }
    const { data } = await queryAnalytics(payload)
    results.value = Array.isArray(data) ? data : data.results || data.items || []
    tableColumns.value = form.value.selectedFields.map(f => {
      const fd = fields.value.find(x => (x.key || x.name) === f)
      return { key: f, label: fd?.label || fd?.name || f, sortable: true }
    })
    buildChart()
  } catch (error) {
    console.error('Query failed:', error)
    results.value = []
  } finally {
    querying.value = false
  }
}

function buildChart() {
  if (form.value.chartType === 'table' || results.value.length === 0) { chartOption.value = null; return }
  const f0 = form.value.selectedFields[0]
  const f1 = form.value.selectedFields[1]
  if (form.value.chartType === 'pie') {
    chartOption.value = {
      tooltip: { trigger: 'item' },
      legend: { type: 'scroll', bottom: 0, textStyle: { color: '#9ca3af' } },
      series: [{ type: 'pie', radius: ['40%', '70%'], data: results.value.map(r => ({ name: r[f0], value: f1 ? Number(r[f1]) : 1 })), backgroundColor: 'transparent' }],
    }
  } else {
    chartOption.value = {
      tooltip: { trigger: 'axis' },
      legend: { textStyle: { color: '#9ca3af' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
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
    await createAnalysis({
      name: form.value.name,
      description: form.value.description,
      source_id: form.value.sourceId,
      fields: form.value.selectedFields,
      filters: form.value.filters.filter(f => f.field && f.value),
      chart_type: form.value.chartType,
    })
    router.push({ name: 'SavedAnalyses' })
  } catch (error) {
    console.error('Failed to create analysis:', error)
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

onMounted(() => { loadSources() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="New Analysis" subtitle="Create a new data analysis" :breadcrumbs="[{ text: 'Analytics', to: { name: 'AnalyticsHub' } }, { text: 'New Analysis' }]" />

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left: Configuration -->
      <div class="lg:col-span-1 space-y-5">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
          <TextInput v-model="form.name" label="Analysis Name" name="name" placeholder="e.g., Monthly Sales Trend" required />
          <TextareaInput v-model="form.description" label="Description" name="description" placeholder="Describe this analysis..." />
          <SelectInput v-model="form.sourceId" label="Data Source" name="source" :options="sourceOptions" placeholder="Select source..." required />
          <SelectInput v-model="form.chartType" label="Chart Type" name="chart_type" :options="chartTypeOptions" />
        </div>

        <!-- Fields -->
        <div v-if="fieldOptions.length > 0" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4">
          <SelectInput v-model="form.selectedFields" label="Fields" name="fields" :options="fieldOptions" placeholder="Select fields..." multiple required />

          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Filters</span>
              <button type="button" class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300" @click="addFilter">+ Add</button>
            </div>
            <div v-for="(filter, index) in form.filters" :key="index" class="flex gap-2 mb-2">
              <select v-model="filter.field" class="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 px-2 py-1.5 text-gray-700 dark:text-gray-300">
                <option value="">Field</option>
                <option v-for="fo in fieldOptions" :key="fo.value" :value="fo.value">{{ fo.label }}</option>
              </select>
              <select v-model="filter.operator" class="w-20 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 px-2 py-1.5 text-gray-700 dark:text-gray-300">
                <option v-for="op in operatorOptions" :key="op.value" :value="op.value">{{ op.label }}</option>
              </select>
              <input v-model="filter.value" type="text" placeholder="Value" class="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 px-2 py-1.5 text-gray-700 dark:text-gray-300" />
              <button type="button" class="text-red-400 hover:text-red-600 text-xs" @click="removeFilter(index)">&times;</button>
            </div>
          </div>

          <div class="flex gap-2">
            <button type="button" class="flex-1 px-3 py-2 text-xs font-medium text-gray-700 bg-gray-100 dark:bg-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors" @click="runQuery" :disabled="!form.sourceId || form.selectedFields.length === 0">
              Preview
            </button>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3">
          <button type="button" class="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors" @click="router.back()">
            Cancel
          </button>
          <button type="button" class="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors" :disabled="!form.name || !form.sourceId || form.selectedFields.length === 0 || saving" @click="handleSubmit">
            {{ saving ? 'Saving...' : 'Save Analysis' }}
          </button>
        </div>
      </div>

      <!-- Right: Preview -->
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
        <div v-else class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12 text-center">
          <svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5" />
          </svg>
          <p class="text-sm text-gray-500 dark:text-gray-400">Configure and run a query to preview results</p>
        </div>
      </div>
    </div>
  </div>
</template>
