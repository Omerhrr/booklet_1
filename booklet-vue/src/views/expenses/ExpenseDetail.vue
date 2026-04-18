<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { getExpense, deleteExpense } from '@/api/expenses'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const expense = ref(null)
const loading = ref(true)

const showDeleteDialog = ref(false)
const deleting = ref(false)

async function fetchExpense() {
  loading.value = true
  try {
    const { data } = await getExpense(route.params.id)
    expense.value = data
  } catch (error) {
    console.error('Failed to fetch expense:', error)
    toast.show('Failed to load expense', 'error')
    router.push({ name: 'ExpenseList' })
  } finally {
    loading.value = false
  }
}

function editExpense() {
  router.push({ name: 'ExpenseEdit', params: { id: route.params.id } })
}

function confirmDelete() {
  showDeleteDialog.value = true
}

async function handleDelete() {
  deleting.value = true
  try {
    await deleteExpense(route.params.id)
    toast.show('Expense deleted successfully', 'success')
    router.push({ name: 'ExpenseList' })
  } catch (error) {
    console.error('Failed to delete expense:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to delete expense'
    toast.show(message, 'error')
  } finally {
    deleting.value = false
  }
}

function goBack() {
  router.push({ name: 'ExpenseList' })
}

const paymentMethodLabel = computed(() => {
  if (!expense.value?.payment_method) return '—'
  return expense.value.payment_method.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
})

onMounted(() => {
  fetchExpense()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Expense Details"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Expenses', to: { name: 'ExpenseList' } },
        { text: expense?.reference || 'Details' }
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
            v-if="auth.hasPermission('expenses:edit')"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
            @click="editExpense"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
            Edit
          </button>
          <button
            v-if="auth.hasPermission('expenses:delete')"
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

    <LoadingSpinner v-if="loading" text="Loading expense..." />

    <template v-else-if="expense">
      <!-- Expense Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                {{ expense.reference || `EXP-${String(expense.id).padStart(4, '0')}` }}
              </h2>
              <StatusBadge :status="expense.status" />
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Created {{ formatDate(expense.created_at, 'datetime') }}
            </p>
          </div>
          <div class="text-right">
            <p class="text-2xl font-bold text-gray-900 dark:text-white">
              {{ formatCurrency(expense.amount, auth.branchCurrency) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Expense Details -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Expense Information</h3>
          <dl class="space-y-4">
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Date</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ formatDate(expense.date, 'short') }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Category</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ expense.category_name || expense.category || '—' }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Payment Method</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ paymentMethodLabel }}</dd>
            </div>
            <div class="flex items-start justify-between">
              <dt class="text-sm text-gray-500 dark:text-gray-400">Bank Account</dt>
              <dd class="text-sm font-medium text-gray-900 dark:text-white">{{ expense.bank_account_name || expense.bank_account?.name || '—' }}</dd>
            </div>
          </dl>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Description & Notes</h3>
          <div class="space-y-4">
            <div>
              <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Description</p>
              <p class="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">{{ expense.description || '—' }}</p>
            </div>
            <div v-if="expense.notes">
              <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Notes</p>
              <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ expense.notes }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Expense"
      message="Are you sure you want to delete this expense? This action cannot be undone."
      confirm-text="Delete"
      cancel-text="Cancel"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
