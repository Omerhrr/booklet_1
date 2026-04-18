<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import FileUpload from '@/components/common/FileUpload.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import * as bankingApi from '@/api/banking'

const authStore = useAuthStore()
const toastStore = useToastStore()

const accounts = ref([])
const selectedAccountId = ref('')
const accountStatus = ref(null)
const statementLines = ref([])
const unclearedTransactions = ref([])
const history = ref([])
const loading = ref(true)
const loadingStatus = ref(false)
const importing = ref(false)
const matching = ref(false)
const completing = ref(false)
const autoMatching = ref(false)

// Selection state
const selectedStatementLine = ref(null)
const selectedCashbookEntry = ref(null)

const breadcrumbs = [
  { text: 'Banking' },
  { text: 'Bank Reconciliation' },
]

const accountOptions = computed(() => {
  return accounts.value.map(acc => ({
    value: acc.id,
    label: `${acc.account_name} (${acc.bank_name})`,
  }))
})

function formatAmount(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

const statementBalance = computed(() => {
  return accountStatus.value?.statement_balance || 0
})

const bookBalance = computed(() => {
  return accountStatus.value?.book_balance || 0
})

const difference = computed(() => {
  return statementBalance.value - bookBalance.value
})

const isBalanced = computed(() => {
  return Math.abs(difference.value) < 0.01
})

const unmatchedStatementCount = computed(() => {
  return statementLines.value.filter(sl => !sl.cleared).length
})

const unmatchedCashbookCount = computed(() => {
  return unclearedTransactions.value.filter(tx => !tx.cleared).length
})

async function fetchAccounts() {
  try {
    const { data } = await bankingApi.getReconciliationAccounts()
    accounts.value = Array.isArray(data) ? data : data.items || data.accounts || []
  } catch (error) {
    console.error('Failed to fetch reconciliation accounts:', error)
    toastStore.show('Failed to load accounts', 'error')
  }
}

async function fetchReconciliationData() {
  if (!selectedAccountId.value) {
    accountStatus.value = null
    statementLines.value = []
    unclearedTransactions.value = []
    return
  }

  loadingStatus.value = true
  try {
    const [statusRes, statementRes, cashbookRes] = await Promise.all([
      bankingApi.getReconciliationAccountStatus(selectedAccountId.value),
      bankingApi.getStatementLines(selectedAccountId.value),
      bankingApi.getUnclearedTransactions(selectedAccountId.value),
    ])

    accountStatus.value = statusRes.data || statusRes
    statementLines.value = Array.isArray(statementRes.data) ? statementRes.data : statementRes.data?.items || statementRes.data?.lines || []
    unclearedTransactions.value = Array.isArray(cashbookRes.data) ? cashbookRes.data : cashbookRes.data?.items || cashbookRes.data?.transactions || []

    selectedStatementLine.value = null
    selectedCashbookEntry.value = null
  } catch (error) {
    console.error('Failed to fetch reconciliation data:', error)
    toastStore.show('Failed to load reconciliation data', 'error')
  } finally {
    loadingStatus.value = false
  }
}

async function fetchHistory() {
  try {
    const { data } = await bankingApi.getReconciliationHistory()
    history.value = Array.isArray(data) ? data : data.items || data.history || []
  } catch (error) {
    console.error('Failed to fetch history:', error)
  }
}

async function handleFileUpload(file) {
  if (!selectedAccountId.value) {
    toastStore.show('Please select an account first', 'error')
    return
  }

  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    await bankingApi.importStatement(selectedAccountId.value, formData)
    toastStore.show('Statement imported successfully')
    await fetchReconciliationData()
  } catch (error) {
    console.error('Failed to import statement:', error)
    toastStore.show('Failed to import statement. Please ensure the file is a valid CSV.', 'error')
  } finally {
    importing.value = false
  }
}

async function autoMatch() {
  if (!selectedAccountId.value) return
  autoMatching.value = true
  try {
    await bankingApi.autoMatch(selectedAccountId.value)
    toastStore.show('Auto-match completed')
    await fetchReconciliationData()
  } catch (error) {
    console.error('Auto-match failed:', error)
    toastStore.show('Auto-match failed', 'error')
  } finally {
    autoMatching.value = false
  }
}

function selectStatementLine(line) {
  selectedStatementLine.value = selectedStatementLine.value?.id === line.id ? null : line
}

function selectCashbookEntry(entry) {
  selectedCashbookEntry.value = selectedCashbookEntry.value?.id === entry.id ? null : entry
}

async function matchSelected() {
  if (!selectedStatementLine.value || !selectedCashbookEntry.value) {
    toastStore.show('Please select one item from each panel to match', 'error')
    return
  }

  matching.value = true
  try {
    await bankingApi.matchTransaction({
      statement_line_id: selectedStatementLine.value.id,
      cashbook_entry_id: selectedCashbookEntry.value.id,
    })
    toastStore.show('Items matched successfully')
    await fetchReconciliationData()
  } catch (error) {
    console.error('Match failed:', error)
    toastStore.show('Failed to match items', 'error')
  } finally {
    matching.value = false
  }
}

