import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import * as settingsApi from '@/api/settings'
import * as saasApi from '@/api/saas'

export const useAuthStore = defineStore('auth', () => {
  // ── State ────────────────────────────────────────────────
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const isAuthenticated = ref(!!accessToken.value)
  const isSuperuser = ref(localStorage.getItem('is_superuser') === 'true')
  const businessId = ref(null)
  const planLimits = ref(null)
  const branches = ref([])
  const selectedBranchId = ref(localStorage.getItem('selected_branch_id') || null)
  const selectedBranchName = ref(localStorage.getItem('selected_branch_name') || '')
  const branchCurrency = ref(localStorage.getItem('branch_currency') || 'USD')
  const businessName = ref('')
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '[]'))

  if (localStorage.getItem('plan_limits') && localStorage.getItem('plan_limits') !== 'null') {
    try {
      planLimits.value = JSON.parse(localStorage.getItem('plan_limits'))
    } catch {}
  }

  const isInitialized = ref(false)

  // ── Getters ──────────────────────────────────────────────
  const hasPermission = computed(() => {
    return (perm) => {
      if (isSuperuser.value) return true
      if (!permissions.value || permissions.value.length === 0) return false
      return permissions.value.includes(perm)
    }
  })

  const hasAnyPermission = computed(() => {
    return (perms) => {
      if (isSuperuser.value) return true
      if (!permissions.value || permissions.value.length === 0) return false
      return perms.some((p) => permissions.value.includes(p))
    }
  })

  const hasPlanFeature = computed(() => {
    return (feature) => {
      if (!planLimits.value) return false
      const slug = planLimits.value.slug || planLimits.value.plan || 'basic'
      if (slug === 'enterprise') return true
      if (slug === 'advanced') return true
      if (slug === 'premium') {
        return ['ai', 'analytics', 'hr', 'budgets', 'fixed_assets', 'agents'].includes(feature)
      }
      return false
    }
  })

  const canCreateBranch = computed(() => {
    return () => {
      if (!planLimits.value) return false
      const limits = planLimits.value
      const maxBranches = limits.max_branches ?? Infinity
      const currentBranches = branches.value.length
      return currentBranches < maxBranches
    }
  })

  const canCreateUser = computed(() => {
    return () => {
      if (!planLimits.value) return false
      const limits = planLimits.value
      const maxUsers = limits.max_users ?? Infinity
      const currentUsers = limits.current_users ?? 0
      return currentUsers < maxUsers
    }
  })

  // ── Actions ──────────────────────────────────────────────
  async function login(credentials) {
    const { data } = await authApi.login(credentials)
    accessToken.value = data.access_token
    localStorage.setItem('access_token', data.access_token)

    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token)
    }

    isAuthenticated.value = true
    await fetchUser()
    return data
  }

  async function signup(signupData) {
    const { data } = await authApi.signup(signupData)
    accessToken.value = data.access_token
    localStorage.setItem('access_token', data.access_token)

    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token)
    }

    isAuthenticated.value = true
    await fetchUser()
    return data
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // Best-effort — we clear local state regardless
    } finally {
      user.value = null
      accessToken.value = ''
      isAuthenticated.value = false
      isSuperuser.value = false
      businessId.value = null
      planLimits.value = null
      branches.value = []
      selectedBranchId.value = null
      selectedBranchName.value = ''
      branchCurrency.value = 'USD'
      businessName.value = ''
      permissions.value = []

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('selected_branch_id')
      localStorage.removeItem('selected_branch_name')
      localStorage.removeItem('branch_currency')
      localStorage.removeItem('permissions')
      localStorage.removeItem('is_superuser')
      localStorage.removeItem('plan_limits')
    }
  }

  async function fetchUser() {
    try {
      const { data } = await authApi.getMe()
      user.value = data
      isSuperuser.value = data.is_superuser || false
      businessId.value = data.business_id || null
      businessName.value = data.business_name || ''
      localStorage.setItem('is_superuser', String(data.is_superuser || false))
      return data
    } catch (error) {
      console.error('Failed to fetch user:', error)
      throw error
    }
  }

  async function fetchPermissions() {
    try {
      const { data } = await authApi.getPermissions()
      permissions.value = data.permissions || []
      localStorage.setItem('permissions', JSON.stringify(data.permissions || []))
      return data
    } catch (error) {
      console.error('Failed to fetch permissions:', error)
      throw error
    }
  }

  async function fetchPlanLimits() {
    if (!businessId.value) return null
    try {
      const { data } = await saasApi.getPlanLimits(businessId.value)
      planLimits.value = data
      localStorage.setItem('plan_limits', JSON.stringify(data))
      return data
    } catch (error) {
      console.error('Failed to fetch plan limits:', error)
      throw error
    }
  }

  async function fetchBranches() {
    try {
      const { data } = await settingsApi.listBranches()
      branches.value = Array.isArray(data) ? data : data.items || data.branches || []

      // Auto-select default branch if none selected
      if (!selectedBranchId.value && branches.value.length > 0) {
        const defaultBranch = branches.value.find((b) => b.is_default) || branches.value[0]
        setBranch(defaultBranch.id)
      }

      return branches.value
    } catch (error) {
      console.error('Failed to fetch branches:', error)
      throw error
    }
  }

  async function setBranch(id) {
    const branch = branches.value.find((b) => String(b.id) === String(id))
    if (branch) {
      selectedBranchId.value = String(branch.id)
      selectedBranchName.value = branch.name || ''
      branchCurrency.value = branch.currency || 'USD'

      localStorage.setItem('selected_branch_id', selectedBranchId.value)
      localStorage.setItem('selected_branch_name', selectedBranchName.value)
      localStorage.setItem('branch_currency', branchCurrency.value)
    }
  }

  async function refreshPermissions() {
    try {
      await fetchPermissions()
      await fetchPlanLimits()
    } catch (error) {
      console.error('Failed to refresh permissions:', error)
    }
  }

  async function initialize() {
    if (!accessToken.value) {
      isInitialized.value = true
      return
    }

    try {
      await fetchUser()
      await Promise.allSettled([
        fetchPermissions(),
        fetchPlanLimits(),
        fetchBranches(),
      ])
    } catch (error) {
      if (error?.response?.status === 401) {
        await logout()
      }
    } finally {
      isInitialized.value = true
    }
  }

  return {
    // State
    user,
    accessToken,
    isAuthenticated,
    isSuperuser,
    businessId,
    planLimits,
    branches,
    selectedBranchId,
    selectedBranchName,
    branchCurrency,
    businessName,
    permissions,
    // Getters
    hasPermission,
    hasAnyPermission,
    hasPlanFeature,
    canCreateBranch,
    canCreateUser,
    // Actions
    login,
    signup,
    logout,
    fetchUser,
    fetchPermissions,
    fetchPlanLimits,
    fetchBranches,
    setBranch,
    refreshPermissions,
    initialize,
    isInitialized,
  }
})
