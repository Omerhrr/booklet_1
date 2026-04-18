import api from './axios'

export function listOtherIncomes(params) {
  return api.get('/other-incomes', { params })
}

export function createOtherIncome(data) {
  return api.post('/other-incomes', data)
}

export function getOtherIncome(id) {
  return api.get(`/other-incomes/${id}`)
}

export function updateOtherIncome(id, data) {
  return api.put(`/other-incomes/${id}`, data)
}

export function deleteOtherIncome(id) {
  return api.delete(`/other-incomes/${id}`)
}

export function getOtherIncomeCategories() {
  return api.get('/other-incomes/categories')
}

export function getNextOtherIncomeNumber() {
  return api.get('/other-incomes/next-number')
}
