<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { createJournalEntry } from '@/api/accounting'
import { listAccounts } from '@/api/accounting'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const submitting = ref(false)
const loadingOptions = ref(true)
const errors = ref({})

// Form data
const form = ref({
  date: new Date().toISOString().split('T')[0],
  description: '',
  reference: '',
  line_items: [createEmptyLineItem()],
})

// Dropdown options
const accountOptions = ref([])

function createEmptyLineItem() {
  return {
    account_id: '',
    description: '',
    debit: '',
    credit: '',
  }
}

// Computed totals
const totalDebits = computed(() => {
  return form.value.line_items.reduce((sum, item) => sum + (Number(item.debit) || 0), 0)
})

const totalCredits = computed(() => {
  return form.value.line_items.reduce((sum, item) => sum + (Number(item.credit) || 0), 0)
})

const difference = computed(() => {
  return Math.abs(totalDebits.value - totalCredits.value)
})

const isBalanced = computed(() => {
  return difference.value < 0.01 && (totalDebits.value > 0 || totalCredits.value > 0)
})

function addLineItem() {
  form.value.line_items.push(createEmptyLineItem())
}

function removeLineItem(index) {
  if (form.value.line_items.length > 2) {
    form.value.line_items.splice(index, 1)
  }
}

function onDebitChange(index) {
  if (Number(form.value.line_items[index].debit) > 0) {
    form.value.line_items[index].credit = ''
  }
}

function onCreditChange(index) {
  if (Number(form.value.line_items[index].credit) > 0) {
    form.value.line_items[index].debit = ''
  }
}

