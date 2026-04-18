<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const loading = ref(false)
const saving = ref(false)
const errors = reactive({
  username: '',
  email: '',
})

const form = reactive({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  role_id: '',
  branch_id: '',
  is_active: true,
})

const roleOptions = ref([])
const branchOptions = ref([])

const breadcrumbs = computed(() => [
  { text: 'Settings', to: '/settings' },
  { text: 'Users', to: '/settings' },
  { text: 'Edit User' },
])

const isMultiBranch = computed(() => authStore.branches.length > 1)

function validate() {
  let valid = true
  errors.username = ''
  errors.email = ''

  if (!form.username.trim()) {
    errors.username = 'Username is required'
    valid = false
  }
  if (!form.email.trim()) {
    errors.email = 'Email is required'
    valid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Please enter a valid email address'
    valid = false
  }

  return valid
}

async function fetchUser() {
  loading.value = true
  try {
    const { data } = await settingsApi.getUser(route.params.id)
    Object.keys(form).forEach((key) => {
      if (data[key] !== undefined) {
        form[key] = data[key]
      }
    })
    // Handle role_id from roles array
    if (!form.role_id && data.roles && Array.isArray(data.roles) && data.roles.length > 0) {
      form.role_id = String(data.roles[0].id || data.roles[0])
    }
    // Handle branch_id from branch object
    if (!form.branch_id && data.branch) {
      form.branch_id = String(data.branch.id || data.branch)
    }
  } catch (error) {
    console.error('Failed to fetch user:', error)
    toastStore.show('Failed to load user', 'error')
    router.push({ name: 'SettingsIndex' })
  } finally {
    loading.value = false
  }
}

async function fetchOptions() {
  try {
    const [rolesRes] = await Promise.all([
      settingsApi.listRoles(),
      authStore.fetchBranches(),
    ])
    const roles = Array.isArray(rolesRes.data) ? rolesRes.data : rolesRes.data.items || rolesRes.data.roles || []
    roleOptions.value = roles.map((r) => ({
      value: String(r.id),
      label: r.name,
    }))
    branchOptions.value = authStore.branches.map((b) => ({
      value: String(b.id),
      label: b.name,
    }))
  } catch (error) {
    console.error('Failed to load options:', error)
  }
}

async function handleSubmit() {
  if (!validate()) return

  saving.value = true
  try {
    await settingsApi.updateUser(route.params.id, form)
    toastStore.show('User updated successfully')
    router.push({ name: 'UserDetail', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update user:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to update user'
    toastStore.show(message, 'error')
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'UserDetail', params: { id: route.params.id } })
}

onMounted(async () => {
  await Promise.all([fetchOptions(), fetchUser()])
})
</script>

<template>
  <div>
    <PageHeader title="Edit User" :breadcrumbs="breadcrumbs" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading user..." />
    </div>

    <div v-else class="max-w-3xl mx-auto">
      <form
        class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
        @submit.prevent="handleSubmit"
      >
        <!-- Username & Email -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.username"
            label="Username"
            name="username"
            placeholder="Enter username"
            required
            :error="errors.username"
          />
          <TextInput
            v-model="form.email"
            label="Email"
            name="email"
            type="email"
            placeholder="Enter email address"
            required
            :error="errors.email"
          />
        </div>

        <!-- First Name & Last Name -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.first_name"
            label="First Name"
            name="first_name"
            placeholder="Enter first name"
          />
          <TextInput
            v-model="form.last_name"
            label="Last Name"
            name="last_name"
            placeholder="Enter last name"
          />
        </div>

        <!-- Role & Branch -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <SelectInput
            v-model="form.role_id"
            label="Role"
            name="role_id"
            :options="roleOptions"
            placeholder="Select a role"
          />
          <SelectInput
            v-if="isMultiBranch"
            v-model="form.branch_id"
            label="Branch"
            name="branch_id"
            :options="branchOptions"
            placeholder="Select branch"
          />
        </div>

        <!-- Is Active -->
        <label class="flex items-center gap-3 cursor-pointer">
          <input
            v-model="form.is_active"
            type="checkbox"
            class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
          />
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            User is active
          </span>
        </label>

        <!-- Info Banner -->
        <div class="p-3 rounded-lg bg-gray-50 border border-gray-200 dark:bg-gray-700 dark:border-gray-600">
          <p class="text-xs text-gray-500 dark:text-gray-400">
            <svg class="w-4 h-4 inline-block mr-1 -mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
            To change the user's password, use the Change Password page from the user's profile.
          </p>
        </div>

        <!-- Actions -->
        <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
            @click="handleCancel"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="saving"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <LoadingSpinner v-if="saving" size="sm" />
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
