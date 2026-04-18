<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Badge from '@/components/common/Badge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatRelative } from '@/utils/dates'
import * as auditApi from '@/api/audit'

const router = useRouter()
const route = useRoute()
const toastStore = useToastStore()

const log = ref(null)
const loading = ref(true)
const showRawJson = ref(false)

const breadcrumbs = computed(() => [
  { text: 'Audit Logs', to: '/audit' },
  { text: log.value ? `Log #${log.value.id}` : 'Audit Detail' },
])

function formatUser(data) {
  if (!data) return '—'
  if (data.user_name) return data.user_name
  if (data.user?.username) return data.user.username
  if (data.user?.first_name) {
    return `${data.user.first_name} ${data.user.last_name || ''}`.trim()
  }
  return data.user_id || 'System'
}

function formatResourceType(type) {
  if (!type) return '—'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}

function formatChanges(changes) {
  if (!changes) return []
  if (typeof changes === 'string') {
    try {
      changes = JSON.parse(changes)
    } catch {
      return []
    }
  }
  if (Array.isArray(changes)) return changes
  if (typeof changes === 'object') {
    return Object.entries(changes).map(([key, value]) => ({
      field: key,
      before: value?.before ?? value?.old_value ?? '—',
      after: value?.after ?? value?.new_value ?? '—',
    }))
  }
  return []
}

function hasBeforeAfter(value) {
  return value !== null && value !== undefined && typeof value === 'object' && ('before' in value || 'after' in value || 'old_value' in value || 'new_value' in value)
}

async function fetchLog() {
  loading.value = true
  try {
    const { data } = await auditApi.getAuditLog(route.params.id)
    log.value = data
  } catch (error) {
    console.error('Failed to fetch audit log:', error)
    toastStore.show('Failed to load audit log', 'error')
    router.push({ name: 'AuditLogs' })
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'AuditLogs' })
}

onMounted(fetchLog)
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading audit log..." />
    </div>

    <template v-else-if="log">
      <PageHeader :title="`Audit Log #${log.id}`" :breadcrumbs="breadcrumbs">
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

      <!-- Summary Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Log Summary</h3>
        <dl class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Timestamp</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ formatDate(log.timestamp, 'datetime') }}</dd>
            <dd class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ formatRelative(log.timestamp) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">User</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ formatUser(log) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Action</dt>
            <dd class="mt-0.5">
              <Badge :text="log.action || 'unknown'" variant="info" size="sm" />
            </dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Resource Type</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ formatResourceType(log.resource_type) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Resource ID</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5 font-mono">{{ log.resource_id || '—' }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Status</dt>
            <dd class="mt-0.5">
              <StatusBadge :status="log.status || 'success'" />
            </dd>
          </div>
        </dl>
      </div>

      <!-- IP & User Agent -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">IP Address</h3>
          <p class="text-sm font-mono text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900 rounded-lg px-4 py-3">
            {{ log.ip_address || 'Not recorded' }}
          </p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">User Agent</h3>
          <p class="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900 rounded-lg px-4 py-3 break-all">
            {{ log.user_agent || 'Not recorded' }}
          </p>
        </div>
      </div>

      <!-- Changes Detail -->
      <div v-if="log.changes || log.details" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Changes Detail</h3>
          <button
            type="button"
            class="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
            @click="showRawJson = !showRawJson"
          >
            {{ showRawJson ? 'Hide' : 'Show' }} Raw JSON
          </button>
        </div>

        <!-- Raw JSON View -->
        <div v-if="showRawJson" class="mb-4">
          <pre class="text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900 rounded-lg p-4 overflow-x-auto max-h-96 overflow-y-auto">{{ JSON.stringify(log.changes || log.details, null, 2) }}</pre>
        </div>

        <!-- Before/After Comparison -->
        <div v-if="!showRawJson">
          <template v-if="formatChanges(log.changes).length > 0">
            <div class="space-y-3">
              <div
                v-for="(change, index) in formatChanges(log.changes)"
                :key="index"
                class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
              >
                <div class="bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ change.field }}</span>
                </div>
                <div class="grid grid-cols-2 divide-x divide-gray-200 dark:divide-gray-700">
                  <div class="px-4 py-3">
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Before</p>
                    <p class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded px-2 py-1 break-all">
                      {{ typeof change.before === 'object' ? JSON.stringify(change.before) : (change.before ?? '—') }}
                    </p>
                  </div>
                  <div class="px-4 py-3">
                    <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">After</p>
                    <p class="text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded px-2 py-1 break-all">
                      {{ typeof change.after === 'object' ? JSON.stringify(change.after) : (change.after ?? '—') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </template>
          <template v-else-if="log.description">
            <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ log.description }}</p>
          </template>
          <template v-else>
            <p class="text-sm text-gray-500 dark:text-gray-400">No change details available.</p>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>
