const SalesRoutes = {
  path: '/sales',
  children: [
    {
      path: 'invoices',
      name: 'InvoiceList',
      component: () => import('@/views/sales/invoices/InvoiceList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'invoices:view',
        title: 'Invoices'
      }
    },
    {
      path: 'invoices/new',
      name: 'InvoiceCreate',
      component: () => import('@/views/sales/invoices/InvoiceCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'invoices:create',
        title: 'New Invoice'
      }
    },
    {
      path: 'invoices/:id',
      name: 'InvoiceDetail',
      component: () => import('@/views/sales/invoices/InvoiceDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'invoices:view',
        title: 'Invoice Details'
      }
    },
    {
      path: 'credit-notes',
      name: 'CreditNoteList',
      component: () => import('@/views/sales/credit-notes/CreditNoteList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'credit_notes:view',
        title: 'Credit Notes'
      }
    },
    {
      path: 'credit-notes/:id',
      name: 'CreditNoteDetail',
      component: () => import('@/views/sales/credit-notes/CreditNoteDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'credit_notes:view',
        title: 'Credit Note Details'
      }
    },
    {
      path: 'invoices/:id/credit-note',
      name: 'CreditNoteCreate',
      component: () => import('@/views/sales/credit-notes/CreditNoteCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'credit_notes:create',
        title: 'Create Credit Note'
      }
    }
  ]
}

export default SalesRoutes
