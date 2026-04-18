<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import TextInput from '@/components/forms/TextInput.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Modal from '@/components/common/Modal.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import { getSources, getSourceFields, queryAnalytics, createAnalysis } from '@/api/analytics'

use([CanvasRenderer, LineChart, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()

const loading = ref(false)
const querying = ref(false)
const sources = ref([])
const fields = ref([])
const results = ref([])
const columns = ref([])
const chartOption = ref(null)

const form = ref({
  sourceId: '',
  selectedFields: [],
  filters: [],
  chartType: 'table',
})

const saveModal = ref(false)
const saveForm = ref({
  name: '',
  description: '',
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
  { value: 'starts_with', label: 'Starts With' },
]

const tableColumns = ref([])

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
  if (!form.value.sourceId) {
    fieldOptions.value = []
    fields.value = []
    return
  }
  try {
    const { data } = await getSourceFields(form.value.sourceId)
    fields.value = Array.isArray(data) ? data : data.items || data.fields || []
    fieldOptions.value = fields.value.map(f => ({ value: f.key || f.name, label: f.label || f.name }))
  } catch (error) {
    console.error('Failed to load fields:', error)
  }
}

function addFilter() {
  form.value.filters.push({ field: '', operator: 'eq', value: '' })
}

function removeFilter(index) {
  form.value.filters.splice(index, 1)
}

function updateFilterField(index, fieldKey) {
  form.value.filters[index].field = fieldKey
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
      const fieldDef = fields.value.find(fd => (fd.key || fd.name) === f)
      return { key: f, label: fieldDef?.label || fieldDef?.name || f, sortable: true }
    })

    if (form.value.chartType !== 'table' && results.value.length > 0) {
      buildChart()
    } else {
      chartOption.value = null
    }
  } catch (error) {
    console.error('Query failed:', error)
    results.value = []
  } finally {
    querying.value = false
  }
}

function buildChart() {
  if (results.value.length === 0) return

  const firstField = form.value.selectedFields[0]
  const secondField = form.value.selectedFields[1]

  if (form.value.chartType === 'pie') {
    const pieData = results.value.map(r => ({
      name: r[firstField],
      value: secondField ? Number(r[secondField]) : 1,
    }))
    chartOption.value = {
      tooltip: { trigger: 'item' },
      legend: { type: 'scroll', orient: 'horizontal', bottom: 0, textStyle: { color: '#9ca3af' } },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, color: '#9ca3af' },
        data: pieData,
      }],
      backgroundColor: 'transparent',
    }
  } else {
    const xData = results.value.map(r => r[firstField])
    const series = form.value.selectedFields.slice(1).map(f => ({
      name: f,
      type: form.value.chartType,
      data: results.value.map(r => Number(r[f]) || 0),
      smooth: true,
    }))
    chartOption.value = {
      tooltip: { trigger: 'axis' },
      legend: { data: series.map(s => s.name), textStyle: { color: '#9ca3af' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: xData, axisLabel: { color: '#9ca3af' }, axisLine: { lineStyle: { color: '#4b5563' } } },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' }, splitLine: { lineStyle: { color: '#374151' } } },
      series,
      backgroundColor: 'transparent',
    }
  }
}

function openSaveModal() {
  saveForm.value = { name: '', description: '' }
  saveModal.value = true
}

async function saveAnalysis() {
  if (!saveForm.value.name) return
  try {
    await createAnalysis({
      name: saveForm.value.name,
      description: saveForm.value.description,
      source_id: form.value.sourceId,
      fields: form.value.selectedFields,
      filters: form.value.filters.filter(f => f.field && f.value),
      chart_type: form.value.chartType,
    })
    saveModal.value = false
    router.push({ name: 'SavedAnalyses' })
  } catch (error) {
    console.error('Failed to save analysis:', error)
  }
}

watch(() => form.value.sourceId, () => {
  form.value.selectedFields = []
  form.value.filters = []
  results.value = []
  chartOption.value = null
  loadFields()
})

onMounted(() => {
  loadSources()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Query Builder"
      subtitle="Build custom queries and visualize results"
      :breadcrumbs="[
        { text: 'Analytics', to: { name: 'AnalyticsHub' } },
        { text: 'Query Builder' },
      ]"
    >
      <template #actions>
        <button
          v-if="results.length > 0"
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
          @click="openSaveModal"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
          </svg>
          Save Analysis
        </button>
      </template>
    </PageHeader>

    <!-- Query Configuration -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-5">
      <!-- Data Source -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <SelectInput
          v-model="form.sourceId"
          label="Data Source"
          name="source"
          :options="sourceOptions"
          placeholder="Select a data source..."
          required
        />
        <SelectInput
          v-model="form.chartType"
          label="Chart Type"
          name="chart_type"
          :options="chartTypeOptions"
        />
      </div>

      <!-- Fields Selector -->
      <div v-if="fieldOptions.length > 0">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Fields</label>
        <SelectInput
          v-model="form.selectedFields"
          label=""
          name="fields"
          :options="fieldOptions"
          placeholder="Select fields..."
          multiple
          required
        />
      </div>

      <!-- Filter Conditions -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Filter Conditions</label>
          <button
            type="button"
            class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            @click="addFilter"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Add Filter
          </button>
        </div>
        <div v-for="(filter, index) in form.filters" :key="index" class="flex items-end gap-3 mb-3">
          <div class="flex-1">
            <SelectInput
              :model-value="filter.field"
              label="Field"
              :name="`filter_field_${index}`"
              :options="fieldOptions"
              placeholder="Select field"
              @update:model-value="updateFilterField(index, $event)"
            />
          </div>
          <div class="w-40">
            <SelectInput
              v-model="filter.operator"
              label="Operator"
              :name="`filter_op_${index}`"
              :options="operatorOptions"
            />
          </div>
          <div class="flex-1">
            <TextInput
              v-model="filter.value"
              label="Value"
              :name="`filter_val_${index}`"
              placeholder="Filter value"
            />
          </div>
          <button
            type="button"
            class="p-2.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            @click="removeFilter(index)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Run Button -->
      <div class="flex justify-end">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          :disabled="!form.sourceId || form.selectedFields.length === 0 || querying"
          @click="runQuery"
        >
          <svg v-if="querying" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
          </svg>
          Run Query
        </button>
      </div>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="querying" size="lg" text="Running query..." />

    <!-- Results -->
    <div v-else-if="results.length > 0">
      <!-- Chart -->
      <div v-if="form.chartType !== 'table' && chartOption" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <v-chart :option="chartOption" style="height: 400px" autoresize />
      </div>

      <!-- Table -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <DataTable
          :columns="tableColumns"
          :data="results"
          :loading="false"
          :searchable="true"
          empty-message="No results"
        />
      </div>
    </div>

    <!-- Save Modal -->
    <Modal v-model:show="saveModal" title="Save Analysis" size="md">
      <div class="space-y-4">
        <TextInput
          v-model="saveForm.name"
          label="Analysis Name"
          name="name"
          placeholder="e.g., Monthly Sales Trend"
          required
        />
        <TextareaInput
          v-model="saveForm.description"
          label="Description"
          name="description"
          placeholder="Describe what this analysis shows..."
        />
      </div>
      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="saveModal = false"
        >
          Cancel
        </button>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
          :disabled="!saveForm.name"
          @click="saveAnalysis"
        >
          Save
        </button>
      </template>
    </Modal>
  </div>
</template>
