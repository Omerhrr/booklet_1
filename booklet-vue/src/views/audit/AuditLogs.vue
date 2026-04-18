<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import Pagination from '@/components/common/Pagination.vue'
import DateInput from '@/components/forms/DateInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useToastStore } from '@/stores/toast'
import { formatRelative } from '@/utils/dates'
import * as auditApi from '@/api/audit'

const router = useRouter()
const toastStore = useToastStore()

const loading = ref(true)
const logs = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  start_date: '',
  end_date: '',
  user_id: '',
  action: '',
  resource_type: '',
  status: '',
  search: '',
})

const userOptions = ref([])
const actionOptions = ref([])
const resourceTypeOptions = ref([
  { value: 'user', label: 'User' },
  { value: 'role', label: 'Role' },
  { value: 'branch', label: 'Branch' },
  { value: 'customer', label: 'Customer' },
  { value: 'vendor', label: 'Vendor' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'bill', label: 'Bill' },
  { value: 'product', label: 'Product' },
  { value: 'expense', label: 'Expense' },
  { value: 'payment', label: 'Payment' },
  { value: 'account', label: 'Account' },
  { value: 'journal_entry', label: 'Journal Entry' },
  { value: 'fiscal_year', label: 'Fiscal Year' },
  { value: 'employee', label: 'Employee' },
  { value: 'bank_account', label: 'Bank Account' },
  { value: 'ai_config', label: 'AI Config' },
  { value: 'agent', label: 'Agent' },
])

const statusOptions = [
  { value: 'success', label: 'Success' },
  { value: 'failed', label: 'Failed' },
  { value: 'error', label: 'Error' },
]

const tableColumns = [
  { key: 'timestamp', label: 'Timestamp', sortable: true },
  { key: 'user', label: 'User', sortable: true },
  { key: 'action', label: 'Action', sortable: true },
  { key: 'resource_type', label: 'Resource Type', sortable: true },
  { key: 'resource_id', label: 'Resource ID', sortable: true },
  { key: 'details', label: 'Details' },
  { key: 'ip_address', label: 'IP Address' },
  { key: 'status', label: 'Status', sortable: true },
]

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

async function fetchLogs() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      search: filters.search || undefined,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
      user_id: filters.user_id || undefined,
      action: filters.action || undefined,
      resource_type: filters.resource_type || undefined,
      status: filters.status || undefined,
    }

    const { data } = await auditApi.listAuditLogs(params)
    logs.value = Array.isArray(data) ? data : data.items || data.results || data.logs || []
    totalCount.value = data.total || data.count || logs.value.length
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
    toastStore.show('Failed to load audit logs', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchFiltersData() {
  try {
    const { data } = await auditApi.getAuditActions()
    if (Array.isArray(data)) {
      actionOptions.value = data.map((a) => ({ value: a, label: a }))
    } else if (data.actions) {
      actionOptions.value = data.actions.map((a) => ({ value: a, label: a }))
    }
  } catch (error) {
    console.error('Failed to load filter options:', error)
  }
}

function handleRowClick(row) {
  if (row.id) {
    router.push({ name: 'AuditDetail', params: { id: row.id } })
  }
}

function handlePageChange(page) {
  currentPage.value = page
  fetchLogs()
}

function applyFilters() {
  currentPage.value = 1
  fetchLogs()
}

function resetFilters() {
  filters.start_date = ''
  filters.end_date = ''
  filters.user_id = ''
  filters.action = ''
  filters.resource_type = ''
  filters.status = ''
  filters.search = ''
  currentPage.value = 1
  fetchLogs()
}

function truncateText(text, maxLen = 50) {
  if (!text) return '—'
  const str = typeof text === 'string' ? text : JSON.stringify(text)
  return str.length > maxLen ? str.substring(0, maxLen) + '...' : str
}

function formatUser(row) {
  if (row.user_name) return row.user_name
  if (row.user?.username) return row.user.username
  if (row.user?.first_name) {
    return `${row.user.first_name} ${row.user.last_name || ''}`.trim()
  }
  return row.user_id || '—'
}

function formatAction(row) {
  return row.action || '—'
}

function formatResourceType(row) {
  if (!row.resource_type) return '—'
  return row.resource_type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

onMounted(() => {
  fetchLogs()
  fetchFiltersData()
})
</script>

<template>
  <div>
    <PageHeader title="Audit Logs" subtitle="Track all changes and actions across the system" />

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DateInput
          v-model="filters.start_date"
          label="Start Date"
          name="start_date"
        />
        <DateInput
          v-model="filters.end_date"
          label="End Date"
          name="end_date"
          :min="filters.start_date"
        />
        <SelectInput
          v-model="filters.action"
          label="Action"
          name="action"
          :options="actionOptions"
          placeholder="All actions"
        />
        <SelectInput
          v-model="filters.resource_type"
          label="Resource Type"
          name="resource_type"
          :options="resourceTypeOptions"
          placeholder="All types"
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
        <SelectInput
          v-model="filters.status"
          label="Status"
          name="status"
          :options="statusOptions"
          placeholder="All statuses"
        />
        <div class="sm:col-span-3 flex items-end gap-3">
          <div class="flex-1">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Search
            </label>
            <input
              v-model="filters.search"
              type="text"
              placeholder="Search logs..."
              class="block w-full px-3 py-2.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              @keyup.enter="applyFilters"
            />
          </div>
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
            @click="applyFilters"
          >
            Apply
          </button>
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
            @click="resetFilters"
          >
            Reset
          </button>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Timestamp</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">User</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Action</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Resource Type</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Resource ID</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Details</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">IP Address</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            <!-- Loading -->
            <tr v-if="loading">
              <td colspan="8" class="px-4 py-12">
                <div class="flex items-center justify-center">
                  <LoadingSpinner size="lg" text="Loading logs..." />
                </div>
              </td>
            </tr>

            <!-- Empty -->
            <tr v-else-if="logs.length === 0">
              <td colspan="8" class="px-4 py-12">
                <div class="flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                  <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
                  </svg>
                  <p class="text-sm">No audit logs found</p>
                </div>
              </td>
            </tr>

            <!-- Data Rows -->
            <tr
              v-for="log in logs"
              :key="log.id"
              class="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
              @click="handleRowClick(log)"
            >
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
                <span :title="log.timestamp">{{ formatRelative(log.timestamp) }}</span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-900 dark:text-white font-medium whitespace-nowrap">
                {{ formatUser(log) }}
              </td>
              <td class="px-4 py-3">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                  {{ formatAction(log) }}
                </span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
                {{ formatResourceType(log) }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 font-mono whitespace-nowrap">
                {{ log.resource_id || '—' }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">
                {{ truncateText(log.details || log.description) }}
              </td>
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 font-mono whitespace-nowrap">
                {{ log.ip_address || '—' }}
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <StatusBadge :status="log.status || 'success'" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="logs.length > 0 && totalCount > pageSize" class="px-4 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, totalCount) }} of {{ totalCount }} results
        </p>
        <Pagination
          :current-page="currentPage"
          :total-pages="totalPages"
          @page-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>
