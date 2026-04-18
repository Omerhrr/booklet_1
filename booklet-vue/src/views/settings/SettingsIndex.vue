<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useAuthStore } from '@/stores/auth'
import * as settingsApi from '@/api/settings'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const branchCount = ref(0)
const userCount = ref(0)
const roleCount = ref(0)

const sections = computed(() => {
  const items = []

  if (authStore.hasPermission('settings:edit')) {
    items.push({
      title: 'Business Settings',
      description: 'Edit your business information, logo, and contact details',
      icon: 'M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21',
      route: { name: 'BusinessSettings' },
      color: 'blue',
    })
  }

  if (authStore.hasPermission('branches:view')) {
    items.push({
      title: 'Branches',
      description: 'Manage your business branches and locations',
      icon: 'M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z',
      route: { name: 'BranchCreate' },
      count: branchCount.value,
      color: 'green',
    })
  }

  if (authStore.hasPermission('users:view')) {
    items.push({
      title: 'Users',
      description: 'Manage user accounts and access control',
      icon: 'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z',
      route: { name: 'UserCreate' },
      count: userCount.value,
      color: 'purple',
    })
  }

  if (authStore.hasPermission('roles:view')) {
    items.push({
      title: 'Roles & Permissions',
      description: 'Configure roles and granular permission levels',
      icon: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
      route: { name: 'RoleCreate' },
      count: roleCount.value,
      color: 'amber',
    })
  }

  if (authStore.hasPermission('fiscal_year:view') || authStore.hasPermission('settings:edit')) {
    items.push({
      title: 'Fiscal Years',
      description: 'Manage fiscal year periods and settings',
      icon: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5',
      route: { name: 'FiscalYearCreate' },
      color: 'red',
    })
  }

  return items
})

async function fetchStats() {
  loading.value = true
  try {
    const [branchesRes, usersRes, rolesRes] = await Promise.allSettled([
      settingsApi.listBranches(),
      settingsApi.listUsers(),
      settingsApi.listRoles(),
    ])

    if (branchesRes.status === 'fulfilled') {
      const data = branchesRes.value.data
      branchCount.value = Array.isArray(data) ? data.length : data.items?.length || data.branches?.length || 0
    }
    if (usersRes.status === 'fulfilled') {
      const data = usersRes.value.data
      userCount.value = Array.isArray(data) ? data.length : data.items?.length || data.users?.length || 0
    }
    if (rolesRes.status === 'fulfilled') {
      const data = rolesRes.value.data
      roleCount.value = Array.isArray(data) ? data.length : data.items?.length || data.roles?.length || 0
    }
  } catch (error) {
    console.error('Failed to fetch settings stats:', error)
  } finally {
    loading.value = false
  }
}

function navigateTo(route) {
  router.push(route)
}

onMounted(fetchStats)
</script>

<template>
  <div>
    <PageHeader title="Settings" subtitle="Manage your business settings, users, and permissions" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading settings..." />
    </div>

    <template v-else>
      <!-- Quick Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard
          title="Branches"
          :value="branchCount"
          icon="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6H15m-1.5 3H15m-1.5 3H15M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z"
          color="green"
        />
        <StatCard
          title="Users"
          :value="userCount"
          icon="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
          color="purple"
        />
        <StatCard
          title="Roles"
          :value="roleCount"
          icon="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
          color="amber"
        />
      </div>

      <!-- Section Cards Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <button
          v-for="section in sections"
          :key="section.title"
          type="button"
          class="group bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 text-left hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
          @click="navigateTo(section.route)"
        >
          <div class="flex items-start justify-between mb-4">
            <div
              :class="[
                'w-12 h-12 rounded-lg flex items-center justify-center',
                section.color === 'blue' && 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400',
                section.color === 'green' && 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400',
                section.color === 'purple' && 'bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400',
                section.color === 'amber' && 'bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400',
                section.color === 'red' && 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400',
              ]"
            >
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" :d="section.icon" />
              </svg>
            </div>
            <span
              v-if="section.count !== undefined"
              class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
            >
              {{ section.count }}
            </span>
          </div>
          <h3 class="text-base font-semibold text-gray-900 dark:text-white mb-1 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
            {{ section.title }}
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            {{ section.description }}
          </p>
          <div class="mt-4 flex items-center text-sm font-medium text-blue-600 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">
            <span>Manage</span>
            <svg class="w-4 h-4 ml-1" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </div>
        </button>
      </div>
    </template>
  </div>
</template>
