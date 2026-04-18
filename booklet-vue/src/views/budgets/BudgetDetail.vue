<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { getBudget, deleteBudget } from '@/api/budgets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const budget = ref(null)
const loading = ref(true)

const showDeleteDialog = ref(false)
const deleting = ref(false)

const totalRevenue = computed(() => {
  if (!budget.value?.revenue_items) return 0
  return budget.value.revenue_items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const totalExpenses = computed(() => {
  if (!budget.value?.expense_items) return 0
  return budget.value.expense_items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const netBudget = computed(() => totalRevenue.value - totalExpenses.value)

async function fetchBudget() {
  loading.value = true
  try {
    const { data } = await getBudget(route.params.id)
    budget.value = data
  } catch (error) {
    console.error('Failed to fetch budget:', error)
    toast.show('Failed to load budget', 'error')
    router.push({ name: 'BudgetList' })
  } finally {
    loading.value = false
  }
}

function editBudget() {
  router.push({ name: 'BudgetEdit', params: { id: route.params.id } })
}

function viewVsActual() {
  router.push({ name: 'BudgetVsActual', params: { id: route.params.id } })
}

function confirmDelete() {
  showDeleteDialog.value = true
}

async function handleDelete() {
  deleting.value = true
  try {
    await deleteBudget(route.params.id)
    toast.show('Budget deleted successfully', 'success')
    router.push({ name: 'BudgetList' })
  } catch (error) {
    console.error('Failed to delete budget:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to delete budget'
    toast.show(message, 'error')
  } finally {
    deleting.value = false
  }
}

function goBack() {
  router.push({ name: 'BudgetList' })
}

function getAccountName(item) {
  return item.account_name || item.account?.name || item.account?.code || '—'
}

onMounted(() => {
  fetchBudget()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Budget Details"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Budgets', to: { name: 'BudgetList' } },
        { text: budget?.name || 'Details' }
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
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors"
            @click="viewVsActual"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
            vs Actual
          </button>
          <button
            v-if="auth.hasPermission('budgets:edit')"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
            @click="editBudget"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
            Edit
          </button>
          <button
            v-if="auth.hasPermission('budgets:delete')"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
            @click="confirmDelete"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
            Delete
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading budget..." />

    <template v-else-if="budget">
      <!-- Budget Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ budget.name }}</h2>
              <StatusBadge :status="budget.status" />
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Fiscal Year: {{ budget.fiscal_year_name || budget.fiscal_year || '—' }}
            </p>
            <p v-if="budget.description" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ budget.description }}</p>
          </div>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-emerald-200 dark:border-emerald-800 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Budgeted Revenue</p>
          <p class="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{{ formatCurrency(totalRevenue, auth.branchCurrency) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-red-200 dark:border-red-800 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Budgeted Expenses</p>
          <p class="text-xl font-bold text-red-600 dark:text-red-400 mt-1">{{ formatCurrency(totalExpenses, auth.branchCurrency) }}</p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-4" :class="netBudget >= 0 ? 'border-gray-200 dark:border-gray-700' : 'border-red-200 dark:border-red-800'">
          <p class="text-sm text-gray-500 dark:text-gray-400">Net Budget</p>
          <p class="text-xl font-bold mt-1" :class="netBudget >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400'">
            {{ formatCurrency(netBudget, auth.branchCurrency) }}
          </p>
        </div>
      </div>

      <!-- Revenue Items -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Revenue Line Items</h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Monthly Amount</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Annual Amount</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="(item, index) in (budget.revenue_items || [])" :key="'rev-' + index" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ getAccountName(item) }}</td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(item.amount, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right text-sm font-medium text-emerald-600 dark:text-emerald-400">{{ formatCurrency((Number(item.amount) || 0) * 12, auth.branchCurrency) }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <td class="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white">Total</td>
                <td class="px-4 py-3 text-right text-sm font-bold text-gray-900 dark:text-white">{{ formatCurrency(totalRevenue, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right text-sm font-bold text-emerald-600 dark:text-emerald-400">{{ formatCurrency(totalRevenue * 12, auth.branchCurrency) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Expense Items -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-4">Expense Line Items</h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Monthly Amount</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Annual Amount</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr v-for="(item, index) in (budget.expense_items || [])" :key="'exp-' + index" class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{{ getAccountName(item) }}</td>
                <td class="px-4 py-3 text-right text-sm text-gray-700 dark:text-gray-300">{{ formatCurrency(item.amount, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right text-sm font-medium text-red-600 dark:text-red-400">{{ formatCurrency((Number(item.amount) || 0) * 12, auth.branchCurrency) }}</td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <td class="px-4 py-3 text-sm font-semibold text-gray-900 dark:text-white">Total</td>
                <td class="px-4 py-3 text-right text-sm font-bold text-gray-900 dark:text-white">{{ formatCurrency(totalExpenses, auth.branchCurrency) }}</td>
                <td class="px-4 py-3 text-right text-sm font-bold text-red-600 dark:text-red-400">{{ formatCurrency(totalExpenses * 12, auth.branchCurrency) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </template>

    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Budget"
      :message="`Are you sure you want to delete budget '${budget?.name || ''}'? This action cannot be undone.`"
      confirm-text="Delete"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
