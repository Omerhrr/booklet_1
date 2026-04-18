const AuditRoutes = {
  path: '/audit',
  children: [
    {
      path: '',
      name: 'AuditLogs',
      component: () => import('@/views/audit/AuditLogs.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'settings:view',
        title: 'Audit Logs'
      }
    },
    {
      path: ':id',
      name: 'AuditDetail',
      component: () => import('@/views/audit/AuditDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'settings:view',
        title: 'Audit Detail'
      }
    },
    {
      path: 'resource/:type/:id',
      name: 'ResourceHistory',
      component: () => import('@/views/audit/ResourceHistory.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'settings:view',
        title: 'Resource History'
      }
    },
    {
      path: 'user/:id',
      name: 'UserHistory',
      component: () => import('@/views/audit/UserHistory.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'settings:view',
        title: 'User History'
      }
    },
    {
      path: 'login-history',
      name: 'LoginHistory',
      component: () => import('@/views/audit/LoginHistory.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'settings:view',
        title: 'Login History'
      }
    }
  ]
}

export default AuditRoutes
