<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { getBudget, updateBudget, getFiscalYears, getAvailableAccounts } from '@/api/budgets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(false)
const fetchLoading = ref(true)
const errors = ref({})

const form = ref({
  name: '',
  fiscal_year: '',
  description: '',
  revenue_items: [],
  expense_items: [],
})

const fiscalYearOptions = ref([])
const accountOptions = ref([])

function createEmptyLineItem(type) {
  return { account_id: '', amount: '', type }
}

const totalRevenue = computed(() => {
  return form.value.revenue_items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const totalExpenses = computed(() => {
  return form.value.expense_items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const netBudget = computed(() => totalRevenue.value - totalExpenses.value)

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

async function fetchBudget() {
  fetchLoading.value = true
  try {
    const [budgetRes, fyRes, accountsRes] = await Promise.all([
      getBudget(route.params.id),
      getFiscalYears(),
      getAvailableAccounts(),
    ])

    const data = budgetRes.data
    form.value = {
      name: data.name || '',
      fiscal_year: data.fiscal_year || data.fiscal_year_id || '',
      description: data.description || '',
      revenue_items: (data.revenue_items || []).map(item => ({
        account_id: item.account_id || '',
        amount: item.amount || '',
        type: 'revenue',
      })),
      expense_items: (data.expense_items || []).map(item => ({
        account_id: item.account_id || '',
        amount: item.amount || '',
        type: 'expense',
      })),
    }

    if (form.value.revenue_items.length === 0) form.value.revenue_items = [createEmptyLineItem('revenue')]
    if (form.value.expense_items.length === 0) form.value.expense_items = [createEmptyLineItem('expense')]

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
    console.error('Failed to fetch budget:', error)
    toast.show('Failed to load budget', 'error')
    router.push({ name: 'BudgetList' })
  } finally {
    fetchLoading.value = false
  }
}

function validate() {
  const newErrors = {}
  if (!form.value.name?.trim()) newErrors.name = 'Budget name is required'
  if (!form.value.fiscal_year) newErrors.fiscal_year = 'Fiscal year is required'
  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    const payload = {
      name: form.value.name,
      fiscal_year: form.value.fiscal_year,
      description: form.value.description,
      revenue_items: form.value.revenue_items
        .filter(item => item.account_id && item.amount)
        .map(item => ({ account_id: item.account_id, amount: Number(item.amount) })),
      expense_items: form.value.expense_items
        .filter(item => item.account_id && item.amount)
        .map(item => ({ account_id: item.account_id, amount: Number(item.amount) })),
    }

    await updateBudget(route.params.id, payload)
    toast.show('Budget updated successfully', 'success')
    router.push({ name: 'BudgetDetail', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update budget:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to update budget'
    toast.show(message, 'error')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push({ name: 'BudgetDetail', params: { id: route.params.id } })
}

onMounted(() => {
  fetchBudget()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Edit Budget"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Budgets', to: { name: 'BudgetList' } },
        { text: 'Edit' }
      ]"
    />

    <LoadingSpinner v-if="fetchLoading" text="Loading budget..." />

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
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Revenue Items</h2>
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
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Expense Items</h2>
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
          :disabled="loading"
          @click="handleCancel"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="loading"
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <LoadingSpinner v-if="loading" size="sm" />
          {{ loading ? 'Saving...' : 'Update Budget' }}
        </button>
      </div>
    </form>
  </div>
</template>
