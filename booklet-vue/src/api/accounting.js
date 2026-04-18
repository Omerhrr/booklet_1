import api from './axios'

// ── Chart of Accounts ──────────────────────────────────────
export function listAccounts() {
  return api.get('/accounting/accounts')
}

export function createAccount(data) {
  return api.post('/accounting/accounts', data)
}

export function getAccount(id) {
  return api.get(`/accounting/accounts/${id}`)
}

export function getAccountBalance(id) {
  return api.get(`/accounting/accounts/${id}/balance`)
}

export function getAccountLedger(id, params) {
  return api.get(`/accounting/accounts/${id}/ledger`, { params })
}

// ── Journal Entries ────────────────────────────────────────
export function listJournalEntries(params) {
  return api.get('/accounting/journal', { params })
}

export function createJournalEntry(data) {
  return api.post('/accounting/journal', data)
}

export function getJournalEntry(id) {
  return api.get(`/accounting/journal/${id}`)
}

export function postJournalEntry(id) {
  return api.post(`/accounting/journal/${id}/post`)
}

// ── Reports ────────────────────────────────────────────────
export function getGeneralLedger(params) {
  return api.get('/accounting/reports/general-ledger', { params })
}

export function getBalanceSheet(params) {
  return api.get('/accounting/reports/balance-sheet', { params })
}

export function getIncomeStatement(params) {
  return api.get('/accounting/reports/income-statement', { params })
}

export function getTrialBalance(params) {
  return api.get('/accounting/reports/trial-balance', { params })
}
