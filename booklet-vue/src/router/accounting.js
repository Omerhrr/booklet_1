const AccountingRoutes = {
  path: '/accounting',
  children: [
    {
      path: 'chart-of-accounts',
      name: 'ChartOfAccounts',
      component: () => import('@/views/accounting/accounts/ChartOfAccounts.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounts:view',
        title: 'Chart of Accounts'
      }
    },
    {
      path: 'accounts/:id',
      name: 'AccountDetail',
      component: () => import('@/views/accounting/accounts/AccountDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounts:view',
        title: 'Account Details'
      }
    },
    {
      path: 'journal',
      name: 'JournalList',
      component: () => import('@/views/accounting/journal/JournalList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'journal:view',
        title: 'Journal Entries'
      }
    },
    {
      path: 'journal/new',
      name: 'JournalCreate',
      component: () => import('@/views/accounting/journal/JournalCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'journal:create',
        title: 'New Journal Entry'
      }
    },
    {
      path: 'journal/:id',
      name: 'JournalDetail',
      component: () => import('@/views/accounting/journal/JournalDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'journal:view',
        title: 'Journal Entry Details'
      }
    },
    {
      path: 'ledger',
      name: 'GeneralLedger',
      component: () => import('@/views/accounting/ledger/GeneralLedger.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounts:view',
        title: 'General Ledger'
      }
    },
    {
      path: 'balance-sheet',
      name: 'BalanceSheet',
      component: () => import('@/views/accounting/reports/BalanceSheet.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Balance Sheet'
      }
    },
    {
      path: 'profit-loss',
      name: 'ProfitLoss',
      component: () => import('@/views/accounting/reports/ProfitLoss.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Profit & Loss'
      }
    },
    {
      path: 'trial-balance',
      name: 'TrialBalance',
      component: () => import('@/views/accounting/reports/TrialBalance.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'reports:view',
        title: 'Trial Balance'
      }
    }
  ]
}

export default AccountingRoutes
