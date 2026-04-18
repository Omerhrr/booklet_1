const BankingRoutes = {
  path: '/banking',
  children: [
    {
      path: 'accounts',
      name: 'BankAccountList',
      component: () => import('@/views/banking/accounts/BankAccountList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'banking:view',
        title: 'Bank Accounts'
      }
    },
    {
      path: 'accounts/new',
      name: 'BankAccountCreate',
      component: () => import('@/views/banking/accounts/BankAccountCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'banking:create',
        title: 'New Bank Account'
      }
    },
    {
      path: 'accounts/:id',
      name: 'BankAccountDetail',
      component: () => import('@/views/banking/accounts/BankAccountDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'banking:view',
        title: 'Bank Account Details'
      }
    },
    {
      path: 'transfers',
      name: 'TransferList',
      component: () => import('@/views/banking/transfers/TransferList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'transfers:view',
        title: 'Transfers'
      }
    },
    {
      path: 'reconciliation',
      name: 'ReconciliationList',
      component: () => import('@/views/banking/reconciliation/ReconciliationList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reconciliation:view',
        title: 'Reconciliation'
      }
    }
  ]
}

export default BankingRoutes
