<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { getSubscription, getPlans, getUsage } from '@/api/saas'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

// ── Loading State ───────────────────────────────────────────
const loading = ref(true)
const planActionLoading = ref(false)

// ── Data ────────────────────────────────────────────────────
const subscription = ref(null)
const plans = ref([])
const usage = ref(null)
const planLimits = computed(() => authStore.planLimits)

// ── Cancel Subscription Dialog ──────────────────────────────
const showCancelDialog = ref(false)
const cancelLoading = ref(false)

// ── Derived ─────────────────────────────────────────────────
const currentPlan = computed(() => subscription.value?.plan || null)
const currentPlanId = computed(() => currentPlan.value?.id || null)

const usageStats = computed(() => {
  const u = usage.value
  const limits = planLimits.value
  return {
    branches: {
      used: u?.branches?.used || limits?.current_branches || authStore.branches.length || 0,
      limit: u?.branches?.limit || limits?.max_branches || 1,
    },
    users: {
      used: u?.users?.used || limits?.current_users || 0,
      limit: u?.users?.limit || limits?.max_users || 1,
    },
  }
})

const branchPercent = computed(() => {
  const u = usageStats.value.branches
  return u.limit > 0 ? Math.min((u.used / u.limit) * 100, 100) : 0
})

const userPercent = computed(() => {
  const u = usageStats.value.users
  return u.limit > 0 ? Math.min((u.used / u.limit) * 100, 100) : 0
})

function getPlanAction(plan) {
  if (!currentPlan.value) return 'Select'
  if (plan.id === currentPlanId.value) return 'Current'
  if ((plan.monthly_price || 0) > (currentPlan.value.monthly_price || 0)) return 'Upgrade'
  if ((plan.monthly_price || 0) < (currentPlan.value.monthly_price || 0)) return 'Downgrade'
  return 'Switch'
}

// ── Actions ─────────────────────────────────────────────────
async function fetchData() {
  loading.value = true
  try {
    const [subRes, plansRes, usageRes] = await Promise.allSettled([
      getSubscription(),
      getPlans(),
      getUsage(),
    ])

    if (subRes.status === 'fulfilled') subscription.value = subRes.value.data
    if (plansRes.status === 'fulfilled') plans.value = plansRes.value.data?.plans || plansRes.value.data || []
    if (usageRes.status === 'fulfilled') usage.value = usageRes.value.data
  } catch (err) {
    console.error('Failed to load subscription data:', err)
  } finally {
    loading.value = false
  }
}

async function handlePlanAction(plan) {
  const action = getPlanAction(plan)
  if (action === 'Current') return

  const confirmMsg = action === 'Upgrade'
    ? `Upgrade to the ${plan.name} plan for $${plan.monthly_price}/mo?`
    : action === 'Downgrade'
    ? `Downgrade to the ${plan.name} plan? You may lose access to some features.`
    : `Switch to the ${plan.name} plan for $${plan.monthly_price}/mo?`

  if (!confirm(confirmMsg)) return

  planActionLoading.value = true
  try {
    // Redirect to checkout / API call
    window.location.href = `/api/v1/saas/checkout?plan=${plan.slug}`
  } catch (err) {
    toastStore.show('Failed to process plan change. Please try again.', 'error')
  } finally {
    planActionLoading.value = false
  }
}

