<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'
import * as crmApi from '@/api/crm'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const customer = ref(null)
const invoices = ref([])
const payments = ref([])
const loading = ref(true)
const showDeleteDialog = ref(false)
const deleting = ref(false)
const activeTab = ref('info')

const breadcrumbs = computed(() => [
  { text: 'CRM', to: '/crm' },
  { text: 'Customers', to: '/crm/customers' },
  { text: customer.value?.name || 'Customer Details' },
])

async function fetchCustomer() {
  loading.value = true
  try {
    const { data } = await crmApi.getCustomer(route.params.id)
    customer.value = data
    invoices.value = data.invoices || []
    payments.value = data.payments || []
  } catch (error) {
    console.error('Failed to fetch customer:', error)
    toastStore.show('Failed to load customer', 'error')
  } finally {
    loading.value = false
  }
}

function formatBalance(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

function editCustomer() {
  router.push({ name: 'CustomerEdit', params: { id: route.params.id } })
}

function goBack() {
  router.push({ name: 'CustomerList' })
}

async function toggleStatus() {
  if (!customer.value) return
  try {
    await crmApi.toggleCustomerStatus(customer.value.id)
    customer.value.status = customer.value.status === 'active' ? 'inactive' : 'active'
    toastStore.show(`Customer ${customer.value.status === 'active' ? 'activated' : 'deactivated'}`)
  } catch (error) {
    console.error('Failed to toggle status:', error)
    toastStore.show('Failed to update status', 'error')
  }
}

async function handleDelete() {
  deleting.value = true
  try {
    await crmApi.deleteCustomer(route.params.id)
    toastStore.show('Customer deleted successfully')
    router.push({ name: 'CustomerList' })
  } catch (error) {
    console.error('Failed to delete customer:', error)
    toastStore.show('Failed to delete customer', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(fetchCustomer)
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading customer..." />
    </div>

    <template v-else-if="customer">
      <PageHeader :title="customer.name" :breadcrumbs="breadcrumbs">
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
              Back to List
            </button>

            <button
              v-if="authStore.hasPermission('customers:edit')"
              type="button"
              :class="[
                'inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors',
                customer.status === 'active'
                  ? 'text-amber-700 bg-amber-50 border border-amber-300 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700 dark:hover:bg-amber-900/50'
                  : 'text-green-700 bg-green-50 border border-green-300 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:border-green-700 dark:hover:bg-green-900/50',
              ]"
              @click="toggleStatus"
            >
              {{ customer.status === 'active' ? 'Deactivate' : 'Activate' }}
            </button>

            <button
              v-if="authStore.hasPermission('customers:edit')"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
              @click="editCustomer"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
              Edit
            </button>

            <button
              v-if="authStore.hasPermission('customers:delete')"
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

      <!-- Balance Summary Card -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Balance</p>
          <p
            :class="[
              'text-xl font-bold mt-1',
              (customer.balance || 0) > 0
                ? 'text-red-600 dark:text-red-400'
                : (customer.balance || 0) < 0
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-gray-900 dark:text-white',
            ]"
          >
            {{ formatBalance(customer.balance || 0) }}
          </p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Total Invoices</p>
          <p class="text-xl font-bold text-gray-900 dark:text-white mt-1">
            {{ customer.total_invoices || invoices.length || 0 }}
          </p>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Status</p>
          <div class="mt-2">
            <StatusBadge :status="customer.status" />
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav class="flex gap-6" aria-label="Tabs">
          <button
            v-for="tab in [
              { key: 'info', label: 'Details' },
              { key: 'invoices', label: 'Invoices' },
              { key: 'payments', label: 'Payments' },
            ]"
            :key="tab.key"
            type="button"
            :class="[
              'pb-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:border-gray-600',
            ]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Info Tab -->
      <div v-if="activeTab === 'info'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Customer Information</h3>
        <dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
          <div v-if="customer.email">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Email</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ customer.email }}</dd>
          </div>
          <div v-if="customer.phone">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Phone</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ customer.phone }}</dd>
          </div>
          <div v-if="customer.address">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Address</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ customer.address }}</dd>
          </div>
          <div v-if="customer.city">
            <dt class="text-sm text-gray-500 dark:text-gray-400">City</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ customer.city }}</dd>
          </div>
          <div v-if="customer.state">
            <dt class="text-sm text-gray-500 dark:text-gray-400">State</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ customer.state }}</dd>
          </div>
          <div v-if="customer.country">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Country</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ customer.country }}</dd>
          </div>
          <div v-if="customer.tax_id">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Tax ID</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ customer.tax_id }}</dd>
          </div>
          <div v-if="customer.created_at">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Created</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ formatDate(customer.created_at) }}</dd>
          </div>
          <div v-if="customer.notes" class="sm:col-span-2">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Notes</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5 whitespace-pre-wrap">{{ customer.notes }}</dd>
          </div>
        </dl>
      </div>

      <!-- Invoices Tab -->
      <div v-if="activeTab === 'invoices'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div v-if="invoices.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No invoices found for this customer.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Invoice #</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Amount</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="invoice in invoices"
                :key="invoice.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-6 py-4 text-sm font-medium text-blue-600 dark:text-blue-400">{{ invoice.invoice_number }}</td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(invoice.date) }}</td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{{ formatBalance(invoice.amount) }}</td>
                <td class="px-6 py-4"><StatusBadge :status="invoice.status" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Payments Tab -->
      <div v-if="activeTab === 'payments'" class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div v-if="payments.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No payments found for this customer.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Reference</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Amount</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Method</th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="payment in payments"
                :key="payment.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{{ payment.reference }}</td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(payment.date) }}</td>
                <td class="px-6 py-4 text-sm font-medium text-green-600 dark:text-green-400">{{ formatBalance(payment.amount) }}</td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ payment.method }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Customer"
      :message="`Are you sure you want to delete '${customer?.name}'? This action cannot be undone and will remove all associated data.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
