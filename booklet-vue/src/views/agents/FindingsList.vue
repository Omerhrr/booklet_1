<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Badge from '@/components/common/Badge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { listFindings, resolveFinding } from '@/api/agents'
import { formatDate } from '@/utils/dates'

const loading = ref(true)
const findings = ref([])
const searchQuery = ref('')
const severityFilter = ref('')
const statusFilter = ref('')
const resolveDialog = ref({ show: false, id: null })

const severityOptions = [
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

const statusOptions = [
  { value: 'open', label: 'Open' },
  { value: 'resolved', label: 'Resolved' },
]

const columns = [
  { key: 'title', label: 'Title', sortable: true },
  { key: 'severity', label: 'Severity', sortable: true },
  { key: 'agent_type', label: 'Agent', sortable: true },
  { key: 'created_at', label: 'Created', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

const severityVariant = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'info',
}

async function fetchFindings() {
  loading.value = true
  try {
    const params = {}
    if (searchQuery.value) params.search = searchQuery.value
    if (severityFilter.value) params.severity = severityFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    const { data } = await listFindings(params)
    findings.value = Array.isArray(data) ? data : data.items || []
  } catch (error) {
    console.error('Failed to fetch findings:', error)
    findings.value = []
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  fetchFindings()
}

function confirmResolve(item) {
  resolveDialog.value = { show: true, id: item.id }
}

async function handleResolve() {
  const id = resolveDialog.value.id
  if (!id) return
  try {
    await resolveFinding(id)
    findings.value = findings.value.map(f => f.id === id ? { ...f, status: 'resolved' } : f)
  } catch (error) {
    console.error('Failed to resolve finding:', error)
  }
}

onMounted(() => { fetchFindings() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Agent Findings"
      subtitle="Review and manage agent-generated findings"
      :breadcrumbs="[
        { text: 'Agents', to: { name: 'AgentDashboard' } },
        { text: 'Findings' },
      ]"
    />

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Search</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <svg class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
            </div>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search findings..."
              class="block w-full pl-10 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-rose-500 transition-colors"
              @keyup.enter="applyFilters"
            />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Severity</label>
          <select
            v-model="severityFilter"
            class="block w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-rose-500 transition-colors"
            @change="applyFilters"
          >
            <option value="">All Severities</option>
            <option v-for="opt in severityOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Status</label>
          <select
            v-model="statusFilter"
            class="block w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-rose-500 transition-colors"
            @change="applyFilters"
          >
            <option value="">All Statuses</option>
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="flex items-end">
          <button
            type="button"
            class="w-full px-4 py-2 text-sm font-medium text-rose-600 bg-rose-50 dark:bg-rose-900/20 dark:text-rose-400 border border-rose-200 dark:border-rose-800 rounded-lg hover:bg-rose-100 dark:hover:bg-rose-900/30 transition-colors"
            @click="applyFilters"
          >
            Filter
          </button>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable :columns="columns" :data="findings" :loading="loading" :searchable="false" empty-message="No findings found">
      <template #cell-title="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ row.title }}</span>
      </template>
      <template #cell-severity="{ row }">
        <Badge :text="row.severity || 'info'" :variant="severityVariant[row.severity] || 'default'" size="sm" />
      </template>
      <template #cell-agent_type="{ row }">
        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 capitalize">
          {{ row.agent_type || 'unknown' }}
        </span>
      </template>
      <template #cell-created_at="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.created_at, 'short') }}</span>
      </template>
      <template #cell-status="{ row }">
        <Badge :text="row.status || 'open'" :variant="row.status === 'resolved' ? 'success' : 'warning'" size="sm" />
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <button type="button" class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="View Details">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </button>
          <button
            v-if="row.status !== 'resolved'"
            type="button"
            class="p-1.5 text-gray-400 hover:text-green-600 dark:hover:text-green-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Resolve"
            @click="confirmResolve(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </button>
        </div>
      </template>
    </DataTable>

    <ConfirmDialog
      :show="resolveDialog.show"
      title="Resolve Finding"
      message="Mark this finding as resolved?"
      confirm-text="Resolve"
      type="info"
      @confirm="handleResolve"
      @update:show="resolveDialog.show = $event"
    />
  </div>
</template>
