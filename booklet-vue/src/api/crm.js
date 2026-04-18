import api from './axios'

// ── Customers ──────────────────────────────────────────────
export function listCustomers(params) {
  return api.get('/crm/customers', { params })
}

export function createCustomer(data) {
  return api.post('/crm/customers', data)
}

export function getCustomer(id) {
  return api.get(`/crm/customers/${id}`)
}

export function updateCustomer(id, data) {
  return api.put(`/crm/customers/${id}`, data)
}

export function deleteCustomer(id) {
  return api.delete(`/crm/customers/${id}`)
}

export function toggleCustomerStatus(id) {
  return api.patch(`/crm/customers/${id}/toggle-status`)
}

// ── Vendors ────────────────────────────────────────────────
export function listVendors(params) {
  return api.get('/crm/vendors', { params })
}

export function createVendor(data) {
  return api.post('/crm/vendors', data)
}

export function getVendor(id) {
  return api.get(`/crm/vendors/${id}`)
}

export function updateVendor(id, data) {
  return api.put(`/crm/vendors/${id}`, data)
}

export function deleteVendor(id) {
  return api.delete(`/crm/vendors/${id}`)
}

export function toggleVendorStatus(id) {
  return api.patch(`/crm/vendors/${id}/toggle-status`)
}
