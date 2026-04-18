const DashboardRoutes = {
  path: '/dashboard',
  children: [
    {
      path: '',
      name: 'DashboardIndex',
      component: () => import('@/views/dashboard/Index.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: null,
        title: 'Dashboard',
        icon: 'pie-chart'
      }
    },
    {
      path: 'subscription',
      name: 'DashboardSubscription',
      component: () => import('@/views/dashboard/Subscription.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: null,
        title: 'Subscription'
      }
    }
  ]
}

export default DashboardRoutes
