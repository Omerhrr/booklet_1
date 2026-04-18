import api from './axios'

export function login(data) {
  return api.post('/auth/login', data)
}

export function signup(data) {
  return api.post('/auth/signup', data)
}

export function getMe() {
  return api.get('/auth/me')
}

export function getPermissions() {
  return api.get('/auth/permissions')
}

export function changePassword(data) {
  return api.post('/settings/users/change-password', data)
}

export function verifyToken(token) {
  return api.post('/saas/auth/verify-token', { token })
}

export function logout() {
  return api.post('/auth/logout')
}

export function forgotPassword(data) {
  return api.post('/auth/forgot-password', data)
}
