const CashbookRoutes = {
  path: '/cashbook',
  children: [
    {
      path: '',
      name: 'CashbookList',
      component: () => import('@/views/cashbook/CashbookList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounting:view',
        title: 'Cash Book'
      }
    },
    {
      path: 'create',
      name: 'CashbookCreate',
      component: () => import('@/views/cashbook/CashbookCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounting:create',
        title: 'New Cash Book Entry'
      }
    },
    {
      path: 'account/:id',
      name: 'CashbookAccountDetail',
      component: () => import('@/views/cashbook/CashbookAccountDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounting:view',
        title: 'Cash Book Account Details'
      }
    }
  ]
}

export default CashbookRoutes
