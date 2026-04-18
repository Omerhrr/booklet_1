import api from './axios'

// ── Data Sources ───────────────────────────────────────────
export function getSources() {
  return api.get('/analytics/sources')
}

export function getSourceFields(id) {
  return api.get(`/analytics/sources/${id}/fields`)
}

// ── Query ──────────────────────────────────────────────────
export function queryAnalytics(data) {
  return api.post('/analytics/query', data)
}

// ── Analyses ───────────────────────────────────────────────
export function getAnalyses(params) {
  return api.get('/analytics/analyses', { params })
}

export function createAnalysis(data) {
  return api.post('/analytics/analyses', data)
}

export function getAnalysis(id) {
  return api.get(`/analytics/analyses/${id}`)
}

export function updateAnalysis(id, data) {
  return api.put(`/analytics/analyses/${id}`, data)
}

export function deleteAnalysis(id) {
  return api.delete(`/analytics/analyses/${id}`)
}

export function toggleAnalysisFavorite(id) {
  return api.post(`/analytics/analyses/${id}/toggle-favorite`)
}

// ── Dashboards ─────────────────────────────────────────────
export function getDashboards(params) {
  return api.get('/analytics/dashboards', { params })
}

export function createDashboard(data) {
  return api.post('/analytics/dashboards', data)
}

export function getDashboard(id) {
  return api.get(`/analytics/dashboards/${id}`)
}

export function updateDashboard(id, data) {
  return api.put(`/analytics/dashboards/${id}`, data)
}

export function deleteDashboard(id) {
  return api.delete(`/analytics/dashboards/${id}`)
}

// ── Filters ────────────────────────────────────────────────
export function saveFilter(data) {
  return api.post('/analytics/filters', data)
}
