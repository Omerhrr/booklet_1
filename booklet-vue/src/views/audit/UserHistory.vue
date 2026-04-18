<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Badge from '@/components/common/Badge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Pagination from '@/components/common/Pagination.vue'
import DateInput from '@/components/forms/DateInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useToastStore } from '@/stores/toast'
import { formatRelative, formatDate } from '@/utils/dates'
import * as auditApi from '@/api/audit'

const router = useRouter()
const route = useRoute()
const toastStore = useToastStore()

const loading = ref(true)
const logs = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const userInfo = ref(null)

const filters = reactive({
  start_date: '',
  end_date: '',
  action: '',
})

const actionOptions = ref([])

const totalPages = () => Math.ceil(totalCount.value / pageSize.value)

const breadcrumbs = computed(() => [
  { text: 'Audit Logs', to: '/audit' },
  { text: userInfo.value ? `User: ${userInfo.value.username || userInfo.value.first_name || 'Activity'}` : 'User Activity' },
])

async function fetchHistory() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
      action: filters.action || undefined,
    }

    const { data } = await auditApi.getUserHistory(route.params.id)
    const result = Array.isArray(data) ? data : data.items || data.results || data.logs || []
    logs.value = result

    // Extract user info from the first entry
    if (result.length > 0) {
      const first = result[0]
      userInfo.value = first.user || { username: first.user_name || `User #${route.params.id}` }
    }

    totalCount.value = data.total || data.count || logs.value.length
  } catch (error) {
    console.error('Failed to fetch user history:', error)
    toastStore.show('Failed to load user activity', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchActionOptions() {
  try {
    const { data } = await auditApi.getAuditActions()
    if (Array.isArray(data)) {
      actionOptions.value = data.map((a) => ({ value: a, label: a }))
    } else if (data.actions) {
      actionOptions.value = data.actions.map((a) => ({ value: a, label: a }))
    }
  } catch (error) {
    console.error('Failed to load action options:', error)
  }
}

function formatUser(entry) {
  if (!entry) return '—'
  if (entry.user_name) return entry.user_name
  if (entry.user?.username) return entry.user.username
  if (entry.user?.first_name) {
    return `${entry.user.first_name} ${entry.user.last_name || ''}`.trim()
  }
  return entry.user_id || 'System'
}

function formatResourceType(type) {
  if (!type) return '—'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

function truncateText(text, maxLen = 60) {
  if (!text) return '—'
  const str = typeof text === 'string' ? text : JSON.stringify(text)
  return str.length > maxLen ? str.substring(0, maxLen) + '...' : str
}

function handlePageChange(page) {
  currentPage.value = page
  fetchHistory()
}

function applyFilters() {
  currentPage.value = 1
  fetchHistory()
}

function resetFilters() {
  filters.start_date = ''
  filters.end_date = ''
  filters.action = ''
  currentPage.value = 1
  fetchHistory()
}

function goBack() {
  router.push({ name: 'AuditLogs' })
}

function handleRowClick(row) {
  if (row.id) {
    router.push({ name: 'AuditDetail', params: { id: row.id } })
  }
}

onMounted(() => {
  fetchHistory()
  fetchActionOptions()
})
</script>

<template>
  <div>
    <PageHeader :title="`User Activity: ${userInfo?.username || userInfo?.first_name || 'Loading...'}`" :breadcrumbs="breadcrumbs">
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="goBack"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          Back to Logs
        </button>
      </template>
    </PageHeader>

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
          label="Action Type"
          name="action"
          :options="actionOptions"
          placeholder="All actions"
        />
        <div class="flex items-end gap-3">
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
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
              <td colspan="7" class="px-4 py-12">
                <div class="flex items-center justify-center">
                  <LoadingSpinner size="lg" text="Loading user activity..." />
                </div>
              </td>
            </tr>

            <!-- Empty -->
            <tr v-else-if="logs.length === 0">
              <td colspan="7" class="px-4 py-12">
                <div class="flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                  <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p class="text-sm">No activity recorded for this user</p>
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
              <td class="px-4 py-3">
                <Badge :text="log.action || 'unknown'" variant="info" size="sm" />
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
                {{ formatResourceType(log.resource_type) }}
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
          :total-pages="totalPages()"
          @page-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>
