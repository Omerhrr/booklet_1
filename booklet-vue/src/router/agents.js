const AgentsRoutes = {
  path: '/agents',
  children: [
    {
      path: '',
      name: 'AgentDashboard',
      component: () => import('@/views/agents/AgentDashboard.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'agents:use',
        planFeature: 'agents',
        title: 'Agents'
      }
    },
    {
      path: 'automation',
      name: 'AutomationAgent',
      component: () => import('@/views/agents/AutomationAgent.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'agents:use',
        planFeature: 'agents',
        title: 'Automation Agent'
      }
    },
    {
      path: 'audit',
      name: 'AuditAgent',
      component: () => import('@/views/agents/AuditAgent.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'agents:use',
        planFeature: 'agents',
        title: 'Audit Agent'
      }
    },
    {
      path: 'wizard',
      name: 'DocWizard',
      component: () => import('@/views/agents/DocWizard.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'doc_wizard:use',
        planFeature: 'agents',
        title: 'Document Wizard'
      }
    },
    {
      path: 'findings',
      name: 'FindingsList',
      component: () => import('@/views/agents/FindingsList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'agents:view_findings',
        planFeature: 'agents',
        title: 'Findings'
      }
    },
    {
      path: 'settings',
      name: 'AgentSettings',
      component: () => import('@/views/agents/AgentSettings.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'agents:configure',
        planFeature: 'agents',
        title: 'Agent Settings'
      }
    }
  ]
}

export default AgentsRoutes
