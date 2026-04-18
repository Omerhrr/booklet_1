<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import TextInput from '@/components/forms/TextInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import DateInput from '@/components/forms/DateInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import { getFixedAsset, updateFixedAsset, getFixedAssetCategories } from '@/api/fixedAssets'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(false)
const fetchLoading = ref(true)
const errors = ref({})

const form = ref({
  asset_name: '',
  category: '',
  purchase_date: '',
  cost: '',
  useful_life: '',
  salvage_value: '0',
  depreciation_method: 'straight_line',
  location: '',
  department: '',
  notes: '',
  account_id: '',
})

const categoryOptions = ref([])
const depreciationMethodOptions = [
  { value: 'straight_line', label: 'Straight-line' },
  { value: 'declining_balance', label: 'Declining Balance' },
]

async function fetchAsset() {
  fetchLoading.value = true
  try {
    const [assetRes, categoriesRes] = await Promise.all([
      getFixedAsset(route.params.id),
      getFixedAssetCategories(),
    ])

    const data = assetRes.data
    form.value = {
      asset_name: data.asset_name || data.name || '',
      category: data.category || data.category_id || '',
      purchase_date: data.purchase_date || '',
      cost: data.cost || '',
      useful_life: data.useful_life || '',
      salvage_value: data.salvage_value ?? '0',
      depreciation_method: data.depreciation_method || 'straight_line',
      location: data.location || '',
      department: data.department || '',
      notes: data.notes || '',
      account_id: data.account_id || '',
    }

    const categories = Array.isArray(categoriesRes.data)
      ? categoriesRes.data
      : categoriesRes.data.categories || []
    categoryOptions.value = categories.map(c => ({
      value: typeof c === 'string' ? c : c.id || c.name,
      label: typeof c === 'string' ? c : c.name || c.label,
    }))
  } catch (error) {
    console.error('Failed to fetch fixed asset:', error)
    toast.show('Failed to load fixed asset', 'error')
    router.push({ name: 'FixedAssetList' })
  } finally {
    fetchLoading.value = false
  }
}

function validate() {
  const newErrors = {}
  if (!form.value.asset_name?.trim()) newErrors.asset_name = 'Asset name is required'
  if (!form.value.purchase_date) newErrors.purchase_date = 'Purchase date is required'
  if (!form.value.cost || Number(form.value.cost) <= 0) newErrors.cost = 'Valid cost is required'
  if (!form.value.useful_life || Number(form.value.useful_life) <= 0) newErrors.useful_life = 'Valid useful life is required'
  if (form.value.salvage_value === '' || form.value.salvage_value === undefined) newErrors.salvage_value = 'Salvage value is required'
  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  loading.value = true
  try {
    const payload = {
      asset_name: form.value.asset_name,
      category: form.value.category,
      purchase_date: form.value.purchase_date,
      cost: Number(form.value.cost),
      useful_life: Number(form.value.useful_life),
      salvage_value: Number(form.value.salvage_value) || 0,
      depreciation_method: form.value.depreciation_method,
      location: form.value.location || null,
      department: form.value.department || null,
      notes: form.value.notes || null,
      account_id: form.value.account_id || null,
    }

    await updateFixedAsset(route.params.id, payload)
    toast.show('Fixed asset updated successfully', 'success')
    router.push({ name: 'FixedAssetDetail', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update fixed asset:', error)
    const message = error.response?.data?.message || error.response?.data?.detail || 'Failed to update fixed asset'
    toast.show(message, 'error')
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  router.push({ name: 'FixedAssetDetail', params: { id: route.params.id } })
}

onMounted(() => {
  fetchAsset()
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Edit Fixed Asset"
      :breadcrumbs="[
        { text: 'Accounting' },
        { text: 'Fixed Assets', to: { name: 'FixedAssetList' } },
        { text: 'Edit' }
      ]"
    />

    <LoadingSpinner v-if="fetchLoading" text="Loading fixed asset..." />

    <form v-else class="max-w-3xl mx-auto space-y-6" @submit.prevent="handleSubmit">
      <!-- Asset Details -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Asset Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TextInput
            v-model="form.asset_name"
            label="Asset Name"
            name="asset_name"
            placeholder="Enter asset name"
            :required="true"
            :error="errors.asset_name"
          />
          <SelectInput
            v-model="form.category"
            label="Category"
            name="category"
            :options="categoryOptions"
            placeholder="Select category"
          />
          <DateInput
            v-model="form.purchase_date"
            label="Purchase Date"
            name="purchase_date"
            :required="true"
            :error="errors.purchase_date"
          />
          <TextInput
            v-model="form.cost"
            label="Cost"
            name="cost"
            type="number"
            placeholder="0.00"
            :required="true"
            :error="errors.cost"
          />
          <TextInput
            v-model="form.useful_life"
            label="Useful Life (Years)"
            name="useful_life"
            type="number"
            placeholder="e.g., 5"
            :required="true"
            :error="errors.useful_life"
          />
          <TextInput
            v-model="form.salvage_value"
            label="Salvage Value"
            name="salvage_value"
            type="number"
            placeholder="0.00"
            :error="errors.salvage_value"
          />
          <SelectInput
            v-model="form.depreciation_method"
            label="Depreciation Method"
            name="depreciation_method"
            :options="depreciationMethodOptions"
            placeholder="Select method"
          />
          <TextInput
            v-model="form.location"
            label="Location"
            name="location"
            placeholder="e.g., Headquarters"
          />
          <TextInput
            v-model="form.department"
            label="Department"
            name="department"
            placeholder="e.g., IT"
          />
        </div>
      </div>

      <!-- Notes -->
      <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <TextareaInput
          v-model="form.notes"
          label="Notes"
          name="notes"
          placeholder="Additional notes about the asset..."
          :rows="3"
        />
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-col-reverse sm:flex-row items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          class="w-full sm:w-auto px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          :disabled="loading"
          @click="handleCancel"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="loading"
          class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <LoadingSpinner v-if="loading" size="sm" />
          {{ loading ? 'Saving...' : 'Update Asset' }}
        </button>
      </div>
    </form>
  </div>
</template>