async function clearStatementLine(line) {
  try {
    await bankingApi.clearStatementLine(line.id)
    toastStore.show('Statement line cleared')
    await fetchReconciliationData()
  } catch (error) {
    console.error('Failed to clear statement line:', error)
    toastStore.show('Failed to clear statement line', 'error')
  }
}

async function clearCashbookEntry(entry) {
  try {
    await bankingApi.clearCashbookEntry(entry.id)
    toastStore.show('Cashbook entry cleared')
    await fetchReconciliationData()
  } catch (error) {
    console.error('Failed to clear cashbook entry:', error)
    toastStore.show('Failed to clear cashbook entry', 'error')
  }
}

async function completeReconciliation() {
  if (!isBalanced.value) {
    toastStore.show('Cannot complete reconciliation: the difference must be zero', 'error')
    return
  }

  completing.value = true
  try {
    await bankingApi.completeReconciliation({
      account_id: selectedAccountId.value,
      statement_balance: statementBalance.value,
      book_balance: bookBalance.value,
    })
    toastStore.show('Reconciliation completed successfully')
    await fetchReconciliationData()
    await fetchHistory()
  } catch (error) {
    console.error('Failed to complete reconciliation:', error)
    toastStore.show('Failed to complete reconciliation', 'error')
  } finally {
    completing.value = false
  }
}

watch(selectedAccountId, fetchReconciliationData)

onMounted(async () => {
  loading.value = true
  await Promise.all([fetchAccounts(), fetchHistory()])
  loading.value = false
})
</script>

