const OtherIncomesRoutes = {
  path: '/other-incomes',
  children: [
    {
      path: '',
      name: 'OtherIncomeList',
      component: () => import('@/views/other-incomes/OtherIncomeList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'other_income:view',
        title: 'Other Income'
      }
    },
    {
      path: 'new',
      name: 'OtherIncomeCreate',
      component: () => import('@/views/other-incomes/OtherIncomeCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'other_income:create',
        title: 'New Other Income'
      }
    },
    {
      path: ':id',
      name: 'OtherIncomeDetail',
      component: () => import('@/views/other-incomes/OtherIncomeDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'other_income:view',
        title: 'Other Income Details'
      }
    },
    {
      path: ':id/edit',
      name: 'OtherIncomeEdit',
      component: () => import('@/views/other-incomes/OtherIncomeEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'other_income:edit',
        title: 'Edit Other Income'
      }
    }
  ]
}

export default OtherIncomesRoutes