async function handleCancelSubscription() {
  cancelLoading.value = true
  try {
    toastStore.show('Subscription cancellation requested. Please contact support to complete the process.', 'warning')
  } catch (err) {
    toastStore.show('Failed to cancel subscription.', 'error')
  } finally {
    cancelLoading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader
      title="Subscription"
      subtitle="Manage your plan and billing"
    />

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading subscription details..." />
    </div>

    <div v-else class="space-y-6">
      <!-- ═══ Current Plan ═══ -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Current Plan</h2>

        <div v-if="subscription && currentPlan" class="p-5 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ currentPlan.name }}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Status:
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ml-1',
                    subscription.status === 'active'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-400',
                  ]"
                >
                  {{ subscription.status?.charAt(0).toUpperCase() + subscription.status?.slice(1) || 'Unknown' }}
                </span>
              </p>
              <p v-if="subscription.current_period_end" class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Renews: {{ subscription.current_period_end }}
              </p>
            </div>
            <div class="text-left sm:text-right">
              <p class="text-3xl font-bold text-gray-900 dark:text-white">
                ${{ currentPlan.monthly_price || '0' }}
                <span class="text-sm font-normal text-gray-500 dark:text-gray-400">/mo</span>
              </p>
            </div>
          </div>

          <!-- Features list -->
          <div v-if="currentPlan.features && currentPlan.features.length" class="mt-4 pt-4 border-t border-blue-200/50 dark:border-blue-800/50">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Included Features</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="feature in currentPlan.features"
                :key="feature"
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/70 dark:bg-gray-800 text-xs font-medium text-gray-700 dark:text-gray-300"
              >
                <svg class="w-3.5 h-3.5 text-green-500" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                {{ feature }}
              </span>
            </div>
          </div>
        </div>

        <!-- No Subscription -->
        <div v-else class="p-5 bg-gray-50 dark:bg-gray-700 rounded-xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
              <svg class="w-5 h-5 text-gray-500 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
            </div>
            <div>
              <p class="font-medium text-gray-700 dark:text-gray-300">No active subscription</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">Choose a plan below to get started.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ Usage Stats ═══ -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Usage</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Branches -->
          <div class="p-4 border border-gray-200 dark:border-gray-700 rounded-xl">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Branches</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ usageStats.branches.used }}/{{ usageStats.branches.limit }}
              </span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="branchPercent >= 100 ? 'bg-red-500' : branchPercent >= 80 ? 'bg-amber-500' : 'bg-blue-500'"
                :style="{ width: `${branchPercent}%` }"
              />
            </div>
            <p
              v-if="usageStats.branches.used >= usageStats.branches.limit"
              class="text-xs text-amber-600 dark:text-amber-400 mt-2 flex items-center gap-1"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              Limit reached — upgrade to add more
            </p>
          </div>

          <!-- Users -->
          <div class="p-4 border border-gray-200 dark:border-gray-700 rounded-xl">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Users</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ usageStats.users.used }}/{{ usageStats.users.limit }}
              </span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="userPercent >= 100 ? 'bg-red-500' : userPercent >= 80 ? 'bg-amber-500' : 'bg-blue-500'"
                :style="{ width: `${userPercent}%` }"
              />
            </div>
            <p
              v-if="usageStats.users.used >= usageStats.users.limit"
              class="text-xs text-amber-600 dark:text-amber-400 mt-2 flex items-center gap-1"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              Limit reached — upgrade to add more
            </p>
          </div>
        </div>
      </div>

      <!-- ═══ Available Plans ═══ -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6">Available Plans</h2>

        <div v-if="plans.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div
            v-for="plan in plans"
            :key="plan.id"
            :class="[
              'relative rounded-2xl p-6 transition-all duration-200',
              plan.id === currentPlanId
                ? 'border-2 border-blue-500 ring-2 ring-blue-500/20 shadow-lg shadow-blue-500/10'
                : 'border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-md',
            ]"
          >
            <!-- Popular Badge -->
            <div v-if="plan.slug === 'premium'" class="absolute -top-3 left-1/2 transform -translate-x-1/2">
              <span class="bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-semibold px-3 py-1 rounded-full shadow-sm">
                Most Popular
              </span>
            </div>

            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ plan.name }}</h3>
            <p class="text-3xl font-bold text-gray-900 dark:text-white mt-2">
              ${{ plan.monthly_price || 0 }}
              <span class="text-sm font-normal text-gray-500 dark:text-gray-400">/mo</span>
            </p>

            <!-- Features -->
            <ul class="mt-4 space-y-2.5">
              <li class="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <svg class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                {{ plan.max_branches || 1 }} branch{{ (plan.max_branches || 1) !== 1 ? 'es' : '' }}
              </li>
              <li class="flex items-center text-sm text-gray-600 dark:text-gray-400">
                <svg class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                {{ plan.max_users || 1 }} user{{ (plan.max_users || 1) !== 1 ? 's' : '' }}
              </li>
              <li
                v-for="feature in (plan.description || []).slice(0, 4)"
                :key="feature"
                class="flex items-center text-sm text-gray-600 dark:text-gray-400"
              >
                <svg class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                {{ feature }}
              </li>
            </ul>

            <!-- Action Button -->
            <button
              v-if="plan.id === currentPlanId"
              disabled
              class="mt-6 w-full py-2.5 px-4 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 font-medium rounded-xl cursor-not-allowed"
            >
              Current Plan
            </button>
            <button
              v-else
              :disabled="planActionLoading"
              @click="handlePlanAction(plan)"
              :class="[
                'mt-6 w-full py-2.5 px-4 text-white font-medium rounded-xl transition-all duration-200 shadow-sm hover:shadow-md',
                plan.slug === 'premium'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700'
                  : 'bg-blue-600 hover:bg-blue-700',
                'disabled:opacity-60 disabled:cursor-not-allowed',
              ]"
            >
              <span v-if="planActionLoading" class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Processing...
              </span>
              <span v-else>{{ getPlanAction(plan) }}</span>
            </button>
          </div>
        </div>

        <!-- No Plans -->
        <div v-else class="text-center py-12 text-gray-400 dark:text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
          </svg>
          <p class="text-sm">No plans available at this time.</p>
        </div>

        <!-- Enterprise CTA -->
        <div class="mt-6 p-6 bg-gradient-to-r from-gray-900 to-gray-800 dark:from-gray-800 dark:to-gray-700 rounded-2xl">
          <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 class="text-lg font-semibold text-white">Need more?</h3>
              <p class="text-gray-300 mt-1">Enterprise plan with unlimited branches, users, and custom integrations.</p>
            </div>
            <a
              href="mailto:support@booklet.com"
              class="px-6 py-2.5 bg-white text-gray-900 font-medium rounded-xl hover:bg-gray-100 transition-colors flex-shrink-0 text-sm"
            >
              Contact Sales
            </a>
          </div>
        </div>
      </div>

      <!-- ═══ Billing History ═══ -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Billing History</h2>

        <div v-if="subscription && subscription.invoices && subscription.invoices.length > 0" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-b border-gray-100 dark:border-gray-700">
                <th class="pb-3 pr-4">Date</th>
                <th class="pb-3 pr-4">Description</th>
                <th class="pb-3 pr-4">Amount</th>
                <th class="pb-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
              <tr
                v-for="invoice in subscription.invoices"
                :key="invoice.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
              >
                <td class="py-3 pr-4 text-gray-600 dark:text-gray-400">
                  {{ invoice.date || '—' }}
                </td>
                <td class="py-3 pr-4 text-gray-900 dark:text-white font-medium">
                  {{ invoice.description || 'Subscription' }}
                </td>
                <td class="py-3 pr-4 text-gray-900 dark:text-white font-medium">
                  ${{ invoice.amount || '0.00' }}
                </td>
                <td class="py-3 text-right">
                  <span
                    :class="[
                      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                      invoice.status === 'paid' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400' :
                      invoice.status === 'pending' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-400' :
                      'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
                    ]"
                  >
                    {{ invoice.status || 'Pending' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="text-center py-10 text-gray-400 dark:text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-2 text-gray-300 dark:text-gray-600" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <p class="text-sm">No billing history yet</p>
        </div>
      </div>

      <!-- ═══ Cancel Subscription ═══ -->
      <div
        v-if="subscription && subscription.status === 'active'"
        class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-red-200 dark:border-red-900/50 p-6"
      >
        <h2 class="text-xl font-semibold text-red-600 dark:text-red-400 mb-2">Cancel Subscription</h2>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          If you cancel your subscription, you will lose access to all features at the end of your current billing period. This action cannot be undone.
        </p>
        <button
          @click="showCancelDialog = true"
          class="px-4 py-2.5 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-xl hover:bg-red-100 dark:text-red-400 dark:bg-red-900/20 dark:border-red-800 dark:hover:bg-red-900/30 transition-colors"
        >
          Cancel Subscription
        </button>
      </div>
    </div>

    <!-- Cancel Confirmation Dialog -->
    <ConfirmDialog
      v-model:show="showCancelDialog"
      title="Cancel Subscription"
      message="Are you sure you want to cancel your subscription? You will retain access until the end of your current billing period. This action cannot be undone."
      confirm-text="Yes, Cancel"
      cancel-text="Keep Subscription"
      type="danger"
      @confirm="handleCancelSubscription"
    />
  </div>
</template>
