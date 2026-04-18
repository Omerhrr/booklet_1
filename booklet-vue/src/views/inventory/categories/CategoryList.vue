<script setup>
import { ref, reactive, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DataTable from '@/components/common/DataTable.vue'
import Modal from '@/components/common/Modal.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import * as inventoryApi from '@/api/inventory'

const authStore = useAuthStore()
const toastStore = useToastStore()

const categories = ref([])
const loading = ref(true)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDeleteDialog = ref(false)
const selectedCategory = ref(null)
const formLoading = ref(false)

const createForm = reactive({
  name: '',
  description: '',
})

const editForm = reactive({
  id: null,
  name: '',
  description: '',
})

const createErrors = reactive({
  name: '',
})

const editErrors = reactive({
  name: '',
})

const breadcrumbs = [
  { text: 'Inventory' },
  { text: 'Categories' },
]

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'description', label: 'Description' },
  { key: 'product_count', label: 'Product Count', sortable: true, class: 'text-right' },
]

async function fetchCategories() {
  loading.value = true
  try {
    const { data } = await inventoryApi.listCategories()
    categories.value = Array.isArray(data) ? data : data.items || data.categories || []
  } catch (error) {
    console.error('Failed to fetch categories:', error)
    toastStore.show('Failed to load categories', 'error')
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  createForm.name = ''
  createForm.description = ''
  createErrors.name = ''
  showCreateModal.value = true
}

function openEditModal(category) {
  editForm.id = category.id
  editForm.name = category.name || ''
  editForm.description = category.description || ''
  editErrors.name = ''
  selectedCategory.value = category
  showEditModal.value = true
}

function confirmDelete(category) {
  selectedCategory.value = category
  showDeleteDialog.value = true
}

function validateCreate() {
  let valid = true
  createErrors.name = ''
  if (!createForm.name.trim()) {
    createErrors.name = 'Name is required'
    valid = false
  }
  return valid
}

function validateEdit() {
  let valid = true
  editErrors.name = ''
  if (!editForm.name.trim()) {
    editErrors.name = 'Name is required'
    valid = false
  }
  return valid
}

async function handleCreate() {
  if (!validateCreate()) return
  formLoading.value = true
  try {
    await inventoryApi.createCategory({
      name: createForm.name,
      description: createForm.description,
    })
    toastStore.show('Category created successfully')
    showCreateModal.value = false
    await fetchCategories()
  } catch (error) {
    console.error('Failed to create category:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to create category'
    toastStore.show(message, 'error')
  } finally {
    formLoading.value = false
  }
}

async function handleEdit() {
  if (!validateEdit()) return
  formLoading.value = true
  try {
    await inventoryApi.updateCategory(editForm.id, {
      name: editForm.name,
      description: editForm.description,
    })
    toastStore.show('Category updated successfully')
    showEditModal.value = false
    await fetchCategories()
  } catch (error) {
    console.error('Failed to update category:', error)
    const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to update category'
    toastStore.show(message, 'error')
  } finally {
    formLoading.value = false
  }
}

async function handleDelete() {
  if (!selectedCategory.value) return
  formLoading.value = true
  try {
    await inventoryApi.deleteCategory(selectedCategory.value.id)
    toastStore.show('Category deleted successfully')
    await fetchCategories()
  } catch (error) {
    console.error('Failed to delete category:', error)
    toastStore.show('Failed to delete category', 'error')
  } finally {
    formLoading.value = false
    selectedCategory.value = null
  }
}

onMounted(fetchCategories)
</script>

<template>
  <div>
    <PageHeader title="Categories" :breadcrumbs="breadcrumbs">
      <template #actions>
        <button
          v-if="authStore.hasPermission('categories:create')"
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-900 transition-colors"
          @click="openCreateModal"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Category
        </button>
      </template>
    </PageHeader>

    <!-- Empty State -->
    <EmptyState
      v-if="!loading && categories.length === 0"
      title="No categories yet"
      message="Get started by creating your first category."
      :action-text="authStore.hasPermission('categories:create') ? 'Add Category' : ''"
      @action="openCreateModal"
    />

    <!-- Data Table -->
    <div v-else>
      <DataTable
        :columns="columns"
        :data="categories"
        :loading="loading"
        search-placeholder="Search categories..."
      >
        <!-- Name Column -->
        <template #cell-name="{ row }">
          <span class="text-sm font-medium text-gray-900 dark:text-white">{{ row.name }}</span>
        </template>

        <!-- Description Column -->
        <template #cell-description="{ row }">
          <span class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
            {{ row.description || '—' }}
          </span>
        </template>

        <!-- Product Count Column -->
        <template #cell-product_count="{ row }">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
            {{ row.product_count ?? 0 }} products
          </span>
        </template>

        <!-- Actions -->
        <template #actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <!-- Edit -->
            <button
              v-if="authStore.hasPermission('categories:edit')"
              type="button"
              class="p-1.5 text-gray-500 hover:text-amber-600 dark:text-gray-400 dark:hover:text-amber-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title="Edit"
              @click="openEditModal(row)"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
              </svg>
            </button>

            <!-- Delete -->
            <button
              v-if="authStore.hasPermission('categories:delete')"
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

    <!-- Create Category Modal -->
    <Modal v-model:show="showCreateModal" title="New Category" size="md">
      <form class="space-y-4" @submit.prevent="handleCreate">
        <TextInput
          v-model="createForm.name"
          label="Category Name"
          name="name"
          placeholder="Enter category name"
          required
          :error="createErrors.name"
        />
        <TextareaInput
          v-model="createForm.description"
          label="Description"
          name="description"
          placeholder="Optional description for this category..."
          :rows="3"
        />
      </form>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="showCreateModal = false"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="formLoading"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleCreate"
        >
          <LoadingSpinner v-if="formLoading" size="sm" />
          {{ formLoading ? 'Creating...' : 'Create Category' }}
        </button>
      </template>
    </Modal>

    <!-- Edit Category Modal -->
    <Modal v-model:show="showEditModal" title="Edit Category" size="md">
      <form class="space-y-4" @submit.prevent="handleEdit">
        <TextInput
          v-model="editForm.name"
          label="Category Name"
          name="name"
          placeholder="Enter category name"
          required
          :error="editErrors.name"
        />
        <TextareaInput
          v-model="editForm.description"
          label="Description"
          name="description"
          placeholder="Optional description for this category..."
          :rows="3"
        />
      </form>

      <template #footer>
        <button
          type="button"
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-600 transition-colors"
          @click="showEditModal = false"
        >
          Cancel
        </button>
        <button
          type="button"
          :disabled="formLoading"
          class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          @click="handleEdit"
        >
          <LoadingSpinner v-if="formLoading" size="sm" />
          {{ formLoading ? 'Saving...' : 'Update Category' }}
        </button>
      </template>
    </Modal>

    <!-- Delete Confirmation -->
    <ConfirmDialog
      v-model:show="showDeleteDialog"
      title="Delete Category"
      :message="`Are you sure you want to delete '${selectedCategory?.name}'? Products in this category will be uncategorized.`"
      confirm-text="Delete"
      type="danger"
      @confirm="handleDelete"
    />
  </div>
</template>
