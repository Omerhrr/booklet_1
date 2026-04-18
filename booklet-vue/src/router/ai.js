const AiRoutes = {
  path: '/ai',
  children: [
    {
      path: '',
      name: 'AiChat',
      component: () => import('@/views/ai/AiChat.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'ai:use',
        planFeature: 'ai',
        title: 'AI Assistant'
      }
    },
    {
      path: 'settings',
      name: 'AiSettings',
      component: () => import('@/views/ai/AiSettings.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'ai:use',
        planFeature: 'ai',
        title: 'AI Settings'
      }
    },
    {
      path: 'usage',
      name: 'AiUsage',
      component: () => import('@/views/ai/AiUsage.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'ai:use',
        planFeature: 'ai',
        title: 'AI Usage'
      }
    }
  ]
}

export default AiRoutes
