import api from './axios'

// ── Business ───────────────────────────────────────────────
export function getBusiness() {
  return api.get('/settings/business')
}

export function updateBusiness(data) {
  return api.put('/settings/business', data)
}

// ── Branches ───────────────────────────────────────────────
export function listBranches() {
  return api.get('/settings/branches')
}

export function createBranch(data) {
  return api.post('/settings/branches', data)
}

export function getBranch(id) {
  return api.get(`/settings/branches/${id}`)
}

export function updateBranch(id, data) {
  return api.put(`/settings/branches/${id}`, data)
}

export function setDefaultBranch(id) {
  return api.post(`/settings/branches/${id}/set-default`)
}

// ── Roles ──────────────────────────────────────────────────
export function listRoles() {
  return api.get('/settings/roles')
}

export function createRole(data) {
  return api.post('/settings/roles', data)
}

export function getRole(id) {
  return api.get(`/settings/roles/${id}`)
}

export function updateRole(id, data) {
  return api.put(`/settings/roles/${id}`, data)
}

export function deleteRole(id) {
  return api.delete(`/settings/roles/${id}`)
}

// ── Users ──────────────────────────────────────────────────
export function listUsers() {
  return api.get('/settings/users')
}

export function createUser(data) {
  return api.post('/settings/users', data)
}

export function getUser(id) {
  return api.get(`/settings/users/${id}`)
}

export function updateUser(id, data) {
  return api.put(`/settings/users/${id}`, data)
}

export function deleteUser(id) {
  return api.delete(`/settings/users/${id}`)
}

export function assignUserRole(userId, data) {
  return api.post(`/settings/users/${userId}/assign-role`, data)
}

// ── Branch Context ─────────────────────────────────────────
export function setBranch(id) {
  return api.post(`/settings/branches/set-active/${id}`)
}

export function getSettingsPermissions() {
  return api.get('/settings/permissions')
}

export function seedPermissions() {
  return api.post('/settings/permissions/seed')
}
