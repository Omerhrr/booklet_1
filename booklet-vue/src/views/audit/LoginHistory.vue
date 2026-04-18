<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
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
const toastStore = useToastStore()

const loading = ref(true)
const logins = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  start_date: '',
  end_date: '',
  status: '',
})

const statusOptions = [
  { value: 'success', label: 'Success' },
  { value: 'failed', label: 'Failed' },
]

const statusVariantMap = {
  success: 'success',
  failed: 'danger',
}

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

async function fetchLogins() {
  loading.value = true
  try {
    const { data } = await auditApi.getRecentLogins()
    const result = Array.isArray(data) ? data : data.items || data.results || data.logins || []

    // Client-side filtering
    let filtered = result

    if (filters.status) {
      filtered = filtered.filter((l) => (l.status || 'success') === filters.status)
    }

    if (filters.start_date) {
      filtered = filtered.filter((l) => {
        if (!l.login_time && !l.timestamp) return false
        const date = new Date(l.login_time || l.timestamp)
        return date >= new Date(filters.start_date)
      })
    }

    if (filters.end_date) {
      filtered = filtered.filter((l) => {
        if (!l.login_time && !l.timestamp) return false
        const date = new Date(l.login_time || l.timestamp)
        const end = new Date(filters.end_date)
        end.setHours(23, 59, 59, 999)
        return date <= end
      })
    }

    totalCount.value = filtered.length
    const start = (currentPage.value - 1) * pageSize.value
    logins.value = filtered.slice(start, start + pageSize.value)
  } catch (error) {
    console.error('Failed to fetch login history:', error)
    toastStore.show('Failed to load login history', 'error')
  } finally {
    loading.value = false
  }
}

function formatUser(entry) {
  if (!entry) return '—'
  if (entry.user_name) return entry.user_name
  if (entry.user?.username) return entry.user.username
  if (entry.user?.first_name) {
    return `${entry.user.first_name} ${entry.user.last_name || ''}`.trim()
  }
  if (entry.username) return entry.username
  return entry.user_id || 'Unknown'
}

function formatTimestamp(entry) {
  const ts = entry.login_time || entry.timestamp || entry.created_at
  return ts ? formatRelative(ts) : '—'
}

function formatFullTimestamp(entry) {
  const ts = entry.login_time || entry.timestamp || entry.created_at
  return ts ? formatDate(ts, 'datetime') : '—'
}

function formatUserAgent(ua) {
  if (!ua) return '—'
  if (ua.length > 80) return ua.substring(0, 80) + '...'
  return ua
}

function handlePageChange(page) {
  currentPage.value = page
  fetchLogins()
}

function applyFilters() {
  currentPage.value = 1
  fetchLogins()
}

function resetFilters() {
  filters.start_date = ''
  filters.end_date = ''
  filters.status = ''
  currentPage.value = 1
  fetchLogins()
}

onMounted(fetchLogins)
</script>

<template>
  <div>
    <PageHeader title="Login History" subtitle="Monitor all login attempts across the system" />

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
          v-model="filters.status"
          label="Status"
          name="status"
          :options="statusOptions"
          placeholder="All statuses"
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
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">User</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Login Time</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">IP Address</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">User Agent</th>
              <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            <!-- Loading -->
            <tr v-if="loading">
              <td colspan="5" class="px-4 py-12">
                <div class="flex items-center justify-center">
                  <LoadingSpinner size="lg" text="Loading login history..." />
                </div>
              </td>
            </tr>

            <!-- Empty -->
            <tr v-else-if="logins.length === 0">
              <td colspan="5" class="px-4 py-12">
                <div class="flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                  <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                  </svg>
                  <p class="text-sm">No login history found</p>
                </div>
              </td>
            </tr>

            <!-- Data Rows -->
            <tr
              v-for="login in logins"
              :key="login.id"
              :class="[
                'transition-colors',
                (login.status || '') === 'failed'
                  ? 'bg-red-50/50 dark:bg-red-900/10 hover:bg-red-50 dark:hover:bg-red-900/20'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-800',
              ]"
            >
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <div
                    :class="[
                      'w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold',
                      (login.status || '') === 'failed'
                        ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400'
                        : 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400',
                    ]"
                  >
                    {{ formatUser(login).charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ formatUser(login) }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3">
                <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ formatTimestamp(login) }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ formatFullTimestamp(login) }}</p>
              </td>
              <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400 font-mono whitespace-nowrap">
                {{ login.ip_address || '—' }}
              </td>
              <td class="px-4 py-3">
                <p class="text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate" :title="login.user_agent">
                  {{ formatUserAgent(login.user_agent) }}
                </p>
              </td>
              <td class="px-4 py-3 whitespace-nowrap">
                <StatusBadge :status="login.status || 'success'" :variant-map="statusVariantMap" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="logins.length > 0 && totalCount > pageSize" class="px-4 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Showing {{ ((currentPage - 1) * pageSize) + 1 }} to {{ Math.min(currentPage * pageSize, totalCount) }} of {{ totalCount }} results
        </p>
        <Pagination
          :current-page="currentPage"
          :total-pages="totalPages"
          @page-change="handlePageChange"
        />
      </div>

      <!-- Summary -->
      <div v-if="logins.length > 0" class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Showing {{ logins.length }} login records
          <span v-if="filters.status || filters.start_date || filters.end_date">
            (filtered)
          </span>
        </p>
      </div>
    </div>
  </div>
</template>
