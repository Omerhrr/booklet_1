<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { listInvoices } from '@/api/sales'
import { useAuthStore } from '@/stores/auth'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const auth = useAuthStore()

const invoices = ref([])
const loading = ref(true)
const activeStatus = ref('all')
const searchQuery = ref('')

const statusTabs = [
  { key: 'all', label: 'All' },
  { key: 'draft', label: 'Draft' },
  { key: 'sent', label: 'Sent' },
  { key: 'paid', label: 'Paid' },
  { key: 'overdue', label: 'Overdue' },
  { key: 'cancelled', label: 'Cancelled' },
]

const columns = [
  { key: 'invoice_number', label: 'Invoice #', sortable: true },
  { key: 'customer_name', label: 'Customer', sortable: true },
  { key: 'date', label: 'Date', sortable: true },
  { key: 'due_date', label: 'Due Date', sortable: true },
  { key: 'subtotal', label: 'Amount', sortable: true },
  { key: 'tax_total', label: 'Tax', sortable: true },
  { key: 'total', label: 'Total', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchInvoices() {
  loading.value = true
  try {
    const params = {}
    if (activeStatus.value !== 'all') {
      params.status = activeStatus.value
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }
    const { data } = await listInvoices(params)
    invoices.value = Array.isArray(data) ? data : data.items || data.invoices || []
  } catch (error) {
    console.error('Failed to fetch invoices:', error)
    invoices.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch(query) {
  searchQuery.value = query
  fetchInvoices()
}

function viewInvoice(invoice) {
  router.push({ name: 'InvoiceDetail', params: { id: invoice.id } })
}

function createCreditNote(invoice) {
  router.push({ name: 'CreditNoteCreate', params: { id: invoice.id } })
}

function createNewInvoice() {
  router.push({ name: 'InvoiceCreate' })
}

watch(activeStatus, () => {
  fetchInvoices()
})

onMounted(() => {
  fetchInvoices()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Invoices"
      :breadcrumbs="[
        { text: 'Sales' },
        { text: 'Invoices' }
      ]"
    >
      <template #actions>
        <button
          v-if="auth.hasPermission('invoices:create')"
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          @click="createNewInvoice"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Invoice
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
              ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
          ]"
          @click="activeStatus = tab.key"
        >
          {{ tab.label }}
          <span
            v-if="activeStatus === tab.key"
            class="ml-2 text-xs bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full"
          >
            {{ invoices.length }}
          </span>
        </button>
      </nav>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="invoices"
      :loading="loading"
      :searchable="false"
      empty-message="No invoices found"
    >
      <template #cell-invoice_number="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors"
          @click="viewInvoice(row)"
        >
          {{ row.invoice_number || `INV-${String(row.id).padStart(4, '0')}` }}
        </button>
      </template>

      <template #cell-customer_name="{ row }">
        <span class="text-sm text-gray-900 dark:text-white font-medium">
          {{ row.customer_name || row.customer?.name || '—' }}
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
            @click="viewInvoice(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            v-if="row.status === 'draft' || row.status === 'sent'"
            type="button"
            class="p-1.5 text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Create Credit Note"
            @click="createCreditNote(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </button>
        </div>
      </template>
    </DataTable>

    <!-- Search Bar (below table for consistent UX) -->
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
          placeholder="Search invoices..."
          class="block w-full pl-10 pr-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
          @input.debounce.300ms="handleSearch(searchQuery)"
        />
      </div>
    </div>
  </div>
</template>
