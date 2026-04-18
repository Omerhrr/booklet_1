<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { listBills } from '@/api/purchases'
import { useAuthStore } from '@/stores/auth'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const auth = useAuthStore()

const bills = ref([])
const loading = ref(true)
const activeStatus = ref('all')
const searchQuery = ref('')

const statusTabs = [
  { key: 'all', label: 'All' },
  { key: 'draft', label: 'Draft' },
  { key: 'received', label: 'Received' },
  { key: 'partial', label: 'Partial' },
  { key: 'paid', label: 'Paid' },
  { key: 'overdue', label: 'Overdue' },
  { key: 'cancelled', label: 'Cancelled' },
]

const columns = [
  { key: 'bill_number', label: 'Bill #', sortable: true },
  { key: 'vendor_name', label: 'Vendor', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'due_date', label: 'Due Date', sortable: true },
  { key: 'subtotal', label: 'Amount', sortable: true },
  { key: 'tax_total', label: 'Tax', sortable: true },
  { key: 'total', label: 'Total', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchBills() {
  loading.value = true
  try {
    const params = {}
    if (activeStatus.value !== 'all') {
      params.status = activeStatus.value
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    const { data } = await listBills(params)
    bills.value = Array.isArray(data) ? data : data.items || data.bills || []
  } catch (error) {
    console.error('Failed to fetch bills:', error)
    bills.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch(query) {
  searchQuery.value = query
  fetchBills()
}

function viewBill(bill) {
  router.push({ name: 'BillDetail', params: { id: bill.id } })
}

function createNewBill() {
  router.push({ name: 'BillCreate' })
}

watch(activeStatus, () => {
  fetchBills()
})

onMounted(() => {
  fetchBills()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Bills"
      :breadcrumbs="[
        { text: 'Purchases' },
        { text: 'Bills' }
      ]"
    >
      <template #actions>
        <button
          v-if="auth.hasPermission('bills:create')"
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          @click="createNewBill"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Bill
        </button>
      </template>
    </PageHeader>

    <!-- Status Filter Tabs -->
    <div class="border-b border-gray-200 dark:border-gray-700">
      <nav class="flex gap-0 -mb-px overflow-x-auto" aria-label="Status filter">
        <button
          v-for="tab in statusTabs"
          :key="tab.key"
          type="button"
          :class="[
            'whitespace-nowrap px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            activeStatus === tab.key
              ? 'border-violet-500 text-violet-600 dark:text-violet-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
          ]"
          @click="activeStatus = tab.key"
        >
          {{ tab.label }}
          <span
            v-if="activeStatus === tab.key"
            class="ml-2 text-xs bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400 px-2 py-0.5 rounded-full"
          >
            {{ bills.length }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="bills"
      :loading="loading"
      :searchable="false"
      empty-message="No bills found"
    >
      <template #cell-bill_number="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-300 transition-colors"
          @click="viewBill(row)"
        >
          {{ row.bill_number || `BILL-${String(row.id).padStart(4, '0')}` }}
        </button>
      </template>

      <template #cell-vendor_name="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">
          {{ row.vendor_name || row.vendor?.name || '—' }}
        </span>
      </template>

      <template #cell-date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.date, 'short') }}</span>
      </template>

      <template #cell-due_date="{ row }">
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(row.due_date, 'short') }}</span>
      </template>

      <template #cell-subtotal="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(row.subtotal, auth.branchCurrency) }}</span>
      </template>

      <template #cell-tax_total="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(row.tax_total, auth.branchCurrency) }}</span>
      </template>

      <template #cell-total="{ row }">
        <span class="text-sm font-medium text-gray-900 dark:text-white">{{ formatCurrency(row.total, auth.branchCurrency) }}</span>
      </template>

      <template #cell-status="{ row }">
        <StatusBadge :status="row.status" />
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="View"
            @click="viewBill(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Search Bar -->
    <div class="flex justify-end">
      <div class="relative w-full max-w-xs">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <svg class="w-4 h-4 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
        </div>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search bills..."
          class="block w-full pl-10 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-colors"
          @input.debounce.300ms="handleSearch(searchQuery)"
        />
      </div>
    </div>
  </div>
</template>
