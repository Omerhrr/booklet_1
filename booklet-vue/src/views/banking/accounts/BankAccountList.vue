<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import StatCard from '@/components/common/StatCard.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import * as bankingApi from '@/api/banking'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const accounts = ref([])
const loading = ref(true)
const showDeleteDialog = ref(false)
const selectedAccount = ref(null)
const deleting = ref(false)

const breadcrumbs = [
  { text: 'Banking' },
  { text: 'Bank Accounts' },
]

const accountTypeVariantMap = {
  checking: 'info',
  savings: 'success',
}

const columns = [
  { key: 'account_name', label: 'Account Name', sortable: true },
  { key: 'bank_name', label: 'Bank', sortable: true },
  { key: 'account_number', label: 'Account Number', sortable: true },
  { key: 'account_type', label: 'Type', sortable: true },
  { key: 'currency', label: 'Currency', sortable: true },
  { key: 'balance', label: 'Current Balance', sortable: true, class: 'text-right' },
  { key: 'status', label: 'Status', sortable: true },
]

const totalBalance = computed(() => {
  return accounts.value.reduce((sum, acc) => sum + (Number(acc.balance) || 0), 0)
})

function formatBalance(amount, currency) {
  return formatCurrency(amount, currency || authStore.branchCurrency)
}

async function fetchAccounts() {
  loading.value = true
  try {
    const { data } = await bankingApi.listBankAccounts()
    accounts.value = Array.isArray(data) ? data : data.items || data.accounts || []
  } catch (error) {
    console.error('Failed to fetch bank accounts:', error)
    toastStore.show('Failed to load bank accounts', 'error')
  } finally {
    loading.value = false
  }
}

function viewAccount(account) {
  router.push({ name: 'BankAccountDetail', params: { id: account.id } })
}

function confirmDelete(account) {
  selectedAccount.value = account
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!selectedAccount.value) return
  deleting.value = true
  try {
    await bankingApi.deleteBankAccount(selectedAccount.value.id)
    toastStore.show('Bank account deleted successfully')
    await fetchAccounts()
  } catch (error) {
    console.error('Failed to delete bank account:', error)
    toastStore.show('Failed to delete bank account', 'error')
  } finally {
    deleting.value = false
    selectedAccount.value = null
  }
}

onMounted(fetchAccounts)
</script>

<template>
  <div>
    <PageHeader title="Bank Accounts" :breadcrumbs="breadcrumbs">
      <template #actions>
        <router-link
          v-if="authStore.hasPermission('banking:create')"
          :to="{ name: 'BankAccountCreate' }"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Account
        </router-link>
      </template>
    </PageHeader>

    <!-- Total Balance Card -->
    <StatCard
      v-if="accounts.length > 0"
      title="Total Balance (All Accounts)"
      :value="formatBalance(totalBalance)"
      color="green"
      icon="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"
      class="mb-6"
    />

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && accounts.length === 0"
      title="No bank accounts yet"
      message="Get started by adding your first bank account."
      :action-text="authStore.hasPermission('banking:create') ? 'Add Account' : ''"
      action-route="/banking/accounts/new"
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="accounts"
        :loading="loading"
        search-placeholder="Search bank accounts..."
      >
        <!-- Account Name Column -->
        <template #cell-account_name="{ row }">
          <button
            type="button"
            class="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
            @click="viewAccount(row)"
          >
            {{ row.account_name }}
          </button>
        </template>

        <!-- Account Number Column -->
        <template #cell-account_number="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300 font-mono">
            {{ row.account_number }}
          </span>
        </template>

        <!-- Account Type Column -->
        <template #cell-account_type="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300 capitalize">
            {{ row.account_type }}
          </span>
        </template>

        <!-- Currency Column -->
        <template #cell-currency="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300 font-medium">
            {{ row.currency || 'NGN' }}
          </span>
        </template>

        <!-- Balance Column -->
        <template #cell-balance="{ row }">
          <span
            :class="[
              'text-sm font-bold text-right block',
              (row.balance || 0) >= 0 ? 'text-gray-900 dark:text-white' : 'text-red-600 dark:text-red-400',
            ]"
          >
            {{ formatBalance(row.balance, row.currency) }}
          </span>
        </template>

        <!-- Status Column -->
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" />
        </template>

        <!-- Actions -->
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <!-- View -->
            <button
              type="button"
              class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="View"
              @click="viewAccount(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>

            <!-- Delete -->
            <button
              v-if="authStore.hasPermission('banking:delete')"
              type="button"
              class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
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
    </div>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Bank Account"
      :message="`Are you sure you want to delete '${selectedAccount?.account_name}'? This action cannot be undone and will remove all associated transaction history.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
