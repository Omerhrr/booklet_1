const InventoryRoutes = {
  path: '/inventory',
  children: [
    {
      path: 'products',
      name: 'ProductList',
      component: () => import('@/views/inventory/products/ProductList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'products:view',
        title: 'Products'
      }
    },
    {
      path: 'products/low-stock',
      name: 'ProductLowStock',
      component: () => import('@/views/inventory/products/ProductLowStock.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'products:view',
        title: 'Low Stock Products'
      }
    },
    {
      path: 'products/new',
      name: 'ProductCreate',
      component: () => import('@/views/inventory/products/ProductCreate.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'products:create',
        title: 'New Product'
      }
    },
    {
      path: 'products/:id',
      name: 'ProductDetail',
      component: () => import('@/views/inventory/products/ProductDetail.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'products:view',
        title: 'Product Details'
      }
    },
    {
      path: 'products/:id/edit',
      name: 'ProductEdit',
      component: () => import('@/views/inventory/products/ProductEdit.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'products:edit',
        title: 'Edit Product'
      }
    },
    {
      path: 'categories',
      name: 'CategoryList',
      component: () => import('@/views/inventory/categories/CategoryList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'categories:view',
        title: 'Categories'
      }
    },
    {
      path: 'stock-adjustments',
      name: 'StockAdjustmentList',
      component: () => import('@/views/inventory/stock/StockAdjustmentList.vue'),
      meta: {
        layout: 'default',
        requiresAuth: true,
        permission: 'stock:view',
        title: 'Stock Adjustments'
      }
    }
  ]
}

export default InventoryRoutes
