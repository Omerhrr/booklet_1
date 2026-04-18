const SettingsRoutes = {
  path: '/settings',
  children: [
    {
      path: '',
      name: 'SettingsIndex',
      component: () => import('@/views/settings/SettingsIndex.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'users:view',
        permissionAny: ['users:view', 'roles:view', 'branches:view'],
        title: 'Settings'
      }
    },
    {
      path: 'business',
      name: 'BusinessSettings',
      component: () => import('@/views/settings/BusinessSettings.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'settings:edit',
        title: 'Business Settings'
      }
    },
    {
      path: 'branches/new',
      name: 'BranchCreate',
      component: () => import('@/views/settings/branches/BranchCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'branches:create',
        title: 'New Branch'
      }
    },
    {
      path: 'branches/:id/edit',
      name: 'BranchEdit',
      component: () => import('@/views/settings/branches/BranchEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'branches:edit',
        title: 'Edit Branch'
      }
    },
    {
      path: 'roles/new',
      name: 'RoleCreate',
      component: () => import('@/views/settings/roles/RoleCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'roles:create',
        title: 'New Role'
      }
    },
    {
      path: 'roles/:id/edit',
      name: 'RoleEdit',
      component: () => import('@/views/settings/roles/RoleEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'roles:edit',
        title: 'Edit Role'
      }
    },
    {
      path: 'users/new',
      name: 'UserCreate',
      component: () => import('@/views/settings/users/UserCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'users:create',
        title: 'New User'
      }
    },
    {
      path: 'users/:id',
      name: 'UserDetail',
      component: () => import('@/views/settings/users/UserDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'users:view',
        title: 'User Details'
      }
    },
    {
      path: 'users/:id/edit',
      name: 'UserEdit',
      component: () => import('@/views/settings/users/UserEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'users:edit',
        title: 'Edit User'
      }
    },
    {
      path: 'fiscal-years/new',
      name: 'FiscalYearCreate',
      component: () => import('@/views/settings/fiscal-years/FiscalYearCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'fiscal_year:create',
        title: 'New Fiscal Year'
      }
    }
  ]
}

export default SettingsRoutes
