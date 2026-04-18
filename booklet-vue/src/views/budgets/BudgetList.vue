<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { listBudgets, deleteBudget, getFiscalYears } from '@/api/budgets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const budgets = ref([])
const loading = ref(true)
const fiscalYears = ref([])
const filterFiscalYear = ref('')

const showDeleteDialog = ref(false)
const deleteTarget = ref(null)
const deleting = ref(false)

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'fiscal_year', label: 'Fiscal Year', sortable: true },
  { key: 'total_revenue', label: 'Total Revenue', sortable: true },
  { key: 'total_expenses', label: 'Total Expenses', sortable: true },
  { key: 'variance', label: 'Variance', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchBudgets() {
  loading.value = true
  try {
    const params = {}
    if (filterFiscalYear.value) params.fiscal_year = filterFiscalYear.value

    const { data } = await listBudgets(params)
    budgets.value = Array.isArray(data) ? data : data.items || data.budgets || []
  } catch (error) {
    console.error('Failed to fetch budgets:', error)
    budgets.value = []
  } finally {
    loading.value = false
  }
}

async function fetchFiscalYears() {
  try {
    const { data } = await getFiscalYears()
    fiscalYears.value = (Array.isArray(data) ? data : data.fiscal_years || []).map(fy => ({
      value: fy.id || fy.year,
      label: fy.name || fy.label || String(fy.year || fy.id),
    }))
  } catch (error) {
    console.error('Failed to fetch fiscal years:', error)
  }
}

function viewBudget(budget) {
  router.push({ name: 'BudgetDetail', params: { id: budget.id } })
}

function editBudget(budget) {
  router.push({ name: 'BudgetEdit', params: { id: budget.id } })
}

function viewVsActual(budget) {
  router.push({ name: 'BudgetVsActual', params: { id: budget.id } })
}

function confirmDelete(budget) {
  deleteTarget.value = budget
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await deleteBudget(deleteTarget.value.id)
    toast.show('Budget deleted successfully', 'success')
    await fetchBudgets()
  } catch (error) {
    console.error('Failed to delete budget:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to delete budget'
    toast.show(message, 'error')
  } finally {
    deleting.value = false
    deleteTarget.value = null
  }
}

function computeVariance(budget) {
  const revenue = Number(budget.total_revenue) || 0
  const expenses = Number(budget.total_expenses) || 0
  return revenue - expenses
}

watch(filterFiscalYear, () => {
  fetchBudgets()
})

onMounted(() => {
  fetchBudgets()
  fetchFiscalYears()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Budgets"
      subtitle="Plan and track your financial budget"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Budgets' }
      ]"
    >
      <template #actions>
        <button
          v-if="auth.hasPermission('budgets:create')"
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          @click="router.push({ name: 'BudgetCreate' })"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Budget
        </button>
      </template>
    </PageHeader>

    <!-- Filter -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div class="flex flex-col sm:flex-row gap-4">
        <div class="sm:w-64">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Fiscal Year</label>
          <select
            v-model="filterFiscalYear"
            class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
          >
            <option value="">All Fiscal Years</option>
            <option v-for="fy in fiscalYears" :key="fy.value" :value="fy.value">{{ fy.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Data Table -->
    <DataTable
      :columns="columns"
      :data="budgets"
      :loading="loading"
      :searchable="true"
      search-placeholder="Search budgets..."
      empty-message="No budgets found"
    >
      <template #cell-name="{ row }">
        <button
          type="button"
          class="text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors"
          @click="viewBudget(row)"
        >
          {{ row.name }}
        </button>
      </template>

      <template #cell-fiscal_year="{ row }">
        <span class="text-sm text-gray-700 dark:text-gray-300">{{ row.fiscal_year_name || row.fiscal_year || '—' }}</span>
      </template>

      <template #cell-total_revenue="{ row }">
        <span class="text-sm font-medium text-emerald-600 dark:text-emerald-400">{{ formatCurrency(row.total_revenue, auth.branchCurrency) }}</span>
      </template>

      <template #cell-total_expenses="{ row }">
        <span class="text-sm font-medium text-red-600 dark:text-red-400">{{ formatCurrency(row.total_expenses, auth.branchCurrency) }}</span>
      </template>

      <template #cell-variance="{ row }">
        <span
          :class="[
            'text-sm font-medium',
            computeVariance(row) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
          ]"
        >
          {{ formatCurrency(computeVariance(row), auth.branchCurrency) }}
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
            @click="viewBudget(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Budget vs Actual"
            @click="viewVsActual(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          </button>
          <button
            v-if="auth.hasPermission('budgets:edit')"
            type="button"
            class="p-1.5 text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="Edit"
            @click="editBudget(row)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
          </button>
          <button
            v-if="auth.hasPermission('budgets:delete')"
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
      title="Delete Budget"
      :message="`Are you sure you want to delete budget '${deleteTarget?.name || ''}'? This action cannot be undone.`"
      confirm-text="Delete"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
