import api from './axios'

export function getFull() {
  return api.get('/dashboard/full')
}

export function getStats() {
  return api.get('/dashboard/stats')
}

export function getSalesChart(days = 30) {
  return api.get('/dashboard/sales-chart', { params: { days } })
}

export function getExpenseChart(days = 30) {
  return api.get('/dashboard/expense-chart', { params: { days } })
}

export function getAging() {
  return api.get('/dashboard/aging')
}
