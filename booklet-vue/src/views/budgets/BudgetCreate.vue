<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { createBudget, getFiscalYears, getAvailableAccounts } from '@/api/budgets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const submitting = ref(false)
const loadingOptions = ref(true)
const errors = ref({})

const form = ref({
  name: '',
  fiscal_year: '',
  description: '',
  revenue_items: [createEmptyLineItem('revenue')],
  expense_items: [createEmptyLineItem('expense')],
})

const fiscalYearOptions = ref([])
const accountOptions = ref([])

function createEmptyLineItem(type) {
  return {
    account_id: '',
    amount: '',
    type,
  }
}

const totalRevenue = computed(() => {
  return form.value.revenue_items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const totalExpenses = computed(() => {
  return form.value.expense_items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const netBudget = computed(() => {
  return totalRevenue.value - totalExpenses.value
})

async function loadOptions() {
  loadingOptions.value = true
  try {
    const [fyRes, accountsRes] = await Promise.all([
      getFiscalYears(),
      getAvailableAccounts(),
    ])

    const fiscalYears = Array.isArray(fyRes.data) ? fyRes.data : fyRes.data.fiscal_years || []
    fiscalYearOptions.value = fiscalYears.map(fy => ({
      value: fy.id || fy.year,
      label: fy.name || fy.label || String(fy.year || fy.id),
    }))

    const accounts = Array.isArray(accountsRes.data) ? accountsRes.data : accountsRes.data.accounts || []
    accountOptions.value = accounts.map(a => ({
      value: a.id,
      label: a.name || a.code + ' - ' + a.name,
    }))
  } catch (error) {
    console.error('Failed to load options:', error)
    toast.show('Failed to load form options', 'error')
  } finally {
    loadingOptions.value = false
  }
}

function addRevenueItem() {
  form.value.revenue_items.push(createEmptyLineItem('revenue'))
}

function removeRevenueItem(index) {
  if (form.value.revenue_items.length > 1) {
    form.value.revenue_items.splice(index, 1)
  }
}

function addExpenseItem() {
  form.value.expense_items.push(createEmptyLineItem('expense'))
}

function removeExpenseItem(index) {
  if (form.value.expense_items.length > 1) {
    form.value.expense_items.splice(index, 1)
  }
}

function validate() {
  const newErrors = {}
  if (!form.value.name?.trim()) newErrors.name = 'Budget name is required'
  if (!form.value.fiscal_year) newErrors.fiscal_year = 'Fiscal year is required'

  const hasEmptyRevenue = form.value.revenue_items.some(item => !item.account_id || !item.amount)
  const hasEmptyExpense = form.value.expense_items.some(item => !item.account_id || !item.amount)

  if (hasEmptyRevenue) newErrors.revenue_items = 'All revenue line items must have an account and amount'
  if (hasEmptyExpense) newErrors.expense_items = 'All expense line items must have an account and amount'

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      fiscal_year: form.value.fiscal_year,
      description: form.value.description,
      revenue_items: form.value.revenue_items.map(item => ({
        account_id: item.account_id,
        amount: Number(item.amount),
      })),
      expense_items: form.value.expense_items.map(item => ({
        account_id: item.account_id,
        amount: Number(item.amount),
      })),
    }

    await createBudget(payload)
    toast.show('Budget created successfully', 'success')
    router.push({ name: 'BudgetList' })
  } catch (error) {
    console.error('Failed to create budget:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to create budget'
    toast.show(message, 'error')
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  router.push({ name: 'BudgetList' })
}

onMounted(() => {
  loadOptions()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="New Budget"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Budgets', to: { name: 'BudgetList' } },
        { text: 'New' }
      ]"
    />

    <LoadingSpinner v-if="loadingOptions" text="Loading form options..." />

    <form v-else class="space-y-6" @submit.prevent="handleSubmit">
      <!-- Budget Info -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Budget Information</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextInput
            v-model="form.name"
            label="Budget Name"
            name="name"
            placeholder="Enter budget name"
            :required="true"
            :error="errors.name"
          />
          <SelectInput
            v-model="form.fiscal_year"
            label="Fiscal Year"
            name="fiscal_year"
            :options="fiscalYearOptions"
            placeholder="Select fiscal year"
            :required="true"
            :error="errors.fiscal_year"
          />
        </div>
        <div class="mt-4">
          <TextareaInput
            v-model="form.description"
            label="Description"
            name="description"
            placeholder="Optional budget description..."
            :rows="3"
          />
        </div>
      </div>

      <!-- Revenue Line Items -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Revenue Items</h2>
            <p v-if="errors.revenue_items" class="text-sm text-red-600 dark:text-red-400 mt-1">{{ errors.revenue_items }}</p>
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-emerald-700 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors"
            @click="addRevenueItem"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Add Revenue
          </button>
        </div>

        <div class="space-y-3">
          <div
            v-for="(item, index) in form.revenue_items"
            :key="'rev-' + index"
            class="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
          >
            <div class="flex-1">
              <select
                v-model="item.account_id"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
              >
                <option value="">Select account</option>
                <option v-for="account in accountOptions" :key="account.value" :value="account.value">
                  {{ account.label }}
                </option>
              </select>
            </div>
            <div class="w-40">
              <input
                v-model="item.amount"
                type="number"
                min="0"
                step="0.01"
                placeholder="Monthly amount"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors"
              />
            </div>
            <button
              type="button"
              :disabled="form.revenue_items.length <= 1"
              :class="[
                'p-2 rounded-md transition-colors mt-0.5',
                form.revenue_items.length <= 1
                  ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                  : 'text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
              ]"
              @click="removeRevenueItem(index)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <span class="text-sm text-gray-500 dark:text-gray-400">Total Revenue (Monthly): </span>
          <span class="ml-2 text-sm font-bold text-emerald-600 dark:text-emerald-400">{{ formatCurrency(totalRevenue, auth.branchCurrency) }}</span>
        </div>
      </div>

      <!-- Expense Line Items -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Expense Items</h2>
            <p v-if="errors.expense_items" class="text-sm text-red-600 dark:text-red-400 mt-1">{{ errors.expense_items }}</p>
          </div>
          <button
            type="button"
            class="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-700 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
            @click="addExpenseItem"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Add Expense
          </button>
        </div>

        <div class="space-y-3">
          <div
            v-for="(item, index) in form.expense_items"
            :key="'exp-' + index"
            class="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
          >
            <div class="flex-1">
              <select
                v-model="item.account_id"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors"
              >
                <option value="">Select account</option>
                <option v-for="account in accountOptions" :key="account.value" :value="account.value">
                  {{ account.label }}
                </option>
              </select>
            </div>
            <div class="w-40">
              <input
                v-model="item.amount"
                type="number"
                min="0"
                step="0.01"
                placeholder="Monthly amount"
                class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-colors"
              />
            </div>
            <button
              type="button"
              :disabled="form.expense_items.length <= 1"
              :class="[
                'p-2 rounded-md transition-colors mt-0.5',
                form.expense_items.length <= 1
                  ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                  : 'text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
              ]"
              @click="removeExpenseItem(index)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <span class="text-sm text-gray-500 dark:text-gray-400">Total Expenses (Monthly): </span>
          <span class="ml-2 text-sm font-bold text-red-600 dark:text-red-400">{{ formatCurrency(totalExpenses, auth.branchCurrency) }}</span>
        </div>
      </div>

      <!-- Summary -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Budget Summary (Monthly)</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500 dark:text-gray-400">Total Revenue</span>
            <span class="text-sm font-medium text-emerald-600 dark:text-emerald-400">{{ formatCurrency(totalRevenue, auth.branchCurrency) }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-500 dark:text-gray-400">Total Expenses</span>
            <span class="text-sm font-medium text-red-600 dark:text-red-400">{{ formatCurrency(totalExpenses, auth.branchCurrency) }}</span>
          </div>
          <div class="border-t border-gray-200 dark:border-gray-700 pt-3">
            <div class="flex items-center justify-between">
              <span class="text-base font-semibold text-gray-900 dark:text-white">Net Budget</span>
              <span
                :class="[
                  'text-lg font-bold',
                  netBudget >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                ]"
              >
                {{ formatCurrency(netBudget, auth.branchCurrency) }}
              </span>
            </div>
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
          {{ submitting ? 'Creating...' : 'Create Budget' }}
        </button>
      </div>
    </form>
  </div>
</template>
