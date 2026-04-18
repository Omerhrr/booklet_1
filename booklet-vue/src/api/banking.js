import api from './axios'

// ── Bank Accounts ──────────────────────────────────────────
export function listBankAccounts() {
  return api.get('/banking/accounts')
}

export function createBankAccount(data) {
  return api.post('/banking/accounts', data)
}

export function getBankAccount(id) {
  return api.get(`/banking/accounts/${id}`)
}

export function updateBankAccount(id, data) {
  return api.put(`/banking/accounts/${id}`, data)
}

export function deleteBankAccount(id) {
  return api.delete(`/banking/accounts/${id}`)
}

// ── Transfers ──────────────────────────────────────────────
export function listTransfers() {
  return api.get('/banking/transfers')
}

export function createTransfer(data) {
  return api.post('/banking/transfers', data)
}

// ── Reconciliation ─────────────────────────────────────────
export function getReconciliationAccounts() {
  return api.get('/banking/reconciliation/accounts')
}

export function getReconciliationAccountStatus(id) {
  return api.get(`/banking/reconciliation/accounts/${id}/status`)
}

export function getStatementLines(id) {
  return api.get(`/banking/reconciliation/accounts/${id}/statement-lines`)
}

export function getUnclearedTransactions(id) {
  return api.get(`/banking/reconciliation/accounts/${id}/uncleared`)
}

export function completeReconciliation(data) {
  return api.post('/banking/reconciliation/complete', data)
}

export function matchTransaction(data) {
  return api.post('/banking/reconciliation/match', data)
}

export function autoMatch(id) {
  return api.post(`/banking/reconciliation/accounts/${id}/auto-match`)
}

export function clearStatementLine(id) {
  return api.post(`/banking/reconciliation/statement-lines/${id}/clear`)
}

export function clearCashbookEntry(id) {
  return api.post(`/banking/reconciliation/cashbook-entries/${id}/clear`)
}

export function getReconciliationHistory() {
  return api.get('/banking/reconciliation/history')
}

// ── Payment Accounts ───────────────────────────────────────
export function getPaymentAccounts() {
  return api.get('/banking/payment-accounts')
}

// ── Exports ────────────────────────────────────────────────
export function exportStatementPdf(id) {
  return api.get(`/banking/accounts/${id}/export/pdf`, { responseType: 'blob' })
}

export function exportStatementExcel(id) {
  return api.get(`/banking/accounts/${id}/export/excel`, { responseType: 'blob' })
}

export function importStatement(accountId, formData) {
  return api.post(`/reconciliation/accounts/${accountId}/import-statement`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
