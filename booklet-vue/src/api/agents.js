import api from './axios'

// ── Configurations & Types ─────────────────────────────────
export function getConfigurations() {
  return api.get('/agents/configurations')
}

export function getAgentTypes() {
  return api.get('/agents/types')
}

// ── Executions ─────────────────────────────────────────────
export function getExecutions(params) {
  return api.get('/agents/executions', { params })
}

export function getExecution(id) {
  return api.get(`/agents/executions/${id}`)
}

// ── Automation ─────────────────────────────────────────────
export function runAutomation(data) {
  return api.post('/agents/automation/run', data)
}

export function getAutomationConfig() {
  return api.get('/agents/automation/config')
}

// ── Audit Agent ────────────────────────────────────────────
export function runAudit(data) {
  return api.post('/agents/audit/run', data)
}

export function getAuditConfig() {
  return api.get('/agents/audit/config')
}

// ── Wizard ─────────────────────────────────────────────────
export function getWizardSessions() {
  return api.get('/agents/wizard/sessions')
}

export function createWizardSession(data) {
  return api.post('/agents/wizard/sessions', data)
}

export function getWizardSession(id) {
  return api.get(`/agents/wizard/sessions/${id}`)
}

export function addWizardMessage(id, data) {
  return api.post(`/agents/wizard/sessions/${id}/messages`, data)
}

export function resolveWizardSession(id) {
  return api.post(`/agents/wizard/sessions/${id}/resolve`)
}

// ── Findings ───────────────────────────────────────────────
export function listFindings(params) {
  return api.get('/agents/findings', { params })
}

export function resolveFinding(id) {
  return api.post(`/agents/findings/${id}/resolve`)
}

// ── Settings ───────────────────────────────────────────────
export function getAgentSettings() {
  return api.get('/agents/settings')
}

export function updateAgentSettings(data) {
  return api.put('/agents/settings', data)
}
