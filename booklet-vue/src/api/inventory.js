import api from './axios'

// ── Products ───────────────────────────────────────────────
export function listProducts(params) {
  return api.get('/inventory/products', { params })
}

export function createProduct(data) {
  return api.post('/inventory/products', data)
}

export function getProduct(id) {
  return api.get(`/inventory/products/${id}`)
}

export function updateProduct(id, data) {
  return api.put(`/inventory/products/${id}`, data)
}

export function deleteProduct(id) {
  return api.delete(`/inventory/products/${id}`)
}

export function toggleProductStatus(id) {
  return api.patch(`/inventory/products/${id}/toggle-status`)
}

export function lowStock() {
  return api.get('/inventory/products/low-stock')
}

export function adjustStock(id, data) {
  return api.post(`/inventory/products/${id}/adjust-stock`, data)
}

// ── Categories ─────────────────────────────────────────────
export function listCategories() {
  return api.get('/inventory/categories')
}

export function createCategory(data) {
  return api.post('/inventory/categories', data)
}

export function getCategory(id) {
  return api.get(`/inventory/categories/${id}`)
}

export function updateCategory(id, data) {
  return api.put(`/inventory/categories/${id}`, data)
}

export function deleteCategory(id) {
  return api.delete(`/inventory/categories/${id}`)
}

// ── Stock Adjustments ──────────────────────────────────────
export function listStockAdjustments() {
  return api.get('/inventory/stock-adjustments')
}
