<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { formatCurrency } from '@/utils/currency'
import * as inventoryApi from '@/api/inventory'

const router = useRouter()
const authStore = useAuthStore()
const toastStore = useToastStore()

const products = ref([])
const loading = ref(true)

const breadcrumbs = [
  { text: 'Inventory', to: '/inventory' },
  { text: 'Products', to: '/inventory/products' },
  { text: 'Low Stock' },
]

const columns = [
  { key: 'sku', label: 'SKU', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'quantity', label: 'Current Qty', sortable: true, class: 'text-right' },
  { key: 'low_stock_threshold', label: 'Threshold', sortable: true, class: 'text-right' },
  { key: 'status', label: 'Status', sortable: true },
]

async function fetchLowStockProducts() {
  loading.value = true
  try {
    const { data } = await inventoryApi.lowStock()
    products.value = Array.isArray(data) ? data : data.items || data.products || []
  } catch (error) {
    console.error('Failed to fetch low stock products:', error)
    toastStore.show('Failed to load low stock products', 'error')
  } finally {
    loading.value = false
  }
}

function viewProduct(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

function adjustStock(product) {
  router.push({ name: 'ProductDetail', params: { id: product.id } })
}

function formatPrice(amount) {
  return formatCurrency(amount, authStore.branchCurrency)
}

const lowStockCount = computed(() => products.value.length)

onMounted(fetchLowStockProducts)
</script>

<template>
  <div>
    <PageHeader title="Low Stock Products" :breadcrumbs="breadcrumbs">
      <template #actions>
        <!-- Warning Badge -->
        <div
          class="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-full dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-700"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
          </svg>
          {{ lowStockCount }} item{{ lowStockCount !== 1 ? 's' : '' }} below threshold
        </div>

        <router-link
          :to="{ name: 'ProductList' }"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
          </svg>
          All Products
        </router-link>
      </template>
    </PageHeader>

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && products.length === 0"
      title="All stock levels are healthy"
      message="No products are currently below their low stock thresholds."
      action-text="View All Products"
      action-route="/inventory/products"
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="products"
        :loading="loading"
        search-placeholder="Search low stock products..."
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

        <!-- Quantity Column -->
        <template #cell-quantity="{ row }">
          <span class="text-sm font-bold text-red-600 dark:text-red-400">
            {{ row.quantity }}
            <span v-if="row.unit" class="text-xs font-normal text-gray-500 dark:text-gray-400 ml-1">{{ row.unit }}</span>
          </span>
        </template>

        <!-- Threshold Column -->
        <template #cell-low_stock_threshold="{ row }">
          <span class="text-sm text-gray-600 dark:text-gray-400">
            {{ row.low_stock_threshold || 0 }}
            <span v-if="row.unit" class="text-xs text-gray-400 dark:text-gray-500 ml-1">{{ row.unit }}</span>
          </span>
        </template>

        <!-- Status Column -->
        <template #cell-status="{ row }">
          <StatusBadge :status="row.status" />
        </template>

        <!-- Actions -->
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <!-- Adjust Stock -->
            <button
              v-if="authStore.hasPermission('products:edit')"
              type="button"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-700 dark:hover:bg-blue-900/50 transition-colors"
              title="Adjust Stock"
              @click="adjustStock(row)"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Adjust Stock
            </button>

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
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>
