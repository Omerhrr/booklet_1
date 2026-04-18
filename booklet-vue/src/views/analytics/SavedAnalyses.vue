<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { getAnalyses, deleteAnalysis, toggleAnalysisFavorite } from '@/api/analytics'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const loading = ref(true)
const analyses = ref([])
const searchQuery = ref('')
const deleteDialog = ref({ show: false, item: null })

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'data_source', label: 'Data Source', sortable: true },
  { key: 'chart_type', label: 'Chart Type', sortable: true },
  { key: 'created_at', label: 'Created', sortable: true },
  { key: 'is_favorite', label: 'Favorite', sortable: true },
]

async function fetchAnalyses() {
  loading.value = true
  try {
    const { data } = await getAnalyses({ search: searchQuery.value })
    analyses.value = Array.isArray(data) ? data : data.items || []
  } catch (error) {
    console.error('Failed to fetch analyses:', error)
    analyses.value = []
  } finally {
    loading.value = false
  }
}

function viewAnalysis(item) {
  router.push({ name: 'AnalysisView', params: { id: item.id } })
}

function editAnalysis(item) {
  router.push({ name: 'AnalysisEdit', params: { id: item.id } })
}

function confirmDelete(item) {
  deleteDialog.value = { show: true, item }
}

async function handleDelete() {
  const item = deleteDialog.value.item
  if (!item) return
  try {
    await deleteAnalysis(item.id)
    analyses.value = analyses.value.filter(a => a.id !== item.id)
  } catch (error) {
    console.error('Failed to delete analysis:', error)
  }
}

async function toggleFavorite(item) {
  try {
    await toggleAnalysisFavorite(item.id)
    item.is_favorite = !item.is_favorite
  } catch (error) {
    console.error('Failed to toggle favorite:', error)
  }
}

function handleSearch() {
  fetchAnalyses()
}

onMounted(() => {
  fetchAnalyses()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Saved Analyses"
      subtitle="Manage your saved data analyses"
      :breadcrumbs="[
        { text: 'Analytics', to: { name: 'AnalyticsHub' } },
        { text: 'Saved Analyses' },
      ]"
    >
      <template #actions>
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
          @click="router.push({ name: 'AnalysisCreate' })"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Analysis
        </button>
      </template>
    </PageHeader>

    <!-- Search -->
    <div class="relative w-full max-w-sm">
      <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
        <svg class="w-4 h-4 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
      </div>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Search analyses..."
        class="block w-full pl-10 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
        @keyup.enter="handleSearch"
      />
    </div>

    <DataTable
      :columns="columns"
      :data="analyses"
      :loading="loading"
      :searchable="false"
      empty-message="No analyses found"
    >
      <template #cell-name="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:underline"
          @click="viewAnalysis(row)"
        >
          {{ row.name }}
        </button>
      </template>
      <template #cell-chart_type="{ row }">
        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 capitalize">
          {{ row.chart_type }}
        </span>
      </template>
      <template #cell-created_at="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.created_at, 'short') }}</span>
      </template>
      <template #cell-is_favorite="{ row }">
        <button
          type="button"
          class="p-1 transition-colors"
          @click="toggleFavorite(row)"
        >
          <svg
            :class="['w-5 h-5', row.is_favorite ? 'text-amber-400 fill-amber-400' : 'text-gray-300 dark:text-gray-600']"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
          </svg>
        </button>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <button type="button" class="p-1.5 text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="View" @click="viewAnalysis(row)">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </button>
          <button type="button" class="p-1.5 text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors" title="Edit" @click="editAnalysis(row)">
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
      title="Delete Analysis"
      message="Are you sure you want to delete this analysis? This action cannot be undone."
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
      @update:show="deleteDialog.show = $event"
    />
  </div>
</template>
