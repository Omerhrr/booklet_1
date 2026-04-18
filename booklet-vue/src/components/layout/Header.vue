<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useSidebarStore } from '@/stores/sidebar'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

const props = defineProps({
  title: {
    type: String,
    default: 'Dashboard',
  },
})

const router = useRouter()
const sidebarStore = useSidebarStore()
const authStore = useAuthStore()
const themeStore = useThemeStore()

// ── Branch selector dropdown ───────────────────────────────
const showBranchDropdown = ref(false)
const showUserDropdown = ref(false)

const showBranchSelector = computed(() => {
  return authStore.isSuperuser && authStore.branches.length > 1
})

const currentBranchName = computed(() => {
  return authStore.selectedBranchName || 'Select Branch'
})

function selectBranch(id) {
  authStore.setBranch(id)
  showBranchDropdown.value = false
  // Optionally reload data for the selected branch
  window.location.reload()
}

// ── Theme toggle ───────────────────────────────────────────
function toggleTheme() {
  themeStore.toggle()
}

// ── User actions ───────────────────────────────────────────
function handleChangePassword() {
  showUserDropdown.value = false
  router.push('/auth/change-password')
}

function handleLogout() {
  showUserDropdown.value = false
  authStore.logout()
  router.push('/auth/login')
}

// ── Mobile sidebar toggle ──────────────────────────────────
function toggleMobileSidebar() {
  sidebarStore.toggleMobile()
}

// ── Close dropdowns on outside click ───────────────────────
function handleClickOutside(event) {
  if (!event.target.closest('.branch-dropdown')) {
    showBranchDropdown.value = false
  }
  if (!event.target.closest('.user-dropdown')) {
    showUserDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// ── User display name ──────────────────────────────────────
const userDisplayName = computed(() => {
  if (authStore.user) {
    return authStore.user.first_name && authStore.user.last_name
      ? `${authStore.user.first_name} ${authStore.user.last_name}`
      : authStore.user.username || authStore.user.email || 'User'
  }
  return 'User'
})

const userEmail = computed(() => {
  return authStore.user?.email || ''
})
</script>

<template>
  <header
    class="sticky top-0 z-30 bg-white/80 dark:bg-gray-800 backdrop-blur-md border-b border-gray-200 dark:border-gray-700 transition-colors"
  >
    <div class="flex items-center justify-between h-16 px-4 sm:px-6">
      <!-- ── Left Section ────────────────────────────── -->
      <div class="flex items-center gap-3">
        <!-- Mobile Hamburger -->
        <button
          class="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          @click="toggleMobileSidebar"
          aria-label="Toggle mobile menu"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <!-- Desktop Sidebar Collapse Toggle -->
        <button
          class="hidden lg:block p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          @click="sidebarStore.toggleCollapsed"
          :aria-label="sidebarStore.isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        >
          <svg
            class="w-5 h-5 transition-transform duration-200"
            :class="{ 'rotate-180': sidebarStore.isCollapsed }"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>

        <!-- Page Title -->
        <h1 class="text-lg font-semibold text-gray-900 dark:text-white truncate">
          {{ title }}
        </h1>
      </div>

      <!-- ── Right Section ───────────────────────────── -->
      <div class="flex items-center gap-2 sm:gap-3">

        <!-- Branch Selector (superuser with multiple branches) -->
        <div v-if="showBranchSelector" class="relative branch-dropdown">
          <button
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors border border-gray-200 dark:border-gray-600"
            @click.stop="showBranchDropdown = !showBranchDropdown"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span class="hidden sm:inline truncate max-w-32">{{ currentBranchName }}</span>
            <svg
              class="w-3 h-3 transition-transform duration-200"
              :class="{ 'rotate-180': showBranchDropdown }"
              fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Branch Dropdown -->
          <transition name="dropdown">
            <div
              v-if="showBranchDropdown"
              class="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50"
            >
              <div class="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Select Branch
              </div>
              <button
                v-for="branch in authStore.branches"
                :key="branch.id"
                class="flex items-center w-full px-3 py-2 text-sm text-left transition-colors"
                :class="[
                  String(branch.id) === authStore.selectedBranchId
                    ? 'bg-blue-50 dark:bg-gray-700 text-blue-600 dark:text-blue-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                ]"
                @click="selectBranch(branch.id)"
              >
                <span class="flex-1 truncate">{{ branch.name }}</span>
                <svg
                  v-if="String(branch.id) === authStore.selectedBranchId"
                  class="w-4 h-4 text-blue-600 dark:text-blue-400 ml-2 flex-shrink-0"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
          </transition>
        </div>

        <!-- Theme Toggle -->
        <button
          class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          @click="toggleTheme"
          :aria-label="themeStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        >
          <!-- Sun icon (shown in dark mode) -->
          <svg
            v-if="themeStore.isDark"
            class="w-5 h-5"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <!-- Moon icon (shown in light mode) -->
          <svg
            v-else
            class="w-5 h-5"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        </button>

        <!-- User Dropdown -->
        <div class="relative user-dropdown">
          <button
            class="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            @click.stop="showUserDropdown = !showUserDropdown"
            aria-label="User menu"
          >
            <!-- User Avatar -->
            <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
              <span class="text-white text-sm font-medium">
                {{ userDisplayName.charAt(0).toUpperCase() }}
              </span>
            </div>
            <!-- User Info (hidden on small screens) -->
            <div class="hidden sm:block text-left">
              <div class="text-sm font-medium text-gray-900 dark:text-white truncate max-w-40">
                {{ userDisplayName }}
              </div>
              <div v-if="userEmail" class="text-xs text-gray-500 dark:text-gray-400 truncate max-w-40">
                {{ userEmail }}
              </div>
            </div>
            <svg
              class="w-3 h-3 text-gray-400 hidden sm:block transition-transform duration-200"
              :class="{ 'rotate-180': showUserDropdown }"
              fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- User Dropdown Menu -->
          <transition name="dropdown">
            <div
              v-if="showUserDropdown"
              class="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50"
            >
              <!-- User Info Header -->
              <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <div class="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {{ userDisplayName }}
                </div>
                <div v-if="userEmail" class="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                  {{ userEmail }}
                </div>
              </div>

              <!-- Change Password -->
              <button
                class="flex items-center w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                @click="handleChangePassword"
              >
                <svg class="w-4 h-4 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
                Change Password
              </button>

              <!-- Logout -->
              <button
                class="flex items-center w-full px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-gray-700 transition-colors"
                @click="handleLogout"
              >
                <svg class="w-4 h-4 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign Out
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
.dropdown-enter-to,
.dropdown-leave-from {
  opacity: 1;
  transform: translateY(0);
}
</style>