function validate() {
  const newErrors = {}

  if (!form.value.date) {
    newErrors.date = 'Date is required'
  }

  if (!form.value.description?.trim()) {
    newErrors.description = 'Description is required'
  }

  // Validate line items
  const hasEmptyAccount = form.value.line_items.some(
    (item) => !item.account_id
  )
  if (hasEmptyAccount) {
    newErrors.line_items = 'All line items must have an account selected'
  }

  const hasEmptyAmounts = form.value.line_items.some(
    (item) => !item.debit && !item.credit
  )
  if (hasEmptyAmounts) {
    newErrors.line_items = 'All line items must have a debit or credit amount'
  }

  if (!isBalanced.value) {
    newErrors.balance = `Total debits must equal total credits (difference: ${formatCurrency(difference.value, auth.branchCurrency)})`
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function loadAccountOptions() {
  loadingOptions.value = true
  try {
    const { data } = await listAccounts()
    const accounts = Array.isArray(data) ? data : data.items || data.accounts || []

    accountOptions.value = accounts
      .filter((a) => a.status !== 'inactive' && a.status !== 'closed')
      .map((a) => ({
        value: String(a.id),
        label: `${a.code ? a.code + ' — ' : ''}${a.name}`,
      }))
      .sort((a, b) => a.label.localeCompare(b.label))
  } catch (error) {
    console.error('Failed to load account options:', error)
    toast.show('Failed to load account options', 'error')
  } finally {
    loadingOptions.value = false
  }
}

async function handleSubmit() {
  if (!validate()) return

  submitting.value = true
  try {
    const payload = {
      date: form.value.date,
      description: form.value.description,
      reference: form.value.reference,
      line_items: form.value.line_items
        .filter((item) => item.account_id && (Number(item.debit) > 0 || Number(item.credit) > 0))
        .map((item) => ({
          account_id: item.account_id,
          description: item.description,
          debit: Number(item.debit) || 0,
          credit: Number(item.credit) || 0,
        })),
    }

    await createJournalEntry(payload)
    toast.show('Journal entry created successfully', 'success')
    router.push({ name: 'JournalList' })
  } catch (error) {
    console.error('Failed to create journal entry:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to create journal entry'
    toast.show(message, 'error')
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  router.push({ name: 'JournalList' })
}

onMounted(() => {
  loadAccountOptions()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="New Journal Entry"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Journal Entries', to: { name: 'JournalList' } },
        { text: 'New' }
      ]"
    />

    <LoadingSpinner v-if="loadingOptions" text="Loading account options..." />

    <form v-else class="space-y-6" @submit.prevent="handleSubmit">
      <!-- Journal Entry Details -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Entry Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DateInput
            v-model="form.date"
            label="Date"
            name="date"
            :required="true"
            :error="errors.date"
          />

          <TextInput
            v-model="form.reference"
            label="Reference"
            name="reference"
            placeholder="e.g., JE-001"
          />

          <div class="md:col-span-2">
            <TextareaInput
              v-model="form.description"
              label="Description"
              name="description"
              placeholder="Enter a description for this journal entry"
              :rows="2"
              :required="true"
              :error="errors.description"
            />
          </div>
        </div>
      </div>

      <!-- Line Items Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Line Items</h2>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-emerald-700 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors"
            @click="addLineItem"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Add Line
          </button>
        </div>

        <p v-if="errors.line_items" class="mb-4 text-sm text-red-600 dark:text-red-400">{{ errors.line_items }}</p>

        <!-- Line Items Table -->
        <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-8">#</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Account</th>
                <th class="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Description</th>
                <th class="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-32">Debit</th>
                <th class="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-32">Credit</th>
                <th class="px-3 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="(item, index) in form.line_items"
                :key="index"
                class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <td class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">{{ index + 1 }}</td>

                <td class="px-3 py-2">
                  <select
                    v-model="item.account_id"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                  >
                    <option value="">Select account</option>
                    <option v-for="account in accountOptions" :key="account.value" :value="account.value">
                      {{ account.label }}
                    </option>
                  </select>
                </td>

                <td class="px-3 py-2">
                  <input
                    v-model="item.description"
                    type="text"
                    placeholder="Description"
                    class="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                  />
                </td>

                <td class="px-3 py-2">
                  <input
                    v-model="item.debit"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    class="w-full px-2 py-1.5 text-sm text-right border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                    @input="onDebitChange(index)"
                  />
                </td>

                <td class="px-3 py-2">
                  <input
                    v-model="item.credit"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    class="w-full px-2 py-1.5 text-sm text-right border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
                    @input="onCreditChange(index)"
                  />
                </td>

                <td class="px-3 py-2 text-center">
                  <button
                    type="button"
                    :disabled="form.line_items.length <= 2"
                    :class="[
                      'p-1 rounded-md transition-colors',
                      form.line_items.length <= 2
                        ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                        : 'text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
                    ]"
                    title="Remove line"
                    @click="removeLineItem(index)"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>

            <!-- Totals Row -->
            <tfoot class="bg-gray-50 dark:bg-gray-900">
              <tr>
                <td colspan="3" class="px-3 py-3 text-right text-sm font-semibold text-gray-900 dark:text-white">
                  Totals
                </td>
                <td class="px-3 py-3 text-right text-sm font-semibold text-gray-900 dark:text-white">
                  {{ formatCurrency(totalDebits, auth.branchCurrency) }}
                </td>
                <td class="px-3 py-3 text-right text-sm font-semibold text-gray-900 dark:text-white">
                  {{ formatCurrency(totalCredits, auth.branchCurrency) }}
                </td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Balance Check Indicator -->
        <div class="mt-4 flex items-center justify-between">
          <div
            v-if="errors.balance"
            class="flex items-center gap-2 text-sm text-red-600 dark:text-red-400"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            {{ errors.balance }}
          </div>
          <div v-else class="flex items-center gap-2 text-sm" :class="isBalanced ? 'text-green-600 dark:text-green-400' : 'text-amber-600 dark:text-amber-400'">
            <svg v-if="isBalanced" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <span v-if="isBalanced">Entry is balanced</span>
            <span v-else>Entry is not balanced (difference: {{ formatCurrency(difference, auth.branchCurrency) }})</span>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-col-reverse sm:flex-row items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          class="w-full sm:w-auto px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          :disabled="submitting"
          @click="handleCancel"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="submitting"
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
          {{ submitting ? 'Saving...' : 'Create Entry' }}
        </button>
      </div>
    </form>
  </div>
</template>
