const AuthRoutes = {
  path: '/auth',
  children: [
    {
      path: 'login',
      name: 'AuthLogin',
      component: () => import('@/views/auth/Login.vue'),
      meta: {
        layout: 'auth',
        guestOnly: true,
        title: 'Sign In'
      }
    },
    {
      path: 'signup',
      name: 'AuthSignup',
      component: () => import('@/views/auth/Signup.vue'),
      meta: {
        layout: 'auth',
        guestOnly: true,
        title: 'Sign Up'
      }
    },
    {
      path: 'forgot-password',
      name: 'AuthForgotPassword',
      component: () => import('@/views/auth/ForgotPassword.vue'),
      meta: {
        layout: 'auth',
        guestOnly: true,
        title: 'Forgot Password'
      }
    },
    {
      path: 'change-password',
      name: 'AuthChangePassword',
      component: () => import('@/views/auth/ChangePassword.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        title: 'Change Password'
      }
    }
  ]
}

export default AuthRoutes
