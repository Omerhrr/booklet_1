import api from './axios'

// ── Conversations ──────────────────────────────────────────
export function getConversations() {
  return api.get('/ai/conversations')
}

export function createChat(data) {
  return api.post('/ai/chat', data)
}

export function getConversation(id) {
  return api.get(`/ai/conversations/${id}`)
}

export function deleteConversation(id) {
  return api.delete(`/ai/conversations/${id}`)
}

export function archiveConversation(id) {
  return api.post(`/ai/conversations/${id}/archive`)
}

// ── Settings ───────────────────────────────────────────────
export function getAiSettings() {
  return api.get('/ai/settings')
}

export function updateAiSettings(data) {
  return api.put('/ai/settings', data)
}

// ── Providers & Usage ──────────────────────────────────────
export function getAiProviders() {
  return api.get('/ai/providers')
}

export function getAiUsage() {
  return api.get('/ai/usage')
}

// ── Permissions ────────────────────────────────────────────
export function fixAiPermissions() {
  return api.post('/ai/fix-permissions')
}
