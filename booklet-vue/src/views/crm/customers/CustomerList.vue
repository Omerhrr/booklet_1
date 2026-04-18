<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import * as crmApi from '@/api/crm'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const customers = ref([])
const loading = ref(true)
const showDeleteDialog = ref(false)
const selectedCustomer = ref(null)
const deleting = ref(false)

const breadcrumbs = [
  { text: 'CRM' },
  { text: 'Customers' },
]

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'phone', label: 'Phone' },
  { key: 'city', label: 'City', sortable: true },
  { key: 'balance', label: 'Balance', sortable: true, class: 'text-right' },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchCustomers() {
  loading.value = true
  try {
    const { data } = await crmApi.listCustomers()
    customers.value = Array.isArray(data) ? data : data.items || data.customers || []
  } catch (error) {
    console.error('Failed to fetch customers:', error)
    toastStore.show('Failed to load customers', 'error')
  } finally {
    loading.value = false
  }
}

function viewCustomer(customer) {
  router.push({ name: 'CustomerDetail', params: { id: customer.id } })
}

function editCustomer(customer) {
  router.push({ name: 'CustomerEdit', params: { id: customer.id } })
}

function confirmDelete(customer) {
  selectedCustomer.value = customer
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!selectedCustomer.value) return
  deleting.value = true
  try {
    await crmApi.deleteCustomer(selectedCustomer.value.id)
    toastStore.show('Customer deleted successfully')
    await fetchCustomers()
  } catch (error) {
    console.error('Failed to delete customer:', error)
    toastStore.show('Failed to delete customer', 'error')
  } finally {
    deleting.value = false
    selectedCustomer.value = null
  }
}

async function toggleStatus(customer) {
  try {
    await crmApi.toggleCustomerStatus(customer.id)
    customer.status = customer.status === 'active' ? 'inactive' : 'active'
    toastStore.show(`Customer ${customer.status === 'active' ? 'activated' : 'deactivated'}`)
  } catch (error) {
    console.error('Failed to toggle status:', error)
    toastStore.show('Failed to update status', 'error')
  }
}

function formatBalance(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

onMounted(fetchCustomers)
</script>

<template>
  <div>
    <PageHeader title="Customers" :breadcrumbs="breadcrumbs">
      <template #actions>
        <router-link
          v-if="authStore.hasPermission('customers:create')"
          :to="{ name: 'CustomerCreate' }"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Customer
        </router-link>
      </template>
    </PageHeader>

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && customers.length === 0"
      title="No customers yet"
      message="Get started by adding your first customer."
      :action-text="authStore.hasPermission('customers:create') ? 'Add Customer' : ''"
      action-route="/crm/customers/new"
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="customers"
        :loading="loading"
        search-placeholder="Search customers..."
      >
        <!-- Name Column -->
        <template #cell-name="{ row }">
          <button
            type="button"
            class="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
            @click="viewCustomer(row)"
          >
            {{ row.name }}
          </button>
        </template>

        <!-- Balance Column -->
        <template #cell-balance="{ row }">
          <span
            :class="[
              'text-sm font-medium',
              row.balance > 0
                ? 'text-red-600 dark:text-red-400'
                : row.balance < 0
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-gray-700 dark:text-gray-300',
            ]"
          >
            {{ formatBalance(row.balance) }}
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
              @click="viewCustomer(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>

            <!-- Edit -->
            <button
              v-if="authStore.hasPermission('customers:edit')"
              type="button"
              class="p-1.5 text-gray-500 hover:text-amber-600 dark:text-gray-400 dark:hover:text-amber-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Edit"
              @click="editCustomer(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
            </button>

            <!-- Toggle Status -->
            <button
              v-if="authStore.hasPermission('customers:edit')"
              type="button"
              :class="[
                'p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
                row.status === 'active'
                  ? 'text-gray-500 hover:text-amber-600 dark:text-gray-400 dark:hover:text-amber-400'
                  : 'text-gray-500 hover:text-green-600 dark:text-gray-400 dark:hover:text-green-400',
              ]"
              :title="row.status === 'active' ? 'Deactivate' : 'Activate'"
              @click="toggleStatus(row)"
            >
              <svg v-if="row.status === 'active'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25v13.5m-7.5-13.5v13.5" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
              </svg>
            </button>

            <!-- Delete -->
            <button
              v-if="authStore.hasPermission('customers:delete')"
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
      title="Delete Customer"
      :message="`Are you sure you want to delete '${selectedCustomer?.name}'? This action cannot be undone.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
