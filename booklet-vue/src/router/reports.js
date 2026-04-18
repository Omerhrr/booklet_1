const ReportsRoutes = {
  path: '/reports',
  children: [
    {
      path: '',
      name: 'ReportsIndex',
      component: () => import('@/views/reports/ReportsIndex.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Reports'
      }
    },
    {
      path: 'sales',
      name: 'SalesReport',
      component: () => import('@/views/reports/SalesReport.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Sales Report'
      }
    },
    {
      path: 'purchases',
      name: 'PurchasesReport',
      component: () => import('@/views/reports/PurchasesReport.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Purchases Report'
      }
    },
    {
      path: 'expenses',
      name: 'ExpensesReport',
      component: () => import('@/views/reports/ExpensesReport.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Expenses Report'
      }
    },
    {
      path: 'inventory',
      name: 'InventoryReport',
      component: () => import('@/views/reports/InventoryReport.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Inventory Report'
      }
    },
    {
      path: 'aging',
      name: 'AgingReport',
      component: () => import('@/views/reports/AgingReport.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Aging Report'
      }
    },
    {
      path: 'trial-balance',
      name: 'TrialBalanceReport',
      component: () => import('@/views/reports/TrialBalanceReport.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Trial Balance Report'
      }
    },
    {
      path: 'vat',
      name: 'VatReport',
      component: () => import('@/views/reports/VatReport.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'VAT Report'
      }
    }
  ]
}

export default ReportsRoutes
