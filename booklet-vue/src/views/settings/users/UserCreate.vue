<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const loading = ref(false)
const saving = ref(false)
const errors = reactive({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  password: '',
})

const form = reactive({
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  password: '',
  role_id: '',
  branch_id: '',
  is_active: true,
})

const roleOptions = ref([])
const branchOptions = ref([])

const breadcrumbs = [
  { text: 'Settings', to: '/settings' },
  { text: 'New User' },
]

const isMultiBranch = computed(() => authStore.branches.length > 1)

const atUserLimit = computed(() => {
  return !authStore.canCreateUser()
})

function validate() {
  let valid = true
  errors.username = ''
  errors.email = ''
  errors.first_name = ''
  errors.last_name = ''
  errors.password = ''

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
  if (!form.first_name.trim()) {
    errors.first_name = 'First name is required'
    valid = false
  }
  if (!form.last_name.trim()) {
    errors.last_name = 'Last name is required'
    valid = false
  }
  if (!form.password) {
    errors.password = 'Password is required'
    valid = false
  } else if (form.password.length < 8) {
    errors.password = 'Password must be at least 8 characters'
    valid = false
  }

  return valid
}

async function fetchOptions() {
  loading.value = true
  try {
    await Promise.all([
      authStore.fetchPlanLimits(),
      authStore.fetchBranches(),
      loadRoles(),
    ])
    branchOptions.value = authStore.branches.map((b) => ({
      value: String(b.id),
      label: b.name,
    }))
  } catch (error) {
    console.error('Failed to load options:', error)
  } finally {
    loading.value = false
  }
}

async function loadRoles() {
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

async function handleSubmit() {
  if (!validate()) return
  if (atUserLimit.value) {
    toastStore.show('You have reached the user limit for your plan. Please upgrade to add more users.', 'error')
    return
  }

  saving.value = true
  try {
    await settingsApi.createUser(form)
    toastStore.show('User created successfully')
    router.push({ name: 'SettingsIndex' })
  } catch (error) {
    console.error('Failed to create user:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to create user'
    toastStore.show(message, 'error')
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  router.push({ name: 'SettingsIndex' })
}

onMounted(fetchOptions)
</script>

<template>
  <div>
    <PageHeader title="Create User" :breadcrumbs="breadcrumbs" />

    <!-- Plan Limit Warning -->
    <div v-if="atUserLimit && !loading" class="mb-6 p-4 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-700">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <div class="ml-3">
          <h3 class="text-sm font-medium text-amber-800 dark:text-amber-300">User Limit Reached</h3>
          <p class="mt-1 text-sm text-amber-700 dark:text-amber-400">
            You have reached the maximum number of users allowed by your current plan. Please upgrade your subscription to add more users.
          </p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading..." />
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
            :disabled="atUserLimit"
          />
          <TextInput
            v-model="form.email"
            label="Email"
            name="email"
            type="email"
            placeholder="Enter email address"
            required
            :error="errors.email"
            :disabled="atUserLimit"
          />
        </div>

        <!-- First Name & Last Name -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <TextInput
            v-model="form.first_name"
            label="First Name"
            name="first_name"
            placeholder="Enter first name"
            required
            :error="errors.first_name"
            :disabled="atUserLimit"
          />
          <TextInput
            v-model="form.last_name"
            label="Last Name"
            name="last_name"
            placeholder="Enter last name"
            required
            :error="errors.last_name"
            :disabled="atUserLimit"
          />
        </div>

        <!-- Password -->
        <TextInput
          v-model="form.password"
          label="Password"
          name="password"
          type="password"
          placeholder="Enter password (min 8 characters)"
          required
          :error="errors.password"
          :disabled="atUserLimit"
          help-text="Minimum 8 characters"
        />

        <!-- Role & Branch -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <SelectInput
            v-model="form.role_id"
            label="Role"
            name="role_id"
            :options="roleOptions"
            placeholder="Select a role"
            required
            :disabled="atUserLimit"
          />
          <SelectInput
            v-if="isMultiBranch"
            v-model="form.branch_id"
            label="Branch"
            name="branch_id"
            :options="branchOptions"
            placeholder="Select branch"
            :disabled="atUserLimit"
          />
        </div>

        <!-- Is Active -->
        <label class="flex items-center gap-3 cursor-pointer">
          <input
            v-model="form.is_active"
            type="checkbox"
            :disabled="atUserLimit"
            class="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800"
          />
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
            User is active
          </span>
        </label>

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
            :disabled="saving || atUserLimit"
            class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <LoadingSpinner v-if="saving" size="sm" />
            {{ saving ? 'Creating...' : 'Create User' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
