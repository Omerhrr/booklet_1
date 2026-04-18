<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import * as inventoryApi from '@/api/inventory'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const products = ref([])
const categories = ref([])
const loading = ref(true)
const showDeleteDialog = ref(false)
const selectedProduct = ref(null)
const deleting = ref(false)
const categoryFilter = ref('')

const breadcrumbs = [
  { text: 'Inventory' },
  { text: 'Products' },
]

const columns = [
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'selling_price', label: 'Price', sortable: true, class: 'text-right' },
  { key: 'cost_price', label: 'Cost', sortable: true, class: 'text-right' },
  { key: 'quantity', label: 'Quantity', sortable: true, class: 'text-right' },
  { key: 'status', label: 'Status', sortable: true },
]

const filteredProducts = computed(() => {
  if (!categoryFilter.value) return products.value
  return products.value.filter((p) => String(p.category_id || p.category) === categoryFilter.value)
})

const categoryOptions = computed(() => {
  return categories.value.map((c) => ({
    value: String(c.id),
    label: c.name,
  }))
})

async function fetchProducts() {
  loading.value = true
  try {
    const [productsRes, categoriesRes] = await Promise.all([
      inventoryApi.listProducts(),
      inventoryApi.listCategories(),
    ])
    products.value = Array.isArray(productsRes.data) ? productsRes.data : productsRes.data.items || productsRes.data.products || []
    categories.value = Array.isArray(categoriesRes.data) ? categoriesRes.data : categoriesRes.data.items || categoriesRes.data.categories || []
  } catch (error) {
    console.error('Failed to fetch products:', error)
    toastStore.show('Failed to load products', 'error')
  } finally {
    loading.value = false
  }
}

function viewProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

function editProduct(product) {
  router.push({ name: 'ProductEdit', params: { id: product.id } })
}

function confirmDelete(product) {
  selectedProduct.value = product
  showDeleteDialog.value = true
}

async function handleDelete() {
  if (!selectedProduct.value) return
  deleting.value = true
  try {
    await inventoryApi.deleteProduct(selectedProduct.value.id)
    toastStore.show('Product deleted successfully')
    await fetchProducts()
  } catch (error) {
    console.error('Failed to delete product:', error)
    toastStore.show('Failed to delete product', 'error')
  } finally {
    deleting.value = false
    selectedProduct.value = null
  }
}

async function toggleStatus(product) {
  try {
    await inventoryApi.toggleProductStatus(product.id)
    product.status = product.status === 'active' ? 'inactive' : 'active'
    toastStore.show(`Product ${product.status === 'active' ? 'activated' : 'deactivated'}`)
  } catch (error) {
    console.error('Failed to toggle status:', error)
    toastStore.show('Failed to update status', 'error')
  }
}

function formatPrice(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

function isLowStock(product) {
  return product.quantity <= (product.low_stock_threshold || 0)
}

function getCategoryName(product) {
  const cat = categories.value.find((c) => String(c.id) === String(product.category_id || product.category))
  return cat ? cat.name : product.category || '—'
}

onMounted(fetchProducts)
</script>

<template>
  <div>
    <PageHeader title="Products" :breadcrumbs="breadcrumbs">
      <template #actions>
        <router-link
          :to="{ name: 'ProductLowStock' }"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-300 rounded-lg hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700 dark:hover:bg-amber-900/50 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
          Low Stock
        </router-link>

        <router-link
          v-if="authStore.hasPermission('products:create')"
          :to="{ name: 'ProductCreate' }"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Product
        </router-link>
      </template>
    </PageHeader>

    <!-- Category Filter -->
    <div v-if="categories.length > 0" class="mb-4">
      <select
        v-model="categoryFilter"
        class="block w-full sm:w-64 px-3 py-2.5 text-sm text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white transition-colors"
      >
        <option value="">All Categories</option>
        <option v-for="cat in categoryOptions" :key="cat.value" :value="cat.value">
          {{ cat.label }}
        </option>
      </select>
    </div>

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && filteredProducts.length === 0"
      title="No products yet"
      message="Get started by adding your first product."
      :action-text="authStore.hasPermission('products:create') ? 'Add Product' : ''"
      action-route="/inventory/products/new"
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="filteredProducts"
        :loading="loading"
        search-placeholder="Search products..."
      >
        <!-- SKU Column -->
        <template #cell-sku="{ row }">
          <span class="text-sm font-mono text-gray-600 dark:text-gray-400">{{ row.sku }}</span>
        </template>

        <!-- Name Column -->
        <template #cell-name="{ row }">
          <button
            type="button"
            class="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
            @click="viewProduct(row)"
          >
            {{ row.name }}
          </button>
        </template>

        <!-- Category Column -->
        <template #cell-category="{ row }">
          <span class="text-sm text-gray-700 dark:text-gray-300">{{ getCategoryName(row) }}</span>
        </template>

        <!-- Price Column -->
        <template #cell-selling_price="{ row }">
          <span class="text-sm font-medium text-gray-900 dark:text-white">{{ formatPrice(row.selling_price) }}</span>
        </template>

        <!-- Cost Column -->
        <template #cell-cost_price="{ row }">
          <span class="text-sm text-gray-600 dark:text-gray-400">{{ formatPrice(row.cost_price) }}</span>
        </template>

        <!-- Quantity Column -->
        <template #cell-quantity="{ row }">
          <span
            :class="[
              'text-sm font-medium',
              isLowStock(row)
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-900 dark:text-white',
            ]"
          >
            {{ row.quantity }}
            <span
              v-if="isLowStock(row)"
              class="ml-1 inline-flex items-center"
              title="Low stock"
            >
              <svg class="w-3.5 h-3.5 text-red-500 dark:text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
              </svg>
            </span>
          </span>
        </template>

        <!-- Status Column -->
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" />
        </template>

        <!-- Actions -->
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <!-- View -->
            <button
              type="button"
              class="p-1.5 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="View"
              @click="viewProduct(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>

            <!-- Edit -->
            <button
              v-if="authStore.hasPermission('products:edit')"
              type="button"
              class="p-1.5 text-gray-500 hover:text-amber-600 dark:text-gray-400 dark:hover:text-amber-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Edit"
              @click="editProduct(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
            </button>

            <!-- Toggle Status -->
            <button
              v-if="authStore.hasPermission('products:edit')"
              type="button"
              :class="[
                'p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
                row.status === 'active'
                  ? 'text-gray-500 hover:text-amber-600 dark:text-gray-400 dark:hover:text-amber-400'
                  : 'text-gray-500 hover:text-green-600 dark:text-gray-400 dark:hover:text-green-400',
              ]"
              :title="row.status === 'active' ? 'Deactivate' : 'Activate'"
              @click="toggleStatus(row)"
            >
              <svg v-if="row.status === 'active'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25v13.5m-7.5-13.5v13.5" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
              </svg>
            </button>

            <!-- Delete -->
            <button
              v-if="authStore.hasPermission('products:delete')"
              type="button"
              class="p-1.5 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Delete"
              @click="confirmDelete(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
            </button>
          </div>
        </template>
      </DataTable>
    </div>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Product"
      :message="`Are you sure you want to delete '${selectedProduct?.name}'? This action cannot be undone.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
