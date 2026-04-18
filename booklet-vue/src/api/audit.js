import api from './axios'

export function listAuditLogs(params) {
  return api.get('/audit', { params })
}

export function getAuditLog(id) {
  return api.get(`/audit/${id}`)
}

export function getResourceHistory(type, id) {
  return api.get(`/audit/resource/${type}/${id}`)
}

export function getUserHistory(id) {
  return api.get(`/audit/user/${id}`)
}

export function getRecentLogins() {
  return api.get('/audit/recent-logins')
}

export function getAuditActions() {
  return api.get('/audit/actions')
}

export function getAuditSummary() {
  return api.get('/audit/summary')
}
