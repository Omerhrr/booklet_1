<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { getAnalyses, getDashboards } from '@/api/analytics'
import { formatDate } from '@/utils/dates'

const router = useRouter()
const loading = ref(true)
const analysesCount = ref(0)
const dashboardsCount = ref(0)
const recentAnalyses = ref([])
const recentDashboards = ref([])

async function fetchData() {
  loading.value = true
  try {
    const [analysesRes, dashboardsRes] = await Promise.all([
      getAnalyses({ page_size: 5 }),
      getDashboards({ page_size: 5 }),
    ])
    const analysesData = analysesRes.data
    const dashboardsData = dashboardsRes.data
    recentAnalyses.value = Array.isArray(analysesData) ? analysesData.slice(0, 5) : (analysesData.items || []).slice(0, 5)
    recentDashboards.value = Array.isArray(dashboardsData) ? dashboardsData.slice(0, 5) : (dashboardsData.items || []).slice(0, 5)
    analysesCount.value = analysesData.total || recentAnalyses.value.length
    dashboardsCount.value = dashboardsData.total || recentDashboards.value.length
  } catch (error) {
    console.error('Failed to fetch analytics hub data:', error)
  } finally {
    loading.value = false
  }
}

const quickActions = [
  {
    title: 'New Analysis',
    description: 'Build a custom query and visualize your data',
    icon: 'M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605',
    route: { name: 'AnalysisCreate' },
    color: 'emerald',
  },
  {
    title: 'New Dashboard',
    description: 'Create a dashboard with multiple analyses',
    icon: 'M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z',
    route: { name: 'DashboardCreate' },
    color: 'violet',
  },
  {
    title: 'Saved Analyses',
    description: 'View and manage your saved analyses',
    icon: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
    route: { name: 'SavedAnalyses' },
    countKey: 'analyses',
    color: 'blue',
  },
  {
    title: 'Saved Dashboards',
    description: 'View and manage your dashboards',
    icon: 'M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5',
    route: { name: 'DashboardList' },
    countKey: 'dashboards',
    color: 'amber',
  },
]

const colorMap = {
  emerald: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400',
  violet: 'bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400',
  blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400',
  amber: 'bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400',
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Analytics Hub" subtitle="Build analyses and dashboards from your data" />

    <LoadingSpinner v-if="loading" size="lg" text="Loading analytics..." />

    <template v-else>
      <!-- Quick Actions -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <router-link
          v-for="action in quickActions"
          :key="action.title"
          :to="action.route"
          class="group flex flex-col p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm hover:-translate-y-1 hover:shadow-lg transition-all duration-200"
        >
          <div :class="['w-10 h-10 rounded-lg flex items-center justify-center mb-3', colorMap[action.color]]">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" :d="action.icon" />
            </svg>
          </div>
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white mb-0.5">{{ action.title }}</h3>
          <p class="text-xs text-gray-500 dark:text-gray-400 mb-3">{{ action.description }}</p>
          <div v-if="action.countKey" class="mt-auto">
            <span class="text-xs font-medium text-gray-400 dark:text-gray-500">
              {{ action.countKey === 'analyses' ? analysesCount : dashboardsCount }} items
            </span>
          </div>
          <div v-else class="mt-auto flex items-center gap-1 text-xs font-medium text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors">
            Get started
            <svg class="w-3 h-3 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </div>
        </router-link>
      </div>

      <!-- Recent Analyses -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Recent Analyses</h3>
          <router-link :to="{ name: 'SavedAnalyses' }" class="text-xs font-medium text-emerald-600 dark:text-emerald-400 hover:underline">
            View All
          </router-link>
        </div>
        <EmptyState v-if="recentAnalyses.length === 0" title="No analyses yet" message="Create your first analysis to see it here." :action-text="'New Analysis'" :action-route="{ name: 'AnalysisCreate' }" />
        <div v-else class="space-y-2 max-h-64 overflow-y-auto">
          <router-link
            v-for="analysis in recentAnalyses"
            :key="analysis.id"
            :to="{ name: 'AnalysisView', params: { id: analysis.id } }"
            class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
                <svg class="w-4 h-4 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ analysis.name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ analysis.data_source }} &middot; {{ analysis.chart_type }}</p>
              </div>
            </div>
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ formatDate(analysis.created_at, 'short') }}</span>
          </router-link>
        </div>
      </div>

      <!-- Recent Dashboards -->
      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-white">Recent Dashboards</h3>
          <router-link :to="{ name: 'DashboardList' }" class="text-xs font-medium text-violet-600 dark:text-violet-400 hover:underline">
            View All
          </router-link>
        </div>
        <EmptyState v-if="recentDashboards.length === 0" title="No dashboards yet" message="Create your first dashboard to see it here." :action-text="'New Dashboard'" :action-route="{ name: 'DashboardCreate' }" />
        <div v-else class="space-y-2 max-h-64 overflow-y-auto">
          <router-link
            v-for="dashboard in recentDashboards"
            :key="dashboard.id"
            :to="{ name: 'DashboardView', params: { id: dashboard.id } }"
            class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center">
                <svg class="w-4 h-4 text-violet-600 dark:text-violet-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ dashboard.name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ dashboard.description || 'No description' }}</p>
              </div>
            </div>
            <span class="text-xs text-gray-400 dark:text-gray-500">{{ formatDate(dashboard.created_at, 'short') }}</span>
          </router-link>
        </div>
      </div>
    </template>
  </div>
</template>
