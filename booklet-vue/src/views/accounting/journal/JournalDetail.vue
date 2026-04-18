<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { getJournalEntry, postJournalEntry } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const entry = ref(null)
const loading = ref(true)
const posting = ref(false)

// Post confirmation
const showPostDialog = ref(false)

const lineItems = computed(() => {
  return entry.value?.line_items || entry.value?.entries || []
})

const totalDebit = computed(() => {
  return lineItems.value.reduce((sum, item) => sum + (Number(item.debit) || 0), 0)
})

const totalCredit = computed(() => {
  return lineItems.value.reduce((sum, item) => sum + (Number(item.credit) || 0), 0)
})

async function fetchEntry() {
  loading.value = true
  try {
    const { data } = await getJournalEntry(route.params.id)
    entry.value = data
  } catch (error) {
    console.error('Failed to fetch journal entry:', error)
    toast.show('Failed to load journal entry', 'error')
    router.push({ name: 'JournalList' })
  } finally {
    loading.value = false
  }
}

function confirmPost() {
  showPostDialog.value = true
}

async function handlePost() {
  posting.value = true
  try {
    await postJournalEntry(route.params.id)
    toast.show('Journal entry posted successfully', 'success')
    await fetchEntry()
  } catch (error) {
    console.error('Failed to post entry:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to post journal entry'
    toast.show(message, 'error')
  } finally {
    posting.value = false
  }
}

function goBack() {
  router.push({ name: 'JournalList' })
}

function handlePrint() {
  window.print()
}

onMounted(() => {
  fetchEntry()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Journal Entry Details"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Journal Entries', to: { name: 'JournalList' } },
        { text: entry?.entry_number || 'Details' }
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
            Back to List
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            @click="handlePrint"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 011.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18.75 7.131s0 0 0 0" />
            </svg>
            Print
          </button>
          <button
            v-if="entry && entry.status === 'draft'"
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
            @click="confirmPost"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Post Entry
          </button>
        </div>
      </template>
    </PageHeader>

    <LoadingSpinner v-if="loading" text="Loading journal entry..." />

    <template v-else-if="entry">
      <!-- Entry Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div class="flex items-center gap-3 mb-2">
              <h2 class="text-xl font-bold text-gray-900 dark:text-white">
                {{ entry.entry_number || `JE-${String(entry.id).padStart(4, '0')}` }}
              </h2>
              <StatusBadge :status="entry.status" />
            </div>
            <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                </svg>
                {{ formatDate(entry.date, 'short') }}
              </span>
              <span v-if="entry.reference" class="flex items-center gap-1.5">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 8.25h15m-16.5 7.5h15m-1.8-13.5l-3.9 19.5m-2.1-19.5l-3.9 19.5" />
                </svg>
                {{ entry.reference }}
              </span>
            </div>
            <p v-if="entry.description" class="mt-2 text-sm text-gray-700 dark:text-gray-300">
              {{ entry.description }}
            </p>
          </div>
        </div>
      </div>

      <!-- Line Items Table -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-4">Line Items</h3>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account</th>
                <th class="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Description</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Debit</th>
                <th class="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Credit</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(item, index) in lineItems"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <td class="px-4 py-3">
                  <p class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ item.account_name || item.account?.name || `Account #${item.account_id}` }}
                  </p>
                  <p v-if="item.account?.code" class="text-xs text-gray-500 dark:text-gray-400">{{ item.account.code }}</p>
                </td>
                <td class="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
                  {{ item.description || '—' }}
                </td>
                <td class="px-4 py-3 text-right">
                  <span v-if="item.debit" class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(item.debit, auth.branchCurrency) }}
                  </span>
                  <span v-else class="text-sm text-gray-400 dark:text-gray-500">—</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <span v-if="item.credit" class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ formatCurrency(item.credit, auth.branchCurrency) }}
                  </span>
                  <span v-else class="text-sm text-gray-400 dark:text-gray-500">—</span>
                </td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <td colspan="2" class="px-4 py-3 text-right text-sm font-semibold text-gray-900 dark:text-white">
                  Total
                </td>
                <td class="px-4 py-3 text-right text-sm font-bold text-gray-900 dark:text-white">
                  {{ formatCurrency(totalDebit, auth.branchCurrency) }}
                </td>
                <td class="px-4 py-3 text-right text-sm font-bold text-gray-900 dark:text-white">
                  {{ formatCurrency(totalCredit, auth.branchCurrency) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Balance Check -->
        <div class="mt-4 flex items-center justify-end">
          <div class="flex items-center gap-2 px-3 py-2 rounded-lg" :class="Math.abs(totalDebit - totalCredit) < 0.01 ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'">
            <svg
              class="w-4 h-4"
              :class="Math.abs(totalDebit - totalCredit) < 0.01 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
            >
              <path
                v-if="Math.abs(totalDebit - totalCredit) < 0.01"
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
            <span
              class="text-sm font-medium"
              :class="Math.abs(totalDebit - totalCredit) < 0.01 ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'"
            >
              {{ Math.abs(totalDebit - totalCredit) < 0.01 ? 'Entry is balanced' : 'Entry is not balanced' }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- Post Confirmation Dialog -->
    <ConfirmDialog
      v-model:show="showPostDialog"
      title="Post Journal Entry"
      message="Are you sure you want to post this journal entry? Once posted, the entry cannot be modified. This will update the account balances."
      confirm-text="Post Entry"
      cancel-text="Cancel"
      type="info"
      @confirm="handlePost"
    />
  </div>
</template>
