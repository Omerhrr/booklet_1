import api from './axios'

// ── Invoices ───────────────────────────────────────────────
export function listInvoices(params) {
  return api.get('/sales/invoices', { params })
}

export function createInvoice(data) {
  return api.post('/sales/invoices', data)
}

export function getInvoice(id) {
  return api.get(`/sales/invoices/${id}`)
}

export function recordPayment(id, data) {
  return api.post(`/sales/invoices/${id}/record-payment`, data)
}

export function deleteInvoice(id) {
  return api.delete(`/sales/invoices/${id}`)
}

export function writeOff(id) {
  return api.post(`/sales/invoices/${id}/write-off`)
}

// ── Credit Notes ───────────────────────────────────────────
export function listCreditNotes() {
  return api.get('/sales/credit-notes')
}

export function getCreditNote(id) {
  return api.get(`/sales/credit-notes/${id}`)
}

export function createCreditNote(data) {
  return api.post('/sales/credit-notes', data)
}

export function applyCreditNote(id) {
  return api.post(`/sales/credit-notes/${id}/apply`)
}
