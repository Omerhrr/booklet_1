<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Badge from '@/components/common/Badge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { runAutomation, getAutomationConfig, getExecutions } from '@/api/agents'
import { formatRelative, formatDate } from '@/utils/dates'

const loading = ref(true)
const running = ref(false)
const config = ref(null)
const executions = ref([])
const lastResult = ref(null)
const confirmRun = ref(false)

async function fetchData() {
  loading.value = true
  try {
    const [configRes, execsRes] = await Promise.all([
      getAutomationConfig(),
      getExecutions({ agent_type: 'automation', page_size: 1 }),
    ])
    config.value = configRes.data
    const data = execsRes.data
    const items = Array.isArray(data) ? data : data.items || []
    executions.value = items
    lastResult.value = items[0] || null
  } catch (error) {
    console.error('Failed to fetch automation data:', error)
  } finally {
    loading.value = false
  }
}

async function handleRun() {
  running.value = true
  try {
    const { data } = await runAutomation({})
    lastResult.value = data
    await fetchData()
  } catch (error) {
    console.error('Failed to run automation:', error)
  } finally {
    running.value = false
    confirmRun.value = false
  }
}

onMounted(() => { fetchData() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Automation Agent"
      subtitle="Automate repetitive business tasks"
      :breadcrumbs="[
        { text: 'Agents', to: { name: 'AgentDashboard' } },
        { text: 'Automation' },
      ]"
    >
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          :disabled="running"
          @click="confirmRun = true"
        >
          <svg v-if="running" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
          </svg>
          {{ running ? 'Running...' : 'Run Now' }}
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" size="lg" text="Loading..." />

    <template v-else>
      <!-- Description -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-2">About Automation Agent</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
          The Automation Agent helps streamline your business operations by automatically processing routine tasks.
          It can handle invoice matching, data synchronization, payment reminders, and scheduled report generation.
          Configure the tasks below and run the agent on demand or on a schedule.
        </p>
      </div>

      <!-- Configuration -->
      <div v-if="config" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Configuration</h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
            <span class="text-sm text-gray-700 dark:text-gray-300">Schedule</span>
            <Badge :text="config.schedule || 'Manual'" variant="info" size="sm" />
          </div>
          <div class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
            <span class="text-sm text-gray-700 dark:text-gray-300">Tasks Enabled</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ config.enabled_tasks || 0 }}</span>
          </div>
          <div v-if="config.last_run" class="flex items-center justify-between py-2">
            <span class="text-sm text-gray-700 dark:text-gray-300">Last Run</span>
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatRelative(config.last_run) }}</span>
          </div>
        </div>
      </div>

      <!-- Last Execution Results -->
      <div v-if="lastResult" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Last Execution Results</h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
            <span class="text-sm text-gray-700 dark:text-gray-300">Status</span>
            <Badge :text="lastResult.status || 'completed'" :variant="lastResult.status === 'failed' ? 'danger' : 'success'" size="sm" />
          </div>
          <div class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
            <span class="text-sm text-gray-700 dark:text-gray-300">Tasks Processed</span>
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ lastResult.tasks_processed || 0 }}</span>
          </div>
          <div class="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700">
            <span class="text-sm text-gray-700 dark:text-gray-300">Errors</span>
            <span class="text-sm font-medium" :class="(lastResult.errors || 0) > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'">
              {{ lastResult.errors || 0 }}
            </span>
          </div>
          <div v-if="lastResult.output" class="py-2">
            <span class="text-sm text-gray-700 dark:text-gray-300 block mb-2">Output</span>
            <pre class="text-xs bg-gray-50 dark:bg-gray-900 rounded-lg p-3 text-gray-600 dark:text-gray-400 overflow-x-auto max-h-48">{{ lastResult.output }}</pre>
          </div>
        </div>
      </div>
    </template>

    <ConfirmDialog
      :show="confirmRun"
      title="Run Automation Agent"
      message="This will trigger the automation agent to process all enabled tasks. Continue?"
      confirm-text="Run"
      type="info"
      @confirm="handleRun"
      @update:show="confirmRun = $event"
    />
  </div>
</template>
