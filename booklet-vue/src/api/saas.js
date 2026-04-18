import api from './axios'

export function getPlanLimits(businessId) {
  return api.get(`/saas/plan-limits/${businessId}`)
}

export function getSubscription() {
  return api.get('/saas/subscription')
}

export function getPlans() {
  return api.get('/saas/plans')
}

export function getUsage() {
  return api.get('/saas/usage')
}
