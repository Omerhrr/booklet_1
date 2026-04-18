<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { listFixedAssets, deleteFixedAsset, bulkDepreciation, getFixedAssetCategories } from '@/api/fixedAssets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const assets = ref([])
const loading = ref(true)
const categories = ref([])
const filterStatus = ref('')
const filterCategory = ref('')

const showDeleteDialog = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)
const bulkDepreciating = ref(false)

const statusTabs = [
  { key: '', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'disposed', label: 'Disposed' },
  { key: 'written_off', label: 'Written Off' },
]

const columns = [
  { key: 'asset_name', label: 'Asset Name', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'purchase_date', label: 'Purchase Date', sortable: true },
  { key: 'cost', label: 'Cost', sortable: true },
  { key: 'accumulated_depreciation', label: 'Accum. Depreciation', sortable: true },
  { key: 'net_book_value', label: 'Net Book Value', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchAssets() {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    if (filterCategory.value) params.category = filterCategory.value

    const { data } = await listFixedAssets(params)
    assets.value = Array.isArray(data) ? data : data.items || data.assets || []
  } catch (error) {
    console.error('Failed to fetch fixed assets:', error)
    assets.value = []
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const { data } = await getFixedAssetCategories()
    categories.value = (Array.isArray(data) ? data : data.categories || []).map(c => ({
      value: typeof c === 'string' ? c : c.id || c.name,
      label: typeof c === 'string' ? c : c.name || c.label,
    }))
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

function viewAsset(asset) {
  router.push({ name: 'FixedAssetDetail', params: { id: asset.id } })
}

function editAsset(asset) {
  router.push({ name: 'FixedAssetEdit', params: { id: asset.id } })
}

function confirmDelete(asset) {
  deleteTarget.value = asset
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deleteFixedAsset(deleteTarget.value.id)
    toast.show('Asset deleted successfully', 'success')
    await fetchAssets()
  } catch (error) {
    console.error('Failed to delete asset:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to delete asset'
    toast.show(message, 'error')
  } finally {
    deleting.value = false
    deleteTarget.value = null
  }
}

async function handleBulkDepreciation() {
  bulkDepreciating.value = true
  try {
    await bulkDepreciation({ as_of_date: new Date().toISOString().split('T')[0] })
    toast.show('Bulk depreciation completed successfully', 'success')
    await fetchAssets()
  } catch (error) {
    console.error('Failed to run bulk depreciation:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to run bulk depreciation'
    toast.show(message, 'error')
  } finally {
    bulkDepreciating.value = false
  }
}

function computeNetBookValue(asset) {
  const cost = Number(asset.cost) || 0
  const accumDep = Number(asset.accumulated_depreciation) || 0
  return cost - accumDep
}

watch([filterStatus, filterCategory], () => {
  fetchAssets()
})

onMounted(() => {
  fetchAssets()
  fetchCategories()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Fixed Assets"
      subtitle="Manage your organization's fixed assets and depreciation"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Fixed Assets' }
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            v-if="auth.hasPermission('accounting:create')"
            type="button"
            :disabled="bulkDepreciating"
            class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors disabled:opacity-50"
            @click="handleBulkDepreciation"
          >
            <svg v-if="bulkDepreciating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
            </svg>
            {{ bulkDepreciating ? 'Depreciating...' : 'Bulk Depreciation' }}
          </button>
          <button
            v-if="auth.hasPermission('accounting:create')"
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
            @click="router.push({ name: 'FixedAssetCreate' })"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Create Asset
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Status Tabs -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Status</label>
          <select
            v-model="filterStatus"
            class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
          >
            <option v-for="tab in statusTabs" :key="tab.key" :value="tab.key">{{ tab.label }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Category</label>
          <select
            v-model="filterCategory"
            class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
          >
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="assets"
      :loading="loading"
      :searchable="true"
      search-placeholder="Search assets..."
      empty-message="No fixed assets found"
    >
      <template #cell-asset_name="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors"
          @click="viewAsset(row)"
        >
          {{ row.asset_name || row.name }}
        </button>
      </template>

      <template #cell-category="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ row.category_name || row.category || '—' }}</span>
      </template>

      <template #cell-purchase_date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.purchase_date, 'short') }}</span>
      </template>

      <template #cell-cost="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ formatCurrency(row.cost, auth.branchCurrency) }}</span>
      </template>

      <template #cell-accumulated_depreciation="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(row.accumulated_depreciation, auth.branchCurrency) }}</span>
      </template>

      <template #cell-net_book_value="{ row }">
        <span class="text-sm font-medium" :class="computeNetBookValue(row) > 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'">
          {{ formatCurrency(computeNetBookValue(row), auth.branchCurrency) }}
        </span>
      </template>

      <template #cell-status="{ row }">
        <StatusBadge :status="row.status" />
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="View"
            @click="viewAsset(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            v-if="auth.hasPermission('accounting:edit') && row.status === 'active'"
            type="button"
            class="p-1.5 text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Edit"
            @click="editAsset(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
          </button>
          <button
            v-if="auth.hasPermission('accounting:delete')"
            type="button"
            class="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Delete"
            @click="confirmDelete(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Fixed Asset"
      :message="`Are you sure you want to delete '${deleteTarget?.asset_name || deleteTarget?.name || ''}'? This action cannot be undone.`"
      confirm-text="Delete"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
