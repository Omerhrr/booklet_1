import api from './axios'

export function listExpenses(params) {
  return api.get('/expenses', { params })
}

export function createExpense(data) {
  return api.post('/expenses', data)
}

export function getExpense(id) {
  return api.get(`/expenses/${id}`)
}

export function updateExpense(id, data) {
  return api.put(`/expenses/${id}`, data)
}

export function deleteExpense(id) {
  return api.delete(`/expenses/${id}`)
}

export function getExpenseCategories() {
  return api.get('/expenses/categories')
}

export function getNextExpenseNumber() {
  return api.get('/expenses/next-number')
}

export function getExpenseSummary(params) {
  return api.get('/expenses/summary', { params })
}
