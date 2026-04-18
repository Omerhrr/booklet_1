<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import {
  getFixedAsset,
  deleteFixedAsset,
  depreciateAsset,
  disposeAsset,
  writeOffAsset,
} from '@/api/fixedAssets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const asset = ref(null)
const loading = ref(true)

// Depreciation modal
const showDepreciationModal = ref(false)
const depreciationForm = ref({
  date: new Date().toISOString().split('T')[0],
  amount: '',
  notes: '',
})
const depreciationErrors = ref({})
const depreciating = ref(false)

// Disposal modal
const showDisposalModal = ref(false)
const disposalForm = ref({
  date: new Date().toISOString().split('T')[0],
  disposal_value: '',
  notes: '',
})
const disposalErrors = ref({})
const disposing = ref(false)

// Delete / Write-off confirmation
const showDeleteDialog = ref(false)
const showWriteOffDialog = ref(false)
const deleting = ref(false)
const writingOff = ref(false)

const depreciationMethodLabel = computed(() => {
  if (!asset.value?.depreciation_method) return '—'
  return asset.value.depreciation_method === 'straight_line'
    ? 'Straight-line'
    : 'Declining Balance'
})

const netBookValue = computed(() => {
  if (!asset.value) return 0
  return (Number(asset.value.cost) || 0) - (Number(asset.value.accumulated_depreciation) || 0)
})

const remainingLife = computed(() => {
  if (!asset.value) return 0
  const usefulLife = Number(asset.value.useful_life) || 0
  const schedule = asset.value.depreciation_schedule || []
  return Math.max(0, usefulLife - schedule.length)
})

async function fetchAsset() {
  loading.value = true
  try {
    const { data } = await getFixedAsset(route.params.id)
    asset.value = data
  } catch (error) {
    console.error('Failed to fetch fixed asset:', error)
    toast.show('Failed to load fixed asset', 'error')
    router.push({ name: 'FixedAssetList' })
  } finally {
    loading.value = false
  }
}

function editAsset() {
  router.push({ name: 'FixedAssetEdit', params: { id: route.params.id } })
}

function openDepreciationModal() {
  depreciationForm.value = {
    date: new Date().toISOString().split('T')[0],
    amount: '',
    notes: '',
  }
  depreciationErrors.value = {}
  showDepreciationModal.value = true
}

function closeDepreciationModal() {
  showDepreciationModal.value = false
}

