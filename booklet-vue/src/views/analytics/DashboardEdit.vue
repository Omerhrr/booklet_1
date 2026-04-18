<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import TextInput from '@/components/forms/TextInput.vue'
import TextareaInput from '@/components/forms/TextareaInput.vue'
import SelectInput from '@/components/forms/SelectInput.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { getDashboard, updateDashboard, getAnalyses } from '@/api/analytics'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const saving = ref(false)
const analysesOptions = ref([])

const form = ref({
  name: '',
  description: '',
  analysisIds: [],
})

async function loadDashboard() {
  loading.value = true
  try {
    const { data } = await getDashboard(route.params.id)
    form.value = {
      name: data.name || '',
      description: data.description || '',
      analysisIds: (data.analyses || []).map(a => a.id),
    }
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  } finally {
    loading.value = false
  }
}

async function loadAnalyses() {
  try {
    const { data } = await getAnalyses()
    const items = Array.isArray(data) ? data : data.items || []
    analysesOptions.value = items.map(a => ({ value: a.id, label: a.name }))
  } catch (error) {
    console.error('Failed to load analyses:', error)
  }
}

async function handleSubmit() {
  if (!form.value.name) return
  saving.value = true
  try {
    await updateDashboard(route.params.id, {
      name: form.value.name,
      description: form.value.description,
      analysis_ids: form.value.analysisIds,
    })
    router.push({ name: 'DashboardView', params: { id: route.params.id } })
  } catch (error) {
    console.error('Failed to update dashboard:', error)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadAnalyses(), loadDashboard()])
})
</script>

<template>
  <div class="space-y-6">
    <PageHeader
      title="Edit Dashboard"
      :breadcrumbs="[
        { text: 'Analytics', to: { name: 'AnalyticsHub' } },
        { text: 'Dashboards', to: { name: 'DashboardList' } },
        { text: 'Edit' },
      ]"
    />

    <LoadingSpinner v-if="loading" size="lg" text="Loading..." />

    <template v-else>
      <div class="max-w-2xl mx-auto">
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-5">
          <TextInput v-model="form.name" label="Dashboard Name" name="name" required />
          <TextareaInput v-model="form.description" label="Description" name="description" />
          <SelectInput v-model="form.analysisIds" label="Analyses" name="analyses" :options="analysesOptions" placeholder="Select analyses..." multiple />

          <div v-if="form.analysisIds.length > 0" class="border-t border-gray-200 dark:border-gray-700 pt-4">
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Layout Preview</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div v-for="id in form.analysisIds" :key="id" class="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <div class="flex items-center gap-2 mb-2">
                  <div class="w-3 h-3 rounded-full bg-violet-400" />
                  <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {{ analysesOptions.find(a => a.value === id)?.label || 'Analysis' }}
                  </span>
                </div>
                <div class="h-20 rounded bg-gray-200 dark:bg-gray-700" />
              </div>
            </div>
          </div>

          <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button type="button" class="px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600 transition-colors" @click="router.back()">Cancel</button>
            <button type="button" class="px-4 py-2.5 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 disabled:opacity-50 transition-colors" :disabled="!form.name || saving" @click="handleSubmit">{{ saving ? 'Updating...' : 'Update Dashboard' }}</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
