import { createRouter, createWebHistory } from 'vue-router'

// Import all route modules
import authRoutes from './auth.js'
import dashboardRoutes from './dashboard.js'
import crmRoutes from './crm.js'
import inventoryRoutes from './inventory.js'
import salesRoutes from './sales.js'
import purchasesRoutes from './purchases.js'
import expensesRoutes from './expenses.js'
import otherIncomesRoutes from './otherIncomes.js'
import budgetsRoutes from './budgets.js'
import fixedAssetsRoutes from './fixedAssets.js'
import cashbookRoutes from './cashbook.js'
import accountingRoutes from './accounting.js'
import hrRoutes from './hr.js'
import bankingRoutes from './banking.js'
import reportsRoutes from './reports.js'
import analyticsRoutes from './analytics.js'
import aiRoutes from './ai.js'
import agentsRoutes from './agents.js'
import settingsRoutes from './settings.js'
import auditRoutes from './audit.js'

const routes = [
  { path: '/', redirect: '/dashboard' },
  authRoutes,
  dashboardRoutes,
  crmRoutes,
  inventoryRoutes,
  salesRoutes,
  purchasesRoutes,
  expensesRoutes,
  otherIncomesRoutes,
  budgetsRoutes,
  fixedAssetsRoutes,
  cashbookRoutes,
  accountingRoutes,
  hrRoutes,
  bankingRoutes,
  reportsRoutes,
  analyticsRoutes,
  aiRoutes,
  agentsRoutes,
  settingsRoutes,
  auditRoutes,
  { path: '/forbidden', name: 'Forbidden', component: () => import('../views/shared/Forbidden.vue'), meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/shared/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  }
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const isAuthenticated = !!token

  if (to.meta.requiresAuth && !isAuthenticated) {
    return next({ path: '/auth/login', query: { redirect: to.fullPath } })
  }

  if (to.meta.guestOnly && isAuthenticated) {
    return next('/dashboard')
  }

  if (!isAuthenticated) {
    return next()
  }

  // Permission check
  if (to.meta.permission) {
    const permissions = JSON.parse(localStorage.getItem('permissions') || '[]')
    const isSuperuser = localStorage.getItem('is_superuser') === 'true'
    if (!isSuperuser && !permissions.includes(to.meta.permission)) {
      return next('/forbidden')
    }
  }

  // Plan feature check
  if (to.meta.planFeature) {
    const planLimits = JSON.parse(localStorage.getItem('plan_limits') || '{}')
    const slug = planLimits.slug || planLimits.plan || 'basic'
    const premiumFeatures = ['ai', 'analytics', 'hr', 'budgets', 'fixed_assets', 'agents']
    if (slug === 'enterprise' || slug === 'advanced') {
      // All features available
    } else if (slug === 'premium') {
      if (!premiumFeatures.includes(to.meta.planFeature)) return next('/forbidden')
    } else {
      return next('/forbidden')
    }
  }

  next()
})

export default router
