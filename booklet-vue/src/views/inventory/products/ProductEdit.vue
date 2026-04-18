<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import { useToastStore } from '@/stores/toast'
import * as inventoryApi from '@/api/inventory'

const router = useRouter()
const route = useRoute()
const toastStore = useToastStore()

const loading = ref(false)
const fetchLoading = ref(true)
const errors = reactive({
  sku: '',
  name: '',
  selling_price: '',
  cost_price: '',
  quantity: '',
})

const form = reactive({
  sku: '',
  name: '',
  description: '',
  category_id: '',
  selling_price: '',
  cost_price: '',
  quantity: '',
  unit: '',
  low_stock_threshold: '',
  tax_rate: '',
  notes: '',
})

const categoryOptions = ref([])

const breadcrumbs = computed(() => [
  { text: 'Inventory', to: '/inventory' },
  { text: 'Products', to: '/inventory/products' },
  { text: form.name || 'Product', to: { name: 'ProductDetail', params: { id: route.params.id } } },
  { text: 'Edit' },
])

async function fetchProduct() {
  fetchLoading.value = true
  try {
    const { data } = await inventoryApi.getProduct(route.params.id)
    form.sku = data.sku || ''
    form.name = data.name || ''
    form.description = data.description || ''
    form.category_id = data.category_id ? String(data.category_id) : ''
    form.selling_price = data.selling_price ?? ''
    form.cost_price = data.cost_price ?? ''
    form.quantity = data.quantity ?? ''
    form.unit = data.unit || ''
    form.low_stock_threshold = data.low_stock_threshold ?? ''
    form.tax_rate = data.tax_rate ?? ''
    form.notes = data.notes || ''
  } catch (error) {
    console.error('Failed to fetch product:', error)
    toastStore.show('Failed to load product', 'error')
  } finally {
    fetchLoading.value = false
  }
}

async function fetchCategories() {
  try {
    const { data } = await inventoryApi.listCategories()
    const items = Array.isArray(data) ? data : data.items || data.categories || []
    categoryOptions.value = items.map((c) => ({
      value: String(c.id),
      label: c.name,
    }))
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

function validate() {
  let valid = true
  errors.sku = ''
  errors.name = ''
  errors.selling_price = ''
  errors.cost_price = ''
  errors.quantity = ''

  if (!form.sku.trim()) {
    errors.sku = 'SKU is required'
    valid = false
  }
  if (!form.name.trim()) {
    errors.name = 'Name is required'
    valid = false
  }
  if (!form.selling_price && form.selling_price !== 0) {
    errors.selling_price = 'Selling price is required'
    valid = false
  }
  if (!form.cost_price && form.cost_price !== 0) {
    errors.cost_price = 'Cost price is required'
    valid = false
  }
  if (!form.quantity && form.quantity !== 0) {
    errors.quantity = 'Quantity is required'
    valid = false
  }

  return valid
}

async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    await inventoryApi.updateProduct(route.params.id, form)
    toastStore.show('Product updated successfully')
    router.push({ name: 'ProductDetail', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update product:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to update product'
    toastStore.show(message, 'error')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push({ name: 'ProductDetail', params: { id: route.params.id } })
}

onMounted(async () => {
  await Promise.all([fetchProduct(), fetchCategories()])
})
</script>

<template>
  <div>
    <!-- Loading State -->
    <div v-if="fetchLoading" class="flex items-center justify-center py-20">
      <LoadingSpinner size="lg" text="Loading product..." />
    </div>

    <template v-else>
      <PageHeader title="Edit Product" :breadcrumbs="breadcrumbs" />

      <div class="max-w-3xl mx-auto">
        <form
          class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-6"
          @submit.prevent="handleSubmit"
        >
          <!-- SKU & Name -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TextInput
              v-model="form.sku"
              label="SKU"
              name="sku"
              placeholder="e.g., PROD-001"
              required
              :error="errors.sku"
            />
            <TextInput
              v-model="form.name"
              label="Product Name"
              name="name"
              placeholder="Enter product name"
              required
              :error="errors.name"
            />
          </div>

          <!-- Description -->
          <TextareaInput
            v-model="form.description"
            label="Description"
            name="description"
            placeholder="Enter product description..."
            :rows="3"
          />

          <!-- Category -->
          <SelectInput
            v-model="form.category_id"
            label="Category"
            name="category_id"
            placeholder="Select a category"
            :options="categoryOptions"
            help-text="Optional — select a product category"
          />

          <!-- Selling Price & Cost Price -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TextInput
              v-model="form.selling_price"
              label="Selling Price"
              name="selling_price"
              type="number"
              placeholder="0.00"
              required
              :error="errors.selling_price"
            />
            <TextInput
              v-model="form.cost_price"
              label="Cost Price"
              name="cost_price"
              type="number"
              placeholder="0.00"
              required
              :error="errors.cost_price"
            />
          </div>

          <!-- Quantity & Unit -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TextInput
              v-model="form.quantity"
              label="Quantity"
              name="quantity"
              type="number"
              placeholder="0"
              required
              :error="errors.quantity"
            />
            <TextInput
              v-model="form.unit"
              label="Unit"
              name="unit"
              placeholder="e.g., pcs, kg, liter"
            />
          </div>

          <!-- Low Stock Threshold & Tax Rate -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TextInput
              v-model="form.low_stock_threshold"
              label="Low Stock Threshold"
              name="low_stock_threshold"
              type="number"
              placeholder="0"
              help-text="Alert when stock falls below this number"
            />
            <TextInput
              v-model="form.tax_rate"
              label="Tax Rate (%)"
              name="tax_rate"
              type="number"
              placeholder="0"
              help-text="Tax percentage applied to this product"
            />
          </div>

          <!-- Notes -->
          <TextareaInput
            v-model="form.notes"
            label="Notes"
            name="notes"
            placeholder="Additional notes..."
            :rows="3"
          />

          <!-- Actions -->
          <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
              @click="handleCancel"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="loading"
              class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <LoadingSpinner v-if="loading" size="sm" />
              {{ loading ? 'Saving...' : 'Update Product' }}
            </button>
          </div>
        </form>
      </div>
    </template>
  </div>
</template>
