<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { getDashboards, deleteDashboard } from '@/api/analytics'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const loading = ref(true)
const dashboards = ref([])
const deleteDialog = ref({ show: false, item: null })

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'description', label: 'Description' },
  { key: 'analyses_count', label: 'Analyses', sortable: true },
  { key: 'created_at', label: 'Created', sortable: true },
]

async function fetchDashboards() {
  loading.value = true
  try {
    const { data } = await getDashboards()
    dashboards.value = Array.isArray(data) ? data : data.items || []
  } catch (error) {
    console.error('Failed to fetch dashboards:', error)
    dashboards.value = []
  } finally {
    loading.value = false
  }
}

function viewDashboard(item) {
  router.push({ name: 'DashboardView', params: { id: item.id } })
}

function editDashboard(item) {
  router.push({ name: 'DashboardEdit', params: { id: item.id } })
}

function confirmDelete(item) {
  deleteDialog.value = { show: true, item }
}

async function handleDelete() {
  const item = deleteDialog.value.item
  if (!item) return
  try {
    await deleteDashboard(item.id)
    dashboards.value = dashboards.value.filter(d => d.id !== item.id)
  } catch (error) {
    console.error('Failed to delete dashboard:', error)
  }
}

onMounted(() => { fetchDashboards() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Dashboards"
      subtitle="Manage your analytics dashboards"
      :breadcrumbs="[
        { text: 'Analytics', to: { name: 'AnalyticsHub' } },
        { text: 'Dashboards' },
      ]"
    >
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 transition-colors"
          @click="router.push({ name: 'DashboardCreate' })"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Dashboard
        </button>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :data="dashboards" :loading="loading" empty-message="No dashboards found">
      <template #cell-name="{ row }">
        <button type="button" class="text-sm font-medium text-violet-600 dark:text-violet-400 hover:underline" @click="viewDashboard(row)">
          {{ row.name }}
        </button>
      </template>
      <template #cell-description="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ row.description || '—' }}</span>
      </template>
      <template #cell-analyses_count="{ row }">
        <span class="inline-flex items-center justify-center w-7 h-7 text-xs font-medium bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-400 rounded-full">
          {{ row.analyses_count || row.analyses?.length || 0 }}
        </span>
      </template>
      <template #cell-created_at="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.created_at, 'short') }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <button type="button" class="p-1.5 text-gray-400 hover:text-violet-600 dark:hover:text-violet-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="View" @click="viewDashboard(row)">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </button>
          <button type="button" class="p-1.5 text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="Edit" @click="editDashboard(row)">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg>
          </button>
          <button type="button" class="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="Delete" @click="confirmDelete(row)">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
          </button>
        </div>
      </template>
    </DataTable>

    <ConfirmDialog
      :show="deleteDialog.show"
      title="Delete Dashboard"
      message="Are you sure you want to delete this dashboard?"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
      @update:show="deleteDialog.show = $event"
    />
  </div>
</template>
