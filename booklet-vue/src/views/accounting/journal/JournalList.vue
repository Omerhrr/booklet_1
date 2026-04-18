<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { listJournalEntries } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const journalEntries = ref([])
const loading = ref(true)
const activeStatus = ref('all')

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'posted', label: 'Posted' },
]

const columns = [
  { key: 'entry_number', label: 'Entry #', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'description', label: 'Description', sortable: true },
  { key: 'debit_total', label: 'Debit Total', sortable: true },
  { key: 'credit_total', label: 'Credit Total', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchJournalEntries() {
  loading.value = true
  try {
    const params = {}
    if (activeStatus.value !== 'all') {
      params.status = activeStatus.value
    }
    const { data } = await listJournalEntries(params)
    journalEntries.value = Array.isArray(data) ? data : data.items || data.entries || []
  } catch (error) {
    console.error('Failed to fetch journal entries:', error)
    journalEntries.value = []
  } finally {
    loading.value = false
  }
}

function viewEntry(row) {
  router.push({ name: 'JournalDetail', params: { id: row.id } })
}

function createEntry() {
  router.push({ name: 'JournalCreate' })
}

watch(activeStatus, () => {
  fetchJournalEntries()
})

onMounted(() => {
  fetchJournalEntries()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Journal Entries"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Journal Entries' }
      ]"
    >
      <template #actions>
        <button
          v-if="auth.hasPermission('journal:create')"
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          @click="createEntry"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Entry
        </button>
      </template>
    </PageHeader>

    <!-- Status Filter -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <SelectInput
          v-model="activeStatus"
          label="Filter by Status"
          name="status"
          :options="statusOptions"
        />
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="journalEntries"
      :loading="loading"
      :searchable="false"
      empty-message="No journal entries found"
    >
      <template #cell-entry_number="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors"
          @click="viewEntry(row)"
        >
          {{ row.entry_number || `JE-${String(row.id).padStart(4, '0')}` }}
        </button>
      </template>

      <template #cell-date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
      </template>

      <template #cell-description="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300 max-w-[250px] truncate block">{{ row.description || '—' }}</span>
      </template>

      <template #cell-debit_total="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">
          {{ formatCurrency(row.debit_total || row.total_debit || 0, auth.branchCurrency) }}
        </span>
      </template>

      <template #cell-credit_total="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">
          {{ formatCurrency(row.credit_total || row.total_credit || 0, auth.branchCurrency) }}
        </span>
      </template>

      <template #cell-status="{ row }">
        <StatusBadge :status="row.status" />
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="View Details"
            @click="viewEntry(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>
  </div>
</template>
