import api from './axios'

export function listCashbookEntries(params) {
  return api.get('/cashbook', { params })
}

export function createCashbookEntry(data) {
  return api.post('/cashbook', data)
}

export function deleteCashbookEntry(id) {
  return api.delete(`/cashbook/${id}`)
}

export function getCashbookSummary() {
  return api.get('/cashbook/summary')
}

export function getCashFlow(params) {
  return api.get('/cashbook/cash-flow', { params })
}

export function getAccountTransactions(id, params) {
  return api.get(`/cashbook/accounts/${id}/transactions`, { params })
}

export function getCashbookEntry(id) {
  return api.get(`/cashbook/${id}`)
}

export function fundAccount(data) {
  return api.post('/cashbook/fund', data)
}

export function reconcileCashbook(id, data) {
  return api.post(`/cashbook/${id}/reconcile`, data)
}

export function exportCashbookPdf(params) {
  return api.get('/cashbook/export/pdf', { params, responseType: 'blob' })
}

export function exportCashbookExcel(params) {
  return api.get('/cashbook/export/excel', { params, responseType: 'blob' })
}
