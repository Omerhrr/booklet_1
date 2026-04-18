import api from './axios'

// ── Employees ──────────────────────────────────────────────
export function listEmployees() {
  return api.get('/hr/employees')
}

export function createEmployee(data) {
  return api.post('/hr/employees', data)
}

export function getEmployee(id) {
  return api.get(`/hr/employees/${id}`)
}

export function updateEmployee(id, data) {
  return api.put(`/hr/employees/${id}`, data)
}

export function updatePayrollConfig(id, data) {
  return api.put(`/hr/employees/${id}/payroll-config`, data)
}

export function terminateEmployee(id) {
  return api.post(`/hr/employees/${id}/terminate`)
}

// ── Payroll ────────────────────────────────────────────────
export function runPayroll(data) {
  return api.post('/hr/payroll/run', data)
}

// ── Payslips ───────────────────────────────────────────────
export function listPayslips(params) {
  return api.get('/hr/payslips', { params })
}

export function getPayslip(id) {
  return api.get(`/hr/payslips/${id}`)
}

export function markPayslipPaid(id) {
  return api.post(`/hr/payslips/${id}/mark-paid`)
}

export function exportPayslipsExcel(params) {
  return api.get('/hr/payslips/export/excel', { params, responseType: 'blob' })
}