function validateDepreciation() {
  const newErrors = {}
  if (!depreciationForm.value.date) newErrors.date = 'Date is required'
  if (!depreciationForm.value.amount || Number(depreciationForm.value.amount) <= 0) {
    newErrors.amount = 'Valid amount is required'
  }
  depreciationErrors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleRecordDepreciation() {
  if (!validateDepreciation()) return
  depreciating.value = true
  try {
    await depreciateAsset(route.params.id, {
      date: depreciationForm.value.date,
      amount: Number(depreciationForm.value.amount),
      notes: depreciationForm.value.notes,
    })
    toast.show('Depreciation recorded successfully', 'success')
    closeDepreciationModal()
    await fetchAsset()
  } catch (error) {
    console.error('Failed to record depreciation:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to record depreciation'
    toast.show(message, 'error')
  } finally {
    depreciating.value = false
  }
}

function openDisposalModal() {
  disposalForm.value = {
    date: new Date().toISOString().split('T')[0],
    disposal_value: String(netBookValue.value),
    notes: '',
  }
  disposalErrors.value = {}
  showDisposalModal.value = true
}

function closeDisposalModal() {
  showDisposalModal.value = false
}

function validateDisposal() {
  const newErrors = {}
  if (!disposalForm.value.date) newErrors.date = 'Date is required'
  disposalErrors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleDispose() {
  if (!validateDisposal()) return
  disposing.value = true
  try {
    await disposeAsset(route.params.id, {
      date: disposalForm.value.date,
      disposal_value: Number(disposalForm.value.disposal_value) || 0,
      notes: disposalForm.value.notes,
    })
    toast.show('Asset disposed successfully', 'success')
    closeDisposalModal()
    await fetchAsset()
  } catch (error) {
    console.error('Failed to dispose asset:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to dispose asset'
    toast.show(message, 'error')
  } finally {
    disposing.value = false
  }
}

async function handleWriteOff() {
  writingOff.value = true
  try {
    await writeOffAsset(route.params.id)
    toast.show('Asset written off successfully', 'success')
    await fetchAsset()
  } catch (error) {
    console.error('Failed to write off asset:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to write off asset'
    toast.show(message, 'error')
  } finally {
    writingOff.value = false
  }
}

async function handleDelete() {
  deleting.value = true
  try {
    await deleteFixedAsset(route.params.id)
    toast.show('Asset deleted successfully', 'success')
    router.push({ name: 'FixedAssetList' })
  } catch (error) {
    console.error('Failed to delete asset:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to delete asset'
    toast.show(message, 'error')
  } finally {
    deleting.value = false
  }
}

function goBack() {
  router.push({ name: 'FixedAssetList' })
}

onMounted(() => {
  fetchAsset()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Fixed Asset Details"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Fixed Assets', to: { name: 'FixedAssetList' } },
        { text: asset?.asset_name || asset?.name || 'Details' }
      ]"
    >
      <template #actions>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="goBack"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Back
          </button>
          <button
            v-if="auth.hasPermission('accounting:edit') && asset?.status === 'active'"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
            @click="editAsset"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
            Edit
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading fixed asset..." />

    <template v-else-if="asset">
      <!-- Asset Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ asset.asset_name || asset.name }}</h2>
              <StatusBadge :status="asset.status" />
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Purchased {{ formatDate(asset.purchase_date, 'short') }}
              <span class="mx-2">•</span>
              {{ asset.category_name || asset.category || 'No category' }}
            </p>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <button
              v-if="asset.status === 'active'"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors"
              @click="openDepreciationModal"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
              </svg>
              Record Depreciation
            </button>
            <button
              v-if="asset.status === 'active'"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
              @click="openDisposalModal"
            >
              Dispose
            </button>
            <button
              v-if="asset.status === 'active'"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              @click="showWriteOffDialog = true"
            >
              Write Off
            </button>
            <button
              v-if="auth.hasPermission('accounting:delete')"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
              @click="showDeleteDialog = true"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
              Delete
            </button>
          </div>
        </div>
      </div>

      <!-- Asset Info & Financial Details -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Asset Information</h3>
          <dl class="space-y-4">
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Purchase Date</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatDate(asset.purchase_date, 'short') }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Category</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ asset.category_name || asset.category || '—' }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Depreciation Method</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ depreciationMethodLabel }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Useful Life</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ asset.useful_life }} years ({{ remainingLife }} remaining)</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Location</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ asset.location || '—' }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Department</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ asset.department || '—' }}</dd>
            </div>
          </dl>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Financial Summary</h3>
          <dl class="space-y-4">
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Original Cost</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatCurrency(asset.cost, auth.branchCurrency) }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Salvage Value</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatCurrency(asset.salvage_value, auth.branchCurrency) }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Depreciable Amount</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatCurrency((Number(asset.cost) || 0) - (Number(asset.salvage_value) || 0), auth.branchCurrency) }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Accum. Depreciation</dt>
              <dd class="text-sm font-medium text-red-600 dark:text-red-400">{{ formatCurrency(asset.accumulated_depreciation, auth.branchCurrency) }}</dd>
            </div>
            <div class="border-t border-gray-200 dark:border-gray-700 pt-3 flex items-start justify-between">
              <dt class="text-sm font-semibold text-gray-700 dark:text-gray-300">Net Book Value</dt>
              <dd class="text-lg font-bold" :class="netBookValue > 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'">
                {{ formatCurrency(netBookValue, auth.branchCurrency) }}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Notes -->
      <div v-if="asset.notes" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Notes</h3>
        <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ asset.notes }}</p>
      </div>

      <!-- Depreciation Schedule -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Depreciation Schedule</h3>
        <div v-if="(asset.depreciation_schedule || []).length === 0" class="text-center py-8">
          <svg class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
          </svg>
          <p class="text-sm text-gray-500 dark:text-gray-400">No depreciation recorded yet</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Period</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Depreciation</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Accumulated</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Net Book Value</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(entry, index) in asset.depreciation_schedule"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ entry.period || `Year ${index + 1}` }}</td>
                <td class="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{{ formatDate(entry.date, 'short') }}</td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(entry.amount, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(entry.accumulated_depreciation, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right text-sm font-medium text-gray-900 dark:text-white">{{ formatCurrency(entry.net_book_value, auth.branchCurrency) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Record Depreciation Modal -->
    <Modal
      v-model:show="showDepreciationModal"
      title="Record Depreciation"
      size="md"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <span class="text-sm text-gray-500 dark:text-gray-400">Current Net Book Value</span>
          <span class="text-lg font-bold text-gray-900 dark:text-white">{{ formatCurrency(netBookValue, auth.branchCurrency) }}</span>
        </div>

        <DateInput
          v-model="depreciationForm.date"
          label="Depreciation Date"
          name="date"
          :required="true"
          :error="depreciationErrors.date"
        />

        <TextInput
          v-model="depreciationForm.amount"
          label="Depreciation Amount"
          name="amount"
          type="number"
          placeholder="0.00"
          :required="true"
          :error="depreciationErrors.amount"
        />

        <TextareaInput
          v-model="depreciationForm.notes"
          label="Notes"
          name="notes"
          placeholder="Optional notes..."
          :rows="2"
        />
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          @click="closeDepreciationModal"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="depreciating"
          class="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleRecordDepreciation"
        >
          {{ depreciating ? 'Recording...' : 'Record Depreciation' }}
        </button>
      </template>
    </Modal>

    <!-- Disposal Modal -->
    <Modal
      v-model:show="showDisposalModal"
      title="Dispose Asset"
      size="md"
    >
      <div class="space-y-4">
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
          <span class="text-sm text-gray-500 dark:text-gray-400">Net Book Value</span>
          <span class="text-lg font-bold text-gray-900 dark:text-white">{{ formatCurrency(netBookValue, auth.branchCurrency) }}</span>
        </div>

        <DateInput
          v-model="disposalForm.date"
          label="Disposal Date"
          name="date"
          :required="true"
          :error="disposalErrors.date"
        />

        <TextInput
          v-model="disposalForm.disposal_value"
          label="Disposal Value"
          name="disposal_value"
          type="number"
          placeholder="0.00"
        />

        <TextareaInput
          v-model="disposalForm.notes"
          label="Notes"
          name="notes"
          placeholder="Reason for disposal..."
          :rows="2"
        />
      </div>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
          @click="closeDisposalModal"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="disposing"
          class="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleDispose"
        >
          {{ disposing ? 'Disposing...' : 'Dispose Asset' }}
        </button>
      </template>
    </Modal>

    <!-- Write Off Confirmation -->
    <ConfirmDialog
      v-model:show="showWriteOffDialog"
      title="Write Off Asset"
      message="Are you sure you want to write off this asset? This will set its net book value to zero and cannot be undone."
      confirm-text="Write Off"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleWriteOff"
    />

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Fixed Asset"
      message="Are you sure you want to permanently delete this asset? This action cannot be undone."
      confirm-text="Delete"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
