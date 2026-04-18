<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { changePassword } from '@/api/auth'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

// ── Form State ──────────────────────────────────────────────
const form = ref({
  currentPassword: '',
  newPassword: '',
  confirmNewPassword: '',
})
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const loading = ref(false)
const successMessage = ref('')
const serverError = ref('')

// ── Validation ──────────────────────────────────────────────
const errors = computed(() => {
  const e = {}
  if (!form.value.currentPassword) {
    e.currentPassword = 'Current password is required'
  }
  if (!form.value.newPassword) {
    e.newPassword = 'New password is required'
  } else if (form.value.newPassword.length < 8) {
    e.newPassword = 'Password must be at least 8 characters'
  } else if (form.value.newPassword === form.value.currentPassword) {
    e.newPassword = 'New password must be different from the current password'
  }
  if (!form.value.confirmNewPassword) {
    e.confirmNewPassword = 'Please confirm your new password'
  } else if (form.value.newPassword !== form.value.confirmNewPassword) {
    e.confirmNewPassword = 'Passwords do not match'
  }
  return e
})

const isValid = computed(() => Object.keys(errors.value).length === 0)

// ── Submit ──────────────────────────────────────────────────
async function handleChangePassword() {
  serverError.value = ''
  successMessage.value = ''

  if (!isValid.value) return

  loading.value = true
  try {
    await changePassword({
      current_password: form.value.currentPassword,
      new_password: form.value.newPassword,
      confirm_password: form.value.confirmNewPassword,
    })

    successMessage.value = 'Password changed successfully. You will be signed out shortly.'

    // Auto-logout after a short delay so the user sees the success message
    setTimeout(async () => {
      await authStore.logout()
      toastStore.show('Password updated. Please sign in with your new password.', 'success')
      router.push({ name: 'AuthLogin' })
    }, 2000)
  } catch (err) {
    const data = err.response?.data
    if (data) {
      if (data.detail) {
        serverError.value = data.detail
      } else if (data.message) {
        serverError.value = data.message
      } else if (data.current_password) {
        serverError.value = Array.isArray(data.current_password) ? data.current_password[0] : data.current_password
      } else if (data.new_password) {
        serverError.value = Array.isArray(data.new_password) ? data.new_password[0] : data.new_password
      } else if (typeof data === 'string') {
        serverError.value = data
      } else {
        serverError.value = 'Failed to change password. Please try again.'
      }
    } else {
      serverError.value = 'Network error. Please check your connection and try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader
      title="Change Password"
      subtitle="Update your account password"
      :breadcrumbs="[
        { text: 'Dashboard', to: { name: 'DashboardIndex' } },
        { text: 'Change Password' },
      ]"
    />

    <div class="max-w-xl mx-auto">
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 sm:p-8">
        <!-- Success Message -->
        <div
          v-if="successMessage"
          class="mb-6 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800"
        >
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
            </svg>
            <p class="text-sm text-green-700 dark:text-green-300">{{ successMessage }}</p>
          </div>
        </div>

        <!-- Server Error -->
        <div
          v-if="serverError"
          class="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
        >
          <div class="flex items-start gap-3">
            <svg class="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
            </svg>
            <p class="text-sm text-red-700 dark:text-red-300">{{ serverError }}</p>
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleChangePassword" class="space-y-5" novalidate>
          <!-- Current Password -->
          <div>
            <label for="currentPassword" class="form-label">
              Current Password
            </label>
            <div class="relative">
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <svg class="h-5 w-5 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                </svg>
              </div>
              <input
                id="currentPassword"
                v-model="form.currentPassword"
                :type="showCurrentPassword ? 'text' : 'password'"
                autocomplete="current-password"
                required
                placeholder="Enter your current password"
                :class="[
                  'form-input pl-10 pr-10',
                  errors.currentPassword && 'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-500 dark:focus:border-red-500 dark:focus:ring-red-500/20',
                ]"
                :disabled="loading"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                @click="showCurrentPassword = !showCurrentPassword"
                :aria-label="showCurrentPassword ? 'Hide password' : 'Show password'"
              >
                <svg v-if="!showCurrentPassword" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                </svg>
              </button>
            </div>
            <p v-if="errors.currentPassword" class="mt-1.5 text-sm text-red-600 dark:text-red-400">
              {{ errors.currentPassword }}
            </p>
          </div>

          <!-- New Password -->
          <div>
            <label for="newPassword" class="form-label">
              New Password
            </label>
            <div class="relative">
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <svg class="h-5 w-5 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                </svg>
              </div>
              <input
                id="newPassword"
                v-model="form.newPassword"
                :type="showNewPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                placeholder="Minimum 8 characters"
                :class="[
                  'form-input pl-10 pr-10',
                  errors.newPassword && 'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-500 dark:focus:border-red-500 dark:focus:ring-red-500/20',
                ]"
                :disabled="loading"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                @click="showNewPassword = !showNewPassword"
                :aria-label="showNewPassword ? 'Hide password' : 'Show password'"
              >
                <svg v-if="!showNewPassword" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                </svg>
              </button>
            </div>
            <p v-if="errors.newPassword" class="mt-1.5 text-sm text-red-600 dark:text-red-400">
              {{ errors.newPassword }}
            </p>
            <p v-else class="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
              Must be at least 8 characters and different from your current password.
            </p>
          </div>

          <!-- Confirm New Password -->
          <div>
            <label for="confirmNewPassword" class="form-label">
              Confirm New Password
            </label>
            <div class="relative">
              <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <svg class="h-5 w-5 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
              <input
                id="confirmNewPassword"
                v-model="form.confirmNewPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="new-password"
                required
                placeholder="Repeat your new password"
                :class="[
                  'form-input pl-10 pr-10',
                  errors.confirmNewPassword && 'border-red-500 focus:border-red-500 focus:ring-red-500/20 dark:border-red-500 dark:focus:border-red-500 dark:focus:ring-red-500/20',
                ]"
                :disabled="loading"
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                @click="showConfirmPassword = !showConfirmPassword"
                :aria-label="showConfirmPassword ? 'Hide password' : 'Show password'"
              >
                <svg v-if="!showConfirmPassword" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                </svg>
              </button>
            </div>
            <p v-if="errors.confirmNewPassword" class="mt-1.5 text-sm text-red-600 dark:text-red-400">
              {{ errors.confirmNewPassword }}
            </p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-2">
            <router-link
              :to="{ name: 'DashboardIndex' }"
              class="flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-xl hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 dark:focus:ring-offset-gray-800 transition-colors"
            >
              Cancel
            </router-link>
            <button
              type="submit"
              :disabled="loading"
              class="flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold text-white rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <svg
                v-if="loading"
                class="animate-spin h-5 w-5 text-white"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span>{{ loading ? 'Updating...' : 'Update Password' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
