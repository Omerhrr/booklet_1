<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DataTable from '@/components/common/DataTable.vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { getAiUsage } from '@/api/ai'
import { formatDate } from '@/utils/dates'

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, GridComponent])

const loading = ref(true)
const usage = ref({
  total_messages: 0,
  total_tokens: 0,
  total_conversations: 0,
  daily_usage: [],
})

const columns = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'messages', label: 'Messages', sortable: true },
  { key: 'tokens', label: 'Tokens Used', sortable: true },
  { key: 'conversations', label: 'Conversations', sortable: true },
]

const chartOption = ref(null)

async function fetchUsage() {
  loading.value = true
  try {
    const { data } = await getAiUsage()
    usage.value = {
      total_messages: data.total_messages || 0,
      total_tokens: data.total_tokens || 0,
      total_conversations: data.total_conversations || 0,
      daily_usage: Array.isArray(data.daily_usage) ? data.daily_usage : (data.by_day || []),
    }

    if (usage.value.daily_usage.length > 0) {
      chartOption.value = {
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'category',
          data: usage.value.daily_usage.map(d => d.date),
          axisLabel: { color: '#9ca3af', fontSize: 11 },
          axisLine: { lineStyle: { color: '#4b5563' } },
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#9ca3af' },
          splitLine: { lineStyle: { color: '#374151' } },
        },
        series: [
          {
            name: 'Messages',
            type: 'line',
            data: usage.value.daily_usage.map(d => d.messages || 0),
            smooth: true,
            lineStyle: { color: '#10b981' },
            itemStyle: { color: '#10b981' },
            areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16, 185, 129, 0.2)' }, { offset: 1, color: 'rgba(16, 185, 129, 0)' }] } },
          },
          {
            name: 'Tokens',
            type: 'line',
            data: usage.value.daily_usage.map(d => d.tokens || 0),
            smooth: true,
            lineStyle: { color: '#f59e0b' },
            itemStyle: { color: '#f59e0b' },
          },
        ],
        legend: {
          data: ['Messages', 'Tokens'],
          textStyle: { color: '#9ca3af' },
        },
        backgroundColor: 'transparent',
      }
    }
  } catch (error) {
    console.error('Failed to fetch AI usage:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchUsage()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="AI Usage Statistics"
      subtitle="Monitor your AI usage across the organization"
      :breadcrumbs="[
        { text: 'AI', to: { name: 'AiChat' } },
        { text: 'Usage' },
      ]"
    />

    <LoadingSpinner v-if="loading" size="lg" text="Loading usage data..." />

    <template v-else>
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Total Messages"
          :value="usage.total_messages"
          icon="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
          color="green"
        />
        <StatCard
          title="Total Tokens Used"
          :value="usage.total_tokens.toLocaleString()"
          icon="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5"
          color="amber"
        />
        <StatCard
          title="Total Conversations"
          :value="usage.total_conversations"
          icon="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155"
          color="purple"
        />
      </div>

      <!-- Usage Chart -->
      <div v-if="chartOption" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4">Usage Over Time</h3>
        <v-chart :option="chartOption" style="height: 350px" autoresize />
      </div>

      <!-- Daily Usage Table -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-4">Usage by Day</h3>
        <DataTable
          :columns="columns"
          :data="usage.daily_usage"
          :loading="false"
          :searchable="false"
          empty-message="No usage data available"
        >
          <template #cell-date="{ row }">
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
          </template>
          <template #cell-messages="{ row }">
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ row.messages || 0 }}</span>
          </template>
          <template #cell-tokens="{ row }">
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ (row.tokens || 0).toLocaleString() }}</span>
          </template>
          <template #cell-conversations="{ row }">
            <span class="text-sm text-gray-700 dark:text-gray-300">{{ row.conversations || 0 }}</span>
          </template>
        </DataTable>
      </div>
    </template>
  </div>
</template>
