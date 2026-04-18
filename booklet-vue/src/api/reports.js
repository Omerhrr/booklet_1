import api from './axios'

// ── Report Endpoints ───────────────────────────────────────
export function getSalesReport(params) {
  return api.get('/reports/sales', { params })
}

export function getPurchasesReport(params) {
  return api.get('/reports/purchases', { params })
}

export function getExpensesReport(params) {
  return api.get('/reports/expenses', { params })
}

export function getInventoryReport(params) {
  return api.get('/reports/inventory', { params })
}

export function getAgingReport(params) {
  return api.get('/reports/aging', { params })
}

export function getTrialBalanceReport(params) {
  return api.get('/reports/trial-balance', { params })
}

export function getVatReport(params) {
  return api.get('/reports/vat', { params })
}

// ── PDF Exports ────────────────────────────────────────────
export function getSalesPdf(params) {
  return api.get('/reports/sales/pdf', { params, responseType: 'blob' })
}

export function getPurchasesPdf(params) {
  return api.get('/reports/purchases/pdf', { params, responseType: 'blob' })
}

export function getExpensesPdf(params) {
  return api.get('/reports/expenses/pdf', { params, responseType: 'blob' })
}

export function getInventoryPdf(params) {
  return api.get('/reports/inventory/pdf', { params, responseType: 'blob' })
}

export function getAgingPdf(params) {
  return api.get('/reports/aging/pdf', { params, responseType: 'blob' })
}

export function getTrialBalancePdf(params) {
  return api.get('/reports/trial-balance/pdf', { params, responseType: 'blob' })
}

export function getVatPdf(params) {
  return api.get('/reports/vat/pdf', { params, responseType: 'blob' })
}

// ── Excel Exports ──────────────────────────────────────────
export function getSalesExcel(params) {
  return api.get('/reports/sales/excel', { params, responseType: 'blob' })
}

export function getPurchasesExcel(params) {
  return api.get('/reports/purchases/excel', { params, responseType: 'blob' })
}

export function getExpensesExcel(params) {
  return api.get('/reports/expenses/excel', { params, responseType: 'blob' })
}

export function getInventoryExcel(params) {
  return api.get('/reports/inventory/excel', { params, responseType: 'blob' })
}

export function getAgingExcel(params) {
  return api.get('/reports/aging/excel', { params, responseType: 'blob' })
}

export function getTrialBalanceExcel(params) {
  return api.get('/reports/trial-balance/excel', { params, responseType: 'blob' })
}

export function getVatExcel(params) {
  return api.get('/reports/vat/excel', { params, responseType: 'blob' })
}
