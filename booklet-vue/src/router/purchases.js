const PurchasesRoutes = {
  path: '/purchases',
  children: [
    {
      path: 'bills',
      name: 'BillList',
      component: () => import('@/views/purchases/bills/BillList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'bills:view',
        title: 'Bills'
      }
    },
    {
      path: 'bills/new',
      name: 'BillCreate',
      component: () => import('@/views/purchases/bills/BillCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'bills:create',
        title: 'New Bill'
      }
    },
    {
      path: 'bills/:id',
      name: 'BillDetail',
      component: () => import('@/views/purchases/bills/BillDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'bills:view',
        title: 'Bill Details'
      }
    },
    {
      path: 'debit-notes',
      name: 'DebitNoteList',
      component: () => import('@/views/purchases/debit-notes/DebitNoteList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'debit_notes:view',
        title: 'Debit Notes'
      }
    },
    {
      path: 'debit-notes/:id',
      name: 'DebitNoteDetail',
      component: () => import('@/views/purchases/debit-notes/DebitNoteDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'debit_notes:view',
        title: 'Debit Note Details'
      }
    },
    {
      path: 'bills/:id/debit-note',
      name: 'DebitNoteCreate',
      component: () => import('@/views/purchases/debit-notes/DebitNoteCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'debit_notes:create',
        title: 'Create Debit Note'
      }
    }
  ]
}

export default PurchasesRoutes
