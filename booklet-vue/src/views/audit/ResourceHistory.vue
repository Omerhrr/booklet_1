<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import Badge from '@/components/common/Badge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useToastStore } from '@/stores/toast'
import { formatDate, formatRelative } from '@/utils/dates'
import * as auditApi from '@/api/audit'

const router = useRouter()
const route = useRoute()
const toastStore = useToastStore()

const history = ref([])
const loading = ref(true)
const expandedItems = ref(new Set())

const breadcrumbs = computed(() => [
  { text: 'Audit Logs', to: '/audit' },
  { text: `${formatResourceType(route.params.type)} #${route.params.id}` },
])

function formatResourceType(type) {
  if (!type) return 'Resource'
  return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
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

function parseChanges(changes) {
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
      before: value?.before ?? value?.old_value ?? null,
      after: value?.after ?? value?.new_value ?? null,
    }))
  }
  return []
}

function toggleExpand(index) {
  const updated = new Set(expandedItems.value)
  if (updated.has(index)) {
    updated.delete(index)
  } else {
    updated.add(index)
  }
  expandedItems.value = updated
}

function isExpanded(index) {
  return expandedItems.value.has(index)
}

async function fetchHistory() {
  loading.value = true
  try {
    const { data } = await auditApi.getResourceHistory(route.params.type, route.params.id)
    history.value = Array.isArray(data) ? data : data.items || data.results || data.history || []
  } catch (error) {
    console.error('Failed to fetch resource history:', error)
    toastStore.show('Failed to load resource history', 'error')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'AuditLogs' })
}

onMounted(fetchHistory)
</script>

<template>
  <div>
    <PageHeader :title="`Resource History: ${formatResourceType(route.params.type)} #${route.params.id}`" :breadcrumbs="breadcrumbs">
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

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading resource history..." />
    </div>

    <!-- Empty State -->
    <div v-else-if="history.length === 0" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12">
      <div class="flex flex-col items-center justify-center text-center">
        <div class="w-16 h-16 mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
          <svg class="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">No History Found</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">No changes have been recorded for this resource.</p>
      </div>
    </div>

    <!-- Timeline -->
    <div v-else class="relative">
      <!-- Timeline Line -->
      <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700 hidden sm:block" />

      <div class="space-y-6">
        <div
          v-for="(entry, index) in history"
          :key="entry.id || index"
          class="relative sm:pl-16"
        >
          <!-- Timeline Dot -->
          <div class="absolute left-4 top-6 w-4 h-4 rounded-full bg-blue-600 dark:bg-blue-500 border-2 border-white dark:border-gray-900 hidden sm:block" />

          <!-- Card -->
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <!-- Card Header -->
            <div
              class="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              @click="toggleExpand(index)"
            >
              <div class="flex items-center gap-3 min-w-0">
                <Badge :text="entry.action || 'update'" variant="info" size="sm" />
                <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ formatUser(entry) }}
                </span>
                <span class="text-sm text-gray-500 dark:text-gray-400 hidden sm:inline">
                  {{ formatDate(entry.timestamp, 'datetime') }}
                </span>
              </div>
              <div class="flex items-center gap-2 ml-3">
                <StatusBadge :status="entry.status || 'success'" />
                <svg
                  :class="['w-4 h-4 text-gray-400 transition-transform', isExpanded(index) ? 'rotate-180' : '']"
                  fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </div>
            </div>

            <!-- Mobile timestamp -->
            <div class="px-4 pb-1 sm:hidden">
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatRelative(entry.timestamp) }}
              </span>
            </div>

            <!-- Expanded Details -->
            <div v-if="isExpanded(index)" class="px-4 pb-4 border-t border-gray-100 dark:border-gray-700">
              <div class="pt-3 space-y-3">
                <template v-if="parseChanges(entry.changes).length > 0">
                  <div
                    v-for="(change, cIndex) in parseChanges(entry.changes)"
                    :key="cIndex"
                    class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                  >
                    <div class="bg-gray-50 dark:bg-gray-900 px-3 py-2 border-b border-gray-200 dark:border-gray-700">
                      <span class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">{{ change.field }}</span>
                    </div>
                    <div class="grid grid-cols-2 divide-x divide-gray-200 dark:divide-gray-700">
                      <div class="px-3 py-2">
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Before</p>
                        <p class="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded px-2 py-1 break-all">
                          {{ change.before !== null && change.before !== undefined
                            ? (typeof change.before === 'object' ? JSON.stringify(change.before) : String(change.before))
                            : '—' }}
                        </p>
                      </div>
                      <div class="px-3 py-2">
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">After</p>
                        <p class="text-sm text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded px-2 py-1 break-all">
                          {{ change.after !== null && change.after !== undefined
                            ? (typeof change.after === 'object' ? JSON.stringify(change.after) : String(change.after))
                            : '—' }}
                        </p>
                      </div>
                    </div>
                  </div>
                </template>
                <div v-else class="py-2">
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ entry.description || 'No change details recorded.' }}</p>
                </div>

                <!-- IP Address & User Agent -->
                <div v-if="entry.ip_address || entry.user_agent" class="flex flex-wrap gap-4 pt-2 text-xs text-gray-500 dark:text-gray-400">
                  <span v-if="entry.ip_address">
                    <span class="font-medium">IP:</span> {{ entry.ip_address }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
