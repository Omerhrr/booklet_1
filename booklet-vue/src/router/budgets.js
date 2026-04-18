const BudgetsRoutes = {
  path: '/budgets',
  children: [
    {
      path: '',
      name: 'BudgetList',
      component: () => import('@/views/budgets/BudgetList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'budgets:view',
        planFeature: 'budgets',
        title: 'Budgets'
      }
    },
    {
      path: 'new',
      name: 'BudgetCreate',
      component: () => import('@/views/budgets/BudgetCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'budgets:create',
        planFeature: 'budgets',
        title: 'New Budget'
      }
    },
    {
      path: ':id',
      name: 'BudgetDetail',
      component: () => import('@/views/budgets/BudgetDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'budgets:view',
        planFeature: 'budgets',
        title: 'Budget Details'
      }
    },
    {
      path: ':id/edit',
      name: 'BudgetEdit',
      component: () => import('@/views/budgets/BudgetEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'budgets:edit',
        planFeature: 'budgets',
        title: 'Edit Budget'
      }
    },
    {
      path: ':id/vs-actual',
      name: 'BudgetVsActual',
      component: () => import('@/views/budgets/BudgetVsActual.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'budgets:view',
        planFeature: 'budgets',
        title: 'Budget vs Actual'
      }
    }
  ]
}

export default BudgetsRoutes
