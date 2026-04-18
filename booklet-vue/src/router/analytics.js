const AnalyticsRoutes = {
  path: '/analytics',
  children: [
    {
      path: '',
      name: 'AnalyticsHub',
      component: () => import('@/views/analytics/AnalyticsHub.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Analytics Hub'
      }
    },
    {
      path: 'query',
      name: 'AnalyticsQuery',
      component: () => import('@/views/analytics/AnalyticsQuery.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Query Builder'
      }
    },
    {
      path: 'analyses',
      name: 'SavedAnalyses',
      component: () => import('@/views/analytics/SavedAnalyses.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Saved Analyses'
      }
    },
    {
      path: 'analyses/new',
      name: 'AnalysisCreate',
      component: () => import('@/views/analytics/AnalysisCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'New Analysis'
      }
    },
    {
      path: 'analyses/:id',
      name: 'AnalysisView',
      component: () => import('@/views/analytics/AnalysisView.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Analysis View'
      }
    },
    {
      path: 'analyses/:id/edit',
      name: 'AnalysisEdit',
      component: () => import('@/views/analytics/AnalysisEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Edit Analysis'
      }
    },
    {
      path: 'dashboards',
      name: 'DashboardList',
      component: () => import('@/views/analytics/DashboardList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Dashboards'
      }
    },
    {
      path: 'dashboards/new',
      name: 'DashboardCreate',
      component: () => import('@/views/analytics/DashboardCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'New Dashboard'
      }
    },
    {
      path: 'dashboards/:id',
      name: 'DashboardView',
      component: () => import('@/views/analytics/DashboardView.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Dashboard View'
      }
    },
    {
      path: 'dashboards/:id/edit',
      name: 'DashboardEdit',
      component: () => import('@/views/analytics/DashboardEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        planFeature: 'analytics',
        title: 'Edit Dashboard'
      }
    }
  ]
}

export default AnalyticsRoutes
