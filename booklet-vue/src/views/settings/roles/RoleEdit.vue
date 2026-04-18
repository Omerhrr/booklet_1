<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { useToastStore } from '@/stores/toast'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const route = useRoute()
const toastStore = useToastStore()

const loading = ref(false)
const saving = ref(false)
const errors = reactive({
  name: '',
})

const form = reactive({
  name: '',
  description: '',
})

const breadcrumbs = [
  { text: 'Settings', to: '/settings' },
  { text: 'Edit Role' },
]

// ── Permission Categories ────────────────────────────────────
const permissionCategories = [
  { key: 'crm', label: 'CRM' },
  { key: 'inventory', label: 'Inventory' },
  { key: 'sales', label: 'Sales' },
  { key: 'purchases', label: 'Purchases' },
  { key: 'expenses', label: 'Expenses' },
  { key: 'other_income', label: 'Other Income' },
  { key: 'accounting', label: 'Accounting' },
  { key: 'hr', label: 'HR' },
  { key: 'banking', label: 'Banking' },
  { key: 'reports', label: 'Reports' },
  { key: 'settings', label: 'Settings' },
  { key: 'ai', label: 'AI' },
  { key: 'agents', label: 'Agents' },
]

const permissionActions = ['view', 'create', 'edit', 'delete']

const selectedPermissions = ref(new Set())

function permKey(category, action) {
  return `${category}:${action}`
}

function isPermissionSelected(category, action) {
  return selectedPermissions.value.has(permKey(category, action))
}

function togglePermission(category, action) {
  const key = permKey(category, action)
  const updated = new Set(selectedPermissions.value)
  if (updated.has(key)) {
    updated.delete(key)
  } else {
    updated.add(key)
  }
  selectedPermissions.value = updated
}

function toggleCategoryAll(category) {
  const updated = new Set(selectedPermissions.value)
  const allSelected = permissionActions.every((a) => updated.has(permKey(category, a)))

  if (allSelected) {
    permissionActions.forEach((a) => updated.delete(permKey(category, a)))
  } else {
    permissionActions.forEach((a) => updated.add(permKey(category, a)))
  }
  selectedPermissions.value = updated
}

function isCategoryAllSelected(category) {
  return permissionActions.every((a) => selectedPermissions.value.has(permKey(category, a)))
}

function selectAllPermissions() {
  const updated = new Set(selectedPermissions.value)
  permissionCategories.forEach((cat) => {
    permissionActions.forEach((a) => updated.add(permKey(cat.key, a)))
  })
  selectedPermissions.value = updated
}

function clearAllPermissions() {
  selectedPermissions.value = new Set()
}

const totalSelected = computed(() => selectedPermissions.value.size)
const totalPermissions = computed(() => permissionCategories.length * permissionActions.length)

function validate() {
  let valid = true
  errors.name = ''

  if (!form.name.trim()) {
    errors.name = 'Role name is required'
    valid = false
  }

  return valid
}

async function fetchRole() {
  loading.value = true
  try {
    const { data } = await settingsApi.getRole(route.params.id)
    form.name = data.name || ''
    form.description = data.description || ''
    const perms = data.permissions || []
    selectedPermissions.value = new Set(perms)
  } catch (error) {
    console.error('Failed to fetch role:', error)
    toastStore.show('Failed to load role', 'error')
    router.push({ name: 'SettingsIndex' })
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!validate()) return

  saving.value = true
  try {
    await settingsApi.updateRole(route.params.id, {
      name: form.name,
      description: form.description,
      permissions: Array.from(selectedPermissions.value),
    })
    toastStore.show('Role updated successfully')
    router.push({ name: 'SettingsIndex' })
  } catch (error) {
    console.error('Failed to update role:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to update role'
    toastStore.show(message, 'error')
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'SettingsIndex' })
}

onMounted(fetchRole)
</script>

<template>
  <div>
    <PageHeader title="Edit Role" :breadcrumbs="breadcrumbs" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading role..." />
    </div>

    <div v-else class="max-w-4xl mx-auto space-y-6">
      <!-- Basic Info -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.name"
            label="Role Name"
            name="name"
            placeholder="e.g. Sales Manager"
            required
            :error="errors.name"
          />
          <TextareaInput
            v-model="form.description"
            label="Description"
            name="description"
            placeholder="Describe the purpose of this role..."
            :rows="3"
          />
        </div>
      </div>

      <!-- Permissions Matrix -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Permissions</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
              {{ totalSelected }} of {{ totalPermissions }} permissions selected
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="selectAllPermissions"
            >
              Select All
            </button>
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="clearAllPermissions"
            >
              Clear All
            </button>
          </div>
        </div>

        <!-- Permission Grid -->
        <div class="overflow-x-auto">
          <table class="min-w-full">
            <thead class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 w-48">
                  Category
                </th>
                <th
                  v-for="action in permissionActions"
                  :key="action"
                  class="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400"
                >
                  {{ action }}
                </th>
                <th class="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  All
                </th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="category in permissionCategories"
                :key="category.key"
                class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <td class="px-6 py-3 text-sm font-medium text-gray-900 dark:text-white">
                  {{ category.label }}
                </td>
                <td
                  v-for="action in permissionActions"
                  :key="action"
                  class="px-4 py-3 text-center"
                >
                  <input
                    type="checkbox"
                    :checked="isPermissionSelected(category.key, action)"
                    class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 cursor-pointer"
                    @change="togglePermission(category.key, action)"
                  />
                </td>
                <td class="px-4 py-3 text-center">
                  <input
                    type="checkbox"
                    :checked="isCategoryAllSelected(category.key)"
                    class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 cursor-pointer"
                    @change="toggleCategoryAll(category.key)"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-end gap-3 pb-6">
        <button
          type="button"
          class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="handleCancel"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="saving"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleSubmit"
        >
          <LoadingSpinner v-if="saving" size="sm" />
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </div>
  </div>
</template>
