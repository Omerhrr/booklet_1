import api from './axios'

export function listFixedAssets(params) {
  return api.get('/fixed-assets', { params })
}

export function createFixedAsset(data) {
  return api.post('/fixed-assets', data)
}

export function getFixedAsset(id) {
  return api.get(`/fixed-assets/${id}`)
}

export function updateFixedAsset(id, data) {
  return api.put(`/fixed-assets/${id}`, data)
}

export function deleteFixedAsset(id) {
  return api.delete(`/fixed-assets/${id}`)
}

export function getFixedAssetSummary() {
  return api.get('/fixed-assets/summary')
}

export function getFixedAssetCategories() {
  return api.get('/fixed-assets/categories')
}

export function depreciateAsset(id, data) {
  return api.post(`/fixed-assets/${id}/depreciate`, data)
}

export function disposeAsset(id, data) {
  return api.post(`/fixed-assets/${id}/dispose`, data)
}

export function writeOffAsset(id) {
  return api.post(`/fixed-assets/${id}/write-off`)
}

export function bulkDepreciation(data) {
  return api.post('/fixed-assets/bulk-depreciation', data)
}
