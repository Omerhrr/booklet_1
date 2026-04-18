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
import { formatDate } from '@/utils/dates'
import * as hrApi from '@/api/hr'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const employees = ref([])
const loading = ref(true)
const showTerminateDialog = ref(false)
const selectedEmployee = ref(null)
const terminating = ref(false)

const breadcrumbs = [
  { text: 'HR' },
  { text: 'Employees' },
]

const statusVariantMap = {
  active: 'success',
  terminated: 'danger',
}

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'department', label: 'Department', sortable: true },
  { key: 'position', label: 'Position', sortable: true },
  { key: 'hire_date', label: 'Hire Date', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchEmployees() {
  loading.value = true
  try {
    const { data } = await hrApi.listEmployees()
    employees.value = Array.isArray(data) ? data : data.items || data.employees || []
  } catch (error) {
    console.error('Failed to fetch employees:', error)
    toastStore.show('Failed to load employees', 'error')
  } finally {
    loading.value = false
  }
}

function getFullName(emp) {
  return `${emp.first_name || ''} ${emp.last_name || ''}`.trim() || emp.name || '—'
}

function viewEmployee(employee) {
  router.push({ name: 'EmployeeDetail', params: { id: employee.id } })
}

function editEmployee(employee) {
  router.push({ name: 'EmployeeEdit', params: { id: employee.id } })
}

function configurePayroll(employee) {
  router.push({ name: 'EmployeeDetail', params: { id: employee.id }, query: { tab: 'payroll' } })
}

function confirmTerminate(employee) {
  selectedEmployee.value = employee
  showTerminateDialog.value = true
}

async function handleTerminate() {
  if (!selectedEmployee.value) return
  terminating.value = true
  try {
    await hrApi.terminateEmployee(selectedEmployee.value.id)
    toastStore.show(`${getFullName(selectedEmployee.value)} has been terminated`)
    await fetchEmployees()
  } catch (error) {
    console.error('Failed to terminate employee:', error)
    toastStore.show('Failed to terminate employee', 'error')
  } finally {
    terminating.value = false
    selectedEmployee.value = null
  }
}

onMounted(fetchEmployees)
</script>

<template>
  <div>
    <PageHeader title="Employees" :breadcrumbs="breadcrumbs">
      <template #actions>
        <router-link
          v-if="authStore.hasPermission('employees:create')"
          :to="{ name: 'EmployeeCreate' }"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Employee
        </router-link>
      </template>
    </PageHeader>

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && employees.length === 0"
      title="No employees yet"
      message="Get started by adding your first employee."
      :action-text="authStore.hasPermission('employees:create') ? 'Add Employee' : ''"
      action-route="/hr/employees/new"
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="employees"
        :loading="loading"
        search-placeholder="Search employees..."
      >
        <!-- Name Column -->
        <template #cell-name="{ row }">
          <button
            type="button"
            class="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
            @click="viewEmployee(row)"
          >
            {{ getFullName(row) }}
          </button>
        </template>

        <!-- Hire Date Column -->
        <template #cell-hire_date="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300">
            {{ formatDate(row.hire_date, 'short') }}
          </span>
        </template>

        <!-- Status Column -->
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" :variant-map="statusVariantMap" />
        </template>

        <!-- Actions -->
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <!-- View -->
            <button
              type="button"
              class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="View"
              @click="viewEmployee(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>

            <!-- Edit -->
            <button
              v-if="authStore.hasPermission('employees:edit')"
              type="button"
              class="p-1.5 text-gray-500 hover:text-amber-600 dark:text-gray-400 dark:hover:text-amber-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Edit"
              @click="editEmployee(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
            </button>

            <!-- Terminate -->
            <button
              v-if="authStore.hasPermission('employees:edit') && row.status === 'active'"
              type="button"
              class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Terminate"
              @click="confirmTerminate(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </button>

            <!-- Payroll Config -->
            <button
              v-if="authStore.hasPermission('payroll:view')"
              type="button"
              class="p-1.5 text-gray-500 hover:text-green-600 dark:text-gray-400 dark:hover:text-green-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Payroll Config"
              @click="configurePayroll(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Terminate Confirmation -->
    <ConfirmDialog
      v-model:show="showTerminateDialog"
      title="Terminate Employee"
      :message="`Are you sure you want to terminate '${getFullName(selectedEmployee)}'? This action cannot be undone and will affect payroll processing.`"
      confirm-text="Terminate"
      type="danger"
      @confirm="handleTerminate"
    />
  </div>
</template>
