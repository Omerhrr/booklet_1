const FixedAssetsRoutes = {
  path: '/fixed-assets',
  children: [
    {
      path: '',
      name: 'FixedAssetList',
      component: () => import('@/views/fixed-assets/FixedAssetList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounting:view',
        planFeature: 'fixed_assets',
        title: 'Fixed Assets'
      }
    },
    {
      path: 'create',
      name: 'FixedAssetCreate',
      component: () => import('@/views/fixed-assets/FixedAssetCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounting:create',
        planFeature: 'fixed_assets',
        title: 'New Fixed Asset'
      }
    },
    {
      path: ':id',
      name: 'FixedAssetDetail',
      component: () => import('@/views/fixed-assets/FixedAssetDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounting:view',
        planFeature: 'fixed_assets',
        title: 'Fixed Asset Details'
      }
    },
    {
      path: ':id/edit',
      name: 'FixedAssetEdit',
      component: () => import('@/views/fixed-assets/FixedAssetEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'accounting:edit',
        planFeature: 'fixed_assets',
        title: 'Edit Fixed Asset'
      }
    }
  ]
}

export default FixedAssetsRoutes
