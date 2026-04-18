<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import Pagination from '@/components/common/Pagination.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { downloadBlob } from '@/utils/export'
import { formatDate } from '@/utils/dates'
import * as bankingApi from '@/api/banking'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const account = ref(null)
const transactions = ref([])
const loading = ref(true)
const deleting = ref(false)
const showDeleteDialog = ref(false)
const exportingPdf = ref(false)
const exportingExcel = ref(false)

const currentPage = ref(1)
const totalPages = ref(1)

const breadcrumbs = computed(() => [
  { text: 'Banking', to: '/banking' },
  { text: 'Accounts', to: '/banking/accounts' },
  { text: account.value?.account_name || 'Account Details' },
])

function formatAmount(amount) {
  return formatCurrency(amount, account.value?.currency || authStore.branchCurrency)
}

async function fetchAccount() {
  loading.value = true
  try {
    const { data } = await bankingApi.getBankAccount(route.params.id)
    account.value = data
    transactions.value = data.transactions || []
  } catch (error) {
    console.error('Failed to fetch bank account:', error)
    toastStore.show('Failed to load bank account', 'error')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push({ name: 'BankAccountList' })
}

async function handleDelete() {
  deleting.value = true
  try {
    await bankingApi.deleteBankAccount(route.params.id)
    toastStore.show('Bank account deleted successfully')
    router.push({ name: 'BankAccountList' })
  } catch (error) {
    console.error('Failed to delete bank account:', error)
    toastStore.show('Failed to delete bank account', 'error')
  } finally {
    deleting.value = false
  }
}

async function exportPdf() {
  exportingPdf.value = true
  try {
    const { data } = await bankingApi.exportStatementPdf(route.params.id)
    const blob = new Blob([data], { type: 'application/pdf' })
    downloadBlob(blob, `Statement_${account.value.account_name}.pdf`)
    toastStore.show('PDF statement downloaded')
  } catch (error) {
    console.error('Failed to export PDF:', error)
    toastStore.show('Failed to export statement', 'error')
  } finally {
    exportingPdf.value = false
  }
}

async function exportExcel() {
  exportingExcel.value = true
  try {
    const { data } = await bankingApi.exportStatementExcel(route.params.id)
    const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    downloadBlob(blob, `Statement_${account.value.account_name}.xlsx`)
    toastStore.show('Excel statement downloaded')
  } catch (error) {
    console.error('Failed to export Excel:', error)
    toastStore.show('Failed to export statement', 'error')
  } finally {
    exportingExcel.value = false
  }
}

function handlePageChange(page) {
  currentPage.value = page
}

onMounted(fetchAccount)
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading account..." />
    </div>

    <template v-else-if="account">
      <PageHeader :title="account.account_name" :breadcrumbs="breadcrumbs">
        <template #actions>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="goBack"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Back
            </button>

            <button
              type="button"
              :disabled="exportingPdf"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              @click="exportPdf"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              {{ exportingPdf ? 'Exporting...' : 'Export PDF' }}
            </button>

            <button
              type="button"
              :disabled="exportingExcel"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              @click="exportExcel"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              {{ exportingExcel ? 'Exporting...' : 'Export Excel' }}
            </button>

            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-red-700 bg-red-50 border border-red-300 rounded-lg hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-700 dark:hover:bg-red-900/50 transition-colors"
              @click="showDeleteDialog = true"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
              Delete
            </button>
          </div>
        </template>
      </PageHeader>

      <!-- Account Info Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-1">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ account.bank_name }}</h2>
              <StatusBadge :status="account.account_type || 'checking'" :variant-map="{ checking: 'info', savings: 'success' }" />
              <StatusBadge :status="account.status" />
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Account: <span class="font-mono">{{ account.account_number }}</span>
              <span v-if="account.currency" class="ml-3">Currency: <span class="font-medium text-gray-700 dark:text-gray-300">{{ account.currency }}</span></span>
            </p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-500 dark:text-gray-400">Current Balance</p>
            <p
              :class="[
                'text-2xl font-bold',
                (account.balance || 0) >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400',
              ]"
            >
              {{ formatAmount(account.balance) }}
            </p>
          </div>
        </div>
        <p v-if="account.description" class="mt-3 text-sm text-gray-500 dark:text-gray-400">{{ account.description }}</p>
      </div>

      <!-- Transactions Table -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Transactions</h3>
        </div>

        <div v-if="transactions.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
          <svg class="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
          </svg>
          <p class="text-sm text-gray-500 dark:text-gray-400">No transactions found for this account.</p>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Reference</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Description</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Debit</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Credit</th>
                <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Balance</th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="txn in transactions"
                :key="txn.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
                  {{ formatDate(txn.date, 'short') }}
                </td>
                <td class="px-6 py-4 text-sm font-mono text-gray-700 dark:text-gray-300 whitespace-nowrap">
                  {{ txn.reference || '—' }}
                </td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                  {{ txn.description || '—' }}
                </td>
                <td class="px-6 py-4 text-sm font-medium text-red-600 dark:text-red-400 text-right whitespace-nowrap">
                  {{ txn.debit ? formatAmount(txn.debit) : '—' }}
                </td>
                <td class="px-6 py-4 text-sm font-medium text-green-600 dark:text-green-400 text-right whitespace-nowrap">
                  {{ txn.credit ? formatAmount(txn.credit) : '—' }}
                </td>
                <td class="px-6 py-4 text-sm font-bold text-gray-900 dark:text-white text-right whitespace-nowrap">
                  {{ formatAmount(txn.balance) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <Pagination
            :current-page="currentPage"
            :total-pages="totalPages"
            @page-change="handlePageChange"
          />
        </div>
      </div>
    </template>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Bank Account"
      :message="`Are you sure you want to delete '${account?.account_name}'? This will permanently remove this account and all its transaction history.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
