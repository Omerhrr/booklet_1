import api from './axios'

export function listBudgets(params) {
  return api.get('/budgets', { params })
}

export function createBudget(data) {
  return api.post('/budgets', data)
}

export function getBudget(id) {
  return api.get(`/budgets/${id}`)
}

export function updateBudget(id, data) {
  return api.put(`/budgets/${id}`, data)
}

export function deleteBudget(id) {
  return api.delete(`/budgets/${id}`)
}

export function getFiscalYears() {
  return api.get('/budgets/fiscal-years')
}

export function getAvailableAccounts() {
  return api.get('/budgets/available-accounts')
}

export function getBudgetVsActual(id) {
  return api.get(`/budgets/${id}/vs-actual`)
}

export function getBudgetMonthly(id) {
  return api.get(`/budgets/${id}/monthly`)
}
