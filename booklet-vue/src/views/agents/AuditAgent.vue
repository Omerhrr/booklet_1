<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Badge from '@/components/common/Badge.vue'
import DataTable from '@/components/common/DataTable.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { runAudit, getAuditConfig, getExecutions } from '@/api/agents'
import { formatDate } from '@/utils/dates'

const loading = ref(true)
const running = ref(false)
const config = ref(null)
const findings = ref([])
const confirmRun = ref(false)

const columns = [
  { key: 'title', label: 'Finding', sortable: true },
  { key: 'severity', label: 'Severity', sortable: true },
  { key: 'description', label: 'Description' },
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchData() {
  loading.value = true
  try {
    const [configRes, execsRes] = await Promise.all([
      getAuditConfig(),
      getExecutions({ agent_type: 'audit', page_size: 1 }),
    ])
    config.value = configRes.data
    const data = execsRes.data
    const lastExec = (Array.isArray(data) ? data : data.items || [])[0]
    if (lastExec && lastExec.findings) {
      findings.value = lastExec.findings
    }
  } catch (error) {
    console.error('Failed to fetch audit data:', error)
  } finally {
    loading.value = false
  }
}

async function handleRunAudit() {
  running.value = true
  try {
    const { data } = await runAudit({})
    if (data.findings) {
      findings.value = data.findings
    }
    await fetchData()
  } catch (error) {
    console.error('Failed to run audit:', error)
  } finally {
    running.value = false
    confirmRun.value = false
  }
}

const severityVariant = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'info',
}

onMounted(() => { fetchData() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Audit Agent"
      subtitle="Review financial records for anomalies"
      :breadcrumbs="[
        { text: 'Agents', to: { name: 'AgentDashboard' } },
        { text: 'Audit' },
      ]"
    >
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 disabled:opacity-50 transition-colors"
          :disabled="running"
          @click="confirmRun = true"
        >
          <svg v-if="running" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          {{ running ? 'Auditing...' : 'Run Audit' }}
        </button>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" size="lg" text="Loading..." />

    <template v-else>
      <!-- Description -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-2">About Audit Agent</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
          The Audit Agent scans your financial records for anomalies, compliance issues, and potential fraud indicators.
          It reviews transactions, journal entries, and account balances to identify areas that need attention.
          Run an audit to generate findings and recommendations.
        </p>
      </div>

      <!-- Config -->
      <div v-if="config" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Audit Configuration</h3>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
            <p class="text-xs text-gray-500 dark:text-gray-400">Scope</p>
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ config.scope || 'All Records' }}</p>
          </div>
          <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
            <p class="text-xs text-gray-500 dark:text-gray-400">Risk Threshold</p>
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ config.risk_threshold || 'Medium' }}</p>
          </div>
          <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
            <p class="text-xs text-gray-500 dark:text-gray-400">Last Audit</p>
            <p class="text-sm font-medium text-gray-900 dark:text-white">{{ config.last_run ? formatDate(config.last_run, 'short') : 'Never' }}</p>
          </div>
        </div>
      </div>

      <!-- Findings -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">
          Audit Findings
          <span v-if="findings.length > 0" class="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">({{ findings.length }})</span>
        </h3>

        <div v-if="findings.length === 0" class="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
          No audit findings yet. Run an audit to generate findings.
        </div>

        <DataTable v-else :columns="columns" :data="findings" :loading="false" :searchable="false" empty-message="">
          <template #cell-title="{ row }">
            <span class="text-sm font-medium text-gray-900 dark:text-white">{{ row.title }}</span>
          </template>
          <template #cell-severity="{ row }">
            <Badge :text="row.severity || 'info'" :variant="severityVariant[row.severity] || 'default'" size="sm" />
          </template>
          <template #cell-description="{ row }">
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ row.description || '—' }}</span>
          </template>
          <template #cell-created_at="{ row }">
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.created_at, 'short') }}</span>
          </template>
          <template #cell-status="{ row }">
            <Badge :text="row.status || 'open'" :variant="row.status === 'resolved' ? 'success' : 'warning'" size="sm" />
          </template>
        </DataTable>
      </div>
    </template>

    <ConfirmDialog
      :show="confirmRun"
      title="Run Audit"
      message="This will scan your financial records for anomalies and compliance issues. This may take a few moments."
      confirm-text="Run Audit"
      type="warning"
      @confirm="handleRunAudit"
      @update:show="confirmRun = $event"
    />
  </div>
</template>
