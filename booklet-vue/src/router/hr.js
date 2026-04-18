const HrRoutes = {
  path: '/hr',
  children: [
    {
      path: 'employees',
      name: 'EmployeeList',
      component: () => import('@/views/hr/employees/EmployeeList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'employees:view',
        planFeature: 'hr',
        title: 'Employees'
      }
    },
    {
      path: 'employees/new',
      name: 'EmployeeCreate',
      component: () => import('@/views/hr/employees/EmployeeCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'employees:create',
        planFeature: 'hr',
        title: 'New Employee'
      }
    },
    {
      path: 'employees/:id',
      name: 'EmployeeDetail',
      component: () => import('@/views/hr/employees/EmployeeDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'employees:view',
        planFeature: 'hr',
        title: 'Employee Details'
      }
    },
    {
      path: 'employees/:id/edit',
      name: 'EmployeeEdit',
      component: () => import('@/views/hr/employees/EmployeeEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'employees:edit',
        planFeature: 'hr',
        title: 'Edit Employee'
      }
    },
    {
      path: 'payroll',
      name: 'RunPayroll',
      component: () => import('@/views/hr/payroll/RunPayroll.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'payroll:view',
        planFeature: 'hr',
        title: 'Run Payroll'
      }
    },
    {
      path: 'payslips',
      name: 'PayslipList',
      component: () => import('@/views/hr/payslips/PayslipList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'payroll:view',
        planFeature: 'hr',
        title: 'Payslips'
      }
    },
    {
      path: 'payslips/:id',
      name: 'PayslipDetail',
      component: () => import('@/views/hr/payslips/PayslipDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'payroll:view',
        planFeature: 'hr',
        title: 'Payslip Details'
      }
    },
    {
      path: 'payroll/summary',
      name: 'PayrollSummary',
      component: () => import('@/views/hr/payroll/PayrollSummary.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'payroll:view',
        planFeature: 'hr',
        title: 'Payroll Summary'
      }
    }
  ]
}

export default HrRoutes
