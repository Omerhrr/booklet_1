import api from './axios'

// ── Bills ──────────────────────────────────────────────────
export function listBills(params) {
  return api.get('/purchases/bills', { params })
}

export function createBill(data) {
  return api.post('/purchases/bills', data)
}

export function getBill(id) {
  return api.get(`/purchases/bills/${id}`)
}

export function recordPayment(id, data) {
  return api.post(`/purchases/bills/${id}/record-payment`, data)
}

// ── Debit Notes ────────────────────────────────────────────
export function listDebitNotes() {
  return api.get('/purchases/debit-notes')
}

export function getDebitNote(id) {
  return api.get(`/purchases/debit-notes/${id}`)
}

export function createDebitNote(data) {
  return api.post('/purchases/debit-notes', data)
}

export function applyDebitNote(id) {
  return api.post(`/purchases/debit-notes/${id}/apply`)
}
