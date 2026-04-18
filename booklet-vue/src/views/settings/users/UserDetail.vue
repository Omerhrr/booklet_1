<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Badge from '@/components/common/Badge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Modal from '@/components/common/Modal.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatDate } from '@/utils/dates'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const user = ref(null)
const loading = ref(true)
const showDeleteDialog = ref(false)
const showAssignRoleModal = ref(false)
const deleting = ref(false)
const assigning = ref(false)

// Assign role form
const assignRoleId = ref('')
const roleOptions = ref([])

const breadcrumbs = computed(() => [
  { text: 'Settings', to: '/settings' },
  { text: user.value ? `${user.value.first_name} ${user.value.last_name}` : 'User Details' },
])

const userRoles = computed(() => {
  if (!user.value?.roles) return []
  return Array.isArray(user.value.roles) ? user.value.roles : []
})

function getFullName(u) {
  if (!u) return ''
  return `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.username || ''
}

async function fetchUser() {
  loading.value = true
  try {
    const { data } = await settingsApi.getUser(route.params.id)
    user.value = data
  } catch (error) {
    console.error('Failed to fetch user:', error)
    toastStore.show('Failed to load user', 'error')
    router.push({ name: 'SettingsIndex' })
  } finally {
    loading.value = false
  }
}

async function fetchRoles() {
  try {
    const { data } = await settingsApi.listRoles()
    const roles = Array.isArray(data) ? data : data.items || data.roles || []
    roleOptions.value = roles.map((r) => ({
      value: String(r.id),
      label: r.name,
    }))
  } catch (error) {
    console.error('Failed to load roles:', error)
  }
}

function editUser() {
  router.push({ name: 'UserEdit', params: { id: route.params.id } })
}

function goBack() {
  router.push({ name: 'SettingsIndex' })
}

async function handleDelete() {
  deleting.value = true
  try {
    await settingsApi.deleteUser(route.params.id)
    toastStore.show('User deleted successfully')
    router.push({ name: 'SettingsIndex' })
  } catch (error) {
    console.error('Failed to delete user:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to delete user'
    toastStore.show(message, 'error')
  } finally {
    deleting.value = false
  }
}

function openAssignRoleModal() {
  assignRoleId.value = ''
  showAssignRoleModal.value = true
}

async function handleAssignRole() {
  if (!assignRoleId.value) {
    toastStore.show('Please select a role', 'error')
    return
  }

  assigning.value = true
  try {
    await settingsApi.assignUserRole(route.params.id, { role_id: assignRoleId.value })
    toastStore.show('Role assigned successfully')
    showAssignRoleModal.value = false
    await fetchUser()
  } catch (error) {
    console.error('Failed to assign role:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to assign role'
    toastStore.show(message, 'error')
  } finally {
    assigning.value = false
  }
}

onMounted(() => {
  fetchUser()
  fetchRoles()
})
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading user..." />
    </div>

    <template v-else-if="user">
      <PageHeader :title="getFullName(user)" :breadcrumbs="breadcrumbs">
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
              v-if="authStore.hasPermission('users:edit')"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
              @click="editUser"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
              Edit
            </button>

            <button
              v-if="authStore.hasPermission('users:delete')"
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

      <!-- User Info Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">User Information</h3>
        <dl class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Full Name</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ getFullName(user) }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Username</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">@{{ user.username }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Email</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ user.email }}</dd>
          </div>
          <div v-if="user.branch">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Branch</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ user.branch.name || user.branch }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Status</dt>
            <dd class="mt-0.5">
              <StatusBadge :status="user.is_active ? 'active' : 'inactive'" />
            </dd>
          </div>
          <div v-if="user.created_at">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Created</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ formatDate(user.created_at) }}</dd>
          </div>
        </dl>
      </div>

      <!-- Assigned Roles -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Assigned Roles</h3>
          <button
            v-if="authStore.hasPermission('users:edit')"
            type="button"
            class="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700 dark:hover:bg-blue-900/50 transition-colors"
            @click="openAssignRoleModal"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Assign Role
          </button>
        </div>

        <div v-if="userRoles.length === 0" class="py-6 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No roles assigned to this user.</p>
        </div>

        <div v-else class="flex flex-wrap gap-2">
          <Badge
            v-for="role in userRoles"
            :key="role.id || role"
            :text="typeof role === 'string' ? role : role.name"
            variant="info"
            size="md"
          />
        </div>
      </div>

      <!-- Reset Password Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Password Management</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Password changes are handled through the change password page for security.
        </p>
        <router-link
          :to="{ name: 'AuthChangePassword' }"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-300 rounded-lg hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700 dark:hover:bg-amber-900/50 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
          </svg>
          Change Password
        </router-link>
      </div>
    </template>

    <!-- Assign Role Modal -->
    <Modal
      v-model:show="showAssignRoleModal"
      title="Assign Role"
      size="sm"
    >
      <div class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Select a role to assign to {{ getFullName(user) }}
        </p>
        <SelectInput
          v-model="assignRoleId"
          label="Role"
          name="assign_role"
          :options="roleOptions"
          placeholder="Select a role"
          required
        />
      </div>
      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="showAssignRoleModal = false"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="assigning"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          @click="handleAssignRole"
        >
          <LoadingSpinner v-if="assigning" size="sm" />
          {{ assigning ? 'Assigning...' : 'Assign' }}
        </button>
      </template>
    </Modal>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete User"
      :message="`Are you sure you want to delete '${getFullName(user)}'? This action cannot be undone.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
