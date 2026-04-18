const ExpensesRoutes = {
  path: '/expenses',
  children: [
    {
      path: '',
      name: 'ExpenseList',
      component: () => import('@/views/expenses/ExpenseList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'expenses:view',
        title: 'Expenses'
      }
    },
    {
      path: 'new',
      name: 'ExpenseCreate',
      component: () => import('@/views/expenses/ExpenseCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'expenses:create',
        title: 'New Expense'
      }
    },
    {
      path: ':id',
      name: 'ExpenseDetail',
      component: () => import('@/views/expenses/ExpenseDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'expenses:view',
        title: 'Expense Details'
      }
    },
    {
      path: ':id/edit',
      name: 'ExpenseEdit',
      component: () => import('@/views/expenses/ExpenseEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'expenses:edit',
        title: 'Edit Expense'
      }
    },
    {
      path: 'summary',
      name: 'ExpenseSummary',
      component: () => import('@/views/expenses/ExpenseSummary.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'expenses:view',
        title: 'Expense Summary'
      }
    }
  ]
}

export default ExpensesRoutes
