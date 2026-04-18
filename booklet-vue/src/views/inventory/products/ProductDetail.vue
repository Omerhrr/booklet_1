<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import { formatDate } from '@/utils/dates'
import * as inventoryApi from '@/api/inventory'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const toastStore = useToastStore()

const product = ref(null)
const categories = ref([])
const stockAdjustments = ref([])
const loading = ref(true)
const showDeleteDialog = ref(false)
const deleting = ref(false)

const breadcrumbs = computed(() => [
  { text: 'Inventory', to: '/inventory' },
  { text: 'Products', to: '/inventory/products' },
  { text: product.value?.name || 'Product Details' },
])

async function fetchProduct() {
  loading.value = true
  try {
    const { data } = await inventoryApi.getProduct(route.params.id)
    product.value = data
    stockAdjustments.value = data.stock_adjustments || data.stock_history || []
  } catch (error) {
    console.error('Failed to fetch product:', error)
    toastStore.show('Failed to load product', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const { data } = await inventoryApi.listCategories()
    categories.value = Array.isArray(data) ? data : data.items || data.categories || []
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

function formatPrice(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

function getCategoryName() {
  if (!product.value) return '—'
  const cat = categories.value.find((c) => String(c.id) === String(product.value.category_id || product.value.category))
  return cat ? cat.name : product.value.category || '—'
}

function isLowStock() {
  if (!product.value) return false
  return product.value.quantity <= (product.value.low_stock_threshold || 0)
}

function stockPercentage() {
  if (!product.value || !product.value.low_stock_threshold) return 100
  const threshold = product.value.low_stock_threshold
  return Math.min(100, Math.round((product.value.quantity / threshold) * 100))
}

function editProduct() {
  router.push({ name: 'ProductEdit', params: { id: route.params.id } })
}

function goBack() {
  router.push({ name: 'ProductList' })
}

async function toggleStatus() {
  if (!product.value) return
  try {
    await inventoryApi.toggleProductStatus(product.value.id)
    product.value.status = product.value.status === 'active' ? 'inactive' : 'active'
    toastStore.show(`Product ${product.value.status === 'active' ? 'activated' : 'deactivated'}`)
  } catch (error) {
    console.error('Failed to toggle status:', error)
    toastStore.show('Failed to update status', 'error')
  }
}

async function handleDelete() {
  deleting.value = true
  try {
    await inventoryApi.deleteProduct(route.params.id)
    toastStore.show('Product deleted successfully')
    router.push({ name: 'ProductList' })
  } catch (error) {
    console.error('Failed to delete product:', error)
    toastStore.show('Failed to delete product', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchProduct(), fetchCategories()])
})
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading product..." />
    </div>

    <template v-else-if="product">
      <PageHeader :title="product.name" :breadcrumbs="breadcrumbs">
        <template #actions>
          <div class="flex items-center gap-3">
            <button
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="goBack"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Back to List
            </button>

            <button
              v-if="authStore.hasPermission('products:edit')"
              type="button"
              :class="[
                'inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors',
                product.status === 'active'
                  ? 'text-amber-700 bg-amber-50 border border-amber-300 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700 dark:hover:bg-amber-900/50'
                  : 'text-green-700 bg-green-50 border border-green-300 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400 dark:border-green-700 dark:hover:bg-green-900/50',
              ]"
              @click="toggleStatus"
            >
              {{ product.status === 'active' ? 'Deactivate' : 'Activate' }}
            </button>

            <button
              v-if="authStore.hasPermission('products:edit')"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
              @click="editProduct"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
              Edit
            </button>

            <button
              v-if="authStore.hasPermission('products:delete')"
              type="button"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-red-700 bg-red-50 border border-red-300 rounded-lg hover:bg-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-700 dark:hover:bg-red-900/50 transition-colors"
              @click="showDeleteDialog = true"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
              Delete
            </button>
          </div>
        </template>
      </PageHeader>

      <!-- Stock Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Current Stock</p>
          <div class="flex items-center gap-2 mt-1">
            <p
              :class="[
                'text-2xl font-bold',
                isLowStock() ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white',
              ]"
            >
              {{ product.quantity }}
            </p>
            <span v-if="product.unit" class="text-sm text-gray-500 dark:text-gray-400">{{ product.unit }}</span>
            <svg
              v-if="isLowStock()"
              class="w-5 h-5 text-red-500 dark:text-red-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Selling Price</p>
          <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ formatPrice(product.selling_price) }}</p>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Cost Price</p>
          <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ formatPrice(product.cost_price) }}</p>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <p class="text-sm text-gray-500 dark:text-gray-400">Status</p>
          <div class="mt-2">
            <StatusBadge :status="product.status" />
          </div>
        </div>
      </div>

      <!-- Stock Level Indicator -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Stock Level</h3>
        <div class="flex items-center gap-4">
          <div class="flex-1">
            <div class="relative w-full h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                :class="[
                  'absolute inset-y-0 left-0 rounded-full transition-all duration-500',
                  isLowStock()
                    ? 'bg-red-500 dark:bg-red-400'
                    : 'bg-green-500 dark:bg-green-400',
                ]"
                :style="{ width: stockPercentage() + '%' }"
              />
            </div>
            <div class="flex items-center justify-between mt-2">
              <span class="text-xs text-gray-500 dark:text-gray-400">
                Threshold: {{ product.low_stock_threshold || 0 }} {{ product.unit || '' }}
              </span>
              <span
                :class="[
                  'text-xs font-medium',
                  isLowStock() ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400',
                ]"
              >
                {{ isLowStock() ? '⚠ Low Stock' : '✓ In Stock' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Product Info Card -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Product Information</h3>
        <dl class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4">
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">SKU</dt>
            <dd class="text-sm font-mono font-medium text-gray-900 dark:text-white mt-0.5">{{ product.sku }}</dd>
          </div>
          <div>
            <dt class="text-sm text-gray-500 dark:text-gray-400">Category</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ getCategoryName() }}</dd>
          </div>
          <div v-if="product.unit">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Unit</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ product.unit }}</dd>
          </div>
          <div v-if="product.tax_rate">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Tax Rate</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ product.tax_rate }}%</dd>
          </div>
          <div v-if="product.created_at">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Created</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5">{{ formatDate(product.created_at) }}</dd>
          </div>
          <div v-if="product.description" class="sm:col-span-2 lg:col-span-3">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Description</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5 whitespace-pre-wrap">{{ product.description }}</dd>
          </div>
          <div v-if="product.notes" class="sm:col-span-2 lg:col-span-3">
            <dt class="text-sm text-gray-500 dark:text-gray-400">Notes</dt>
            <dd class="text-sm font-medium text-gray-900 dark:text-white mt-0.5 whitespace-pre-wrap">{{ product.notes }}</dd>
          </div>
        </dl>
      </div>

      <!-- Stock Adjustments / History -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Stock History</h3>
        </div>
        <div v-if="stockAdjustments.length === 0" class="flex flex-col items-center justify-center py-12 text-center">
          <p class="text-sm text-gray-500 dark:text-gray-400">No stock adjustments recorded.</p>
        </div>
        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Previous Qty</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">New Qty</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Difference</th>
                <th class="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Reason</th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              <tr
                v-for="adj in stockAdjustments"
                :key="adj.id"
                class="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ formatDate(adj.created_at || adj.date) }}</td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ adj.previous_quantity }}</td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{{ adj.new_quantity }}</td>
                <td class="px-6 py-4">
                  <span
                    :class="[
                      'text-sm font-medium',
                      (adj.difference || 0) >= 0
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400',
                    ]"
                  >
                    {{ (adj.difference || 0) >= 0 ? '+' : '' }}{{ adj.difference }}
                  </span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{{ adj.reason || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Product"
      :message="`Are you sure you want to delete '${product?.name}'? This action cannot be undone and will remove all associated data.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
