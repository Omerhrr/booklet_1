const CrmRoutes = {
  path: '/crm',
  children: [
    {
      path: 'customers',
      name: 'CustomerList',
      component: () => import('@/views/crm/customers/CustomerList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'customers:view',
        title: 'Customers'
      }
    },
    {
      path: 'customers/new',
      name: 'CustomerCreate',
      component: () => import('@/views/crm/customers/CustomerCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'customers:create',
        title: 'New Customer'
      }
    },
    {
      path: 'customers/:id',
      name: 'CustomerDetail',
      component: () => import('@/views/crm/customers/CustomerDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'customers:view',
        title: 'Customer Details'
      }
    },
    {
      path: 'customers/:id/edit',
      name: 'CustomerEdit',
      component: () => import('@/views/crm/customers/CustomerEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'customers:edit',
        title: 'Edit Customer'
      }
    },
    {
      path: 'vendors',
      name: 'VendorList',
      component: () => import('@/views/crm/vendors/VendorList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'vendors:view',
        title: 'Vendors'
      }
    },
    {
      path: 'vendors/new',
      name: 'VendorCreate',
      component: () => import('@/views/crm/vendors/VendorCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'vendors:create',
        title: 'New Vendor'
      }
    },
    {
      path: 'vendors/:id',
      name: 'VendorDetail',
      component: () => import('@/views/crm/vendors/VendorDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'vendors:view',
        title: 'Vendor Details'
      }
    },
    {
      path: 'vendors/:id/edit',
      name: 'VendorEdit',
      component: () => import('@/views/crm/vendors/VendorEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'vendors:edit',
        title: 'Edit Vendor'
      }
    }
  ]
}

export default CrmRoutes