<template>
  <div>
    <PageHeader title="Bank Reconciliation" :breadcrumbs="breadcrumbs" />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading reconciliation..." />
    </div>

    <template v-else>
      <!-- Account Selector -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div class="flex flex-col sm:flex-row sm:items-end gap-4">
          <div class="w-full sm:w-80">
            <SelectInput
              v-model="selectedAccountId"
              label="Select Bank Account"
              name="reconciliation_account"
              :options="accountOptions"
              placeholder="Choose an account to reconcile"
            />
          </div>
          <div v-if="selectedAccountId" class="flex items-center gap-2">
            <button
              type="button"
              :disabled="autoMatching"
              class="inline-flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              @click="autoMatch"
            >
              <LoadingSpinner v-if="autoMatching" size="sm" />
              {{ autoMatching ? 'Matching...' : 'Auto-Match' }}
            </button>
          </div>
        </div>
      </div>

      <template v-if="selectedAccountId && !loadingStatus">
        <!-- Reconciliation Summary -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p class="text-sm text-gray-500 dark:text-gray-400">Statement Balance</p>
            <p class="text-xl font-bold text-gray-900 dark:text-white mt-1">
              {{ formatAmount(statementBalance) }}
            </p>
          </div>
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <p class="text-sm text-gray-500 dark:text-gray-400">Book Balance</p>
            <p class="text-xl font-bold text-gray-900 dark:text-white mt-1">
              {{ formatAmount(bookBalance) }}
            </p>
          </div>
          <div
            :class="[
              'rounded-lg border p-4',
              isBalanced
                ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
            ]"
          >
            <p class="text-sm text-gray-500 dark:text-gray-400">Difference</p>
            <p
              :class="[
                'text-xl font-bold mt-1',
                isBalanced ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400',
              ]"
            >
              {{ formatAmount(difference) }}
              <span v-if="isBalanced" class="text-sm font-normal ml-2">✓ Balanced</span>
            </p>
          </div>
        </div>

        <!-- CSV Import -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-3">Import Bank Statement</h3>
          <FileUpload
            accept=".csv"
            :max-size="5"
            label="Upload CSV"
            help-text="Upload a CSV file exported from your bank (max 5MB)"
            @file-selected="handleFileUpload"
            @error="toastStore.show($event, 'error')"
          />
          <div v-if="importing" class="mt-3 flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
            <LoadingSpinner size="sm" />
            Importing statement...
          </div>
        </div>

        <!-- Two-Panel View -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <!-- Left: Statement Lines -->
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                Statement Lines
                <span class="ml-2 text-xs font-normal text-gray-500 dark:text-gray-400">
                  ({{ unmatchedStatementCount }} unmatched)
                </span>
              </h3>
            </div>
            <div class="max-h-96 overflow-y-auto">
              <div v-if="statementLines.length === 0" class="flex items-center justify-center py-8 text-center">
                <p class="text-sm text-gray-500 dark:text-gray-400">No statement lines. Import a CSV to begin.</p>
              </div>
              <div
                v-for="line in statementLines"
                :key="line.id"
                :class="[
                  'px-4 py-3 border-b border-gray-100 dark:border-gray-700/50 cursor-pointer transition-colors',
                  line.cleared ? 'opacity-50' : 'hover:bg-gray-50 dark:hover:bg-gray-700',
                  selectedStatementLine?.id === line.id ? 'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-200 dark:ring-blue-800' : '',
                ]"
                @click="!line.cleared && selectStatementLine(line)"
              >
                <div class="flex items-center justify-between">
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {{ line.description || '—' }}
                    </p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {{ line.date }}
                    </p>
                  </div>
                  <div class="text-right ml-3">
                    <p :class="['text-sm font-medium', (line.amount || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400']">
                      {{ formatAmount(Math.abs(line.amount || 0)) }}
                    </p>
                    <div v-if="line.cleared" class="text-xs text-gray-400 mt-0.5">
                      Cleared
                    </div>
                  </div>
                </div>
                <button
                  v-if="!line.cleared"
                  type="button"
                  class="mt-1 text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                  @click.stop="clearStatementLine(line)"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>

          <!-- Right: Uncleared Cashbook Transactions -->
          <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
              <h3 class="text-sm font-semibold text-gray-900 dark:text-white">
                Uncleared Cashbook Transactions
                <span class="ml-2 text-xs font-normal text-gray-500 dark:text-gray-400">
                  ({{ unmatchedCashbookCount }} unmatched)
                </span>
              </h3>
            </div>
            <div class="max-h-96 overflow-y-auto">
              <div v-if="unclearedTransactions.length === 0" class="flex items-center justify-center py-8 text-center">
                <p class="text-sm text-gray-500 dark:text-gray-400">All transactions are cleared.</p>
              </div>
              <div
                v-for="entry in unclearedTransactions"
                :key="entry.id"
                :class="[
                  'px-4 py-3 border-b border-gray-100 dark:border-gray-700/50 cursor-pointer transition-colors',
                  entry.cleared ? 'opacity-50' : 'hover:bg-gray-50 dark:hover:bg-gray-700',
                  selectedCashbookEntry?.id === entry.id ? 'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-200 dark:ring-blue-800' : '',
                ]"
                @click="!entry.cleared && selectCashbookEntry(entry)"
              >
                <div class="flex items-center justify-between">
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {{ entry.description || '—' }}
                    </p>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {{ entry.date }} · {{ entry.reference || '' }}
                    </p>
                  </div>
                  <div class="text-right ml-3">
                    <p :class="['text-sm font-medium', (entry.amount || 0) >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400']">
                      {{ formatAmount(Math.abs(entry.amount || 0)) }}
                    </p>
                    <div v-if="entry.cleared" class="text-xs text-gray-400 mt-0.5">
                      Cleared
                    </div>
                  </div>
                </div>
                <button
                  v-if="!entry.cleared"
                  type="button"
                  class="mt-1 text-xs text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                  @click.stop="clearCashbookEntry(entry)"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Match Button -->
        <div v-if="selectedStatementLine && selectedCashbookEntry" class="mb-6 flex items-center justify-center">
          <button
            type="button"
            :disabled="matching"
            class="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            @click="matchSelected"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
            </svg>
            <LoadingSpinner v-if="matching" size="sm" />
            {{ matching ? 'Matching...' : 'Match Selected Items' }}
          </button>
        </div>

        <!-- Complete Reconciliation -->
        <div class="flex items-center justify-end">
          <button
            type="button"
            :disabled="!isBalanced || completing"
            class="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            @click="completeReconciliation"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <LoadingSpinner v-if="completing" size="sm" />
            {{ completing ? 'Completing...' : 'Complete Reconciliation' }}
          </button>
        </div>
      </template>

      <!-- No Account Selected -->
      <div v-else-if="!selectedAccountId" class="flex flex-col items-center justify-center py-20 text-center">
        <svg class="w-16 h-16 text-gray-400 dark:text-gray-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
        <p class="text-lg font-semibold text-gray-900 dark:text-white mb-1">Select an Account</p>
        <p class="text-sm text-gray-500 dark:text-gray-400">Choose a bank account from the dropdown above to start reconciliation.</p>
      </div>

      <!-- History Section -->
      <div v-if="history.length > 0" class="mt-8">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Reconciliation History</h3>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account</th>
                  <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Statement Balance</th>
                  <th class="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Book Balance</th>
                  <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                <tr
                  v-for="record in history"
                  :key="record.id"
                  class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300 whitespace-nowrap">
                    {{ record.date || record.created_at || '—' }}
                  </td>
                  <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">
                    {{ record.account_name || '—' }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300 text-right whitespace-nowrap">
                    {{ formatAmount(record.statement_balance) }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300 text-right whitespace-nowrap">
                    {{ formatAmount(record.book_balance) }}
                  </td>
                  <td class="px-6 py-4">
                    <StatusBadge status="completed" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
